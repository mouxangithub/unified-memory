#!/usr/bin/env python3
"""
Weibull 衰减模型 - Weibull Decay Model

基于生命周期的智能遗忘模型
- 记忆会随时间自然衰减
- 重要记忆衰减更慢
- 频繁访问的记忆衰减更慢
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class WeibullDecay:
    """
    Weibull 衰减模型
    
    公式: score = importance * exp(-(t/half_life)^beta)
    
    特点：
    - beta > 1: 早期快速衰减，后期缓慢
    - beta = 1: 指数衰减
    - beta < 1: 早期缓慢，后期加速衰减
    """
    
    def __init__(self, 
                 base_half_life_days: float = 30.0,
                 reinforcement_factor: float = 0.5,
                 max_multiplier: float = 3.0):
        """
        Args:
            base_half_life_days: 基础半衰期（天）
            reinforcement_factor: 访问强化因子 (0-2)
            max_multiplier: 最大半衰期倍数
        """
        self.base_half_life = base_half_life_days
        self.reinforcement = reinforcement_factor
        self.max_multiplier = max_multiplier
    
    def calculate_half_life(self, memory: Dict) -> float:
        """
        计算记忆的有效半衰期
        
        影响因素：
        - 重要性（重要记忆半衰期更长）
        - 访问频率（频繁访问的记忆半衰期更长）
        """
        importance = memory.get("importance", 0.5)
        access_count = memory.get("access_count", 1)
        
        # 重要性影响：0.5-1.0 -> 0.5x-2x 半衰期
        importance_factor = 0.5 + importance
        
        # 访问频率影响（对数增长，有上限）
        access_factor = 1.0 + self.reinforcement * math.log1p(access_count)
        access_factor = min(access_factor, self.max_multiplier)
        
        # 有效半衰期
        half_life = self.base_half_life * importance_factor * access_factor
        
        return half_life
    
    def calculate_decay_score(self, memory: Dict, current_time: datetime = None) -> float:
        """
        计算衰减后的记忆分数
        
        Returns:
            0.0 - 1.0 的分数
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 获取记忆创建时间
        created_at = memory.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
        
        # 计算年龄（天）
        age = (current_time - created_at).total_seconds() / 86400
        
        # 获取记忆的 beta 参数（用于区分核心/工作/边缘记忆）
        beta = memory.get("decay_beta", 1.0)
        
        # 获取有效半衰期
        half_life = self.calculate_half_life(memory)
        
        # Weibull 衰减公式
        if half_life <= 0:
            return memory.get("importance", 0.5)
        
        # score = importance * exp(-(t/half_life)^beta)
        ratio = age / half_life
        decay = math.exp(-(ratio ** beta))
        
        # 基础分数
        base_score = memory.get("importance", 0.5)
        
        # 最终分数
        final_score = base_score * decay
        
        return max(final_score, 0.0)
    
    def should_demote(self, memory: Dict, threshold: float = 0.2) -> bool:
        """判断是否应该降级"""
        score = self.calculate_decay_score(memory)
        return score < threshold
    
    def should_promote(self, memory: Dict, threshold: float = 0.7) -> bool:
        """判断是否应该升级"""
        score = self.calculate_decay_score(memory)
        access_count = memory.get("access_count", 0)
        return score > threshold and access_count > 5
    
    def get_tier(self, memory: Dict) -> str:
        """
        获取记忆所属层级
        
        层级：
        - core: 核心记忆（高分数，高访问）
        - working: 工作记忆（中等分数）
        - peripheral: 边缘记忆（低分数或久未访问）
        """
        score = self.calculate_decay_score(memory)
        access_count = memory.get("access_count", 0)
        
        if score > 0.6 and access_count > 10:
            return "core"
        elif score > 0.3:
            return "working"
        else:
            return "peripheral"
    
    def decay_all(self, memories: List[Dict]) -> List[Dict]:
        """对所有记忆进行衰减计算"""
        results = []
        for mem in memories:
            decayed = mem.copy()
            decayed["decay_score"] = self.calculate_decay_score(mem)
            decayed["tier"] = self.get_tier(mem)
            results.append(decayed)
        
        # 按衰减分数排序
        results.sort(key=lambda x: x["decay_score"], reverse=True)
        
        return results


class DecayAnalyzer:
    """衰减分析器"""
    
    def __init__(self):
        self.decay = WeibullDecay()
    
    def analyze(self, memories: List[Dict]) -> Dict:
        """分析记忆的衰减状态"""
        decayed = self.decay.decay_all(memories)
        
        tiers = {"core": 0, "working": 0, "peripheral": 0}
        total_score = 0
        
        for mem in decayed:
            tiers[mem["tier"]] += 1
            total_score += mem["decay_score"]
        
        return {
            "total": len(memories),
            "tiers": tiers,
            "avg_score": total_score / len(memories) if memories else 0,
            "demote_candidates": [m["id"] for m in decayed if self.decay.should_demote(m)],
            "promote_candidates": [m["id"] for m in decayed if self.decay.should_promote(m)],
        }


if __name__ == "__main__":
    print("=" * 50)
    print("Weibull 衰减模型测试")
    print("=" * 50)
    
    decay = WeibullDecay(base_half_life_days=30)
    analyzer = DecayAnalyzer()
    
    # 测试记忆
    now = datetime.now()
    
    memories = [
        {
            "id": "mem_1",
            "text": "用户喜欢简洁界面",
            "importance": 0.9,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "access_count": 20,
            "decay_beta": 0.8,  # 核心记忆衰减慢
        },
        {
            "id": "mem_2",
            "text": "今天的会议内容",
            "importance": 0.5,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "access_count": 3,
            "decay_beta": 1.0,
        },
        {
            "id": "mem_3",
            "text": "一个旧的偏好",
            "importance": 0.4,
            "created_at": (now - timedelta(days=60)).isoformat(),
            "access_count": 1,
            "decay_beta": 1.3,  # 边缘记忆衰减快
        },
    ]
    
    print("\n📊 衰减分析:\n")
    
    for mem in memories:
        score = decay.calculate_decay_score(mem)
        tier = decay.get_tier(mem)
        half_life = decay.calculate_half_life(mem)
        
        print(f"  [{mem['id']}] {mem['text'][:30]}...")
        print(f"       衰减分数: {score:.3f}")
        print(f"       层级: {tier}")
        print(f"       半衰期: {half_life:.1f} 天")
        print()
    
    # 整体分析
    analysis = analyzer.analyze(memories)
    
    print("\n📈 整体状态:")
    print(f"  总记忆: {analysis['total']}")
    print(f"  核心: {analysis['tiers']['core']}")
    print(f"  工作: {analysis['tiers']['working']}")
    print(f"  边缘: {analysis['tiers']['peripheral']}")
    print(f"  平均分数: {analysis['avg_score']:.3f}")
    
    print("\n✅ Weibull 衰减模型测试完成")
