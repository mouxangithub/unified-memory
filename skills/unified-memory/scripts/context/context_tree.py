#!/usr/bin/env python3
"""
Context Tree - 统一分层上下文管理系统

整合两个维度:
1. 记忆上下文 (Memory Context) - 来自 memory_context.py
   - qmd://, user:, project: 前缀的记忆分类
   - 层级索引 + 自动上下文扩展搜索
   
2. 项目上下文 (Project Context) - 来自 QMD 风格
   - .context/ 目录结构
   - current.md, decisions/, architecture.md
   - 里程碑 + 进度跟踪

架构:
  workspace/
    memory/
      context_tree.json    # 记忆上下文索引
    projects/
      <project_name>/
        .context/
          current.md       # 当前状态
          decisions/       # 决策日志
          architecture.md  # 架构文档
          summary.md       # 项目摘要
          memory_index.json # 该项目的记忆索引

Usage:
    # 记忆上下文
    ctx = UnifiedContextTree()
    ctx.add_memory("user:刘总", "mem_001", "喜欢深色主题")
    results = ctx.search_with_context("主题")
    
    # 项目上下文
    ctx.init_project("官网重构")
    ctx.update_progress("完成首页设计", 50)
    ctx.record_decision("选择配色", "使用深蓝色调")
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Literal

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
PROJECTS_DIR = WORKSPACE / "memory" / "projects"
CONTEXT_INDEX_FILE = MEMORY_DIR / "context_tree.json"


# ============================================================
# 第一层: 记忆上下文节点
# ============================================================

class MemoryContextNode:
    """记忆上下文节点"""
    
    def __init__(self, path: str, description: str = "", parent: str = ""):
        self.path = path
        self.description = description
        self.parent = parent
        self.children: List[str] = []
        self.memories: List[str] = []
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
    def from_dict(cls, data: Dict) -> "MemoryContextNode":
        node = cls(data.get("path", ""), data.get("description", ""), data.get("parent", ""))
        node.children = data.get("children", [])
        node.memories = data.get("memories", [])
        node.created = data.get("created", datetime.now().isoformat())
        node.updated = data.get("updated", datetime.now().isoformat())
        return node


# ============================================================
# 第二层: 项目上下文管理器
# ============================================================

class ProjectContext:
    """项目级上下文（QMD 风格 .context/ 目录）"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.context_dir = project_path / ".context"
        self.current_file = self.context_dir / "current.md"
        self.decisions_dir = self.context_dir / "decisions"
        self.architecture_file = self.context_dir / "architecture.md"
        self.summary_file = self.context_dir / "summary.md"
        self.memory_index_file = self.context_dir / "memory_index.json"
        
        # 确保目录存在
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(exist_ok=True)
    
    def _load_memory_index(self) -> Dict[str, List[str]]:
        """加载项目的记忆索引"""
        if self.memory_index_file.exists():
            try:
                return json.loads(self.memory_index_file.read_text())
            except:
                pass
        return {}
    
    def _save_memory_index(self, index: Dict[str, List[str]]):
        """保存记忆索引"""
        self.memory_index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    
    def init_project(self, name: str, description: str = ""):
        """初始化项目"""
        self.update_current(
            task="项目初始化",
            progress=0,
            notes=f"项目: {name}\n描述: {description}"
        )
        
        if not self.architecture_file.exists():
            self.architecture_file.write_text(f"""# {name} 架构

## 技术栈
- 待定

## 目录结构
- 待定

## 关键决策
- 待定
""")
        
        if not self.summary_file.exists():
            self.summary_file.write_text(f"""# {name} 项目摘要

## 项目目标
{description}

## 当前进度
0%

## 关键里程碑
- [ ] 项目启动

## 团队成员
- 待添加
""")
        
        # 初始化记忆索引
        self._save_memory_index({})
        return True
    
    def update_current(self, task: str, progress: int, notes: str = ""):
        """更新当前状态"""
        recent_decisions = self._get_recent_decisions(3)
        decision_lines = "\n".join([f"- [{d['time']}] {d['title']}" for d in recent_decisions]) or "- 暂无"
        
        content = f"""# 当前状态

> 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 当前任务
{task}

## 进度
{progress}%

## 备注
{notes}

## 最近决策
{decision_lines}
"""
        self.current_file.write_text(content)
    
    def record_decision(self, title: str, content: str, tags: List[str] = None):
        """记录决策"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title)[:30]
        filename = f"{timestamp}-{safe_title}.md"
        filepath = self.decisions_dir / filename
        
        tags_str = ", ".join(tags) if tags else ""
        filepath.write_text(f"""# {title}

