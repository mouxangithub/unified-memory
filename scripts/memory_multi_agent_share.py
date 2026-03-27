#!/usr/bin/env python3
"""
多智能体记忆共享 - Multi-Agent Memory Sharing

核心概念：
- 不同 Agent 可以共享记忆
- 每个 Agent 有自己的视角
- 共享上下文同步

灵感来自 MetaGPT 的多智能体协作
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SHARE_DIR = MEMORY_DIR / "shared"
AGENT_VIEWS_DIR = SHARE_DIR / "agent_views"


class MultiAgentMemory:
    """多智能体记忆共享"""
    
    def __init__(self):
        SHARE_DIR.mkdir(parents=True, exist_ok=True)
        AGENT_VIEWS_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        config_file = SHARE_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "agents": {},  # agent_id -> {name, role, last_sync}
            "shared_memory": [],  # 共享记忆列表
            "sync_version": 0
        }
    
    def _save_config(self):
        with open(SHARE_DIR / "config.json", "w") as f:
            json.dump(self.config, f, indent=2)
    
    def register_agent(self, agent_id: str, name: str, role: str) -> bool:
        """注册 Agent"""
        self.config["agents"][agent_id] = {
            "name": name,
            "role": role,
            "registered_at": datetime.now().isoformat(),
            "last_sync": None
        }
        self._save_config()
        return True
    
    def share_memory(self, agent_id: str, memory: Dict) -> str:
        """
        共享一条记忆
        
        记忆会上传到共享空间，其他 Agent 可以访问
        """
        share_id = f"share_{uuid.uuid4().hex[:8]}"
        
        shared = {
            "share_id": share_id,
            "agent_id": agent_id,
            "original_id": memory.get("id", ""),
            "text": memory.get("text", ""),
            "category": memory.get("category", "shared"),
            "shared_at": datetime.now().isoformat(),
            "access_count": 0,
            "tags": memory.get("tags", [])
        }
        
        self.config["shared_memory"].append(shared)
        self.config["sync_version"] += 1
        
        # 更新 Agent 的同步时间
        if agent_id in self.config["agents"]:
            self.config["agents"][agent_id]["last_sync"] = datetime.now().isoformat()
        
        self._save_config()
        return share_id
    
    def get_shared_memories(self, agent_id: str = None, since: str = None) -> List[Dict]:
        """
        获取共享记忆
        
        Args:
            agent_id: 如果指定，只获取该 Agent 共享的
            since: 如果指定，只获取指定时间之后的
        """
        memories = self.config["shared_memory"]
        
        if agent_id:
            memories = [m for m in memories if m["agent_id"] == agent_id]
        
        if since:
            memories = [m for m in memories if m["shared_at"] > since]
        
        # 按时间倒序
        memories.sort(key=lambda x: x["shared_at"], reverse=True)
        return memories
    
    def get_agent_view(self, agent_id: str, memories: List[Dict]) -> Dict:
        """
        获取某个 Agent 的记忆视角
        
        返回该 Agent 相关的记忆视图
        """
        # 获取该 Agent 共享的记忆
        my_shares = self.get_shared_memories(agent_id)
        my_ids = {s["original_id"] for s in my_shares}
        
        # 合并：自己的 + 他人的
        view = {
            "agent_id": agent_id,
            "my_memories": [m for m in memories if m.get("id", "") in my_ids],
            "shared_from_others": my_shares,
            "generated_at": datetime.now().isoformat()
        }
        
        return view
    
    def build_shared_context(self, agent_id: str, memories: List[Dict]) -> str:
        """
        为某个 Agent 构建共享上下文
        
        这是多智能体协作的核心：
        - 我知道什么
        - 其他 Agent 知道什么
        - 共同决策
        """
        view = self.get_agent_view(agent_id, memories)
        
        parts = []
        
        # 1. 自己的记忆
        if view["my_memories"]:
            my_text = "\n".join([f"- {m['text']}" for m in view["my_memories"][:10]])
            parts.append(f"【我共享的记忆】\n{my_text}")
        
        # 2. 其他 Agent 的共享
        others_shares = [s for s in view["shared_from_others"] if s["agent_id"] != agent_id]
        if others_shares:
            # 按 Agent 分组
            by_agent = {}
            for s in others_shares:
                aid = s["agent_id"]
                if aid not in by_agent:
                    by_agent[aid] = []
                by_agent[aid].append(s)
            
            others_text = []
            for aid, shares in by_agent.items():
                agent_name = self.config["agents"].get(aid, {}).get("name", aid)
                items = "\n".join([f"- {s['text'][:50]}..." for s in shares[:3]])
                others_text.append(f"{agent_name}:\n{items}")
            
            parts.append(f"【其他 Agent 共享】\n" + "\n".join(others_text))
        
        # 3. 最近的共享
        recent = view["shared_from_others"][:5] if view["shared_from_others"] else []
        if recent:
            recent_text = "\n".join([
                f"- [{s['agent_id']}] {s['text'][:40]}..." 
                for s in recent
            ])
            parts.append(f"【最新共享】\n{recent_text}")
        
        return "\n\n".join(parts)
    
    def sync_from_remote(self, remote_config: Dict):
        """
        从远程同步配置
        
        用于多机器/多实例同步
        """
        if remote_config.get("sync_version", 0) > self.config.get("sync_version", 0):
            # 合并共享记忆
            remote_memories = remote_config.get("shared_memory", [])
            local_ids = {m["share_id"] for m in self.config["shared_memory"]}
            
            for mem in remote_memories:
                if mem["share_id"] not in local_ids:
                    self.config["shared_memory"].append(mem)
            
            self.config["sync_version"] = remote_config.get("sync_version", 0)
            self._save_config()
    
    def export_shared(self) -> Dict:
        """导出共享配置（用于同步）"""
        return {
            "shared_memory": self.config["shared_memory"],
            "sync_version": self.config["sync_version"],
            "exported_at": datetime.now().isoformat()
        }


# 全局实例
_multiagent = None

def get_multiagent_memory() -> MultiAgentMemory:
    global _multiagent
    if _multiagent is None:
        _multiagent = MultiAgentMemory()
    return _multiagent


def share_to_agents(agent_id: str, memory: Dict) -> str:
    """便捷函数：共享记忆"""
    return get_multiagent_memory().share_memory(agent_id, memory)


def get_collaborative_context(agent_id: str, memories: List[Dict]) -> str:
    """便捷函数：获取协作上下文"""
    return get_multiagent_memory().build_shared_context(agent_id, memories)


if __name__ == "__main__":
    print("=" * 60)
    print("多智能体记忆共享测试")
    print("=" * 60)
    
    ma = MultiAgentMemory()
    
    # 注册 Agent
    ma.register_agent("agent_pm", "产品经理", "pm")
    ma.register_agent("agent_eng", "工程师", "engineer")
    
    # 共享记忆
    mem1 = {"id": "mem_1", "text": "决定用微服务架构", "category": "decision"}
    mem2 = {"id": "mem_2", "text": "用户喜欢简洁界面", "category": "preference"}
    
    share1 = ma.share_memory("agent_pm", mem1)
    share2 = ma.share_memory("agent_eng", mem2)
    
    print(f"\n📤 共享记忆:")
    print(f"  mem1 -> {share1}")
    print(f"  mem2 -> {share2}")
    
    # 获取共享
    all_shared = ma.get_shared_memories()
    print(f"\n📥 所有共享记忆: {len(all_shared)} 条")
    
    # 构建协作上下文
    memories = [
        {"id": "mem_1", "text": "决定用微服务架构"},
        {"id": "mem_2", "text": "用户喜欢简洁界面"},
    ]
    
    context = ma.build_shared_context("agent_pm", memories)
    print(f"\n🤝 产品经理的协作上下文:\n{context}")
    
    print("\n✅ 多智能体记忆共享测试完成")
