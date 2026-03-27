#!/usr/bin/env python3
"""
Memory Privacy - 隐私保护 v0.2.1

功能:
- 敏感信息检测
- 自动加密
- 访问日志
- 数据脱敏

Usage:
    python3 scripts/memory_privacy.py scan
    python3 scripts/memory_privacy.py encrypt --text "敏感信息"
    python3 scripts/memory_privacy.py audit-log
"""

import argparse
import base64
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
PRIVACY_CONFIG = MEMORY_DIR / "privacy_config.json"
AUDIT_LOG = MEMORY_DIR / "audit.log"

# 敏感信息模式
SENSITIVE_PATTERNS = {
    "password": [
        r"密码[是为：:]\s*\S+",
        r"password[=:]\s*\S+",
        r"pwd[=:]\s*\S+",
    ],
    "token": [
        r"token[=:]\s*\S+",
        r"令牌[是为：:]\s*\S+",
        r"Bearer\s+\S+",
    ],
    "api_key": [
        r"api_key[=:]\s*\S+",
        r"apikey[=:]\s*\S+",
        r"密钥[是为：:]\s*\S+",
    ],
    "phone": [
        r"1[3-9]\d{9}",
    ],
    "email": [
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    ],
    "id_card": [
        r"\d{17}[\dXx]",
    ],
    "bank_card": [
        r"\d{16,19}",
    ]
}

# 脱敏规则
MASK_RULES = {
    "password": "******",
    "token": "***TOKEN***",
    "api_key": "***KEY***",
    "phone": lambda x: x[:3] + "****" + x[-4:] if len(x) == 11 else x,
    "email": lambda x: x.split("@")[0][:2] + "***@" + x.split("@")[1],
    "id_card": lambda x: x[:6] + "********" + x[-4:],
    "bank_card": lambda x: x[:4] + "****" + x[-4:],
}


def get_encryption_key() -> bytes:
    """获取加密密钥"""
    key_file = MEMORY_DIR / ".enc_key"
    
    if key_file.exists():
        with open(key_file, 'rb') as f:
            return f.read()
    
    # 生成新密钥
    key = os.urandom(32)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    with open(key_file, 'wb') as f:
        f.write(key)
    
    # 设置权限
    os.chmod(key_file, 0o600)
    
    return key


def encrypt_text(text: str) -> str:
    """加密文本"""
    key = get_encryption_key()
    
    # 简单 XOR 加密（生产环境应使用更强加密）
    text_bytes = text.encode('utf-8')
    encrypted = bytearray()
    
    for i, byte in enumerate(text_bytes):
        encrypted.append(byte ^ key[i % len(key)])
    
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_text(encrypted: str) -> str:
    """解密文本"""
    key = get_encryption_key()
    
    try:
        encrypted_bytes = base64.b64decode(encrypted.encode('utf-8'))
        decrypted = bytearray()
        
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ key[i % len(key)])
        
        return decrypted.decode('utf-8')
    except:
        return encrypted


def detect_sensitive(text: str) -> List[Dict]:
    """检测敏感信息"""
    findings = []
    
    for sensitive_type, patterns in SENSITIVE_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": sensitive_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
    
    return findings


def mask_sensitive(text: str, findings: List[Dict] = None) -> str:
    """脱敏敏感信息"""
    if findings is None:
        findings = detect_sensitive(text)
    
    # 按位置倒序排序
    findings_sorted = sorted(findings, key=lambda x: x["start"], reverse=True)
    
    result = text
    for finding in findings_sorted:
        mask = MASK_RULES.get(finding["type"], "***")
        
        # 如果是函数，调用它
        if callable(mask):
            mask = mask(finding["value"])
        
        result = result[:finding["start"]] + mask + result[finding["end"]:]
    
    return result


def log_access(action: str, memory_id: str = "", details: str = ""):
    """记录访问日志"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = f"[{datetime.now().isoformat()}] {action} {memory_id} {details}\n"
    
    with open(AUDIT_LOG, 'a') as f:
        f.write(log_entry)


def scan_memories() -> Dict:
    """扫描所有记忆中的敏感信息"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        results = {
            "total_scanned": 0,
            "sensitive_found": 0,
            "by_type": {},
            "items": []
        }
        
        count = len(data.get("id", []))
        results["total_scanned"] = count
        
        for i in range(count):
            text = data["text"][i] if i < len(data.get("text", [])) else ""
            memory_id = data["id"][i] if i < len(data.get("id", [])) else ""
            
            findings = detect_sensitive(text)
            
            if findings:
                results["sensitive_found"] += 1
                
                for f in findings:
                    f_type = f["type"]
                    results["by_type"][f_type] = results["by_type"].get(f_type, 0) + 1
                
                results["items"].append({
                    "id": memory_id[:8],
                    "text": text[:50],
                    "findings": len(findings)
                })
        
        return results
        
    except Exception as e:
        return {"error": str(e)}


def get_audit_log(limit: int = 20) -> List[Dict]:
    """获取访问日志"""
    if not AUDIT_LOG.exists():
        return []
    
    with open(AUDIT_LOG) as f:
        lines = f.readlines()[-limit:]
    
    logs = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4:
            logs.append({
                "timestamp": parts[0].strip("[]"),
                "action": parts[1],
                "memory_id": parts[2] if len(parts) > 2 else "",
                "details": " ".join(parts[3:]) if len(parts) > 3 else ""
            })
    
    return logs


def main():
    parser = argparse.ArgumentParser(description="Memory Privacy 0.2.1")
    parser.add_argument("command", choices=["scan", "encrypt", "decrypt", "audit-log", "mask"])
    parser.add_argument("--text", "-t", help="文本内容")
    parser.add_argument("--limit", type=int, default=20)
    
    args = parser.parse_args()
    
    if args.command == "scan":
        print("🔍 扫描敏感信息...")
        results = scan_memories()
        
        print(f"\n扫描结果:")
        print(f"   总计: {results.get('total_scanned', 0)} 条")
        print(f"   敏感: {results.get('sensitive_found', 0)} 条")
        
        if results.get("by_type"):
            print(f"\n按类型:")
            for t, count in results["by_type"].items():
                print(f"   {t}: {count}")
        
        if results.get("items"):
            print(f"\n示例:")
            for item in results["items"][:3]:
                print(f"   [{item['id']}] {item['text']}... ({item['findings']} 处)")
    
    elif args.command == "encrypt":
        if not args.text:
            print("请提供文本")
            return
        encrypted = encrypt_text(args.text)
        print(f"🔐 加密后: {encrypted}")
    
    elif args.command == "decrypt":
        if not args.text:
            print("请提供加密文本")
            return
        decrypted = decrypt_text(args.text)
        print(f"🔓 解密后: {decrypted}")
    
    elif args.command == "audit-log":
        logs = get_audit_log(args.limit)
        print(f"📋 访问日志 ({len(logs)} 条):")
        for log in logs:
            print(f"   [{log['timestamp']}] {log['action']} {log['memory_id']}")
    
    elif args.command == "mask":
        if not args.text:
            print("请提供文本")
            return
        masked = mask_sensitive(args.text)
        print(f"🎭 脱敏后: {masked}")


if __name__ == "__main__":
    main()
