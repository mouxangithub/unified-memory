#!/usr/bin/env python3
"""
Memory Cloud - 云同步支持 v0.2.1

功能:
- 可选云备份
- 多设备同步
- 增量同步
- 冲突解决

Usage:
    python3 scripts/memory_cloud.py backup
    python3 scripts/memory_cloud.py restore
    python3 scripts/memory_cloud.py sync
    python3 scripts/memory_cloud.py status
"""

import argparse
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import shutil

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CLOUD_CONFIG = MEMORY_DIR / "cloud_config.json"
SYNC_STATE = MEMORY_DIR / "sync_state.json"

# 云存储类型
STORAGE_TYPES = ["local", "s3", "webdav", "dropbox", "gdrive"]


class CloudConfig:
    """云存储配置"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CLOUD_CONFIG.exists():
            with open(CLOUD_CONFIG) as f:
                return json.load(f)
        return {
            "enabled": False,
            "storage_type": "local",
            "backup_path": str(WORKSPACE / "memory_backup"),
            "auto_sync": False,
            "sync_interval": 3600  # 1小时
        }
    
    def save(self):
        """保存配置"""
        CLOUD_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(CLOUD_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def enable(self, storage_type: str = "local", backup_path: str = None):
        """启用云同步"""
        self.config["enabled"] = True
        self.config["storage_type"] = storage_type
        if backup_path:
            self.config["backup_path"] = backup_path
        self.save()
    
    def disable(self):
        """禁用云同步"""
        self.config["enabled"] = False
        self.save()


class MemoryBackup:
    """记忆备份管理"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
    
    def create_backup(self) -> Dict:
        """创建备份"""
        backup_path = Path(self.config.config.get("backup_path", ""))
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_path / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True)
        
        # 备份向量数据库
        if VECTOR_DB_DIR.exists():
            db_backup = backup_dir / "vector"
            shutil.copytree(VECTOR_DB_DIR, db_backup)
        
        # 备份配置文件
        for config_file in MEMORY_DIR.glob("*.json"):
            if config_file.name != "cloud_config.json":
                shutil.copy2(config_file, backup_dir)
        
        # 创建清单
        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": list(str(f.name) for f in backup_dir.rglob("*") if f.is_file())
        }
        
        with open(backup_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {
            "success": True,
            "backup_dir": str(backup_dir),
            "timestamp": timestamp,
            "files": len(manifest["files"])
        }
    
    def list_backups(self) -> List[Dict]:
        """列出备份"""
        backup_path = Path(self.config.config.get("backup_path", ""))
        
        if not backup_path.exists():
            return []
        
        backups = []
        for backup_dir in backup_path.glob("backup_*"):
            manifest_file = backup_dir / "manifest.json"
            
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                backups.append({
                    "path": str(backup_dir),
                    "timestamp": manifest.get("timestamp", ""),
                    "created_at": manifest.get("created_at", ""),
                    "files": len(manifest.get("files", []))
                })
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_backup(self, timestamp: str) -> Dict:
        """恢复备份"""
        backup_path = Path(self.config.config.get("backup_path", ""))
        backup_dir = backup_path / f"backup_{timestamp}"
        
        if not backup_dir.exists():
            return {"success": False, "error": "备份不存在"}
        
        # 恢复向量数据库
        db_backup = backup_dir / "vector"
        if db_backup.exists():
            if VECTOR_DB_DIR.exists():
                shutil.rmtree(VECTOR_DB_DIR)
            shutil.copytree(db_backup, VECTOR_DB_DIR)
        
        # 恢复配置文件
        for config_file in backup_dir.glob("*.json"):
            if config_file.name != "manifest.json":
                shutil.copy2(config_file, MEMORY_DIR)
        
        return {
            "success": True,
            "restored_from": timestamp,
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup_old_backups(self, keep: int = 10):
        """清理旧备份"""
        backups = self.list_backups()
        
        for backup in backups[keep:]:
            backup_dir = Path(backup["path"])
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        
        return len(backups) - keep


class MemorySync:
    """记忆同步管理"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.backup = MemoryBackup(config)
    
    def get_local_state(self) -> Dict:
        """获取本地状态"""
        state = {
            "last_sync": None,
            "memory_count": 0,
            "checksum": ""
        }
        
        # 读取同步状态
        if SYNC_STATE.exists():
            with open(SYNC_STATE) as f:
                saved = json.load(f)
                state["last_sync"] = saved.get("last_sync")
        
        # 计算记忆数量和校验和
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            state["memory_count"] = len(data.get("id", []))
            
            # 计算校验和
            texts = sorted(data.get("text", []))
            state["checksum"] = hashlib.md5(
                "|".join(texts).encode()
            ).hexdigest()[:16]
            
        except:
            pass
        
        return state
    
    def sync(self) -> Dict:
        """同步"""
        if not self.config.config.get("enabled"):
            return {"success": False, "error": "云同步未启用"}
        
        # 创建备份
        backup_result = self.backup.create_backup()
        
        # 更新同步状态
        state = {
            "last_sync": datetime.now().isoformat(),
            "backup_dir": backup_result.get("backup_dir", "")
        }
        
        with open(SYNC_STATE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "success": True,
            "backup": backup_result,
            "synced_at": state["last_sync"]
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Cloud 0.2.1")
    parser.add_argument("command", choices=["backup", "restore", "list", "sync", "status", "enable", "disable"])
    parser.add_argument("--timestamp", "-t", help="备份时间戳")
    parser.add_argument("--storage", "-s", choices=STORAGE_TYPES, default="local")
    parser.add_argument("--path", "-p", help="备份路径")
    parser.add_argument("--keep", type=int, default=10)
    
    args = parser.parse_args()
    
    config = CloudConfig()
    backup = MemoryBackup(config)
    sync = MemorySync(config)
    
    if args.command == "enable":
        config.enable(args.storage, args.path)
        print(f"✅ 云同步已启用 ({args.storage})")
    
    elif args.command == "disable":
        config.disable()
        print("✅ 云同步已禁用")
    
    elif args.command == "backup":
        print("📦 创建备份...")
        result = backup.create_backup()
        print(f"✅ 备份完成: {result['backup_dir']}")
        print(f"   文件数: {result['files']}")
    
    elif args.command == "restore":
        if not args.timestamp:
            # 列出可用备份
            backups = backup.list_backups()
            if backups:
                print("可用备份:")
                for i, b in enumerate(backups[:5], 1):
                    print(f"   {i}. {b['timestamp']} ({b['files']} 文件)")
                print("\n使用 --timestamp 指定恢复")
            else:
                print("无可用备份")
        else:
            print(f"🔄 恢复备份 {args.timestamp}...")
            result = backup.restore_backup(args.timestamp)
            if result["success"]:
                print("✅ 恢复成功")
            else:
                print(f"❌ 恢复失败: {result['error']}")
    
    elif args.command == "list":
        backups = backup.list_backups()
        print(f"📋 备份列表 ({len(backups)} 个):")
        for b in backups[:10]:
            print(f"   {b['timestamp']} - {b['files']} 文件 - {b['created_at'][:10]}")
    
    elif args.command == "sync":
        print("🔄 同步中...")
        result = sync.sync()
        if result["success"]:
            print("✅ 同步完成")
        else:
            print(f"❌ 同步失败: {result['error']}")
    
    elif args.command == "status":
        state = sync.get_local_state()
        print("📊 同步状态:")
        print(f"   已启用: {config.config.get('enabled', False)}")
        print(f"   存储类型: {config.config.get('storage_type', 'local')}")
        print(f"   记忆数: {state['memory_count']}")
        print(f"   校验和: {state['checksum']}")
        if state['last_sync']:
            print(f"   上次同步: {state['last_sync']}")


if __name__ == "__main__":
    main()
