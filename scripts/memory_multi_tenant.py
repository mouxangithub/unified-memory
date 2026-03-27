#!/usr/bin/env python3
"""
多用户/租户隔离 - Multi-Tenant Isolation

核心：用户隔离、权限控制、访问审计
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
TENANT_DIR = MEMORY_DIR / "tenants"


class MultiTenantMemory:
    """多租户记忆系统"""
    
    def __init__(self):
        TENANT_DIR.mkdir(parents=True, exist_ok=True)
        self.config_file = TENANT_DIR / "config.json"
        self.current_user = None
        self.current_tenant = None
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "tenants": {},      # tenant_id -> {name, created_at}
            "users": {},        # user_id -> {name, tenant_id, role}
            "permissions": {},   # memory_id -> {owner, shared_with: {user_id: permission}}
            "audit_log": []
        }
    
    def _save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _log(self, action: str, user_id: str, target: str, detail: str = ""):
        """审计日志"""
        self.config["audit_log"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_id": user_id,
            "target": target,
            "detail": detail
        })
        # 只保留最近 1000 条
        if len(self.config["audit_log"]) > 1000:
            self.config["audit_log"] = self.config["audit_log"][-1000:]
        self._save_config()
    
    # ===== 租户管理 =====
    
    def create_tenant(self, name: str) -> str:
        """创建租户"""
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        self.config["tenants"][tenant_id] = {
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        self._save_config()
        self._log("create_tenant", "system", tenant_id, name)
        return tenant_id
    
    def list_tenants(self) -> List[Dict]:
        """列出租户"""
        return [
            {"id": tid, **info}
            for tid, info in self.config["tenants"].items()
        ]
    
    # ===== 用户管理 =====
    
    def create_user(self, name: str, tenant_id: str = None, role: str = "user") -> str:
        """创建用户"""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        if tenant_id is None:
            tenant_id = list(self.config["tenants"].keys())[0] if self.config["tenants"] else None
        
        self.config["users"][user_id] = {
            "name": name,
            "tenant_id": tenant_id,
            "role": role,
            "created_at": datetime.now().isoformat()
        }
        self._save_config()
        self._log("create_user", "system", user_id, f"{name} in {tenant_id}")
        return user_id
    
    def list_users(self, tenant_id: str = None) -> List[Dict]:
        """列出用户"""
        users = self.config["users"]
        if tenant_id:
            users = {uid: u for uid, u in users.items() if u["tenant_id"] == tenant_id}
        return [{"id": uid, **info} for uid, info in users.items()]
    
    # ===== 上下文切换 =====
    
    def set_user(self, user_id: str):
        """设置当前用户"""
        if user_id in self.config["users"]:
            self.current_user = user_id
            self.current_tenant = self.config["users"][user_id]["tenant_id"]
            return True
        return False
    
    def set_tenant(self, tenant_id: str):
        """设置当前租户"""
        if tenant_id in self.config["tenants"]:
            self.current_tenant = tenant_id
            self.current_user = None
            return True
        return False
    
    def get_current_context(self) -> Dict:
        """获取当前上下文"""
        return {
            "user_id": self.current_user,
            "tenant_id": self.current_tenant,
            "user_name": self.config["users"].get(self.current_user, {}).get("name", "Unknown"),
            "tenant_name": self.config["tenants"].get(self.current_tenant, {}).get("name", "Unknown")
        }
    
    # ===== 权限控制 =====
    
    def set_permission(self, memory_id: str, user_id: str, permission: str):
        """
        设置权限
        
        permission: read / write / admin
        """
        if memory_id not in self.config["permissions"]:
            self.config["permissions"][memory_id] = {
                "owner": None,
                "shared_with": {}
            }
        
        self.config["permissions"][memory_id]["shared_with"][user_id] = permission
        self._save_config()
        self._log("set_permission", self.current_user or "system", memory_id, f"{user_id}: {permission}")
    
    def check_permission(self, memory_id: str, user_id: str = None, required: str = "read") -> bool:
        """检查权限"""
        if user_id is None:
            user_id = self.current_user
        
        if not user_id:
            return False
        
        perms = self.config["permissions"].get(memory_id, {})
        
        # 所有者有所有权限
        if perms.get("owner") == user_id:
            return True
        
        # 检查共享权限
        user_perm = perms.get("shared_with", {}).get(user_id)
        if not user_perm:
            return False
        
        # 权限等级：admin > write > read
        perm_levels = {"read": 1, "write": 2, "admin": 3}
        return perm_levels.get(user_perm, 0) >= perm_levels.get(required, 0)
    
    def make_private(self, memory_id: str):
        """设为私有（只自己可访问）"""
        if memory_id not in self.config["permissions"]:
            self.config["permissions"][memory_id] = {"owner": None, "shared_with": {}}
        
        self.config["permissions"][memory_id]["owner"] = self.current_user
        self.config["permissions"][memory_id]["shared_with"] = {}
        self._save_config()
        self._log("make_private", self.current_user, memory_id)
    
    def share_with(self, memory_id: str, user_id: str, permission: str = "read"):
        """共享给其他用户"""
        if memory_id not in self.config["permissions"]:
            self.make_private(memory_id)
        
        self.set_permission(memory_id, user_id, permission)
    
    def revoke_share(self, memory_id: str, user_id: str):
        """撤销共享"""
        if memory_id in self.config["permissions"]:
            self.config["permissions"][memory_id]["shared_with"].pop(user_id, None)
            self._save_config()
            self._log("revoke_share", self.current_user, memory_id, user_id)
    
    # ===== 过滤和查询 =====
    
    def filter_by_access(self, memories: List[Dict], user_id: str = None) -> List[Dict]:
        """根据用户权限过滤记忆"""
        if user_id is None:
            user_id = self.current_user
        
        if not user_id:
            return []
        
        filtered = []
        for mem in memories:
            mem_id = mem.get("id", "")
            
            # 检查权限
            if self.check_permission(mem_id, user_id, "read"):
                filtered.append(mem)
        
        return filtered
    
    def filter_by_tenant(self, memories: List[Dict], tenant_id: str = None) -> List[Dict]:
        """根据租户过滤记忆"""
        if tenant_id is None:
            tenant_id = self.current_tenant
        
        if not tenant_id:
            return []
        
        filtered = []
        for mem in memories:
            if mem.get("tenant_id") == tenant_id or mem.get("tenant_id") is None:
                filtered.append(mem)
        
        return filtered
    
    # ===== 审计 =====
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        return self.config["audit_log"][-limit:]
    
    def search_audit(self, user_id: str = None, action: str = None) -> List[Dict]:
        """搜索审计日志"""
        logs = self.config["audit_log"]
        
        if user_id:
            logs = [l for l in logs if l["user_id"] == user_id]
        if action:
            logs = [l for l in logs if l["action"] == action]
        
        return logs
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "total_tenants": len(self.config["tenants"]),
            "total_users": len(self.config["users"]),
            "total_permissions": len(self.config["permissions"]),
            "audit_log_size": len(self.config["audit_log"])
        }


# 全局实例
_tenant = None

def get_multi_tenant() -> MultiTenantMemory:
    global _tenant
    if _tenant is None:
        _tenant = MultiTenantMemory()
    return _tenant


if __name__ == "__main__":
    print("=" * 50)
    print("多租户隔离测试")
    print("=" * 50)
    
    mt = MultiTenantMemory()
    
    # 创建租户
    t1 = mt.create_tenant("公司A")
    t2 = mt.create_tenant("公司B")
    print(f"\n🏢 创建租户: {t1}, {t2}")
    
    # 创建用户
    u1 = mt.create_user("刘总", t1, "admin")
    u2 = mt.create_user("员工甲", t1, "user")
    u3 = mt.create_user("王总", t2, "admin")
    print(f"👥 创建用户: {u1}, {u2}, {u3}")
    
    # 设置当前用户
    mt.set_user(u1)
    print(f"\n🔐 当前上下文: {mt.get_current_context()}")
    
    # 设置权限
    mt.share_with("mem_123", u2, "read")
    print(f"📤 共享 mem_123 给 {u2}")
    
    # 检查权限
    print(f"🔍 {u1} 读 mem_123: {mt.check_permission('mem_123', u1, 'read')}")
    print(f"🔍 {u2} 读 mem_123: {mt.check_permission('mem_123', u2, 'read')}")
    print(f"🔍 {u3} 读 mem_123: {mt.check_permission('mem_123', u3, 'read')}")
    
    # 审计日志
    print(f"\n📋 审计日志: {len(mt.get_audit_log())} 条")
    
    print(f"\n📊 统计: {mt.get_stats()}")
    
    print("\n✅ 多租户隔离测试完成")
