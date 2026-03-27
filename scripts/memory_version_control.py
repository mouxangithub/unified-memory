#!/usr/bin/env python3
"""
记忆版本控制 - Git for Memory

核心：每次修改记录历史，支持回滚
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VERSIONS_DIR = MEMORY_DIR / "versions"


class MemoryVersionControl:
    """记忆版本控制"""
    
    def __init__(self):
        VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.history_file = VERSIONS_DIR / "history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"memories": {}}  # memory_id -> [versions]
    
    def _save_history(self):
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def commit(self, memory: Dict, operation: str = "create") -> str:
        """
        提交记忆版本
        
        Args:
            memory: 记忆数据
            operation: create/update/delete
        
        Returns:
            version_id
        """
        mem_id = memory.get("id", "")
        if not mem_id:
            return None
        
        if mem_id not in self.history["memories"]:
            self.history["memories"][mem_id] = []
        
        version_id = f"v_{uuid.uuid4().hex[:8]}"
        
        version = {
            "version_id": version_id,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "text": memory.get("text", ""),
                "category": memory.get("category", "unknown"),
                "tags": memory.get("tags", []),
                "confidence": memory.get("confidence", 0.8),
                "project": memory.get("project", "default")
            }
        }
        
        self.history["memories"][mem_id].append(version)
        self._save_history()
        
        return version_id
    
    def get_versions(self, memory_id: str) -> List[Dict]:
        """获取记忆的所有版本"""
        return self.history["memories"].get(memory_id, [])
    
    def get_version(self, memory_id: str, version_id: str) -> Optional[Dict]:
        """获取特定版本"""
        versions = self.get_versions(memory_id)
        for v in versions:
            if v["version_id"] == version_id:
                return v
        return None
    
    def get_latest(self, memory_id: str) -> Optional[Dict]:
        """获取最新版本"""
        versions = self.get_versions(memory_id)
        if versions:
            return versions[-1]
        return None
    
    def rollback(self, memory_id: str, version_id: str = None) -> Optional[Dict]:
        """
        回滚到指定版本
        
        Args:
            memory_id: 记忆 ID
            version_id: 目标版本，不指定则回滚到上一版本
        
        Returns:
            回滚后的数据
        """
        versions = self.get_versions(memory_id)
        if not versions:
            return None
        
        if version_id is None:
            # 回滚到上一版本（删除最后一个）
            if len(versions) <= 1:
                return None
            target_version = versions[-2]
        else:
            target_version = None
            for v in versions:
                if v["version_id"] == version_id:
                    target_version = v
                    break
            if target_version is None:
                return None
        
        # 创建新的回滚版本
        rollback_version = {
            "version_id": f"v_{uuid.uuid4().hex[:8]}",
            "operation": "rollback",
            "timestamp": datetime.now().isoformat(),
            "rollback_from": versions[-1]["version_id"],
            "rollback_to": target_version["version_id"],
            "data": target_version["data"]
        }
        
        self.history["memories"][memory_id].append(rollback_version)
        self._save_history()
        
        return target_version["data"]
    
    def get_history_tree(self, memory_id: str) -> Dict:
        """获取版本树"""
        versions = self.get_versions(memory_id)
        
        tree = {
            "memory_id": memory_id,
            "total_versions": len(versions),
            "versions": []
        }
        
        for i, v in enumerate(versions):
            tree["versions"].append({
                "index": i,
                "version_id": v["version_id"],
                "operation": v["operation"],
                "timestamp": v["timestamp"],
                "is_latest": i == len(versions) - 1
            })
        
        return tree
    
    def diff(self, memory_id: str, v1: str, v2: str) -> Dict:
        """对比两个版本"""
        version1 = self.get_version(memory_id, v1)
        version2 = self.get_version(memory_id, v2)
        
        if not version1 or not version2:
            return None
        
        data1 = version1["data"]
        data2 = version2["data"]
        
        diffs = []
        for key in set(list(data1.keys()) + list(data2.keys())):
            val1 = data1.get(key)
            val2 = data2.get(key)
            if val1 != val2:
                diffs.append({
                    "field": key,
                    "old": val1,
                    "new": val2
                })
        
        return {
            "v1": v1,
            "v2": v2,
            "diffs": diffs
        }
    
    def prune(self, memory_id: str, keep_last: int = 10):
        """清理旧版本，只保留最近 N 个"""
        versions = self.get_versions(memory_id)
        if len(versions) <= keep_last:
            return
        
        self.history["memories"][memory_id] = versions[-keep_last:]
        self._save_history()
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total_versions = sum(
            len(versions) 
            for versions in self.history["memories"].values()
        )
        return {
            "total_memories": len(self.history["memories"]),
            "total_versions": total_versions,
            "avg_versions_per_memory": total_versions / max(1, len(self.history["memories"]))
        }


# 全局实例
_vc = None

def get_version_control() -> MemoryVersionControl:
    global _vc
    if _vc is None:
        _vc = MemoryVersionControl()
    return _vc


def commit_memory(memory: Dict, operation: str = "create") -> str:
    """提交记忆的便捷函数"""
    return get_version_control().commit(memory, operation)


def rollback_memory(memory_id: str, version_id: str = None) -> Optional[Dict]:
    """回滚记忆的便捷函数"""
    return get_version_control().rollback(memory_id, version_id)


if __name__ == "__main__":
    print("=" * 50)
    print("版本控制测试")
    print("=" * 50)
    
    vc = MemoryVersionControl()
    
    # 创建记忆 v1
    mem_v1 = {
        "id": "mem_test",
        "text": "用户喜欢简洁",
        "category": "preference"
    }
    v1_id = vc.commit(mem_v1, "create")
    print(f"\n📝 v1: {v1_id}")
    
    # 更新记忆 v2
    mem_v2 = {
        "id": "mem_test",
        "text": "用户喜欢简洁界面",
        "category": "preference"
    }
    v2_id = vc.commit(mem_v2, "update")
    print(f"📝 v2: {v2_id}")
    
    # 更新记忆 v3
    mem_v3 = {
        "id": "mem_test",
        "text": "用户明确喜欢简洁界面",
        "category": "preference"
    }
    v3_id = vc.commit(mem_v3, "update")
    print(f"📝 v3: {v3_id}")
    
    # 获取版本历史
    print(f"\n📜 版本历史:")
    tree = vc.get_history_tree("mem_test")
    for v in tree["versions"]:
        print(f"  {v['index']}: {v['version_id']} ({v['operation']})")
    
    # 回滚
    print(f"\n⏪ 回滚到 v1")
    rollback_data = vc.rollback("mem_test", v1_id)
    print(f"  回滚后: {rollback_data['text']}")
    
    # 统计
    print(f"\n📊 统计: {vc.get_stats()}")
    
    print("\n✅ 版本控制测试完成")
