#!/usr/bin/env python3
"""
Memory Context Tree - 上下文树实现
借鉴 QMD 的 Context Tree 概念，实现记忆的层级上下文关系

核心概念:
- 每个 Context 可以有父 Context 和子 Context
- 搜索时自动展开上下文链，附加相关上下文到结果
- 支持任意层级的 Context 树

Context 格式:
  qmd://notes                    -> 个人笔记
  qmd://notes/projects           -> 项目相关笔记
  qmd://meetings                 -> 会议记录
  user:刘总                      -> 用户相关记忆
  project:官网重构               -> 项目相关记忆

Usage:
    from memory_context import ContextTree
    
    tree = ContextTree()
    
    # 添加 Context
    tree.add_context("qmd://notes", "个人笔记和想法")
    tree.add_context("qmd://notes/projects", "项目相关笔记", parent="qmd://notes")
    
    # 添加记忆到 Context
    tree.add_memory("qmd://notes", "mem_001", "用户喜欢深色主题", "preference")
    
    # 搜索时自动附加上下文
    results = tree.search_with_context("主题偏好", limit=5)
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
CONTEXT_FILE = MEMORY_DIR / "context_tree.json"


class ContextNode:
    """Context 节点"""
    
    def __init__(self, path: str, description: str = "", parent: str = ""):
        self.path = path
        self.description = description
        self.parent = parent
        self.children: List[str] = []
        self.memories: List[str] = []  # 记忆 ID 列表
        self.created = datetime.now().isoformat()
        self.updated = self.created
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "description": self.description,
            "parent": self.parent,
            "children": self.children,
            "memories": self.memories,
            "created": self.created,
            "updated": self.updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ContextNode":
        node = cls(data.get("path", ""), data.get("description", ""), data.get("parent", ""))
        node.children = data.get("children", [])
        node.memories = data.get("memories", [])
        node.created = data.get("created", datetime.now().isoformat())
        node.updated = data.get("updated", datetime.now().isoformat())
        return node


class ContextTree:
    """Context Tree 管理"""
    
    def __init__(self):
        self.nodes: Dict[str, ContextNode] = {}
        self.memory_index: Dict[str, str] = {}  # memory_id -> context_path
        self._load()
    
    def _load(self):
        """加载 Context Tree"""
        if not CONTEXT_FILE.exists():
            # 创建默认 Context
            self._create_defaults()
            return
        
        try:
            with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.nodes = {path: ContextNode.from_dict(node_data) for path, node_data in data.get("nodes", {}).items()}
            self.memory_index = data.get("memory_index", {})
        
        except Exception as e:
            print(f"⚠️ 加载 Context Tree 失败: {e}", file=sys.stderr)
            self._create_defaults()
    
    def _create_defaults(self):
        """创建默认 Context 结构"""
        # 用户相关
        self.add_context("user:default", "默认用户", save=False)
        
        # 项目相关
        self.add_context("project:default", "默认项目", save=False)
        
        # QMD 风格 Context
        self.add_context("qmd://notes", "个人笔记和想法", save=False)
        self.add_context("qmd://meetings", "会议记录和纪要", save=False)
        self.add_context("qmd://docs", "工作文档和资料", save=False)
        
        # 子 Context
        self.add_context("qmd://notes/projects", "项目相关笔记", parent="qmd://notes", save=False)
        self.add_context("qmd://notes/ideas", "创意和想法", parent="qmd://notes", save=False)
        
        self._save()
    
    def _save(self):
        """保存 Context Tree"""
        CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "nodes": {path: node.to_dict() for path, node in self.nodes.items()},
            "memory_index": self.memory_index,
            "updated": datetime.now().isoformat()
        }
        
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_context(self, path: str, description: str = "", parent: str = "", save: bool = True):
        """添加 Context"""
        
        # 创建节点
        node = ContextNode(path, description, parent)
        
        # 添加到树
        self.nodes[path] = node
        
        # 更新父节点的 children
        if parent and parent in self.nodes:
            if path not in self.nodes[parent].children:
                self.nodes[parent].children.append(path)
        
        if save:
            self._save()
    
    def get_context(self, path: str) -> Optional[Dict]:
        """获取 Context"""
        node = self.nodes.get(path)
        if node:
            return node.to_dict()
        return None
    
    def list_contexts(self) -> List[Dict]:
        """列出所有 Context"""
        return [node.to_dict() for node in self.nodes.values()]
    
    def search_contexts(self, query: str) -> List[Dict]:
        """搜索 Context"""
        results = []
        query_lower = query.lower()
        
        for node in self.nodes.values():
            if query_lower in node.path.lower() or query_lower in node.description.lower():
                results.append(node.to_dict())
        
        return results
    
    def add_memory(self, context_path: str, memory_id: str, content: str = "", category: str = ""):
        """添加记忆到 Context"""
        
        if context_path not in self.nodes:
            # 自动创建 Context
            self.add_context(context_path, f"Auto-created for {category}")
        
        node = self.nodes[context_path]
        
        if memory_id not in node.memories:
            node.memories.append(memory_id)
            node.updated = datetime.now().isoformat()
        
        # 更新索引
        self.memory_index[memory_id] = context_path
        
        self._save()
    
    def get_context_chain(self, path: str) -> List[str]:
        """
        获取上下文链（从根到当前节点）
        
        例如: qmd://notes/projects -> [qmd://, qmd://notes, qmd://notes/projects]
        """
        chain = []
        current = path
        
        while current:
            if current in self.nodes:
                chain.insert(0, current)
            current = self.nodes[current].parent if current in self.nodes else ""
        
        return chain
    
    def get_all_descendant_memories(self, path: str) -> List[str]:
        """获取所有子孙节点的记忆"""
        memories = []
        
        # 当前节点的记忆
        if path in self.nodes:
            memories.extend(self.nodes[path].memories)
        
        # 递归获取子孙节点
        if path in self.nodes:
            for child in self.nodes[path].children:
                memories.extend(self.get_all_descendant_memories(child))
        
        return memories
    
    def get_context_description_chain(self, path: str) -> str:
        """获取上下文描述链（用于增强搜索结果）"""
        chain = self.get_context_chain(path)
        
        descriptions = []
        for p in chain:
            if p in self.nodes:
                desc = self.nodes[p].description
                if desc:
                    descriptions.append(desc)
        
        return " > ".join(descriptions) if descriptions else path


# ============================================================
# Context-aware 搜索
# ============================================================

def search_with_context(query: str, mode: str = "hybrid", limit: int = 5, 
                        context_tree: ContextTree = None) -> List[Dict]:
    """
    带上下文的搜索
    
    1. 执行搜索
    2. 为每个结果添加上下文链
    """
    
    if context_tree is None:
        context_tree = ContextTree()
    
    # 执行搜索
    from memory_hyde import lex_search, vec_search, hyde_search
    
    if mode == "lex":
        results = lex_search(query, limit)
    elif mode == "vec":
        results = vec_search(query, limit)
    elif mode == "hyde":
        results = hyde_search(query, limit)
    else:
        results = lex_search(query, limit)
    
    # 为每个结果添加上下文
    for r in results:
        memory_id = r.get("id", "")
        
        # 查找记忆所属的 Context
        if memory_id in context_tree.memory_index:
            context_path = context_tree.memory_index[memory_id]
            
            # 添加上下文链
            r["context_path"] = context_path
            r["context_chain"] = context_tree.get_context_chain(context_path)
            r["context_description"] = context_tree.get_context_description_chain(context_path)
    
    return results


def find_best_context(query: str, context_tree: ContextTree = None) -> str:
    """
    根据查询自动匹配最佳 Context
    
    例如:
    - "用户偏好" -> user:default
    - "项目进度" -> project:default
    - "会议记录" -> qmd://meetings
    """
    
    if context_tree is None:
        context_tree = ContextTree()
    
    query_lower = query.lower()
    
    # 匹配规则
    patterns = {
        r"用户|偏好|习惯|喜欢": "user:",
        r"项目|进度|任务": "project:",
        r"会议|纪要": "qmd://meetings",
        r"笔记|想法|创意": "qmd://notes",
        r"文档|资料": "qmd://docs"
    }
    
    for pattern, prefix in patterns.items():
        if re.search(pattern, query_lower):
            # 找到匹配的 Context
            for path in context_tree.nodes:
                if path.startswith(prefix):
                    return path
    
    # 默认返回第一个
    return next(iter(context_tree.nodes.keys()), "user:default")


# ============================================================
# CLI 接口
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Context Tree")
    parser.add_argument("action", choices=["add", "get", "list", "search", "chain"])
    parser.add_argument("--path", help="Context path")
    parser.add_argument("--description", help="Context description")
    parser.add_argument("--parent", help="Parent context")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    tree = ContextTree()
    
    if args.action == "add":
        if not args.path:
            print("❌ 需要指定 --path", file=sys.stderr)
            return
        
        tree.add_context(args.path, args.description or "", args.parent or "")
        print(f"✅ 添加 Context: {args.path}")
    
    elif args.action == "get":
        if not args.path:
            print("❌ 需要指定 --path", file=sys.stderr)
            return
        
        ctx = tree.get_context(args.path)
        if ctx:
            if args.json:
                print(json.dumps(ctx, ensure_ascii=False, indent=2))
            else:
                print(f"📁 Context: {ctx['path']}")
                print(f"   描述: {ctx['description']}")
                print(f"   父节点: {ctx['parent']}")
                print(f"   子节点: {ctx['children']}")
                print(f"   记忆数: {len(ctx['memories'])}")
        else:
            print(f"❌ 未找到 Context: {args.path}")
    
    elif args.action == "list":
        contexts = tree.list_contexts()
        if args.json:
            print(json.dumps(contexts, ensure_ascii=False, indent=2))
        else:
            print(f"📁 Context 列表 ({len(contexts)} 个):\n")
            for ctx in contexts:
                indent = "  " * (len(ctx['path'].split('/')) - 1)
                print(f"{indent}- {ctx['path']}: {ctx['description']}")
    
    elif args.action == "search":
        if not args.path:
            print("❌ 需要指定搜索关键词 --path", file=sys.stderr)
            return
        
        results = tree.search_contexts(args.path)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results:
                print(f"- {r['path']}: {r['description']}")
    
    elif args.action == "chain":
        if not args.path:
            print("❌ 需要指定 --path", file=sys.stderr)
            return
        
        chain = tree.get_context_chain(args.path)
        desc = tree.get_context_description_chain(args.path)
        print(f"🔗 Context 链: {' -> '.join(chain)}")
        print(f"📝 描述链: {desc}")


if __name__ == "__main__":
    main()
