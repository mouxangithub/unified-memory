#!/usr/bin/env python3
"""
Memory Export - 记忆导出 v1.0

功能:
- 导出为 Markdown
- 导出为 HTML
- 导出为 JSON
- 导出为 CSV
- 批量导出

Usage:
    python3 scripts/memory_export.py markdown --output memories.md
    python3 scripts/memory_export.py html --output memories.html
    python3 scripts/memory_export.py json --output memories.json
    python3 scripts/memory_export.py csv --output memories.csv
"""

import argparse
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
EXPORTS_DIR = MEMORY_DIR / "exports"


class MemoryExporter:
    """记忆导出器"""
    
    def __init__(self):
        self.memories = self._load_memories()
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(len(data.get("id", []))):
                memories.append({
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "category": data.get("category", [""])[i] if i < len(data.get("category", [])) else "",
                    "importance": data.get("importance", [0.5])[i] if i < len(data.get("importance", [])) else 0.5,
                    "tags": data.get("tags", [[]])[i] if i < len(data.get("tags", [])) else [],
                    "timestamp": data.get("timestamp", [""])[i] if i < len(data.get("timestamp", [])) else ""
                })
            return memories
        except Exception as e:
            print(f"⚠️ 加载记忆失败: {e}")
            return []
    
    def export_markdown(self, output_path: str = None, 
                       category: str = None, min_importance: float = None) -> str:
        """导出为 Markdown"""
        if not output_path:
            output_path = str(EXPORTS_DIR / f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        # 过滤
        memories = self.memories
        if category:
            memories = [m for m in memories if m["category"] == category]
        if min_importance is not None:
            memories = [m for m in memories if m["importance"] >= min_importance]
        
        # 按类别分组
        by_category = {}
        for mem in memories:
            cat = mem["category"] or "未分类"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)
        
        # 生成 Markdown
        lines = [
            f"# 记忆导出",
            f"",
            f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 总记忆: {len(memories)} 条",
            f"",
            "---",
            ""
        ]
        
        # 目录
        lines.append("## 目录")
        lines.append("")
        for cat in sorted(by_category.keys()):
            count = len(by_category[cat])
            lines.append(f"- [{cat}](#{cat.lower().replace(' ', '-')}) ({count} 条)")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 内容
        for cat in sorted(by_category.keys()):
            lines.append(f"## {cat}")
            lines.append("")
            
            for mem in sorted(by_category[cat], key=lambda x: x["importance"], reverse=True):
                importance_stars = "⭐" * int(mem["importance"] * 5)
                tags_str = " ".join([f"`{t}`" for t in mem.get("tags", [])])
                
                lines.append(f"### {mem['text'][:50]}{'...' if len(mem['text']) > 50 else ''}")
                lines.append("")
                lines.append(f"- **重要性**: {importance_stars} ({mem['importance']:.2f})")
                if mem["timestamp"]:
                    lines.append(f"- **时间**: {mem['timestamp'][:19]}")
                if tags_str:
                    lines.append(f"- **标签**: {tags_str}")
                lines.append("")
                lines.append(f"{mem['text']}")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return output_path
    
    def export_html(self, output_path: str = None,
                   category: str = None, min_importance: float = None) -> str:
        """导出为 HTML"""
        if not output_path:
            output_path = str(EXPORTS_DIR / f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        # 过滤
        memories = self.memories
        if category:
            memories = [m for m in memories if m["category"] == category]
        if min_importance is not None:
            memories = [m for m in memories if m["importance"] >= min_importance]
        
        # 按类别分组
        by_category = {}
        for mem in memories:
            cat = mem["category"] or "未分类"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)
        
        # 生成 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>记忆导出 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f9f9f9;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .category {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .category h2 {{
            margin: 0 0 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .memory {{
            border-left: 3px solid #667eea;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .memory h3 {{
            margin: 0 0 10px;
            color: #333;
        }}
        .meta {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .importance {{
            color: #f5a623;
        }}
        .tags {{
            margin-top: 5px;
        }}
        .tag {{
            background: #e0e0e0;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 记忆导出</h1>
        <p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 总记忆: {len(memories)} 条</p>
    </div>
"""
        
        for cat in sorted(by_category.keys()):
            html += f"""
    <div class="category">
        <h2>{cat} ({len(by_category[cat])} 条)</h2>
"""
            
            for mem in sorted(by_category[cat], key=lambda x: x["importance"], reverse=True):
                importance_stars = "⭐" * int(mem["importance"] * 5)
                tags_html = " ".join([f'<span class="tag">{t}</span>' for t in mem.get("tags", [])])
                
                html += f"""
        <div class="memory">
            <h3>{mem['text'][:60]}{'...' if len(mem['text']) > 60 else ''}</h3>
            <div class="meta">
                <span class="importance">{importance_stars}</span>
                {mem['timestamp'][:19] if mem['timestamp'] else ''}
            </div>
            <p>{mem['text']}</p>
            {f'<div class="tags">{tags_html}</div>' if tags_html else ''}
        </div>
"""
            
            html += "    </div>\n"
        
        html += """
</body>
</html>"""
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def export_json(self, output_path: str = None,
                   category: str = None, min_importance: float = None) -> str:
        """导出为 JSON"""
        if not output_path:
            output_path = str(EXPORTS_DIR / f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # 过滤
        memories = self.memories
        if category:
            memories = [m for m in memories if m["category"] == category]
        if min_importance is not None:
            memories = [m for m in memories if m["importance"] >= min_importance]
        
        # 导出数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total": len(memories),
            "memories": memories
        }
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_csv(self, output_path: str = None,
                  category: str = None, min_importance: float = None) -> str:
        """导出为 CSV"""
        if not output_path:
            output_path = str(EXPORTS_DIR / f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        # 过滤
        memories = self.memories
        if category:
            memories = [m for m in memories if m["category"] == category]
        if min_importance is not None:
            memories = [m for m in memories if m["importance"] >= min_importance]
        
        # 写入 CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 表头
            writer.writerow(["ID", "Text", "Category", "Importance", "Tags", "Timestamp"])
            
            # 数据
            for mem in memories:
                writer.writerow([
                    mem["id"],
                    mem["text"],
                    mem["category"],
                    mem["importance"],
                    ",".join(mem.get("tags", [])),
                    mem["timestamp"]
                ])
        
        return output_path
    
    def export_all(self, output_dir: str = None) -> Dict[str, str]:
        """导出所有格式"""
        if not output_dir:
            output_dir = str(EXPORTS_DIR / datetime.now().strftime('%Y%m%d_%H%M%S'))
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        base_name = f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            "markdown": self.export_markdown(str(Path(output_dir) / f"{base_name}.md")),
            "html": self.export_html(str(Path(output_dir) / f"{base_name}.html")),
            "json": self.export_json(str(Path(output_dir) / f"{base_name}.json")),
            "csv": self.export_csv(str(Path(output_dir) / f"{base_name}.csv"))
        }
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Memory Export v1.0")
    parser.add_argument("command", choices=["markdown", "html", "json", "csv", "all"])
    parser.add_argument("--output", "-o", help="输出文件/目录")
    parser.add_argument("--category", "-c", help="类别过滤")
    parser.add_argument("--min-importance", "-i", type=float, help="最低重要性")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    exporter = MemoryExporter()
    
    if args.command == "markdown":
        path = exporter.export_markdown(args.output, args.category, args.min_importance)
        print(f"📝 Markdown 导出完成: {path}")
    
    elif args.command == "html":
        path = exporter.export_html(args.output, args.category, args.min_importance)
        print(f"🌐 HTML 导出完成: {path}")
    
    elif args.command == "json":
        path = exporter.export_json(args.output, args.category, args.min_importance)
        print(f"📦 JSON 导出完成: {path}")
    
    elif args.command == "csv":
        path = exporter.export_csv(args.output, args.category, args.min_importance)
        print(f"📊 CSV 导出完成: {path}")
    
    elif args.command == "all":
        results = exporter.export_all(args.output)
        print(f"📤 全部导出完成:")
        for fmt, path in results.items():
            print(f"   {fmt}: {path}")


if __name__ == "__main__":
    main()