> 时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> 标签: {tags_str}

## 决策内容

{content}

## 影响范围
- 待评估

## 替代方案
- 待记录
""")
        
        self._update_current_decisions(title)
        return filepath
    
    def add_memory_to_project(self, memory_id: str, memory_text: str = ""):
        """将记忆关联到项目"""
        index = self._load_memory_index()
        if memory_id not in index:
            index[memory_id] = {
                "added": datetime.now().isoformat(),
                "text": memory_text[:200] if memory_text else ""
            }
            self._save_memory_index(index)
    
    def get_project_memories(self) -> Dict:
        """获取项目中所有记忆"""
        return self._load_memory_index()
    
    def get_current(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.current_file.exists():
            return {"task": "未初始化", "progress": 0, "notes": ""}
        
        content = self.current_file.read_text()
        task = progress = notes = ""
        section = None
        
        for line in content.split("\n"):
            if "## 当前任务" in line: section = "task"
            elif "## 进度" in line: section = "progress"
            elif "## 备注" in line: section = "notes"
            elif line.startswith("## "): section = None
            elif section == "task" and line.strip(): task = line.strip()
            elif section == "progress" and line.strip():
                try: progress = int(line.strip().replace("%", ""))
                except: pass
            elif section == "notes" and line.strip(): notes += line + "\n"
        
        return {"task": task, "progress": progress, "notes": notes.strip()}
    
    def get_decisions(self, limit: int = 10) -> List[Dict]:
        """获取决策列表"""
        decisions = []
        for f in sorted(self.decisions_dir.glob("*.md"), reverse=True)[:limit]:
            lines = f.read_text().split("\n")
            title = lines[0].replace("# ", "")
            time = lines[2].replace("> 时间: ", "").strip() if len(lines) > 2 else ""
            decisions.append({"title": title, "time": time, "file": f.name})
        return decisions
    
    def _get_recent_decisions(self, limit: int = 3) -> List[Dict]:
        decisions = []
        for f in sorted(self.decisions_dir.glob("*.md"), reverse=True)[:limit]:
            lines = f.read_text().split("\n")
            title = lines[0].replace("# ", "")
            time = lines[2].replace("> 时间: ", "").strip() if len(lines) > 2 else ""
            decisions.append({"title": title, "time": time})
        return decisions
    
    def _update_current_decisions(self, title: str):
        if not self.current_file.exists(): return
        content = self.current_file.read_text()
        lines = content.split("\n")
        new_lines, in_decisions = [], False
        for line in lines:
            if "## 最近决策" in line:
                in_decisions = True
                new_lines.append(line)
                new_lines.append(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {title}")
            elif in_decisions and line.startswith("## "):
                in_decisions = False
                new_lines.append(line)
            elif not (in_decisions and "暂无" in line):
                new_lines.append(line)
        self.current_file.write_text("\n".join(new_lines))
    
    def export(self) -> str:
        """导出项目上下文"""
        current = self.get_current()
        output = f"""# 项目上下文

> 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 当前状态
- 任务: {current['task']}
- 进度: {current['progress']}%
- 备注: {current['notes']}

