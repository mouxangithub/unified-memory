#!/usr/bin/env python3
"""
记忆预测模块 v1.0

功能:
- 基于时间模式预测需求
- 基于行为模式预测需求
- 主动推送预测结果

Usage:
    mem predict today        # 预测今日需求
    mem predict week         # 预测本周需求
    mem pattern analyze      # 分析模式
    mem pattern train        # 训练模型
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import re

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
ACCESS_FILE = MEMORY_DIR / "access_history.json"
PATTERN_FILE = MEMORY_DIR / "patterns.json"
PREDICTION_FILE = MEMORY_DIR / "predictions.json"
PREDICTION_CONFIG_FILE = MEMORY_DIR / "prediction_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "enabled": True,
    "min_confidence": 0.7,  # 最低置信度阈值
    "max_predictions": 5,   # 最多预测数量
    "push_enabled": True,   # 是否主动推送
    "patterns": {
        "time_based": True,
        "behavior_based": True,
        "project_based": True,
    },
    "quiet_hours": {
        "start": 23,  # 23:00
        "end": 8,     # 08:00
    }
}

# 时间模式定义
TIME_PATTERNS = {
    "weekday_morning": {
        "condition": lambda dt: dt.weekday() < 5 and 8 <= dt.hour < 12,
        "predictions": ["查看日程", "查看任务", "今日重点"],
        "confidence": 0.8
    },
    "weekday_afternoon": {
        "condition": lambda dt: dt.weekday() < 5 and 14 <= dt.hour < 18,
        "predictions": ["项目进度", "待办事项", "会议安排"],
        "confidence": 0.75
    },
    "weekday_evening": {
        "condition": lambda dt: dt.weekday() < 5 and 18 <= dt.hour < 22,
        "predictions": ["明日计划", "今日总结", "邮件处理"],
        "confidence": 0.7
    },
    "friday_afternoon": {
        "condition": lambda dt: dt.weekday() == 4 and 14 <= dt.hour < 18,
        "predictions": ["周末安排", "下周计划", "项目进度"],
        "confidence": 0.85
    },
    "weekend": {
        "condition": lambda dt: dt.weekday() >= 5,
        "predictions": ["减少打扰", "轻松话题"],
        "confidence": 0.6
    },
}


def load_config() -> Dict:
    """加载配置"""
    if PREDICTION_CONFIG_FILE.exists():
        return json.loads(PREDICTION_CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict):
    """保存配置"""
    PREDICTION_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    if MEMORIES_FILE.exists():
        return json.loads(MEMORIES_FILE.read_text())
    return []


def load_access_history() -> List[Dict]:
    """加载访问历史"""
    if ACCESS_FILE.exists():
        return json.loads(ACCESS_FILE.read_text())
    return []


def analyze_time_patterns(memories: List[Dict], access_history: List[Dict]) -> Dict:
    """分析时间模式"""
    patterns = {
        "hourly": defaultdict(int),
        "daily": defaultdict(int),
        "weekly": defaultdict(int),
        "monthly": defaultdict(int),
    }
    
    # 分析访问时间
    for entry in access_history:
        if isinstance(entry, dict):
            timestamp = entry.get("timestamp") or entry.get("create_time")
        else:
            continue
        
        if not timestamp:
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+08:00"))
            patterns["hourly"][dt.hour] += 1
            patterns["daily"][dt.weekday()] += 1
            patterns["weekly"][dt.isocalendar()[1]] += 1
        except:
            continue
    
    return patterns


def analyze_behavior_patterns(memories: List[Dict], access_history: List[Dict]) -> Dict:
    """分析行为模式"""
    patterns = {
        "search_keywords": defaultdict(int),
        "categories": defaultdict(int),
        "after_meeting": [],
        "after_message": [],
    }
    
    # 分析搜索关键词
    for entry in access_history:
        if isinstance(entry, dict):
            query = entry.get("query") or entry.get("keyword")
            if query:
                patterns["search_keywords"][query] += 1
        
        # 分析分类偏好
        if isinstance(entry, dict):
            category = entry.get("category")
            if category:
                patterns["categories"][category] += 1
    
    return patterns


def analyze_project_patterns(memories: List[Dict]) -> Dict:
    """分析项目模式"""
    projects = defaultdict(lambda: {
        "memories": [],
        "keywords": [],
        "last_access": None,
        "deadline": None,
    })
    
    # 提取项目相关记忆
    project_pattern = re.compile(r'项目[：:]\s*([^\s，。]+)|project[：:]\s*([^\s，。]+)', re.I)
    
    for mem in memories:
        text = mem.get("text", "")
        match = project_pattern.search(text)
        
        if match:
            project_name = match.group(1) or match.group(2)
            projects[project_name]["memories"].append(mem.get("id"))
            projects[project_name]["last_access"] = mem.get("last_accessed")
            
            # 提取截止日期
            deadline_pattern = re.compile(r'截止[日期]*[：:]\s*(\d{4}-\d{2}-\d{2})')
            deadline_match = deadline_pattern.search(text)
            if deadline_match:
                projects[project_name]["deadline"] = deadline_match.group(1)
    
    return dict(projects)


def get_time_based_predictions(now: datetime) -> List[Dict]:
    """获取基于时间的预测"""
    predictions = []
    
    for pattern_name, pattern in TIME_PATTERNS.items():
        if pattern["condition"](now):
            for pred in pattern["predictions"]:
                predictions.append({
                    "type": "time_based",
                    "pattern": pattern_name,
                    "prediction": pred,
                    "confidence": pattern["confidence"],
                    "reason": f"当前时间匹配模式: {pattern_name}"
                })
    
    return predictions


def get_behavior_based_predictions(access_history: List[Dict]) -> List[Dict]:
    """获取基于行为的预测"""
    predictions = []
    
    # 分析最近1小时的访问
    recent = []
    now = datetime.now()
    
    for entry in access_history:
        if isinstance(entry, dict):
            timestamp = entry.get("timestamp") or entry.get("create_time")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+08:00"))
                    if (now - dt).total_seconds() < 3600:
                        recent.append(entry)
                except:
                    pass
    
    # 如果最近频繁访问某个主题，预测需要更多信息
    topics = defaultdict(int)
    for entry in recent:
        if isinstance(entry, dict):
            category = entry.get("category")
            if category:
                topics[category] += 1
    
    for topic, count in topics.items():
        if count >= 2:
            predictions.append({
                "type": "behavior_based",
                "prediction": f"深入了解{topic}相关信息",
                "confidence": 0.7 + count * 0.05,
                "reason": f"最近{count}次访问{topic}相关记忆"
            })
    
    return predictions


def get_project_based_predictions(projects: Dict) -> List[Dict]:
    """获取基于项目的预测"""
    predictions = []
    now = datetime.now()
    
    for project_name, project_data in projects.items():
        deadline = project_data.get("deadline")
        
        if deadline:
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")
                days_left = (deadline_dt - now).days
                
                if 0 < days_left <= 3:
                    predictions.append({
                        "type": "project_based",
                        "prediction": f"项目「{project_name}」即将截止（{days_left}天后）",
                        "confidence": 0.9,
                        "reason": "项目截止时间临近"
                    })
                elif days_left <= 0:
                    predictions.append({
                        "type": "project_based",
                        "prediction": f"项目「{project_name}」已过期，需要更新",
                        "confidence": 0.95,
                        "reason": "项目已过截止日期"
                    })
            except:
                pass
    
    return predictions


def predict_today() -> Dict:
    """预测今日需求"""
    config = load_config()
    memories = load_memories()
    access_history = load_access_history()
    
    now = datetime.now()
    
    # 检查是否在静默时段
    quiet_start = config["quiet_hours"]["start"]
    quiet_end = config["quiet_hours"]["end"]
    
    if quiet_start <= now.hour or now.hour < quiet_end:
        return {
            "predictions": [{
                "type": "quiet_hours",
                "prediction": "静默时段，减少推送",
                "confidence": 1.0,
                "reason": f"当前时间 {now.hour}:00 在静默时段 ({quiet_start}:00-{quiet_end}:00)"
            }],
            "push": False
        }
    
    # 收集预测
    all_predictions = []
    
    # 1. 时间预测
    if config["patterns"]["time_based"]:
        all_predictions.extend(get_time_based_predictions(now))
    
    # 2. 行为预测
    if config["patterns"]["behavior_based"]:
        all_predictions.extend(get_behavior_based_predictions(access_history))
    
    # 3. 项目预测
    if config["patterns"]["project_based"]:
        projects = analyze_project_patterns(memories)
        all_predictions.extend(get_project_based_predictions(projects))
    
    # 过滤低置信度预测
    min_conf = config["min_confidence"]
    filtered = [p for p in all_predictions if p["confidence"] >= min_conf]
    
    # 按置信度排序，取前N个
    filtered.sort(key=lambda x: x["confidence"], reverse=True)
    filtered = filtered[:config["max_predictions"]]
    
    return {
        "predictions": filtered,
        "push": config["push_enabled"] and len(filtered) > 0,
        "generated_at": now.isoformat()
    }


def train_patterns():
    """训练模式（从历史数据中学习）"""
    memories = load_memories()
    access_history = load_access_history()
    
    print("🧠 训练预测模型...\n")
    
    # 分析时间模式
    time_patterns = analyze_time_patterns(memories, access_history)
    print(f"✅ 时间模式分析完成")
    print(f"   小时分布: {dict(time_patterns['hourly'])}")
    print(f"   星期分布: {dict(time_patterns['daily'])}")
    
    # 分析行为模式
    behavior_patterns = analyze_behavior_patterns(memories, access_history)
    print(f"\n✅ 行为模式分析完成")
    print(f"   热门搜索: {dict(behavior_patterns['search_keywords'])}")
    print(f"   分类偏好: {dict(behavior_patterns['categories'])}")
    
    # 分析项目模式
    project_patterns = analyze_project_patterns(memories)
    print(f"\n✅ 项目模式分析完成")
    print(f"   项目数量: {len(project_patterns)}")
    
    # 保存模式
    PATTERN_FILE.write_text(json.dumps({
        "time": time_patterns,
        "behavior": behavior_patterns,
        "projects": project_patterns,
        "trained_at": datetime.now().isoformat()
    }, indent=2, ensure_ascii=False))
    
    print(f"\n💾 模式已保存到 {PATTERN_FILE}")


def print_predictions(result: Dict):
    """打印预测结果"""
    print("🔮 今日需求预测\n")
    print("=" * 50)
    
    predictions = result.get("predictions", [])
    
    if not predictions:
        print("暂无预测")
        return
    
    for i, pred in enumerate(predictions, 1):
        conf_bar = "█" * int(pred["confidence"] * 10) + "░" * (10 - int(pred["confidence"] * 10))
        print(f"\n[{i}] {pred['prediction']}")
        print(f"    置信度: |{conf_bar}| {pred['confidence']:.0%}")
        print(f"    类型: {pred['type']}")
        print(f"    原因: {pred['reason']}")
    
    print(f"\n📱 推送状态: {'启用' if result.get('push') else '禁用'}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="记忆预测模块")
    parser.add_argument("command", choices=["today", "week", "train", "analyze", "config"])
    parser.add_argument("--config-show", action="store_true", help="显示配置")
    parser.add_argument("--enable-push", action="store_true", help="启用推送")
    parser.add_argument("--disable-push", action="store_true", help="禁用推送")
    
    args = parser.parse_args()
    
    if args.config_show or args.command == "config":
        config = load_config()
        print("🔮 预测配置\n")
        for k, v in config.items():
            print(f"   {k}: {v}")
        return
    
    if args.enable_push:
        config = load_config()
        config["push_enabled"] = True
        save_config(config)
        print("✅ 已启用预测推送")
        return
    
    if args.disable_push:
        config = load_config()
        config["push_enabled"] = False
        save_config(config)
        print("✅ 已禁用预测推送")
        return
    
    if args.command == "train":
        train_patterns()
    
    elif args.command == "analyze":
        train_patterns()  # analyze 和 train 相同
    
    elif args.command == "today":
        result = predict_today()
        print_predictions(result)
        
        # 保存预测
        PREDICTION_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "week":
        # 预测本周（简化版）
        print("🔮 本周需求预测\n")
        print("   功能开发中...")
        print("   建议: 先使用 `mem predict train` 训练模型")


if __name__ == "__main__":
    main()
