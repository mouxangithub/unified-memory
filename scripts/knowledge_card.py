#!/usr/bin/env python3
"""
Knowledge Card - 知识卡片导出 v0.1.3

功能:
- 将记忆导出为可分享的知识卡片
- 支持多种格式 (Markdown, JSON, 飞书卡片)
- 精美模板设计
- 批量导出

Usage:
    knowledge_card.py export --memory-id <id> --format markdown
    knowledge_card.py export --memory-id <id> --format feishu
    knowledge_card.py batch --tags "项目,偏好" --format markdown
    knowledge_card.py templates
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CARDS_DIR = MEMORY_DIR / "cards"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False


class KnowledgeCard:
    """知识卡片导出"""
    
    def __init__(self):
        self.memories = self._load_memories()
    
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
    
    def _get_memory(self, memory_id: str) -> Optional[Dict]:
        """获取单个记忆"""
        for mem in self.memories:
            if mem.get("id") == memory_id:
                return mem
        return None
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期"""
        if not date_str:
            return "未知时间"
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    def to_markdown(self, memory: Dict) -> str:
        """转换为 Markdown 卡片"""
        text = memory.get("text", "")
        category = memory.get("category", "未分类")
        importance = memory.get("importance", 0.5)
        created_at = self._format_date(memory.get("created_at") or memory.get("timestamp", ""))
        tags = memory.get("tags", [])
        
        # 重要性星级
        stars = "⭐" * int(importance * 5)
        
        card = f"""### 📚 知识卡片

**类别**: {category}
**重要性**: {stars}
**时间**: {created_at}
**标签**: {', '.join(tags) if tags else '无'}

---

{text}

---

> ID: `{memory.get('id', 'N/A')}`
> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return card
    
    def to_json(self, memory: Dict) -> str:
        """转换为 JSON 卡片"""
        card = {
            "id": memory.get("id"),
            "text": memory.get("text"),
            "category": memory.get("category"),
            "importance": memory.get("importance"),
            "created_at": memory.get("created_at") or memory.get("timestamp"),
            "tags": memory.get("tags", []),
            "exported_at": datetime.now().isoformat()
        }
        
        return json.dumps(card, ensure_ascii=False, indent=2)
    
    def to_feishu(self, memory: Dict) -> Dict:
        """转换为飞书卡片 JSON"""
        text = memory.get("text", "")
        category = memory.get("category", "未分类")
        importance = memory.get("importance", 0.5)
        created_at = self._format_date(memory.get("created_at") or memory.get("timestamp", ""))
        
        # 截断文本
        if len(text) > 200:
            text = text[:200] + "..."
        
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📚 {category}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": text
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**重要性:** {'⭐' * int(importance * 5)}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**时间:** {created_at}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**ID:** `{memory.get('id', 'N/A')[:16]}...`"
                    }
                }
            ]
        }
        
        return card
    
    def to_text(self, memory: Dict) -> str:
        """转换为纯文本卡片"""
        text = memory.get("text", "")
        category = memory.get("category", "未分类")
        
        card = f"""{'='*50}
【{category}】
{'='*50}

{text}

{'='*50}
ID: {memory.get('id', 'N/A')}
时间: {self._format_date(memory.get('created_at') or memory.get('timestamp', ''))}
{'='*50}"""
        
        return card
    
    def export(self, memory_id: str, format: str = "markdown", output: str = None) -> Dict:
        """导出单个记忆"""
        memory = self._get_memory(memory_id)
        
        if not memory:
            return {"error": "Memory not found"}
        
        # 转换格式
        converters = {
            "markdown": self.to_markdown,
            "json": self.to_json,
            "feishu": self.to_feishu,
            "text": self.to_text
        }
        
        converter = converters.get(format, self.to_markdown)
        content = converter(memory)
        
        # 保存文件
        if output:
            output_path = Path(output)
        else:
            CARDS_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{memory_id[:8]}.{format}"
            if format == "feishu":
                filename = f"{memory_id[:8]}.json"
            output_path = CARDS_DIR / filename
        
        if format == "feishu":
            output_path.write_text(json.dumps(content, ensure_ascii=False, indent=2))
        else:
            output_path.write_text(content)
        
        return {
            "memory_id": memory_id,
            "format": format,
            "saved": str(output_path),
            "preview": content[:200] + "..." if isinstance(content, str) else "飞书卡片 JSON"
        }
    
    def batch_export(self, tags: List[str] = None, format: str = "markdown", output_dir: str = None) -> Dict:
        """批量导出"""
        # 筛选记忆
        selected = self.memories
        
        if tags:
            selected = [
                m for m in selected
                if any(t in m.get("tags", []) for t in tags)
            ]
        
        if not selected:
            return {"error": "No memories found", "selected": 0}
        
        # 创建输出目录
        if output_dir:
            out_path = Path(output_dir)
        else:
            out_path = CARDS_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
        
        out_path.mkdir(parents=True, exist_ok=True)
        
        # 导出
        exported = []
        for mem in selected:
            memory_id = mem.get("id")
            if not memory_id:
                continue
            
            result = self.export(memory_id, format, str(out_path / f"{memory_id[:8]}.{format}"))
            if "error" not in result:
                exported.append(result)
        
        return {
            "total_memories": len(self.memories),
            "selected": len(selected),
            "exported": len(exported),
            "output_dir": str(out_path),
            "format": format
        }
    
    def list_templates(self):
        """列出可用模板"""
        templates = [
            {"name": "markdown", "desc": "Markdown 格式，适合文档"},
            {"name": "json", "desc": "JSON 格式，适合程序处理"},
            {"name": "feishu", "desc": "飞书卡片 JSON，适合飞书分享"},
            {"name": "text", "desc": "纯文本格式，简单直接"}
        ]
        
        print("📋 可用模板:")
        for t in templates:
            print(f"  {t['name']:10} - {t['desc']}")


def main():
    parser = argparse.ArgumentParser(description="Knowledge Card 0.1.3")
    parser.add_argument("command", choices=["export", "batch", "templates"])
    parser.add_argument("--memory-id", "-m", help="记忆 ID")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "feishu", "text"], default="markdown")
    parser.add_argument("--tags", "-t", help="逗号分隔的标签")
    parser.add_argument("--output", "-o", help="输出文件/目录")
    parser.add_argument("--count", "-c", type=int, default=10, help="批量导出数量")
    
    args = parser.parse_args()
    
    card = KnowledgeCard()
    
    if args.command == "export":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        
        result = card.export(args.memory_id, args.format, args.output)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ 导出成功:")
            print(f"  格式: {result['format']}")
            print(f"  保存: {result['saved']}")
    
    elif args.command == "batch":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        
        print(f"🔄 批量导出...")
        result = card.batch_export(tags, args.format, args.output)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ 批量导出完成:")
            print(f"  总记忆: {result['total_memories']}")
            print(f"  筛选: {result['selected']}")
            print(f"  导出: {result['exported']}")
            print(f"  目录: {result['output_dir']}")
    
    elif args.command == "templates":
        card.list_templates()


if __name__ == "__main__":
    main()
