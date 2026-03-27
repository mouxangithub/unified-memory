#!/usr/bin/env python3
"""
主动回忆 - Proactive Recall

核心概念：
- 不再等用户问，而是主动推送
- 基于：沉默、情绪、项目阶段等触发
- 模拟人类记忆的主动回忆机制

灵感来自人类记忆的"空闲时自动回忆"机制
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
STATE_FILE = MEMORY_DIR / "proactive_state.json"


class ProactiveRecall:
    """主动回忆引擎"""
    
    def __init__(self):
        self.state = self._load_state()
        self.triggers = self._init_triggers()
        self.last_recall = None
    
    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_interaction": None,
            "idle_seconds": 0,
            "recall_count": 0,
            "suggestions_made": [],
            "last_suggestion": None
        }
    
    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _init_triggers(self) -> List[Dict]:
        """初始化触发器"""
        return [
            {
                "id": "idle_reminder",
                "name": "空闲提醒",
                "condition": lambda s: s.get("idle_seconds", 0) > 300,  # 5分钟
                "priority": 1,
                "message": "你之前说..."
            },
            {
                "id": "project_phase",
                "name": "项目阶段提醒",
                "condition": lambda s: self._check_project_phase(),
                "priority": 2,
                "message": "关于项目进展..."
            },
            {
                "id": "decision_followup",
                "name": "决策跟进",
                "condition": lambda s: self._check_decision_followup(),
                "priority": 2,
                "message": "之前你决定..."
            },
            {
                "id": "preference_context",
                "name": "偏好上下文",
                "condition": lambda s: self._check_preference_context(),
                "priority": 3,
                "message": "根据你的偏好..."
            }
        ]
    
    def _check_project_phase(self) -> bool:
        """检查项目阶段"""
        # 简化版：检查是否有进行中的项目
        return len(self.state.get("suggestions_made", [])) % 10 == 0
    
    def _check_decision_followup(self) -> bool:
        """检查决策跟进"""
        return False  # 简化版
    
    def _check_preference_context(self) -> bool:
        """检查偏好上下文"""
        return False  # 简化版
    
    def update_interaction(self):
        """更新交互时间（用户有活动时调用）"""
        self.state["last_interaction"] = datetime.now().isoformat()
        self.state["idle_seconds"] = 0
        self._save_state()
    
    def tick(self, current_time: datetime = None):
        """心跳 tick（每次检查时调用）"""
        if current_time is None:
            current_time = datetime.now()
        
        # 计算空闲时间
        if self.state["last_interaction"]:
            last = datetime.fromisoformat(self.state["last_interaction"])
            self.state["idle_seconds"] = (current_time - last).total_seconds()
        
        self._save_state()
    
    def should_recall(self) -> bool:
        """是否应该主动回忆"""
        # 检查所有触发器
        for trigger in self.triggers:
            if trigger["condition"](self.state):
                return True
        return False
    
    def generate_recall(self, memories: List[Dict], context: str = "") -> Optional[str]:
        """
        生成主动回忆内容
        
        Returns:
            回忆消息，如果不应该回忆则返回 None
        """
        if not memories:
            return None
        
        # 检查触发器
        for trigger in self.triggers:
            if trigger["condition"](self.state):
                # 根据触发器类型生成不同内容
                if trigger["id"] == "idle_reminder":
                    return self._generate_idle_reminder(memories)
                elif trigger["id"] == "decision_followup":
                    return self._generate_decision_followup(memories)
                elif trigger["id"] == "preference_context":
                    return self._generate_preference_context(memories, context)
        
        return None
    
    def _generate_idle_reminder(self, memories: List[Dict]) -> str:
        """生成空闲提醒"""
        # 获取最近的重要记忆
        recent = sorted(
            [m for m in memories if m.get("category") in ["decision", "preference"]],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:3]
        
        if not recent:
            return None
        
        items = "\n".join([f"- {m['text'][:50]}..." for m in recent])
        return f"💭 你之前提到过：\n{items}"
    
    def _generate_decision_followup(self, memories: List[Dict]) -> str:
        """生成决策跟进"""
        decisions = [m for m in memories if m.get("category") == "decision"]
        if not decisions:
            return None
        
        latest = decisions[0]
        return f"📋 你之前决定：{latest.get('text', '')[:100]}..."
    
    def _generate_preference_context(self, memories: List[Dict], context: str) -> str:
        """生成偏好上下文"""
        prefs = [m for m in memories if m.get("category") == "preference"]
        if not prefs:
            return None
        
        pref_texts = [p.get("text", "")[:50] for p in prefs[:3]]
        return f"⚙️ 你的偏好：{'，'.join(pref_texts)}"
    
    def recall_and_mark(self, message: str):
        """记录已发送的回忆"""
        self.state["suggestions_made"].append({
            "message": message,
            "time": datetime.now().isoformat()
        })
        self.state["recall_count"] += 1
        self.last_recall = message
        self._save_state()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "idle_seconds": self.state["idle_seconds"],
            "recall_count": self.state["recall_count"],
            "last_recall": self.last_recall,
            "should_recall": self.should_recall()
        }


# 全局实例
_recall = None

def get_proactive_recall() -> ProactiveRecall:
    global _recall
    if _recall is None:
        _recall = ProactiveRecall()
    return _recall


def check_and_recall(memories: List[Dict], context: str = "") -> Optional[str]:
    """
    检查是否应该主动回忆
    
    在 heartbeat 或空闲时调用
    """
    recall = get_proactive_recall()
    
    if recall.should_recall():
        message = recall.generate_recall(memories, context)
        if message:
            recall.recall_and_mark(message)
            return message
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("主动回忆测试")
    print("=" * 60)
    
    recall = ProactiveRecall()
    
    # 模拟：空闲 6 分钟
    recall.state["idle_seconds"] = 360
    recall.state["last_interaction"] = (
        datetime.now() - timedelta(seconds=360)
    ).isoformat()
    
    # 测试数据
    memories = [
        {"text": "用户喜欢简洁的界面", "category": "preference", "timestamp": datetime.now().isoformat()},
        {"text": "决定采用微服务架构", "category": "decision", "timestamp": datetime.now().isoformat()},
        {"text": "Python 很好用", "category": "fact", "timestamp": datetime.now().isoformat()},
    ]
    
    print(f"\n📊 状态: {recall.get_status()}")
    print(f"   should_recall: {recall.should_recall()}")
    
    if recall.should_recall():
        message = recall.generate_recall(memories)
        print(f"\n💭 主动回忆:\n{message}")
        
        if message:
            recall.recall_and_mark(message)
            print(f"\n✅ 已记录")
    
    print("\n✅ 主动回忆测试完成")
