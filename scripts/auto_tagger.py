#!/usr/bin/env python3
"""
Auto Tagger - 自动标签提取 v0.1.0

功能:
- NLP 自动提取标签
- 关键词识别
- 实体识别
- 主题聚类

Usage:
    auto_tagger.py tag --text "文本内容"
    auto_tagger.py batch  # 批量打标签
    auto_tagger.py stats  # 标签统计
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
TAGS_FILE = MEMORY_DIR / "tags" / "tags_index.json"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 预定义标签体系
TAG_CATEGORIES = {
    "项目": ["项目", "project", "工程"],
    "协作工具": ["飞书", "微信", "钉钉", "slack", "teams", "feishu"],
    "开发": ["开发", "代码", "git", "api", "编程", "debug", "测试"],
    "管理": ["管理", "任务", "计划", "进度", "里程碑"],
    "用户": ["用户", "客户", "体验", "需求"],
    "系统": ["系统", "配置", "部署", "架构", "记忆"],
    "数据": ["数据", "分析", "统计", "指标"],
    "时间": ["今天", "明天", "下周", "月度", "季度"],
    "优先级": ["紧急", "重要", "高优先", "低优先"],
    "状态": ["完成", "进行中", "待办", "暂停", "取消"],
}

# 关键词模式
KEYWORD_PATTERNS = {
    # 中文关键词
    "zh": [
        (r'(?:项目|Project)[：:]\s*([^\n]+)', "project"),
        (r'(?:任务|Task)[：:]\s*([^\n]+)', "task"),
        (r'(?:负责人|Owner)[：:]\s*([^\n]+)', "owner"),
        (r'(?:截止|Deadline)[：:]\s*([^\n]+)', "deadline"),
        (r'(?:优先级|Priority)[：:]\s*(高|中|低)', "priority"),
        (r'#(\w+)', "hashtag"),
    ],
    # 英文关键词
    "en": [
        (r'(?:Project)[::]\s*([^\n]+)', "project"),
        (r'(?:Task)[::]\s*([^\n]+)', "task"),
        (r'(?:Owner)[::]\s*([^\n]+)', "owner"),
        (r'(?:Deadline)[::]\s*([^\n]+)', "deadline"),
        (r'(?:Priority)[::]\s*(High|Medium|Low)', "priority"),
        (r'#(\w+)', "hashtag"),
    ]
}


class AutoTagger:
    """自动标签提取器"""
    
    def __init__(self):
        self.tags_index = self._load_tags_index()
        self.memories = self._load_memories()
    
    def _load_tags_index(self) -> Dict:
        """加载标签索引"""
        if TAGS_FILE.exists():
            try:
                return json.loads(TAGS_FILE.read_text())
            except:
                pass
        return {"tags": {}, "memories": {}}
    
    def _save_tags_index(self):
        """保存标签索引"""
        TAGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TAGS_FILE.write_text(json.dumps(self.tags_index, ensure_ascii=False, indent=2))
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        memories = []
        
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                
                if result:
                    count = len(result.get("id", []))
                    for i in range(count):
                        mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        memories.append(mem)
            except:
                pass
        
        return memories
    
    def extract_tags_by_rules(self, text: str) -> List[Tuple[str, str, float]]:
        """基于规则提取标签
        
        Returns:
            List of (tag, category, confidence)
        """
        tags = []
        text_lower = text.lower()
        
        # 1. 预定义标签匹配
        for category, keywords in TAG_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    tags.append((kw, category, 0.9))
        
        # 2. 正则模式匹配
        for lang, patterns in KEYWORD_PATTERNS.items():
            for pattern, tag_type in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    tag_value = match.strip()
                    if tag_value:
                        tags.append((f"{tag_type}:{tag_value}", tag_type, 0.8))
        
        # 3. 提取实体（人名、项目名等）
        # 简单规则：首字母大写或中文词组
        entities = re.findall(r'[\u4e00-\u9fa5]{2,4}(?:项目|系统|平台)', text)
        for entity in entities:
            tags.append((entity, "entity", 0.7))
        
        # 去重
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag[0] not in seen:
                seen.add(tag[0])
                unique_tags.append(tag)
        
        return unique_tags
    
    def extract_tags_by_llm(self, text: str) -> List[Tuple[str, str, float]]:
        """使用 LLM 提取标签"""
        if not HAS_REQUESTS:
            return []
        
        try:
            prompt = f"""分析以下文本，提取关键标签。返回 JSON 数组格式：

文本：
{text}

标签类型：
- project: 项目名称
- tool: 工具名称  
- topic: 主题关键词
- entity: 实体（人名、组织名）
- status: 状态
- priority: 优先级

返回格式：
[
  {{"tag": "标签内容", "category": "类型", "confidence": 0.9}}
]

