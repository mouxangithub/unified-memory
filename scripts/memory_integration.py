#!/usr/bin/env python3
"""
Memory Integration Hook - Agent 集成钩子 v0.1.7

功能:
- 对话开始时加载上下文
- 对话结束时自动存储
- 定期健康检查
- 自动提醒检测

集成到 OpenClaw Agent:
  1. 对话开始 → 加载相关上下文
  2. 对话进行 → 预测性加载
  3. 对话结束 → 提取并存储重要信息
  4. 定时任务 → 健康检查 + 提醒

Usage:
    python3 scripts/memory_integration.py session-start --context "用户询问项目进度"
    python3 scripts/memory_integration.py session-end --conversation "对话内容"
    python3 scripts/memory_integration.py heartbeat
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CACHE_DIR = MEMORY_DIR / "cache"
LOG_FILE = MEMORY_DIR / "integration.log"

# 敏感词
SENSITIVE_WORDS = [
    "password", "密码", "token", "密钥", "secret", "api_key",
    "信用卡", "银行卡", "身份证", "手机号", "验证码"
]


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")
    
    print(message)


def is_sensitive(text: str) -> bool:
    """检查敏感信息"""
    text_lower = text.lower()
    for word in SENSITIVE_WORDS:
        if word.lower() in text_lower:
            return True
    return False


def session_start(context: str = "", top_k: int = 10) -> Dict:
    """会话开始 - 加载上下文"""
    result = {
        "loaded": 0,
        "memories": [],
        "suggestions": [],
        "reminders": []
    }
    
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        memories = []
        
        for i in range(total):
            memories.append({
                "id": data["id"][i] if i < len(data.get("id", [])) else "",
                "text": data["text"][i] if i < len(data.get("text", [])) else "",
                "category": data["category"][i] if i < len(data.get("category", [])) else "",
                "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5
            })
        
        # 按重要性排序
        memories.sort(key=lambda x: x.get("importance", 0), reverse=True)
        
        # 如果有上下文，进行相关性过滤
        if context:
            context_lower = context.lower()
            scored = []
            for m in memories:
                score = 0
                text_lower = m["text"].lower()
                for word in context_lower.split():
                    if word in text_lower:
                        score += 2
                if score > 0:
                    m["_score"] = score
                    scored.append(m)
            
            if scored:
                scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
                memories = scored
        
        result["memories"] = memories[:top_k]
        result["loaded"] = len(result["memories"])
        
        # 生成建议
        if result["loaded"] > 0:
            categories = {}
            for m in result["memories"]:
                cat = m.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                top_cat = max(categories, key=categories.get)
                result["suggestions"].append(f"相关记忆: {top_cat} ({categories[top_cat]}条)")
        
        log(f"📥 加载上下文: {result['loaded']} 条记忆")
        
    except Exception as e:
        log(f"❌ 加载失败: {e}")
    
    return result


def session_end(conversation: str) -> Dict:
    """会话结束 - 自动存储"""
    result = {
        "extracted": 0,
        "stored": 0,
        "skipped": 0
    }
    
    if not conversation or len(conversation) < 10:
        log("⏭️ 对话过短，跳过存储")
        return result
    
    try:
        # 提取重要信息
        important_patterns = [
            (r"(喜欢|偏好|爱|习惯用)", "preference"),
            (r"(项目.*?名称|类型|进度)", "project"),
            (r"(决定|确定|选择|采用)", "decision"),
            (r"(会议|生日|截止|安排)", "event"),
            (r"(学到|学会|掌握|发现)", "learning"),
        ]
        
        import re
        extracted = []
        lines = conversation.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue
            
            # 跳过敏感信息
            if is_sensitive(line):
                continue
            
            # 模式匹配
            for pattern, category in important_patterns:
                if re.search(pattern, line):
                    content = line
                    if '：' in line:
                        content = line.split('：', 1)[1].strip()
                    elif ':' in line:
                        content = line.split(':', 1)[1].strip()
                    
                    if len(content) > 3:
                        extracted.append({"text": content, "category": category})
                    break
        
        result["extracted"] = len(extracted)
        
        # 存储
        import uuid
        import lancedb
        
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        # 获取向量（简化版，使用空向量）
        for item in extracted:
            try:
                table.add([{
                    "id": str(uuid.uuid4()),
                    "text": item["text"],
                    "category": item["category"],
                    "importance": 0.6,
                    "timestamp": datetime.now().isoformat(),
                    "vector": []
                }])
                result["stored"] += 1
            except:
                result["skipped"] += 1
        
        log(f"📤 存储记忆: {result['stored']}/{result['extracted']} 条")
        
    except Exception as e:
        log(f"❌ 存储失败: {e}")
    
    return result


def heartbeat() -> Dict:
    """心跳检查 - 健康检查 + 提醒检测"""
    result = {
        "health": {},
        "reminders": [],
        "actions": []
    }
    
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        
        # 简单健康检查
        result["health"] = {
            "total": total,
            "status": "healthy" if total > 0 else "empty"
        }
        
        # 检查提醒文件
        reminder_file = MEMORY_DIR / "reminders.json"
        if reminder_file.exists():
            with open(reminder_file) as f:
                reminders = json.load(f)
            
            now = datetime.now()
            from datetime import timedelta
            threshold = now + timedelta(hours=24)
            
            for r in reminders:
                try:
                    event_date = datetime.fromisoformat(r.get("date", ""))
                    if now < event_date <= threshold:
                        result["reminders"].append(r)
                except:
                    pass
        
        if result["reminders"]:
            result["actions"].append(f"有 {len(result['reminders'])} 个即将到来的提醒")
        
        log(f"💓 心跳: {total} 条记忆, {len(result['reminders'])} 个提醒")
        
    except Exception as e:
        result["health"]["error"] = str(e)
        log(f"❌ 心跳失败: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Memory Integration Hook 0.1.7")
    parser.add_argument("command", choices=["session-start", "session-end", "heartbeat"])
    parser.add_argument("--context", "-c", help="上下文内容")
    parser.add_argument("--conversation", "-C", help="对话内容")
    parser.add_argument("--top-k", "-k", type=int, default=10)
    
    args = parser.parse_args()
    
    if args.command == "session-start":
        result = session_start(args.context or "", args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "session-end":
        result = session_end(args.conversation or "")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "heartbeat":
        result = heartbeat()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
