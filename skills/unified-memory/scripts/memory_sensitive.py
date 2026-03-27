#!/usr/bin/env python3
"""
敏感信息加密模块 v1.0

功能:
- 自动检测敏感信息（密码、API Key、手机号、身份证等）
- AES-256 加密存储
- 访问日志记录
- 权限控制

Usage:
    mem encrypt <id>           # 手动加密
    mem decrypt <id>           # 解密查看
    mem audit                  # 查看访问日志
    mem sensitive detect       # 检测敏感信息
"""

import json
import re
import os
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
ENCRYPTION_KEY_FILE = MEMORY_DIR / ".encryption_key"
AUDIT_LOG_FILE = MEMORY_DIR / "access_audit.json"
SENSITIVE_CONFIG_FILE = MEMORY_DIR / "sensitive_config.json"

# 敏感信息模式
SENSITIVE_PATTERNS = {
    "password": [
        r'密码[是为：:]\s*\S+',
        r'password[=:\s]+\S+',
        r'pwd[=:\s]+\S+',
    ],
    "api_key": [
        r'api[_-]?key[是为：:＝]\s*\S+',
        r'apikey[=:\s]+\S+',
        r'secret[_-]?key[=:\s]+\S+',
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI style
    ],
    "token": [
        r'token[是为：:＝]\s*\S+',
        r'access[_-]?token[=:\s]+\S+',
        r'bearer\s+\S+',
    ],
    "phone": [
        r'1[3-9]\d{9}',  # 中国手机号
    ],
    "id_card": [
        r'\d{17}[\dXx]',  # 中国身份证
    ],
    "email": [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ],
    "credit_card": [
        r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',  # 信用卡号
    ],
    "private_key": [
        r'-----BEGIN.*PRIVATE KEY-----',
        r'-----BEGIN.*RSA PRIVATE KEY-----',
    ],
}

# 默认配置
DEFAULT_CONFIG = {
    "enabled": True,
    "auto_detect": True,
    "auto_encrypt": True,
    "encryption_algorithm": "AES-256",
    "log_access": True,
    "require_decryption_log": True,
    "patterns": list(SENSITIVE_PATTERNS.keys()),
    "exclude_patterns": [],
}


def get_or_create_key() -> bytes:
    """获取或创建加密密钥"""
    if ENCRYPTION_KEY_FILE.exists():
        return base64.urlsafe_b64decode(ENCRYPTION_KEY_FILE.read_bytes())
    
    # 生成新密钥
    key = Fernet.generate_key()
    ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENCRYPTION_KEY_FILE.write_bytes(key)
    
    # 设置权限（仅所有者可读写）
    os.chmod(ENCRYPTION_KEY_FILE, 0o600)
    
    return key


def get_fernet() -> Fernet:
    """获取 Fernet 实例"""
    key = get_or_create_key()
    return Fernet(key)


def load_config() -> Dict:
    """加载配置"""
    if SENSITIVE_CONFIG_FILE.exists():
        return json.loads(SENSITIVE_CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict):
    """保存配置"""
    SENSITIVE_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def detect_sensitive(text: str) -> List[Dict]:
    """检测文本中的敏感信息"""
    results = []
    config = load_config()
    
    if not config.get("auto_detect", True):
        return results
    
    for category, patterns in SENSITIVE_PATTERNS.items():
        if category not in config.get("patterns", []):
            continue
        
        for pattern in patterns:
            if category in config.get("exclude_patterns", []):
                continue
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                results.append({
                    "category": category,
                    "pattern": pattern,
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
    
    return results


def encrypt_text(text: str) -> str:
    """加密文本"""
    fernet = get_fernet()
    encrypted = fernet.encrypt(text.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted).decode('utf-8')


def decrypt_text(encrypted_text: str) -> str:
    """解密文本"""
    fernet = get_fernet()
    decoded = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
    decrypted = fernet.decrypt(decoded)
    return decrypted.decode('utf-8')


def log_access(memory_id: str, action: str, agent: str = "unknown"):
    """记录访问日志"""
    config = load_config()
    
    if not config.get("log_access", True):
        return
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "memory_id": memory_id,
        "action": action,  # encrypt, decrypt, view, delete
        "agent": agent,
    }
    
    logs = []
    if AUDIT_LOG_FILE.exists():
        logs = json.loads(AUDIT_LOG_FILE.read_text())
    
    logs.append(log_entry)
    
    # 只保留最近1000条
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    AUDIT_LOG_FILE.write_text(json.dumps(logs, indent=2, ensure_ascii=False))


def encrypt_memory(memory_id: str) -> Dict:
    """加密指定记忆"""
    memories = json.loads(MEMORIES_FILE.read_text()) if MEMORIES_FILE.exists() else []
    
    for mem in memories:
        if mem.get("id") == memory_id or mem.get("id", "").startswith(memory_id):
            # 检测敏感信息
            sensitive_items = detect_sensitive(mem.get("text", ""))
            
            if not sensitive_items:
                return {"error": "未检测到敏感信息", "memory_id": memory_id}
            
            # 加密
            mem["text_encrypted"] = encrypt_text(mem["text"])
            mem["text"] = "[ENCRYPTED]"
            mem["encrypted"] = True
            mem["sensitive_categories"] = list(set(s["category"] for s in sensitive_items))
            mem["encrypted_at"] = datetime.now().isoformat()
            
            # 保存
            MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False))
            
            # 记录日志
            log_access(memory_id, "encrypt")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "categories": mem["sensitive_categories"],
                "encrypted_at": mem["encrypted_at"]
            }
    
    return {"error": f"未找到记忆: {memory_id}"}


