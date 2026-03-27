#!/usr/bin/env python3
"""
Memory Reminder - 智能提醒系统 v0.1.6

功能:
- 检测时间敏感信息（生日、会议、截止日期）
- 主动提醒
- 支持 Cron 定时检查

Usage:
    python3 scripts/memory_reminder.py check      # 检查提醒
    python3 scripts/memory_reminder.py list       # 列出所有提醒
    python3 scripts/memory_reminder.py add "明天开会"  # 添加提醒
"""

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
REMINDER_FILE = MEMORY_DIR / "reminders.json"

# 时间模式
TIME_PATTERNS = [
    # 绝对日期
    (r"(\d{4}年\d{1,2}月\d{1,2}日)", "%Y年%m月%d日"),
    (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),
    (r"(\d{1,2}月\d{1,2}日)", "%m月%d日"),
    (r"(\d{1,2}/\d{1,2})", "%m/%d"),
    # 相对时间
    (r"明天", "tomorrow"),
    (r"后天", "day_after_tomorrow"),
    (r"下周([一二三四五六日天])", "next_week"),
    (r"(\d+)天后", "days_later"),
    (r"(\d+)小时后", "hours_later"),
    (r"(\d+)分钟后", "minutes_later"),
    # 生日
    (r"生日[是为]?(\d{1,2}月\d{1,2}日)", "birthday"),
    (r"(\d{1,2}月\d{1,2}日).*?生日", "birthday"),
    # 周期性
    (r"每周([一二三四五六日天])", "weekly"),
    (r"每天(\d{1,2}):?(\d{2})?", "daily"),
    (r"每月(\d{1,2})日", "monthly"),
]

# 事件类型
EVENT_TYPES = [
    "生日", "会议", "截止", "约会", "预约", "提醒", "计划", "安排", "面试", "课程"
]


def parse_date(text: str, now: datetime) -> Optional[datetime]:
    """解析日期文本"""
    text = text.strip()
    
    for pattern, fmt in TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                if fmt == "tomorrow":
                    return now + timedelta(days=1)
                elif fmt == "day_after_tomorrow":
                    return now + timedelta(days=2)
                elif fmt == "days_later":
                    days = int(match.group(1))
                    return now + timedelta(days=days)
                elif fmt == "hours_later":
                    hours = int(match.group(1))
                    return now + timedelta(hours=hours)
                elif fmt == "minutes_later":
                    minutes = int(match.group(1))
                    return now + timedelta(minutes=minutes)
                elif fmt == "next_week":
                    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
                    target = weekday_map.get(match.group(1), 0)
                    days_ahead = (target - now.weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    return now + timedelta(days=days_ahead)
                elif fmt == "birthday":
                    date_str = match.group(1)
                    month = int(re.search(r"(\d+)月", date_str).group(1))
                    day = int(re.search(r"(\d+)日", date_str).group(1))
                    result = datetime(now.year, month, day)
                    if result < now:
                        result = datetime(now.year + 1, month, day)
                    return result
                elif fmt.startswith("%"):
                    date_str = match.group(1)
                    return datetime.strptime(date_str, fmt)
            except:
                pass
    
    return None


def extract_events(text: str) -> List[Dict]:
    """从文本中提取事件"""
    events = []
    now = datetime.now()
    
    # 检测事件类型
    for event_type in EVENT_TYPES:
        if event_type in text:
            # 提取日期
            date = parse_date(text, now)
            if date:
                events.append({
                    "text": text,
                    "type": event_type,
                    "date": date.isoformat(),
                    "reminded": False
                })
    
    return events


def load_reminders() -> List[Dict]:
    """加载提醒列表"""
    if REMINDER_FILE.exists():
        with open(REMINDER_FILE, 'r') as f:
            return json.load(f)
    return []


def save_reminders(reminders: List[Dict]):
    """保存提醒列表"""
    REMINDER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REMINDER_FILE, 'w') as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)


def check_reminders(hours_ahead: int = 24) -> List[Dict]:
    """检查即将到来的提醒"""
    reminders = load_reminders()
    now = datetime.now()
    threshold = now + timedelta(hours=hours_ahead)
    
    due = []
    for r in reminders:
        try:
            event_date = datetime.fromisoformat(r.get("date", ""))
            if now < event_date <= threshold:
                due.append(r)
        except:
            pass
    
    return due


def add_reminder(text: str) -> Dict:
    """添加提醒"""
    now = datetime.now()
    date = parse_date(text, now)
    
    reminder = {
        "id": f"rem_{now.strftime('%Y%m%d%H%M%S')}",
        "text": text,
        "date": date.isoformat() if date else "",
        "created": now.isoformat(),
        "reminded": False
    }
    
    reminders = load_reminders()
    reminders.append(reminder)
    save_reminders(reminders)
    
    return reminder


def scan_memories_for_events() -> List[Dict]:
    """扫描记忆中的事件"""
    events = []
    
    try:
        import lancedb
        db = lancedb.connect(str(MEMORY_DIR / "vector"))
        table = db.open_table("memories")
        result = table.to_lance().to_table().to_pydict()
        
        count = len(result.get("id", []))
        for i in range(count):
            text = result["text"][i] if i < len(result.get("text", [])) else ""
            category = result["category"][i] if i < len(result.get("category", [])) else ""
            
            # 检查是否是事件类型
            if category in ["event", "decision"] or any(e in text for e in EVENT_TYPES):
                extracted = extract_events(text)
                events.extend(extracted)
    except Exception as e:
        print(f"扫描失败: {e}")
    
    return events


def main():
    parser = argparse.ArgumentParser(description="Memory Reminder 0.1.6")
    parser.add_argument("command", choices=["check", "list", "add", "scan"])
    parser.add_argument("text", nargs="?", help="提醒内容")
    parser.add_argument("--hours", "-H", type=int, default=24, help="提前小时数")
    
    args = parser.parse_args()
    
    if args.command == "check":
        due = check_reminders(args.hours)
        if due:
            print(f"⏰ 即将到来的提醒 ({len(due)} 条):")
            for r in due:
                date_str = datetime.fromisoformat(r["date"]).strftime("%Y-%m-%d %H:%M")
                print(f"   [{date_str}] {r['text']}")
        else:
            print("✅ 暂无即将到来的提醒")
    
    elif args.command == "list":
        reminders = load_reminders()
        print(f"📋 所有提醒 ({len(reminders)} 条):")
        for r in reminders:
            status = "✅" if r.get("reminded") else "⏳"
            date_str = r.get("date", "")[:10] if r.get("date") else "无日期"
            print(f"   {status} [{date_str}] {r['text'][:40]}")
    
    elif args.command == "add":
        if not args.text:
            print("请提供提醒内容")
            return
        reminder = add_reminder(args.text)
        print(f"✅ 已添加: {reminder['text']}")
        if reminder.get("date"):
            print(f"   时间: {reminder['date']}")
    
    elif args.command == "scan":
        print("🔍 扫描记忆中的事件...")
        events = scan_memories_for_events()
        print(f"发现 {len(events)} 个事件")
        
        for e in events[:5]:
            print(f"   [{e['type']}] {e['text'][:40]}...")


if __name__ == "__main__":
    main()
