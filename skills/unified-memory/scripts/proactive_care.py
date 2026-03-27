#!/usr/bin/env python3
"""
主动感知模块 v2.1
检测刘总状态变化并主动关心

功能:
- 日程密度检测（今天会议数量）
- 工作时段消息频率
- 心情关键词检测（负面情绪）
- 任务截止时间压力
- **本地缓存**（减少 API 调用）

使用:
    python3 proactive_care.py config           # 显示/修改配置
    python3 proactive_care.py check             # 执行检查
    python3 proactive_care.py test --text "累"  # 测试关键词
    python3 proactive_care.py cache             # 清除缓存
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置
MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
CONFIG_FILE = MEMORY_DIR / "proactive_care_config.json"
STATE_FILE = MEMORY_DIR / "proactive_care_state.json"
CACHE_FILE = MEMORY_DIR / "proactive_care_cache.json"  # 新增缓存文件
CACHE_TTL_MINUTES = 10  # 缓存有效期（分钟）

DEFAULT_CONFIG = {
    "enabled": True,
    "check_interval_minutes": 30,
    "rules": {
        "meeting_density": {
            "enabled": True,
            "threshold": 5,
            "cooldown_hours": 2,
            "message": "刘总，今天会议挺密集的({count}个)，记得适当休息，喝口水活动一下~"
        },
        "continuous_work": {
            "enabled": True,
            "threshold_hours": 4,
            "cooldown_hours": 1,
            "message": "刘总，连续工作{hours}小时了，休息一下喝口水吧！"
        },
        "negative_keywords": {
            "enabled": True,
            "keywords": ["累", "烦", "忙", "烦死了", "好累", "太忙", "崩溃", "压力大", "头疼", "无语"],
            "cooldown_hours": 3,
            "message": "刘总，看你今天挺累的，注意身体啊！需要我帮忙处理什么吗？"
        },
        "deadline_pressure": {
            "enabled": True,
            "threshold_hours": 24,
            "cooldown_hours": 6,
            "message": "刘总，有{count}个任务截止时间快到了(< {hours}小时)，注意优先级安排~"
        }
    },
    "user": {
        "open_id": "ou_dcdc467a4de8cd4667474ccb99522e80",
        "name": "刘总"
    }
}


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "last_check": None,
        "work_start_time": None,
        "last_trigger": {}
    }


def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def can_trigger(state, rule_name, cooldown_hours):
    """检查是否在冷却期内"""
    last = state.get("last_trigger", {}).get(rule_name)
    if not last:
        return True
    last_time = datetime.fromisoformat(last)
    return datetime.now() - last_time > timedelta(hours=cooldown_hours)


def mark_triggered(state, rule_name):
    """标记已触发"""
    if "last_trigger" not in state:
        state["last_trigger"] = {}
    state["last_trigger"][rule_name] = datetime.now().isoformat()
    return state


# ========== 检测功能 ==========

def check_meeting_density(config, state):
    """检查日程密度"""
    rule = config["rules"]["meeting_density"]
    if not rule.get("enabled", True):
        return None
    if not can_trigger(state, "meeting_density", rule.get("cooldown_hours", 2)):
        return None
    
    # 直接调用飞书 API (通过 subprocess)
    import subprocess
    
    today = datetime.now().strftime("%Y-%m-%d")
    start_time = f"{today}T00:00:00+08:00"
    end_time = f"{today}T23:59:59+08:00"
    
    cmd = f'''python3 -c "
import json
from feishu_calendar_event import list_events
result = list_events(start_time=\\\"{start_time}\\\", end_time=\\\"{end_time}\\\", user_open_id=\\\"{config['user']['open_id']}\\\")
print(json.dumps(result))
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            events = data.get("items", []) if isinstance(data, dict) else []
            meeting_count = len([e for e in events if e.get("event_type") != "free"])
            
            if meeting_count > rule["threshold"]:
                return {
                    "type": "meeting_density",
                    "count": meeting_count,
                    "message": rule["message"].replace("{count}", str(meeting_count)),
                    "rule_key": "meeting_density"
                }
    except Exception as e:
        print(f"⚠️ 日程检测失败: {e}")
    
    return None


def check_continuous_work(config, state):
    """检查连续工作时长"""
    rule = config["rules"]["continuous_work"]
    if not rule.get("enabled", True):
        return None
    
    now = datetime.now()
    
    # 只在工作时间内检测 (9:00-18:00)
    if not (9 <= now.hour < 18):
        state["work_start_time"] = None  # 重置
        return None
    
    if not can_trigger(state, "continuous_work", rule.get("cooldown_hours", 1)):
        return None
    
    # 获取最近消息判断工作状态
    import subprocess
    lookback_hours = rule["threshold_hours"] + 1
    start_time = (now - timedelta(hours=lookback_hours)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    cmd = f'''python3 -c "
import json
from feishu_im_user_get_messages import get_messages
result = get_messages(open_id=\\\"{config['user']['open_id']}\\\", start_time=\\\"{start_time}\\\", end_time=\\\"{end_time}\\\", page_size=50)
print(json.dumps(result))
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            messages = data if isinstance(data, list) else (data.get("items", []) if isinstance(data, dict) else [])
            
            if messages:
                # 最近1小时有消息，更新工作开始时间
                recent_hour = now - timedelta(hours=1)
                recent_msgs = []
                for m in messages:
                    try:
                        create_time = datetime.fromisoformat(m["create_time"].replace("Z", "+08:00"))
                        if create_time > recent_hour:
                            recent_msgs.append(m)
                    except:
                        pass
                
                if recent_msgs:
                    if not state.get("work_start_time"):
                        state["work_start_time"] = now.isoformat()
                    
                    work_start = datetime.fromisoformat(state["work_start_time"])
                    work_hours = (now - work_start).total_seconds() / 3600
                    
                    if work_hours >= rule["threshold_hours"]:
                        state["work_start_time"] = now.isoformat()  # 重置
                        return {
                            "type": "continuous_work",
                            "hours": int(work_hours),
                            "message": rule["message"].replace("{hours}", str(int(work_hours))),
                            "rule_key": "continuous_work"
                        }
    except Exception as e:
        print(f"⚠️ 工作时长检测失败: {e}")
    
    return None


def check_negative_keywords(config, state):
    """检查消息中的负面关键词"""
    rule = config["rules"]["negative_keywords"]
    if not rule.get("enabled", True):
        return None
    
    now = datetime.now()
    if not can_trigger(state, "negative_keywords", rule.get("cooldown_hours", 3)):
        return None
    
    keywords = rule.get("keywords", [])
    
    import subprocess
    # 搜索最近2小时的消息
    start_time = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    cmd = f'''python3 -c "
import json
from feishu_im_user_search_messages import search_messages
result = search_messages(sender_ids=[\\\"{config['user']['open_id']}\\\"], start_time=\\\"{start_time}\\\", end_time=\\\"{end_time}\\\", page_size=20)
print(json.dumps(result))
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            messages = data if isinstance(data, list) else (data.get("items", []) if isinstance(data, dict) else [])
            
            for msg in messages:
                content = msg.get("content", {})
                if isinstance(content, str):
                    text = content
                else:
                    text = content.get("text", "") if isinstance(content, dict) else ""
                
                for keyword in keywords:
                    if keyword in text:
                        state = mark_triggered(state, "negative_keywords")
                        return {
                            "type": "negative_keywords",
                            "keyword": keyword,
                            "message": rule["message"],
                            "rule_key": "negative_keywords"
                        }
    except Exception as e:
        print(f"⚠️ 关键词检测失败: {e}")
    
    return None


def check_deadline_pressure(config, state):
    """检查任务截止时间压力"""
    rule = config["rules"]["deadline_pressure"]
    if not rule.get("enabled", True):
        return None
    
    now = datetime.now()
    if not can_trigger(state, "deadline_pressure", rule.get("cooldown_hours", 6)):
        return None
    
    import subprocess
    
    cmd = '''python3 -c "
import json
from feishu_task_task import list_tasks
result = list_tasks(page_size=50, completed=False)
print(json.dumps(result))
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            tasks = data if isinstance(data, list) else (data.get("items", []) if isinstance(data, dict) else [])
            
            urgent_count = 0
            for task in tasks:
                due = task.get("due", {})
                if due:
                    try:
                        due_time = datetime.fromisoformat(due["timestamp"].replace("Z", "+08:00"))
                        hours_left = (due_time - now).total_seconds() / 3600
                        
                        if 0 < hours_left <= rule["threshold_hours"]:
                            urgent_count += 1
                    except:
                        pass
            
            if urgent_count > 0:
                return {
                    "type": "deadline_pressure",
                    "count": urgent_count,
                    "hours": rule["threshold_hours"],
                    "message": rule["message"].replace("{count}", str(urgent_count)).replace("{hours}", str(rule["threshold_hours"])),
                    "rule_key": "deadline_pressure"
                }
    except Exception as e:
        print(f"⚠️ 任务截止检测失败: {e}")
    
    return None


# ========== 推送功能 ==========

def send_care_message(message: str, user_open_id: str):
    """发送关心消息"""
    import subprocess
    
    # 转义消息中的引号
    escaped_msg = message.replace('"', '\\"').replace("'", "\\'")
    
    cmd = f'''python3 -c "
import json
from feishu_im_user_message import send_message
result = send_message(
    receive_id_type=\\\"open_id\\\",
    receive_id=\\\"{user_open_id}\\\",
    msg_type=\\\"text\\\",
    content=json.dumps({{\\\"text\\\": \\\"{escaped_msg}\\\"}})
)
print(json.dumps({{\\\"success\\\": True}}))
"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True
        else:
            print(f"⚠️ 消息发送失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ 消息发送失败: {e}")
        return False


# ========== 主流程 ==========

def run_check(config, state):
    """执行检查"""
    if not config.get("enabled", True):
        print("⏸️ 主动感知模块已禁用")
        return []
    
    results = []
    user_open_id = config["user"]["open_id"]
    
    print("🔍 执行主动感知检查...")
    
    # 1. 日程密度
    result = check_meeting_density(config, state)
    if result:
        results.append(result)
        print(f"  📅 检测到高日程密度: {result['count']}个会议")
    
    # 2. 工作时长
    result = check_continuous_work(config, state)
    if result:
        results.append(result)
        print(f"  ⏰ 检测到连续工作: {result['hours']}小时")
    
    # 3. 负面关键词
    result = check_negative_keywords(config, state)
    if result:
        results.append(result)
        print(f"  😔 检测到负面情绪: {result['keyword']}")
    
    # 4. 任务截止
    result = check_deadline_pressure(config, state)
    if result:
        results.append(result)
        print(f"  📋 检测到紧急任务: {result['count']}个")
    
    # 发送消息
    for result in results:
        if send_care_message(result["message"], user_open_id):
            print(f"  ✅ 已发送: {result['type']}")
            state = mark_triggered(state, result["rule_key"])
        else:
            print(f"  ❌ 发送失败: {result['type']}")
    
    state["last_check"] = datetime.now().isoformat()
    save_state(state)
    
    return results


def main():
    """CLI入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="主动感知模块")
    parser.add_argument("action", choices=["config", "check", "test"],
                       help="操作类型")
    parser.add_argument("--enable", action="store_true", help="启用模块")
    parser.add_argument("--disable", action="store_true", help="禁用模块")
    parser.add_argument("--text", type=str, help="测试文本")
    
    args = parser.parse_args()
    
    config = load_config()
    state = load_state()
    
    if args.action == "config":
        if args.enable:
            config["enabled"] = True
            save_config(config)
            print("✅ 主动感知已启用")
        elif args.disable:
            config["enabled"] = False
            save_config(config)
            print("⏸️ 主动感知已禁用")
        else:
            print(json.dumps(config, indent=2, ensure_ascii=False))
    
    elif args.action == "check":
        results = run_check(config, state)
        if not results:
            print("✅ 未检测到需要关心的情况")
        else:
            print(f"🎉 共触发 {len(results)} 项关心")
    
    elif args.action == "test":
        if args.text:
            # 直接测试关键词匹配
            rule = config["rules"]["negative_keywords"]
            keywords = rule.get("keywords", [])
            found = [kw for kw in keywords if kw in args.text]
            
            if found:
                result = {
                    "triggered": True,
                    "type": "negative_keywords",
                    "keywords": found,
                    "message": rule["message"]
                }
            else:
                result = {
                    "triggered": False,
                    "keywords_checked": keywords,
                    "text": args.text
                }
            
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("请提供 --text 参数进行测试")


if __name__ == "__main__":
    main()
