#!/usr/bin/env python3
"""
Agent Integration - Agent 生命周期集成

功能:
- Agent 启动时自动加载相关记忆
- 对话进行时自动提取记忆
- Agent 结束时自动归档优化

集成到 OpenClaw:
1. 在 AGENTS.md 中添加 hook
2. 在 HEARTBEAT 中自动维护
3. 在对话结束时运行归档
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 添加脚本目录
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入模块
from memory import MemorySystemV7
from auto_extractor import AutoExtractor
from memory_quality import MemoryQuality

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class AgentMemoryIntegration:
    """Agent 记忆集成"""
    
    def __init__(self):
        self.memory = MemorySystemV7()
        self.extractor = AutoExtractor()
        self.quality = MemoryQuality()
        self.session_file = MEMORY_DIR / "session_state.json"
        self._load_session()
    
    def _load_session(self):
        """加载会话状态"""
        self.session = {
            "started_at": None,
            "extracted_memories": 0,
            "queries": []
        }
        
        if self.session_file.exists():
            try:
                self.session = json.loads(self.session_file.read_text())
            except:
                pass
    
    def _save_session(self):
        """保存会话状态"""
        try:
            self.session_file.write_text(json.dumps(self.session, ensure_ascii=False, indent=2))
        except:
            pass
    
    def on_agent_start(self, context: str = "") -> Dict:
        """Agent 启动时调用"""
        self.session["started_at"] = datetime.now().isoformat()
        self._save_session()
        
        # 加载相关记忆
        relevant_memories = self.memory.get_context(context or "当前任务", max_memories=10)
        
        # 预测并预加载
        if context:
            prediction = self.memory.analyze(context)
        else:
            prediction = {"preloaded": 0}
        
        return {
            "status": "initialized",
            "loaded_memories": len(relevant_memories),
            "preloaded": prediction.get("preloaded", 0),
            "session_id": self.session["started_at"]
        }
    
    def on_message(self, user_message: str, agent_response: str) -> Dict:
        """对话进行时调用"""
        # 记录查询
        self.session["queries"].append({
            "query": user_message[:100],
            "timestamp": datetime.now().isoformat()
        })
        
        # 自动提取记忆
        conversation = f"用户: {user_message}\n助手: {agent_response}"
        extracted = self.extractor.extract_from_conversation(conversation, use_llm=False)
        
        # 只存储高价值记忆
        high_value = [m for m in extracted if m.get("importance", 0) > 0.6]
        
        if high_value:
            stored = self.extractor.auto_store(high_value)
            self.session["extracted_memories"] += stored
            self._save_session()
        
        return {
            "extracted": len(extracted),
            "stored": len(high_value)
        }
    
    def on_agent_end(self) -> Dict:
        """Agent 结束时调用"""
        # 运行维护任务
        from subprocess import run
        
        # 1. 验证记忆
        validation = self.memory.validate()
        
        # 2. 应用反馈调整
        feedback = self.memory.feedback()
        
        # 3. 生成质量报告
        report = self.quality.generate_report()
        
        # 4. 计算会话统计
        session_duration = None
        if self.session.get("started_at"):
            try:
                start = datetime.fromisoformat(self.session["started_at"])
                session_duration = (datetime.now() - start).total_seconds()
            except:
                pass
        
        result = {
            "status": "completed",
            "session_duration_seconds": session_duration,
            "extracted_memories": self.session["extracted_memories"],
            "total_queries": len(self.session["queries"]),
            "validation": validation,
            "feedback_adjustments": len(feedback) if feedback else 0,
            "quality_score": report["health_score"]
        }
        
        # 保存会话日志
        log_file = MEMORY_DIR / "sessions" / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps({
            "session": self.session,
            "result": result
        }, ensure_ascii=False, indent=2))
        
        # 重置会话
        self.session = {
            "started_at": None,
            "extracted_memories": 0,
            "queries": []
        }
        self._save_session()
        
        return result
    
    def get_relevant_context(self, query: str) -> List[Dict]:
        """获取相关上下文（供 Agent 调用）"""
        return self.memory.get_context(query, max_memories=5)
    
    def record_feedback(self, memory_id: str, outcome: str):
        """记录反馈"""
        from feedback_learner import FeedbackLearner
        learner = FeedbackLearner()
        learner.track(memory_id, outcome)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "session": self.session,
            "memory_stats": self.memory.stats()
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Memory Integration")
    parser.add_argument("command", choices=["start", "message", "end", "context", "feedback", "status"])
    parser.add_argument("--context", "-c", help="上下文")
    parser.add_argument("--user", help="用户消息")
    parser.add_argument("--agent", help="Agent 响应")
    parser.add_argument("--memory-id", help="记忆 ID")
    parser.add_argument("--outcome", choices=["helpful", "irrelevant", "wrong", "outdated"], help="反馈结果")
    
    args = parser.parse_args()
    
    integration = AgentMemoryIntegration()
    
    if args.command == "start":
        result = integration.on_agent_start(args.context or "")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "message":
        if not args.user or not args.agent:
            print("❌ 请指定 --user 和 --agent")
            sys.exit(1)
        result = integration.on_message(args.user, args.agent)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "end":
        result = integration.on_agent_end()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "context":
        if not args.context:
            print("❌ 请指定 --context")
            sys.exit(1)
        memories = integration.get_relevant_context(args.context)
        print(json.dumps(memories, ensure_ascii=False, indent=2))
    
    elif args.command == "feedback":
        if not args.memory_id or not args.outcome:
            print("❌ 请指定 --memory-id 和 --outcome")
            sys.exit(1)
        integration.record_feedback(args.memory_id, args.outcome)
        print("✅ 反馈已记录")
    
    elif args.command == "status":
        status = integration.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