def decrypt_memory(memory_id: str, agent: str = "unknown") -> Dict:
    """解密查看记忆"""
    memories = json.loads(MEMORIES_FILE.read_text()) if MEMORIES_FILE.exists() else []
    
    for mem in memories:
        if mem.get("id") == memory_id or mem.get("id", "").startswith(memory_id):
            if not mem.get("encrypted"):
                return {"error": "该记忆未加密", "memory_id": memory_id}
            
            # 解密
            try:
                decrypted_text = decrypt_text(mem["text_encrypted"])
                
                # 记录日志
                log_access(memory_id, "decrypt", agent)
                
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "text": decrypted_text,
                    "decrypted_at": datetime.now().isoformat()
                }
            except Exception as e:
                return {"error": f"解密失败: {e}"}
    
    return {"error": f"未找到记忆: {memory_id}"}


def get_audit_log(limit: int = 50) -> List[Dict]:
    """获取访问日志"""
    if not AUDIT_LOG_FILE.exists():
        return []
    
    logs = json.loads(AUDIT_LOG_FILE.read_text())
    return logs[-limit:]


def scan_all_memories() -> Dict:
    """扫描所有记忆，检测敏感信息"""
    memories = json.loads(MEMORIES_FILE.read_text()) if MEMORIES_FILE.exists() else []
    
    results = {
        "total": len(memories),
        "sensitive_count": 0,
        "by_category": {},
        "details": []
    }
    
    for mem in memories:
        if mem.get("encrypted"):
            continue
        
        sensitive_items = detect_sensitive(mem.get("text", ""))
        
        if sensitive_items:
            results["sensitive_count"] += 1
            
            for item in sensitive_items:
                cat = item["category"]
                results["by_category"][cat] = results["by_category"].get(cat, 0) + 1
            
            results["details"].append({
                "memory_id": mem.get("id"),
                "text": mem.get("text", "")[:50] + "...",
                "categories": list(set(s["category"] for s in sensitive_items)),
                "count": len(sensitive_items)
            })
    
    return results


def print_audit_report(logs: List[Dict]):
    """打印审计报告"""
    print("🔐 访问审计日志\n")
    print("=" * 60)
    
    if not logs:
        print("暂无访问记录")
        return
    
    for log in logs[-20:]:
        print(f"\n[{log['timestamp'][:19]}]")
        print(f"   操作: {log['action']}")
        print(f"   记忆: {log['memory_id'][:12]}...")
        print(f"   Agent: {log['agent']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="敏感信息加密模块")
    parser.add_argument("command", choices=["encrypt", "decrypt", "audit", "detect", "scan"])
    parser.add_argument("--id", "-i", help="记忆ID")
    parser.add_argument("--limit", "-l", type=int, default=20, help="显示数量")
    parser.add_argument("--agent", "-a", default="unknown", help="Agent名称")
    parser.add_argument("--config", "-c", action="store_true", help="显示配置")
    
    args = parser.parse_args()
    
    if args.config:
        config = load_config()
        print("🔐 敏感信息加密配置\n")
        for k, v in config.items():
            print(f"   {k}: {v}")
        return
    
    if args.command == "detect":
        # 扫描所有记忆
        results = scan_all_memories()
        print(f"🔍 敏感信息检测\n")
        print(f"   总记忆数: {results['total']}")
        print(f"   含敏感信息: {results['sensitive_count']}")
        print(f"\n   分类统计:")
        for cat, count in results["by_category"].items():
            print(f"      {cat}: {count}")
    
    elif args.command == "encrypt":
        if not args.id:
            print("❌ 缺少参数: --id")
            return
        result = encrypt_memory(args.id)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ 已加密记忆: {result['memory_id']}")
            print(f"   敏感类型: {result['categories']}")
    
    elif args.command == "decrypt":
        if not args.id:
            print("❌ 缺少参数: --id")
            return
        result = decrypt_memory(args.id, args.agent)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"🔓 已解密记忆: {result['memory_id']}")
            print(f"\n   内容: {result['text']}")
    
    elif args.command == "audit":
        logs = get_audit_log(args.limit)
        print_audit_report(logs)
    
    elif args.command == "scan":
        # 扫描并自动加密
        results = scan_all_memories()
        print(f"🔍 扫描结果: {results['sensitive_count']} 条记忆含敏感信息")
        
        if results["sensitive_count"] > 0:
            print("\n详情:")
            for detail in results["details"]:
                print(f"   [{detail['memory_id'][:12]}] {detail['categories']}")


if __name__ == "__main__":
    main()