只返回 JSON，不要其他内容。"""

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "")
                
                # 提取 JSON
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                    return [
                        (t.get("tag"), t.get("category"), t.get("confidence", 0.7))
                        for t in tags
                    ]
        
        except Exception as e:
            print(f"⚠️ LLM 提取失败: {e}", file=sys.stderr)
        
        return []
    
    def tag(self, text: str, use_llm: bool = True) -> List[Dict]:
        """提取标签
        
        Returns:
            List of tag objects
        """
        # 规则提取
        tags = self.extract_tags_by_rules(text)
        
        # LLM 提取（可选）
        if use_llm and HAS_REQUESTS:
            llm_tags = self.extract_tags_by_llm(text)
            tags.extend(llm_tags)
        
        # 去重并排序
        seen = set()
        unique_tags = []
        for tag, category, confidence in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append({
                    "tag": tag,
                    "category": category,
                    "confidence": round(confidence, 2)
                })
        
        unique_tags.sort(key=lambda x: x["confidence"], reverse=True)
        return unique_tags[:10]  # 最多返回 10 个标签
    
    def tag_memory(self, memory_id: str) -> Dict:
        """为单个记忆打标签"""
        memory = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                memory = mem
                break
        
        if not memory:
            return {"error": "Memory not found"}
        
        text = memory.get("text", "")
        tags = self.tag(text)
        
        # 更新索引
        self.tags_index["memories"][memory_id] = {
            "tags": [t["tag"] for t in tags],
            "tagged_at": datetime.now().isoformat()
        }
        
        for tag_obj in tags:
            tag = tag_obj["tag"]
            if tag not in self.tags_index["tags"]:
                self.tags_index["tags"][tag] = {
                    "category": tag_obj["category"],
                    "memories": [],
                    "count": 0
                }
            self.tags_index["tags"][tag]["memories"].append(memory_id)
            self.tags_index["tags"][tag]["count"] += 1
        
        self._save_tags_index()
        
        return {
            "memory_id": memory_id,
            "tags": tags,
            "saved": True
        }
    
    def batch_tag(self) -> Dict:
        """批量打标签"""
        tagged = 0
        total_tags = 0
        
        for memory in self.memories:
            memory_id = memory.get("id")
            if not memory_id:
                continue
            
            result = self.tag_memory(memory_id)
            if "tags" in result:
                tagged += 1
                total_tags += len(result["tags"])
        
        return {
            "tagged_memories": tagged,
            "total_tags": total_tags,
            "unique_tags": len(self.tags_index["tags"])
        }
    
    def stats(self) -> Dict:
        """标签统计"""
        tag_counts = Counter()
        category_counts = Counter()
        
        for tag, data in self.tags_index.get("tags", {}).items():
            count = data.get("count", 0)
            tag_counts[tag] = count
            category_counts[data.get("category", "unknown")] += count
        
        return {
            "total_unique_tags": len(self.tags_index.get("tags", {})),
            "total_tagged_memories": len(self.tags_index.get("memories", {})),
            "top_tags": tag_counts.most_common(10),
            "top_categories": category_counts.most_common(10)
        }
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """按标签搜索记忆"""
        tag_data = self.tags_index.get("tags", {}).get(tag)
        if not tag_data:
            return []
        
        memory_ids = tag_data.get("memories", [])
        results = []
        
        for mem in self.memories:
            if mem.get("id") in memory_ids:
                results.append(mem)
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Auto Tagger 0.1.0")
    parser.add_argument("command", choices=["tag", "batch", "stats", "search"])
    parser.add_argument("--text", "-t", help="文本内容")
    parser.add_argument("--memory-id", "-m", help="记忆 ID")
    parser.add_argument("--tag", "-g", help="标签搜索")
    parser.add_argument("--no-llm", action="store_true", help="禁用 LLM")
    
    args = parser.parse_args()
    
    tagger = AutoTagger()
    
    if args.command == "tag":
        if args.text:
            tags = tagger.tag(args.text, use_llm=not args.no_llm)
            print(f"📋 提取到 {len(tags)} 个标签:")
            for t in tags:
                print(f"  [{t['category']}] {t['tag']} (置信度: {t['confidence']})")
        
        elif args.memory_id:
            result = tagger.tag_memory(args.memory_id)
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"✅ 已为记忆 {args.memory_id} 打标签:")
                for t in result["tags"]:
                    print(f"  [{t['category']}] {t['tag']}")
        
        else:
            print("❌ 请指定 --text 或 --memory-id")
    
    elif args.command == "batch":
        print("🔄 批量打标签中...")
        result = tagger.batch_tag()
        print(f"✅ 完成:")
        print(f"  标记记忆: {result['tagged_memories']} 条")
        print(f"  总标签数: {result['total_tags']}")
        print(f"  唯一标签: {result['unique_tags']}")
    
    elif args.command == "stats":
        stats = tagger.stats()
        print(f"📊 标签统计:")
        print(f"  唯一标签: {stats['total_unique_tags']}")
        print(f"  已标记记忆: {stats['total_tagged_memories']}")
        print()
        print("热门标签:")
        for tag, count in stats['top_tags']:
            print(f"  {tag}: {count}")
    
    elif args.command == "search":
        if not args.tag:
            print("❌ 请指定 --tag")
            sys.exit(1)
        
        results = tagger.search_by_tag(args.tag)
        print(f"📋 找到 {len(results)} 条记忆:")
        for mem in results:
            text = mem.get("text", "")[:60]
            print(f"  - {text}...")


if __name__ == "__main__":
    main()
