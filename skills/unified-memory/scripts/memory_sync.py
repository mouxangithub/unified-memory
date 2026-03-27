#!/usr/bin/env python3
"""
Memory Sync Engine - 多Agent记忆共享 v1.0

功能:
- 多Agent共享记忆
- 验证冲突
- 增量同步
- 审计接口

Usage:
    python3 scripts/memory_sync.py add-node --node-id "agent-2"
    python3 scripts/memory_sync.py record --data '{"text":"偏好飞书"}'
    python3 scripts/memory_sync.py status
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import subprocess

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SHARED_DIR = MEMORY_DIR / "shared"
SYNC_STATE = SHARED_DIR / "sync_state.json"
NODE_REGISTRY = SHARED_DIR / "nodes.json"


class ConflictDetection:
    """冲突检测"""
    
    def __init__(self, existing_data: Dict[str, Any]):
        self.data = existing_data
    
    def detect(self, new_data: Dict[str, Any]) -> List[Dict]:
        """检测冲突"""
        conflicts = []
        
        for key, new_val in new_data.items():
            if key not in self.data:
                continue
            
            existing_val = self.data[key]
            
            if isinstance(existing_val, str) and isinstance(new_val, str):
                if existing_val.strip() != new_val.strip():
                    conflicts.append({
                        "key": key,
                        "existing": existing_val[:50] + "..." if len(str(existing_val)) > 50 else existing_val,
                        "proposed": new_val[:50] + "..." if len(str(new_val)) > 50 else new_val,
                        "type": "text_conflict"
                    })
        
        return conflicts


class SyncNode:
    """同步节点"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.version = 0
        self.last_update = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "version": self.version,
            "last_update": self.last_update
        }


