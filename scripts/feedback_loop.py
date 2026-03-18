#!/usr/bin/env python3
"""反馈循环 - 根据用户反馈调整记忆重要性"""
import re
import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
FEEDBACK_FILE = MEMORY_DIR / ".feedback.json"

FEEDBACK_BOOST = 0.15  # 有用记忆提升
FEEDBACK_PENALTY = 0.1  # 无用记忆降低

def record_feedback(memory_text, helpful=True):
    """记录用户对某个记忆的反馈"""
    feedback = {"timestamp": datetime.now().isoformat(), "text": memory_text, "helpful": helpful}
    
    data = []
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r") as f:
            data = json.load(f)
    
    data.append(feedback)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 反馈已记录: {'有用' if helpful else '无用'}")

def apply_feedback(dry_run=True):
    """应用反馈调整记忆重要性"""
    if not FEEDBACK_FILE.exists():
        print("⚠️ 暂无反馈记录")
        return
    
    with open(FEEDBACK_FILE, "r") as f:
        feedbacks = json.load(f)
    
    if not feedbacks:
        print("⚠️ 暂无反馈记录")
        return
    
    print(f"📊 处理 {len(feedbacks)} 条反馈...")
    
    updated = 0
    for md_file in MEMORY_DIR.glob("*.md"):
        if not md_file.name.startswith("2026-"):
            continue
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        original = content
        
        for fb in feedbacks:
            text = fb["text"][:50]  # 取前50字符匹配
            helpful = fb["helpful"]
            
            # 查找匹配的记忆
            for match in re.finditer(r'\[I=([0-9.]+)\]([^\n]+' + re.escape(text) + r'[^\n]*)', content):
                old_importance = float(match.group(1))
                if helpful:
                    new_importance = min(1.0, old_importance + FEEDBACK_BOOST)
                else:
                    new_importance = max(0.1, old_importance - FEEDBACK_PENALTY)
                
                content = content.replace(
                    match.group(0),
                    match.group(0).replace(f"[I={old_importance:.2f}]", f"[I={new_importance:.2f}]")
                )
                updated += 1
        
        if not dry_run and content != original:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)
    
    if not dry_run:
        # 清空反馈
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)
        print(f"✅ 已更新 {updated} 条记忆")
    else:
        print(f"🔍 预览: 将更新 {updated} 条记忆，使用 --execute 执行")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        apply_feedback(False)
    elif len(sys.argv) > 2 and sys.argv[1] == "record":
        helpful = sys.argv[3] != "false" if len(sys.argv) > 3 else True
        record_feedback(sys.argv[2], helpful)
    else:
        apply_feedback(True)
