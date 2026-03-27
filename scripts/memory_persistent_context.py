#!/usr/bin/env python3
"""
持久化上下文窗口 - Persistent Context Window

核心概念：
- 不再每次"重新理解"项目
- 维护一个持久化的上下文窗口
- 包含：压缩摘要 + 最近对话 + 当前工作区

灵感来自 MemGPT 的持久化上下文机制
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
CONTEXT_FILE = MEMORY_DIR / "persistent_context.json"
MAX_WINDOW_TOKENS = 128000  # 128k


class PersistentContext:
    """持久化上下文窗口"""
    
    def __init__(self, max_window: int = 128000):
        self.max_window = max_window
        self.context = self._load()
    
    def _load(self) -> Dict:
        """加载持久化上下文"""
        if CONTEXT_FILE.exists():
            try:
                with open(CONTEXT_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "summary": "",           # 压缩摘要
            "recent": [],            # 最近对话
            "working": {},           # 当前工作区
            "last_update": None,
            "version": 1.0
        }
    
    def _save(self):
        """保存持久化上下文"""
        self.context["last_update"] = datetime.now().isoformat()
        CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_FILE, "w") as f:
            json.dump(self.context, f, indent=2, ensure_ascii=False)
    
    def update_summary(self, new_info: str):
        """更新摘要（增量合并）"""
        if not self.context["summary"]:
            self.context["summary"] = new_info
        else:
            # 简单合并，实际应该用 LLM 压缩
            self.context["summary"] = f"{self.context['summary']}\n\n{new_info}"
        
        # 简单截断（实际应该用 token 计算）
        if len(self.context["summary"]) > self.max_window * 4:
            self.context["summary"] = self.context["summary"][-self.max_window * 2:]
        
        self._save()
    
    def add_recent(self, role: str, content: str):
        """添加最近对话"""
        self.context["recent"].append({
            "role": role,
            "content": content[:500],  # 截断长消息
            "time": datetime.now().isoformat()
        })
        
        # 只保留最近 20 条
        if len(self.context["recent"]) > 20:
            self.context["recent"] = self.context["recent"][-20:]
        
        self._save()
    
    def set_working(self, key: str, value: any):
        """设置当前工作区"""
        self.context["working"][key] = {
            "value": value,
            "time": datetime.now().isoformat()
        }
        self._save()
    
    def build_window(self) -> str:
        """构建持久化上下文窗口"""
        parts = []
        
        # 1. 压缩摘要
        if self.context["summary"]:
            parts.append(f"【项目摘要】\n{self.context['summary']}")
        
        # 2. 最近对话
        if self.context["recent"]:
            recent_text = "\n".join([
                f"{r['role']}: {r['content']}" 
                for r in self.context["recent"][-10:]
            ])
            parts.append(f"【最近对话】\n{recent_text}")
        
        # 3. 当前工作区
        if self.context["working"]:
            working_text = "\n".join([
                f"- {k}: {v['value']}" 
                for k, v in self.context["working"].items()
            ])
            parts.append(f"【当前工作】\n{working_text}")
        
        return "\n\n".join(parts)
    
    def compress(self, memories: List[Dict], target_size: int = 4000) -> str:
        """
        智能压缩记忆为摘要
        
        保留：
        1. 关键实体（人名、项目名、工具名）
        2. 关键关系（决定、使用、创建）
        3. 最新进展
        """
        if not memories:
            return ""
        
        # 按时间排序，最新的在前
        sorted_memories = sorted(
            memories, 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        # 提取关键信息
        key_decisions = []
        key_preferences = []
        key_facts = []
        
        for m in sorted_memories:
            cat = m.get("category", "")
            text = m.get("text", "")[:200]
            
            if cat == "decision":
                key_decisions.append(text)
            elif cat == "preference":
                key_preferences.append(text)
            elif cat == "fact":
                key_facts.append(text)
        
        # 构建摘要
        summary_parts = []
        
        if key_decisions:
            decisions = "\n".join([f"- {d}" for d in key_decisions[:5]])
            summary_parts.append(f"【关键决策】\n{decisions}")
        
        if key_preferences:
            prefs = "\n".join([f"- {p}" for p in key_preferences[:5]])
            summary_parts.append(f"【偏好设置】\n{prefs}")
        
        if key_facts:
            facts = "\n".join([f"- {f}" for f in key_facts[:10]])
            summary_parts.append(f"【重要事实】\n{facts}")
        
        result = "\n\n".join(summary_parts)
        
        # 截断到目标大小
        if len(result) > target_size * 4:
            result = result[:target_size * 4]
        
        return result
    
    def full_refresh(self, memories: List[Dict]):
        """全量刷新上下文"""
        summary = self.compress(memories)
        self.update_summary(summary)
        self._save()
        return summary


def get_persistent_context() -> PersistentContext:
    """获取持久化上下文实例"""
    return PersistentContext()


def build_context_window(memories: List[Dict] = None) -> str:
    """构建上下文窗口的便捷函数"""
    pc = get_persistent_context()
    
    # 如果有记忆，同步刷新摘要
    if memories:
        pc.full_refresh(memories)
    
    return pc.build_window()


if __name__ == "__main__":
    print("=" * 60)
    print("持久化上下文窗口测试")
    print("=" * 60)
    
    pc = PersistentContext()
    
    # 测试：添加一些内容
    pc.update_summary("用户喜欢简洁的界面，决定采用微服务架构")
    pc.add_recent("user", "我们开始做电商项目")
    pc.add_recent("assistant", "好的，我会帮你记住这个项目")
    pc.set_working("project", "电商网站")
    pc.set_working("stage", "需求分析")
    
    # 构建窗口
    window = pc.build_window()
    print(f"\n📝 上下文窗口:\n{window}")
    
    print(f"\n✅ 持久化上下文已保存到: {CONTEXT_FILE}")