class SyncManager:
    """同步管理器"""
    
    def __init__(self):
        self.registry = self._load_registry()
        self.state = self._load_state()
    
    def _load_registry(self) -> Dict[str, Any]:
        """加载节点注册表"""
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        if NODE_REGISTRY.exists():
            with open(NODE_REGISTRY) as f:
                return json.load(f)
        return {"nodes": {}, "last_updated": datetime.now().isoformat()}
    
    def _load_state(self) -> Dict[str, Any]:
        """加载同步状态"""
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        if SYNC_STATE.exists():
            with open(SYNC_STATE) as f:
                return json.load(f)
        return {
            "schema": "memory-sync-v1",
            "last_sync": None,
            "active_nodes": [],
            "conflicts": {},
            "sync_count": 0
        }
    
    def _save_registry(self):
        """保存节点注册表"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(NODE_REGISTRY, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def _save_state(self):
        """保存同步状态"""
        with open(SYNC_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def register_node(self, node_id: str) -> Dict:
        """注册节点"""
        if node_id not in self.registry["nodes"]:
            self.registry["nodes"][node_id] = {
                "registered_at": datetime.now().isoformat(),
                "version": 0,
                "status": "active"
            }
            self._save_registry()
            return {"registered": True, "node_id": node_id}
        return {"registered": False, "node_id": node_id, "reason": "already exists"}
    
    def unregister_node(self, node_id: str) -> Dict:
        """注销节点"""
        if node_id in self.registry["nodes"]:
            del self.registry["nodes"][node_id]
            self._save_registry()
            return {"unregistered": True}
        return {"unregistered": False, "reason": "not found"}
    
    def get_nodes(self) -> List[Dict]:
        """获取所有节点"""
        return [
            {"node_id": k, **v}
            for k, v in self.registry["nodes"].items()
        ]
    
    def record_data(self, node_id: str, data: Dict[str, Any]) -> Dict:
        """记录数据"""
        # 获取当前记忆
        current_memories = self._get_current_memories()
        
        # 检测冲突
        detector = ConflictDetection(current_memories)
        conflicts = detector.detect(data)
        
        result = {
            "recorded": False,
            "conflicts": conflicts,
            "node_id": node_id
        }
        
        if conflicts:
            # 记录冲突
            self.state["conflicts"][datetime.now().isoformat()] = {
                "node_id": node_id,
                "conflicts": conflicts
            }
            result["needs_resolution"] = True
        
        # 存储到记忆系统
        for key, value in data.items():
            try:
                subprocess.run(
                    ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_agent.py"),
                     "quick-store", str(value)],
                    capture_output=True, timeout=30
                )
                current_memories[key] = value
            except Exception as e:
                result["error"] = str(e)
        
        # 更新节点版本
        if node_id in self.registry["nodes"]:
            self.registry["nodes"][node_id]["version"] += 1
            self.registry["nodes"][node_id]["last_update"] = datetime.now().isoformat()
        
        self._save_state()
        self._save_registry()
        
        result["recorded"] = True
        return result
    
    def _get_current_memories(self) -> Dict[str, str]:
        """获取当前记忆"""
        memories = {}
        try:
            import lancedb
            db = lancedb.connect(str(MEMORY_DIR / "vector"))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            for i, mem_id in enumerate(data.get("id", [])):
                memories[mem_id] = data.get("text", [""])[i] if i < len(data.get("text", [])) else ""
        except:
            pass
        
        return memories
    
    def sync(self, source_node: str = None) -> Dict:
        """执行同步"""
        self.state["last_sync"] = datetime.now().isoformat()
        self.state["sync_count"] = self.state.get("sync_count", 0) + 1
        
        # 更新活跃节点列表
        self.state["active_nodes"] = list(self.registry["nodes"].keys())
        
        self._save_state()
        
        return {
            "synced": True,
            "timestamp": self.state["last_sync"],
            "nodes": len(self.state["active_nodes"]),
            "conflicts_pending": len(self.state["conflicts"])
        }
    
    def resolve_conflicts(self, strategy: str = "last_write_wins") -> Dict:
        """解决冲突"""
        resolved = []
        
        for timestamp, conflict_data in list(self.state["conflicts"].items()):
            for conflict in conflict_data.get("conflicts", []):
                if strategy == "last_write_wins":
                    # 使用最新版本
                    resolved.append({
                        "key": conflict["key"],
                        "strategy": strategy,
                        "result": "accepted_proposed"
                    })
        
        # 清空冲突
        self.state["conflicts"] = {}
        self._save_state()
        
        return {
            "resolved": len(resolved),
            "strategy": strategy,
            "details": resolved
        }
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "nodes": len(self.registry["nodes"]),
            "active_nodes": self.state.get("active_nodes", []),
            "last_sync": self.state.get("last_sync"),
            "sync_count": self.state.get("sync_count", 0),
            "pending_conflicts": len(self.state.get("conflicts", {}))
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Sync Engine v1.0")
    parser.add_argument("command", choices=[
        "init", "add-node", "remove-node", "list-nodes",
        "record", "sync", "resolve", "status"
    ])
    parser.add_argument("--node-id", "-n", help="节点ID")
    parser.add_argument("--data", "-d", help="JSON数据")
    parser.add_argument("--strategy", "-s", default="last_write_wins", help="冲突策略")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    manager = SyncManager()
    
    if args.command == "init":
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        print("✅ 初始化完成")
        print(f"   共享目录: {SHARED_DIR}")
    
    elif args.command == "add-node":
        if not args.node_id:
            print("❌ 请提供 --node-id")
            return
        
        result = manager.register_node(args.node_id)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status = "成功" if result["registered"] else "失败"
            print(f"🆕 注册节点 [{status}]: {args.node_id}")
    
    elif args.command == "remove-node":
        if not args.node_id:
            print("❌ 请提供 --node-id")
            return
        
        result = manager.unregister_node(args.node_id)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status = "成功" if result["unregistered"] else "失败"
            print(f"🗑️ 注销节点 [{status}]: {args.node_id}")
    
    elif args.command == "list-nodes":
        nodes = manager.get_nodes()
        
        if args.json:
            print(json.dumps(nodes, ensure_ascii=False, indent=2))
        else:
            print(f"📋 已注册节点 ({len(nodes)}):")
            for node in nodes:
                print(f"   {node['node_id']}: v{node.get('version', 0)}")
    
    elif args.command == "record":
        if not args.node_id or not args.data:
            print("❌ 请提供 --node-id 和 --data")
            return
        
        try:
            data = json.loads(args.data)
        except:
            print("❌ --data 必须是有效的 JSON")
            return
        
        result = manager.record_data(args.node_id, data)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get("conflicts"):
                print(f"⚠️ 记录完成但有 {len(result['conflicts'])} 个冲突")
            else:
                print(f"✅ 记录完成")
    
    elif args.command == "sync":
        result = manager.sync(args.node_id)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"🔄 同步完成")
            print(f"   节点数: {result['nodes']}")
            print(f"   待处理冲突: {result['conflicts_pending']}")
    
    elif args.command == "resolve":
        result = manager.resolve_conflicts(args.strategy)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 冲突解决")
            print(f"   策略: {args.strategy}")
            print(f"   解决: {result['resolved']} 个")
    
    elif args.command == "status":
        status = manager.get_status()
        
        if args.json:
            print(json.dumps(status, ensure_ascii=False, indent=2))
        else:
            print("📊 同步状态")
            print(f"   节点数: {status['nodes']}")
            print(f"   活跃节点: {len(status['active_nodes'])}")
            print(f"   同步次数: {status['sync_count']}")
            print(f"   待处理冲突: {status['pending_conflicts']}")


if __name__ == "__main__":
    main()
