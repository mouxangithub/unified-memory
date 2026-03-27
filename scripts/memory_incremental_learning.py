#!/usr/bin/env python3
"""
增量学习 - Incremental Learning

核心概念：
- 不再等 batch/会话结束才处理
- 每条记忆立即：向量化 + 聚类 + 合并
- 实时维护记忆网络

灵感来自在线学习算法
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
STATE_FILE = MEMORY_DIR / "incremental_state.json"
CLUSTER_FILE = MEMORY_DIR / "memory_clusters.json"


class IncrementalLearner:
    """增量学习器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold  # 相似度阈值
        self.state = self._load_state()
        self.clusters = self._load_clusters()
        self._embedding_cache = {}  # 简单缓存
    
    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_id": 0,
            "total_processed": 0,
            "merged_count": 0,
            "cluster_count": 0,
            "last_process": None
        }
    
    def _load_clusters(self) -> Dict:
        if CLUSTER_FILE.exists():
            try:
                with open(CLUSTER_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"clusters": []}  # {cluster_id: [memory_ids]}
    
    def _save_state(self):
        self.state["last_process"] = datetime.now().isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _save_clusters(self):
        CLUSTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CLUSTER_FILE, "w") as f:
            json.dump(self.clusters, f, indent=2, ensure_ascii=False)
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本向量（增量方式）"""
        # 简单文本 hash 作为伪向量（实际应该调用 Ollama）
        import hashlib
        h = hashlib.md5(text.encode()).digest()
        # 转换为 768 维向量
        vector = []
        for i in range(768):
            byte_idx = i % len(h)
            val = (h[byte_idx] / 255.0) * 2 - 1  # -1 到 1
            vector.append(val)
        return vector
    
    def compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        if mag1 * mag2 == 0:
            return 0
        return dot / (mag1 * mag2)
    
    def find_similar(self, text: str, existing_memories: List[Dict]) -> List[Tuple[Dict, float]]:
        """查找相似记忆"""
        if not existing_memories:
            return []
        
        query_vec = self.get_embedding(text)
        similarities = []
        
        for mem in existing_memories:
            mem_vec = mem.get("vector", [])
            if not mem_vec or len(mem_vec) != 768:
                continue
            
            sim = self.compute_similarity(query_vec, mem_vec)
            if sim >= self.similarity_threshold:
                similarities.append((mem, sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def should_merge(self, text1: str, text2: str) -> bool:
        """判断两条记忆是否应该合并"""
        # 简单判断：文本相似度
        if text1 == text2:
            return True
        
        # 长度差异检查
        len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))
        if len_ratio < 0.5:
            return False
        
        # 向量相似度
        vec1 = self.get_embedding(text1)
        vec2 = self.get_embedding(text2)
        return self.compute_similarity(vec1, vec2) >= self.similarity_threshold
    
    def merge_memories(self, mem1: Dict, mem2: Dict) -> Dict:
        """
        合并两条记忆
        
        策略：
        1. 保留较新、较长的
        2. 合并元数据
        3. 更新置信度
        """
        # 保留更长的
        if len(mem1.get("text", "")) >= len(mem2.get("text", "")):
            merged = mem1.copy()
            older = mem2
        else:
            merged = mem2.copy()
            older = mem1
        
        # 合并标签
        tags1 = set(merged.get("tags", []))
        tags2 = set(older.get("tags", []))
        merged["tags"] = list(tags1 | tags2)
        
        # 更新置信度（取平均）
        conf1 = merged.get("confidence", 0.8)
        conf2 = older.get("confidence", 0.8)
        merged["confidence"] = (conf1 + conf2) / 2
        
        # 记录合并
        merged["merged_from"] = older.get("id", "")
        merged["merged_at"] = datetime.now().isoformat()
        
        self.state["merged_count"] += 1
        
        return merged
    
    def add_to_cluster(self, memory_id: str, cluster_id: str = None) -> str:
        """将记忆添加到聚类"""
        if cluster_id is None:
            # 创建新聚类
            cluster_id = f"cluster_{len(self.clusters['clusters']) + 1}"
            self.clusters["clusters"].append({
                "id": cluster_id,
                "memory_ids": [memory_id],
                "created_at": datetime.now().isoformat()
            })
        else:
            # 添加到现有聚类
            for cluster in self.clusters["clusters"]:
                if cluster["id"] == cluster_id:
                    if memory_id not in cluster["memory_ids"]:
                        cluster["memory_ids"].append(memory_id)
                    break
        
        self.clusters["cluster_count"] = len(self.clusters["clusters"])
        self._save_clusters()
        return cluster_id
    
    def process_single(self, memory: Dict, existing_memories: List[Dict]) -> Dict:
        """
        处理单条记忆（增量核心）
        
        流程：
        1. 生成向量
        2. 查找相似记忆
        3. 判断是否合并
        4. 更新聚类
        """
        text = memory.get("text", "")
        
        # 1. 生成向量（如果还没有）
        if not memory.get("vector") or len(memory.get("vector", [])) != 768:
            memory["vector"] = self.get_embedding(text)
        
        # 2. 查找相似记忆
        similar = self.find_similar(text, existing_memories)
        
        if similar:
            # 3. 检查是否需要合并
            most_similar = similar[0][0]
            
            if self.should_merge(text, most_similar.get("text", "")):
                # 合并
                merged = self.merge_memories(memory, most_similar)
                self.state["total_processed"] += 1
                self._save_state()
                
                # 添加到聚类
                cluster_id = self.add_to_cluster(merged.get("id", ""))
                
                return {
                    "action": "merge",
                    "merged": merged,
                    "cluster_id": cluster_id,
                    "similar_count": len(similar)
                }
        
        # 不需要合并，直接添加
        self.add_to_cluster(memory.get("id", ""))
        self.state["total_processed"] += 1
        self._save_state()
        
        return {
            "action": "add",
            "memory": memory,
            "similar_count": len(similar)
        }
    
    def auto_merge_duplicates(self, memories: List[Dict]) -> List[Dict]:
        """自动合并重复记忆"""
        if not memories:
            return []
        
        # 按 ID 分组
        by_text = {}
        for mem in memories:
            text = mem.get("text", "")[:100]  # 用前100字符去重
            if text not in by_text:
                by_text[text] = []
            by_text[text].append(mem)
        
        # 合并同组
        merged = []
        for text, group in by_text.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # 合并多条
                result = group[0]
                for mem in group[1:]:
                    result = self.merge_memories(result, mem)
                merged.append(result)
                print(f"  🔗 合并 {len(group)} 条重复记忆")
        
        return merged
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "total_processed": self.state["total_processed"],
            "merged_count": self.state["merged_count"],
            "cluster_count": self.clusters["cluster_count"],
            "last_process": self.state.get("last_process")
        }


# 全局实例
_learner = None

def get_learner() -> IncrementalLearner:
    global _learner
    if _learner is None:
        _learner = IncrementalLearner()
    return _learner


def process_incremental(memory: Dict, existing_memories: List[Dict] = None) -> Dict:
    """增量处理单条记忆"""
    learner = get_learner()
    return learner.process_single(memory, existing_memories or [])


if __name__ == "__main__":
    print("=" * 60)
    print("增量学习测试")
    print("=" * 60)
    
    learner = IncrementalLearner()
    
    # 测试数据
    memories = [
        {"id": "mem_1", "text": "用户喜欢简洁的界面", "category": "preference"},
        {"id": "mem_2", "text": "用户喜欢简洁的界面", "category": "preference"},  # 重复
        {"id": "mem_3", "text": "采用微服务架构", "category": "decision"},
        {"id": "mem_4", "text": "Python 是一种编程语言", "category": "fact"},
    ]
    
    # 处理
    print("\n📝 增量处理:")
    for mem in memories:
        result = learner.process_single(mem, memories)
        print(f"  {result['action']}: {mem['text'][:30]}...")
        if result['action'] == 'merge':
            print(f"    -> 合并到: {result['merged']['text'][:30]}...")
    
    # 统计
    print("\n📊 统计:")
    stats = learner.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n✅ 增量学习测试完成")
