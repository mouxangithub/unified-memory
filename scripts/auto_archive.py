#!/usr/bin/env python3
"""自动过期归档 - 将超过90天的记忆移到 archive"""
import shutil
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

ARCHIVE_DAYS = 90

def auto_archive(dry_run=False):
    cutoff = datetime.now() - timedelta(days=ARCHIVE_DAYS)
    
    archived = []
    for md_file in MEMORY_DIR.glob("*.md"):
        if not md_file.name.startswith("2026-"):
            continue
        try:
            date_str = md_file.stem  # 2026-03-18
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff:
                archived.append((md_file, file_date))
        except ValueError:
            continue
    
    if not archived:
        print(f"✅ 没有过期记忆（保留 {ARCHIVE_DAYS} 天）")
        return
    
    print(f"📦 发现 {len(archived)} 个过期文件")
    
    for f, date in archived:
        print(f"  {f.name} ({date.strftime('%Y-%m-%d')})")
        if not dry_run:
            shutil.move(str(f), ARCHIVE_DIR / f.name)
    
    if not dry_run:
        print(f"\n✅ 已归档到 {ARCHIVE_DIR}")
    else:
        print("\n🔍 预览模式，使用 --execute 执行")

if __name__ == "__main__":
    import sys
    auto_archive("--execute" in sys.argv)