## 决策列表
"""
        for i, d in enumerate(self.get_decisions(20), 1):
            output += f"{i}. [{d['time']}] {d['title']}\n"
        if self.architecture_file.exists():
            output += f"\n## 架构\n\n{self.architecture_file.read_text()}"
        if self.summary_file.exists():
            output += f"\n## 摘要\n\n{self.summary_file.read_text()}"
        return output


# ============================================================
# 统一上下文管理器
# ============================================================

class UnifiedContextTree:
    """
    统一分层上下文管理
    
    Layer 1: 全局记忆上下文 (qmd://, user:, project:)
    Layer 2: 项目级上下文 (.context/ in project dir)
    """
    
    def __init__(self):
        self.memory_nodes: Dict[str, MemoryContextNode] = {}
        self.memory_index: Dict[str, str] = {}  # memory_id -> context_path
        self.current_project: Optional[Path] = None
        self._load_memory_context()
    
    # ---- 记忆上下文 (Layer 1) ----
    
    def _load_memory_context(self):
        """加载记忆上下文"""
        CONTEXT_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if CONTEXT_INDEX_FILE.exists():
            try:
                data = json.loads(CONTEXT_INDEX_FILE.read_text())
                self.memory_nodes = {
                    p: MemoryContextNode.from_dict(n) 
                    for p, n in data.get("nodes", {}).items()
                }
                self.memory_index = data.get("memory_index", {})
                # 恢复当前项目
                current_proj = data.get("current_project")
                if current_proj:
                    proj_path = Path(current_proj)
                    if proj_path.exists():
                        self.current_project = proj_path
                return
            except:
                pass
        
        self._create_default_memory_contexts()
    
    def _save_memory_context(self):
        data = {
            "nodes": {p: n.to_dict() for p, n in self.memory_nodes.items()},
            "memory_index": self.memory_index,
            "current_project": str(self.current_project) if self.current_project else None,
            "updated": datetime.now().isoformat()
        }
        CONTEXT_INDEX_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def _create_default_memory_contexts(self):
        """创建默认上下文"""
        defaults = [
            ("user:default", "默认用户", ""),
            ("project:default", "默认项目", ""),
            ("qmd://notes", "个人笔记", ""),
            ("qmd://meetings", "会议记录", ""),
            ("qmd://docs", "工作文档", ""),
            ("qmd://notes/projects", "项目笔记", "qmd://notes"),
            ("qmd://notes/ideas", "创意想法", "qmd://notes"),
        ]
        for path, desc, parent in defaults:
            self.add_memory_context(path, desc, parent, save=False)
        self._save_memory_context()
    
    def add_memory_context(self, path: str, description: str = "", parent: str = "", save: bool = True):
        """添加记忆上下文节点"""
        node = MemoryContextNode(path, description, parent)
        self.memory_nodes[path] = node
        if parent and parent in self.memory_nodes:
            if path not in self.memory_nodes[parent].children:
                self.memory_nodes[parent].children.append(path)
        if save:
            self._save_memory_context()
    
    def add_memory(self, context_path: str, memory_id: str, content: str = "", category: str = ""):
        """将记忆加入上下文"""
        if context_path not in self.memory_nodes:
            self.add_memory_context(context_path, f"Auto: {category}")
        
        node = self.memory_nodes[context_path]
        if memory_id not in node.memories:
            node.memories.append(memory_id)
            node.updated = datetime.now().isoformat()
        
        self.memory_index[memory_id] = context_path
        self._save_memory_context()
    
    def get_memory_context_chain(self, path: str) -> List[str]:
        """获取上下文链"""
        chain = []
        while path:
            if path in self.memory_nodes:
                chain.insert(0, path)
                path = self.memory_nodes[path].parent
            else:
                break
        return chain
    
    def get_context_description_chain(self, path: str) -> str:
        """获取描述链"""
        chain = self.get_memory_context_chain(path)
        descs = [self.memory_nodes[p].description for p in chain if p in self.memory_nodes and self.memory_nodes[p].description]
        return " > ".join(descs) if descs else path
    
    def find_best_context(self, query: str) -> str:
        """根据查询自动匹配最佳上下文"""
        q = query.lower()
        patterns = [
            (r"用户|偏好|习惯|喜欢", "user:"),
            (r"项目|进度|任务|开发", "project:"),
            (r"会议|纪要|meeting", "qmd://meetings"),
            (r"笔记|想法|idea", "qmd://notes"),
            (r"文档|资料|doc", "qmd://docs"),
        ]
        for pattern, prefix in patterns:
            if re.search(pattern, q):
                for path in self.memory_nodes:
                    if path.startswith(prefix):
                        return path
        return next(iter(self.memory_nodes.keys()), "user:default")
    
    def list_memory_contexts(self) -> List[Dict]:
        return [n.to_dict() for n in self.memory_nodes.values()]
    
    # ---- 项目上下文 (Layer 2) ----
    
    def init_project(self, name: str, description: str = "") -> ProjectContext:
        """初始化项目"""
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        project_path = PROJECTS_DIR / name
        project_path.mkdir(parents=True, exist_ok=True)
        
        ctx = ProjectContext(project_path)
        ctx.init_project(name, description)
        
        # 自动创建对应的记忆上下文
        project_memory_path = f"project:{name}"
        self.add_memory_context(project_memory_path, description, "project:default")
        
        self.current_project = project_path
        return ctx
    
    def open_project(self, name: str) -> Optional[ProjectContext]:
        """打开已有项目"""
        project_path = PROJECTS_DIR / name
        if not project_path.exists():
            return None
        
        ctx = ProjectContext(project_path)
        self.current_project = project_path
        self._save_memory_context()  # 持久化当前项目
        return ctx
    
    def get_current_project_context(self) -> Optional[ProjectContext]:
        """获取当前项目的上下文"""
        if self.current_project and self.current_project.exists():
            return ProjectContext(self.current_project)
        return None
    
    def list_projects(self) -> List[str]:
        """列出所有项目"""
        if not PROJECTS_DIR.exists():
            return []
        return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    
    # ---- 统一搜索 ----
    
    def search_with_context(self, query: str, limit: int = 5) -> List[Dict]:
        """带上下文增强的搜索"""
        # 查找最佳上下文
        best_ctx = self.find_best_context(query)
        
        return {
            "query": query,
            "best_context": best_ctx,
            "context_chain": self.get_memory_context_chain(best_ctx),
            "context_description": self.get_context_description_chain(best_ctx),
            "memory_index": self.memory_index,
        }
    
    # ---- CLI ----
    
    def cli(self, args=None):
        import argparse
        parser = argparse.ArgumentParser(description="Unified Context Tree")
        sub = parser.add_subparsers(dest="cmd")
        
        # Memory contexts
        sub.add_parser("list", help="列出所有记忆上下文")
        sub.add_parser("tree", help="显示上下文树")
        
        add_p = sub.add_parser("ctx-add", help="添加记忆上下文")
        add_p.add_argument("--path", required=True)
        add_p.add_argument("--desc", default="")
        add_p.add_argument("--parent", default="")
        
        # Projects
        init_p = sub.add_parser("project-init", help="初始化项目")
        init_p.add_argument("name")
        init_p.add_argument("--desc", default="")
        
        proj_p = sub.add_parser("project", help="项目操作")
        proj_p.add_argument("action", choices=["list", "open", "status", "export"])
        proj_p.add_argument("name", nargs="?")
        
        update_p = sub.add_parser("update", help="更新当前任务")
        update_p.add_argument("task")
        update_p.add_argument("--progress", type=int, default=0)
        update_p.add_argument("--notes", default="")
        
        dec_p = sub.add_parser("decision", help="记录决策")
        dec_p.add_argument("title")
        dec_p.add_argument("content")
        
        args = parser.parse_args(args)
        
        if args.cmd == "list":
            for ctx in self.list_memory_contexts():
                depth = len(ctx["path"].split("/")) - 1
                indent = "  " * depth
                print(f"{indent}- {ctx['path']}: {ctx['description']}")
        
        elif args.cmd == "tree":
            self._print_tree()
        
        elif args.cmd == "ctx-add":
            self.add_memory_context(args.path, args.desc, args.parent)
            print(f"✅ 添加: {args.path}")
        
        elif args.cmd == "project-init":
            ctx = self.init_project(args.name, args.desc)
            print(f"✅ 项目已初始化: {args.name}")
        
        elif args.cmd == "project":
            if args.action == "list":
                for p in self.list_projects():
                    print(f"  - {p}")
            elif args.action == "open":
                ctx = self.open_project(args.name)
                if ctx:
                    self.current_project = ctx.project_path
                    print(f"📂 已切换到项目: {args.name}")
                else:
                    print(f"❌ 项目不存在: {args.name}")
            elif args.action == "status":
                ctx = self.get_current_project_context()
                if ctx:
                    s = ctx.get_current()
                    print(f"📋 {s['task']} ({s['progress']}%)")
                else:
                    print("❌ 未打开任何项目")
            elif args.action == "export":
                ctx = self.get_current_project_context()
                if ctx:
                    print(ctx.export())
        
        elif args.cmd == "update":
            ctx = self.get_current_project_context()
            if ctx:
                ctx.update_current(args.task, args.progress, args.notes)
                print(f"✅ 已更新: {args.task} ({args.progress}%)")
            else:
                print("❌ 未打开任何项目")
        
        elif args.cmd == "decision":
            ctx = self.get_current_project_context()
            if ctx:
                ctx.record_decision(args.title, args.content)
                print(f"✅ 决策已记录: {args.title}")
            else:
                print("❌ 未打开任何项目")
        
        else:
            parser.print_help()
    
    def _print_tree(self, path: str = "user:default", indent: int = 0):
        node = self.memory_nodes.get(path)
        if not node:
            # 尝试 project:default
            node = self.memory_nodes.get("project:default")
            if not node:
                return
        prefix = "  " * indent + ("├─ " if indent > 0 else "")
        print(f"{prefix}{path}: {node.description} ({len(node.memories)} memories)")
        for child in sorted(node.children):
            self._print_tree(child, indent + 1)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    tree = UnifiedContextTree()
    tree.cli()
