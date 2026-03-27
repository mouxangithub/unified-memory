#!/usr/bin/env python3
from pathlib import Path
"""
分布式记忆同步 - Distributed Memory Sync

支持：
- 多设备同步
- 冲突解决
- 增量同步
- 离线优先
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SYNC_DIR = MEMORY_DIR / "sync"


class DistributedSync:
    """
    分布式记忆同步引擎
    """
    
    def __init__(self):
        SYNC_DIR.mkdir(parents=True, exist_ok=True)
        
        self.state_file = SYNC_DIR / "state.json"
        self.change_log_file = SYNC_DIR / "changes.jsonl"
        self.conflict_file = SYNC_DIR / "conflicts.json"
        
        self.state = self._load_state()
        self.device_id = self._get_device_id()
        
        # 初始化变更日志
        self.change_log = deque(maxlen=10000)  # 保留最近 10000 条
    
    def _load_state(self) -> Dict:
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {
            "last_sync": None,
            "last_sync_timestamp": 0,
            "local_version": 0,
            "remote_version": 0,
            "pending_changes": [],
            "sync_status": "idle"
        }
    
    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _get_device_id(self) -> str:
        """获取设备 ID"""
        device_file = SYNC_DIR / "device_id"
        if device_file.exists():
            return device_file.read_text().strip()
        
        import uuid
        device_id = f"device_{uuid.uuid4().hex[:12]}"
        device_file.write_text(device_id)
        return device_id
    
    def _log_change(self, change: Dict):
        """记录变更"""
        self.change_log.append(change)
        
        # 追加到文件
        with open(self.change_log_file, "a") as f:
            f.write(json.dumps({
                **change,
                "device_id": self.device_id,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False) + "\n")
    
    # ===== 变更追踪 =====
    
    def record_change(self, memory_id: str, operation: str, data: Dict):
        """
        记录本地变更
        
        Args:
            memory_id: 记忆 ID
            operation: create/update/delete
            data: 记忆数据
        """
        change = {
            "memory_id": memory_id,
            "operation": operation,
            "data": data,
            "version": self.state["local_version"] + 1,
            "checksum": self._compute_checksum(data)
        }
        
        self._log_change(change)
        
        self.state["pending_changes"].append(change)
        self.state["local_version"] += 1
        self._save_state()
    
    def _compute_checksum(self, data: Dict) -> str:
        """计算校验和"""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content.encode()).hexdigest()
    
    # ===== 同步操作 =====
    
    def sync_up(self, remote_endpoint: str = None) -> Dict:
        """
        上传本地变更到远程
        
        简化版：只模拟同步成功
        完整版需要实现 HTTP/WebSocket 上传
        """
        if not self.state["pending_changes"]:
            return {"status": "no_changes", "uploaded": 0}
        
        pending = self.state["pending_changes"]
        
        # 模拟上传
        # 实际应该：
        # 1. 构建请求
        # 2. 发送到 remote_endpoint
        # 3. 处理响应
        
        uploaded = []
        failed = []
        
        for change in pending:
            # 模拟上传成功
            uploaded.append(change["memory_id"])
        
        # 清除已上传
        self.state["pending_changes"] = []
        self.state["last_sync"] = datetime.now().isoformat()
        self.state["last_sync_timestamp"] = int(time.time())
        self._save_state()
        
        return {
            "status": "success",
            "uploaded": len(uploaded),
            "failed": len(failed),
            "timestamp": self.state["last_sync"]
        }
    
    def sync_down(self, remote_endpoint: str = None) -> Dict:
        """
        从远程下载变更
        
        简化版：模拟无远程变更
        完整版需要实现 HTTP/WebSocket 下载
        """
        # 模拟下载
        downloaded = []
        conflicts = []
        
        # 实际应该：
        # 1. 获取远程变更列表
        # 2. 对比本地
        # 3. 检测冲突
        # 4. 解决冲突
        # 5. 应用变更
        
        return {
            "status": "success",
            "downloaded": len(downloaded),
            "conflicts": len(conflicts),
            "timestamp": datetime.now().isoformat()
        }
    
    def full_sync(self, remote_endpoint: str = None) -> Dict:
        """完整同步（上下载）"""
        up_result = self.sync_up(remote_endpoint)
        down_result = self.sync_down(remote_endpoint)
        
        return {
            "upload": up_result,
            "download": down_result,
            "device_id": self.device_id,
            "local_version": self.state["local_version"]
        }
    
    # ===== 冲突解决 =====
    
    def resolve_conflict(self, local: Dict, remote: Dict, strategy: str = "last_write_wins") -> Dict:
        """
        解决冲突
        
        Args:
            local: 本地数据
            remote: 远程数据
            strategy: last_write_wins / local_wins / remote_wins / merge
        
        Returns:
            解决后的数据
        """
        if strategy == "last_write_wins":
            # 最后写入胜出
            local_time = local.get("updated_at", local.get("timestamp", ""))
            remote_time = remote.get("updated_at", remote.get("timestamp", ""))
            
            if local_time >= remote_time:
                return {**local, "conflict_resolved": "local"}
            else:
                return {**remote, "conflict_resolved": "remote"}
        
        elif strategy == "local_wins":
            return {**local, "conflict_resolved": "local"}
        
        elif strategy == "remote_wins":
            return {**remote, "conflict_resolved": "remote"}
        
        elif strategy == "merge":
            # 语义合并
            merged = self._semantic_merge(local, remote)
            return {**merged, "conflict_resolved": "merged"}
        
        return local
    
    def _semantic_merge(self, local: Dict, remote: Dict) -> Dict:
        """语义合并"""
        merged = local.copy()
        
        # 合并 tags
        local_tags = set(local.get("tags", []))
        remote_tags = set(remote.get("tags", []))
        merged["tags"] = list(local_tags | remote_tags)
        
        # 保留最新的 timestamp
        if remote.get("updated_at", "") > local.get("updated_at", ""):
            merged["updated_at"] = remote["updated_at"]
        
        # 记录合并历史
        merged["merged_from"] = {
            "local_version": local.get("version", 1),
            "remote_version": remote.get("version", 1)
        }
        
        return merged
    
    def detect_conflict(self, local: Dict, remote: Dict) -> bool:
        """检测是否有冲突"""
        # 简单检查：版本不同且内容不同
        if local.get("version", 1) != remote.get("version", 1):
            local_checksum = self._compute_checksum(local)
            remote_checksum = self._compute_checksum(remote)
            return local_checksum != remote_checksum
        return False
    
    # ===== 状态查询 =====
    
    def get_pending_changes(self) -> List[Dict]:
        """获取待同步的变更"""
        return self.state["pending_changes"]
    
    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        return {
            "device_id": self.device_id,
            "last_sync": self.state["last_sync"],
            "local_version": self.state["local_version"],
            "pending_count": len(self.state["pending_changes"]),
            "status": self.state["sync_status"]
        }
    
    def has_pending(self) -> bool:
        """是否有待同步变更"""
        return len(self.state["pending_changes"]) > 0


# ===== 离线优先 =====
class OfflineFirst(DistributedSync):
    """
    离线优先模式
    
    核心思想：
    1. 离线可写
    2. 联网时自动同步
    3. 冲突自动解决
    """
    
    def __init__(self):
        super().__init__()
        self.offline_queue = deque(maxlen=1000)
    
    def is_online(self) -> bool:
        """检测网络状态"""
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False
    
    def write_offline(self, memory: Dict):
        """离线写入"""
        self.record_change(
            memory.get("id", ""),
            "create",
            memory
        )
        self.offline_queue.append(memory.get("id", ""))
    
    def auto_sync(self, remote_endpoint: str = None):
        """自动同步（联网时）"""
        if self.is_online() and self.has_pending():
            return self.full_sync(remote_endpoint)
        return {"status": "offline", "pending": self.has_pending()}


# 全局实例
_sync = None

def get_distributed_sync() -> DistributedSync:
    global _sync
    if _sync is None:
        _sync = DistributedSync()
    return _sync


if __name__ == "__main__":
    print("=" * 50)
    print("分布式同步测试")
    print("=" * 50)
    
    sync = DistributedSync()
    
    # 记录变更
    print("\n📝 记录变更:")
    sync.record_change("mem_1", "create", {"text": "测试记忆", "version": 1})
    sync.record_change("mem_2", "update", {"text": "更新记忆", "version": 2})
    print(f"  待同步: {len(sync.get_pending_changes())} 条")
    
    # 同步状态
    print(f"\n📊 状态: {sync.get_sync_status()}")
    
    # 冲突解决测试
    print("\n⚔️ 冲突解决测试:")
    local = {"id": "mem_x", "text": "本地版本", "version": 1, "updated_at": "2026-03-23T10:00:00"}
    remote = {"id": "mem_x", "text": "远程版本", "version": 2, "updated_at": "2026-03-23T11:00:00"}
    
    resolved = sync.resolve_conflict(local, remote, "last_write_wins")
    print(f"  策略: last_write_wins")
    print(f"  结果: {resolved.get('text')} (冲突解决方式: {resolved.get('conflict_resolved')})")
    
    print("\n✅ 分布式同步测试完成")
