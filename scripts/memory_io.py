#!/usr/bin/env python3
"""
Memory Import/Export - 数据导出导入 v0.0.7

功能:
- 导出记忆为多种格式 (JSON/CSV/Markdown)
- 导入记忆数据
- 重置记忆系统

Usage:
    memory_io.py export --format json --output backup.json
    memory_io.py export --format csv --output memories.csv
    memory_io.py export --format md --output memories.md
    memory_io.py import --file backup.json
    memory_io.py reset --confirm
"""

import argparse
import csv
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
BACKUP_DIR = MEMORY_DIR / "backups"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False


class MemoryIO:
    """记忆数据导入导出"""
    
    def __init__(self):
        self.memories = self._load_memories()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
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
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        
        return memories
    
    def export_json(self, output_path: Path) -> bool:
        """导出为 JSON"""
        try:
            export_data = {
                "version": "0.0.7",
                "exported_at": datetime.now().isoformat(),
                "total_memories": len(self.memories),
                "memories": self.memories
            }
            
            output_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2))
            print(f"✅ 已导出到 {output_path}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def export_csv(self, output_path: Path) -> bool:
        """导出为 CSV"""
        try:
            if not self.memories:
                print("⚠️ 没有记忆可导出")
                return False
            
            # 提取字段
            fields = ["id", "text", "category", "importance", "created_at"]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.memories)
            
            print(f"✅ 已导出到 {output_path}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def export_markdown(self, output_path: Path) -> bool:
        """导出为 Markdown"""
        try:
            lines = [
                "# Memory Export",
                "",
                f"**Version**: 0.0.7",
                f"**Exported**: {datetime.now().isoformat()}",
                f"**Total Memories**: {len(self.memories)}",
                "",
                "---",
                ""
            ]
            
            # 按分类分组
            from collections import defaultdict
            by_category = defaultdict(list)
            for mem in self.memories:
                by_category[mem.get("category", "other")].append(mem)
            
            for category, mems in by_category.items():
                lines.append(f"## {category.title()}")
                lines.append("")
                
                for mem in mems:
                    importance = mem.get("importance", 0)
                    stars = "⭐" * int(importance * 5)
                    text = mem.get("text", "")
                    created = mem.get("created_at", "unknown")
                    
                    lines.append(f"### {mem.get('id', 'unknown')[:8]}")
                    lines.append(f"- **Importance**: {importance:.2f} {stars}")
                    lines.append(f"- **Created**: {created}")
                    lines.append(f"- **Content**: {text}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
            
            output_path.write_text("\n".join(lines))
            print(f"✅ 已导出到 {output_path}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def import_data(self, file_path: Path, merge: bool = True) -> int:
        """导入记忆数据"""
        try:
            data = json.loads(file_path.read_text())
            
            if isinstance(data, list):
                memories = data
            elif isinstance(data, dict) and "memories" in data:
                memories = data["memories"]
            else:
                print("❌ 无效的数据格式")
                return 0
            
            # 检查是否需要合并
            if merge:
                existing_ids = {m.get("id") for m in self.memories}
                memories = [m for m in memories if m.get("id") not in existing_ids]
            
            # 存储到向量数据库
            if HAS_LANCEDB and memories:
                try:
                    db = lancedb.connect(str(VECTOR_DB_DIR))
                    table = db.open_table("memories")
                    table.add(memories)
                    print(f"✅ 已导入 {len(memories)} 条记忆")
                    return len(memories)
                except Exception as e:
                    print(f"❌ 导入失败: {e}")
                    return 0
            else:
                print("⚠️ 没有新记忆需要导入")
                return 0
        
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return 0
    
    def reset(self, confirm: bool = False) -> bool:
        """重置记忆系统"""
        if not confirm:
            print("⚠️ 这将删除所有记忆数据！")
            print("使用 --confirm 确认重置")
            return False
        
        try:
            # 备份当前数据
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = BACKUP_DIR / backup_name
            
            if VECTOR_DB_DIR.exists():
                shutil.copytree(VECTOR_DB_DIR, backup_path / "vector")
            
            # 清空向量数据库
            if VECTOR_DB_DIR.exists():
                shutil.rmtree(VECTOR_DB_DIR)
                VECTOR_DB_DIR.mkdir(parents=True)
            
            print(f"✅ 已重置记忆系统（备份在 {backup_path}）")
            return True
        
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False
    
    def create_backup(self) -> Path:
        """创建备份"""
        backup_name = f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = BACKUP_DIR / backup_name
        
        self.export_json(backup_path)
        return backup_path


def main():
    parser = argparse.ArgumentParser(description="Memory Import/Export 0.0.7")
    parser.add_argument("command", choices=["export", "import", "reset", "backup"])
    parser.add_argument("--format", "-f", choices=["json", "csv", "md"], default="json")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--file", "-i", help="输入文件路径")
    parser.add_argument("--confirm", action="store_true", help="确认重置")
    parser.add_argument("--merge", action="store_true", default=True, help="合并导入")
    
    args = parser.parse_args()
    
    io = MemoryIO()
    
    if args.command == "export":
        if not args.output:
            args.output = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
        
        output_path = Path(args.output)
        
        if args.format == "json":
            io.export_json(output_path)
        elif args.format == "csv":
            io.export_csv(output_path)
        elif args.format == "md":
            io.export_markdown(output_path)
    
    elif args.command == "import":
        if not args.file:
            print("❌ 请指定 --file")
            sys.exit(1)
        
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)
        
        io.import_data(file_path, merge=args.merge)
    
    elif args.command == "reset":
        io.reset(confirm=args.confirm)
    
    elif args.command == "backup":
        backup_path = io.create_backup()
        print(f"✅ 备份已创建: {backup_path}")


if __name__ == "__main__":
    main()
