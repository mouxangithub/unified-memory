#!/usr/bin/env python3
import base64
from pathlib import Path
"""
隐私计算 - Privacy Computing

支持：
- 本地加密
- 差分隐私
- 隐私检索
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
PRIVACY_DIR = MEMORY_DIR / "privacy"


class PrivacyComputing:
    """
    隐私计算引擎
    
    功能：
    1. 本地加密存储
    2. 差分隐私噪声
    3. 隐私检索（密文搜索）
    """
    
    def __init__(self, key: bytes = None):
        PRIVACY_DIR.mkdir(parents=True, exist_ok=True)
        
        # 密钥管理
        self.key_file = PRIVACY_DIR / ".key"
        self.key = key or self._load_or_create_key()
        
        # 加密器
        self._init_encryptor()
    
    def _load_or_create_key(self) -> bytes:
        """加载或创建密钥"""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        
        # 生成随机密钥
        key = os.urandom(32)  # 256-bit
        self.key_file.write_bytes(key)
        os.chmod(self.key_file, 0o600)  # 只自己可读
        return key
    
    def _init_encryptor(self):
        """初始化加密器"""
        try:
            from cryptography.fernet import Fernet
            # 使用 Fernet (AES-128-CBC + HMAC)
            fernet_key = base64.urlsafe_b64encode(hashlib.sha256(self.key).digest())
            self.fernet = Fernet(fernet_key)
        except ImportError:
            # 降级：简单 XOR
            self.fernet = None
    
    def _xor_encrypt(self, data: str, key: bytes) -> str:
        """简单 XOR 加密（降级方案）"""
        key_bytes = key * (len(data) // len(key) + 1)
        encrypted = bytes(a ^ b for a, b in zip(data.encode(), key_bytes))
        import base64
        return base64.b64encode(encrypted).decode()
    
    def _xor_decrypt(self, encrypted: str, key: bytes) -> str:
        """XOR 解密"""
        import base64
        encrypted_bytes = base64.b64decode(encrypted.encode())
        key_bytes = key * (len(encrypted_bytes) // len(key) + 1)
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_bytes))
        return decrypted.decode()
    
    def encrypt(self, text: str) -> str:
        """加密文本"""
        if self.fernet:
            return self.fernet.encrypt(text.encode()).decode()
        else:
            return self._xor_encrypt(text, self.key)
    
    def decrypt(self, encrypted: str) -> str:
        """解密文本"""
        if self.fernet:
            return self.fernet.decrypt(encrypted.encode()).decode()
        else:
            return self._xor_decrypt(encrypted, self.key)
    
    def encrypt_memory(self, memory: Dict) -> Dict:
        """
        加密记忆
        
        记忆的 text 字段被加密，其他字段保持明文
        """
        encrypted = memory.copy()
        
        if "text" in memory:
            encrypted["text_encrypted"] = self.encrypt(memory["text"])
            encrypted["text"] = None  # 明文清除
            encrypted["is_encrypted"] = True
        
        return encrypted
    
    def decrypt_memory(self, encrypted_memory: Dict) -> Dict:
        """解密记忆"""
        if not encrypted_memory.get("is_encrypted"):
            return encrypted_memory
        
        decrypted = encrypted_memory.copy()
        
        if "text_encrypted" in encrypted_memory:
            decrypted["text"] = self.decrypt(encrypted_memory["text_encrypted"])
            decrypted["text_encrypted"] = None
            decrypted["is_encrypted"] = False
        
        return decrypted


class DifferentialPrivacy:
    """
    差分隐私
    
    用于：
    - 添加噪声到向量
    - 聚合查询时不暴露个人数据
    """
    
    def __init__(self, epsilon: float = 1.0):
        """
        Args:
            epsilon: 隐私预算，越小越隐私
        """
        self.epsilon = epsilon
    
    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """添加拉普拉斯噪声"""
        import numpy as np
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    
    def add_noise_to_vector(self, vector: List[float], sensitivity: float = 1.0) -> List[float]:
        """给向量添加噪声"""
        return [self.add_laplace_noise(v, sensitivity) for v in vector]
    
    def noisy_count(self, true_count: int, sensitivity: float = 1.0) -> int:
        """添加噪声的计数"""
        noisy = self.add_laplace_noise(float(true_count), sensitivity)
        return max(0, int(noisy))
    
    def noisy_average(self, values: List[float], sensitivity: float = 1.0) -> float:
        """添加噪声的平均值"""
        if not values:
            return 0.0
        true_avg = sum(values) / len(values)
        noisy_avg = self.add_laplace_noise(true_avg, sensitivity / len(values))
        return noisy_avg
    
    def private_histogram(self, values: List, bins: int = 10) -> Dict:
        """
        私有直方图
        
        对每个 bin 的计数添加噪声
        """
        import numpy as np
        
        # 计算真实直方图
        hist, edges = np.histogram(values, bins=bins)
        
        # 添加噪声
        noisy_hist = [self.noisy_count(int(h)) for h in hist]
        
        return {
            "bins": bins,
            "counts": noisy_hist,
            "epsilon": self.epsilon
        }


class PrivacySearch:
    """
    隐私检索
    
    思想：
    - 不存储明文向量
    - 使用加密向量搜索（ homomorphism encryption 或保序加密）
    """
    
    def __init__(self, privacy: PrivacyComputing):
        self.privacy = privacy
    
    def searchable_encrypt(self, text: str, keywords: List[str] = None) -> Dict:
        """
        可搜索加密
        
        保留关键词用于搜索，但加密原文
        """
        if keywords is None:
            # 自动提取关键词
            keywords = self._extract_keywords(text)
        
        return {
            "encrypted_text": self.privacy.encrypt(text),
            "keywords": keywords,  # 关键词不加密（用于搜索）
            "keyword_hashes": [self._hash_keyword(kw) for kw in keywords]
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单分词
        words = text.replace(",", " ").replace("。", " ").replace("！", " ").split()
        
        # 过滤停用词
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "以及", "等", "这", "那"}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        return list(set(keywords))[:10]
    
    def _hash_keyword(self, keyword: str) -> str:
        """关键词哈希"""
        return hashlib.sha256(keyword.encode()).hexdigest()[:16]
    
    def search(self, query: str, encrypted_items: List[Dict]) -> List[Dict]:
        """
        隐私搜索
        
        只匹配关键词，不解密原文
        """
        query_keywords = self._extract_keywords(query)
        query_hashes = [self._hash_keyword(kw) for kw in query_keywords]
        
        results = []
        for item in encrypted_items:
            # 检查关键词匹配
            item_hashes = set(item.get("keyword_hashes", []))
            query_hash_set = set(query_hashes)
            
            overlap = item_hashes & query_hash_set
            if overlap:
                # 匹配成功
                results.append({
                    **item,
                    "match_score": len(overlap) / max(len(item_hashes), len(query_hash_set))
                })
        
        # 按匹配度排序
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return results


# 全局实例
_privacy = None

def get_privacy_computing() -> PrivacyComputing:
    global _privacy
    if _privacy is None:
        _privacy = PrivacyComputing()
    return _privacy


if __name__ == "__main__":
    print("=" * 50)
    print("隐私计算测试")
    print("=" * 50)
    
    privacy = PrivacyComputing()
    
    # 测试加密
    print("\n🔐 加密测试:")
    original = "用户喜欢简洁的界面"
    encrypted = privacy.encrypt(original)
    decrypted = privacy.decrypt(encrypted)
    print(f"  原文: {original}")
    print(f"  密文: {encrypted[:50]}...")
    print(f"  解密: {decrypted}")
    
    # 测试记忆加密
    print("\n📝 记忆加密:")
    memory = {"id": "mem_1", "text": "这是一个秘密", "category": "secret"}
    enc_mem = privacy.encrypt_memory(memory)
    print(f"  原文: {enc_mem.get('text')}")
    print(f"  密文: {enc_mem.get('text_encrypted', '')[:30]}...")
    
    # 差分隐私
    print("\n📊 差分隐私:")
    dp = DifferentialPrivacy(epsilon=1.0)
    
    import numpy as np
    np.random.seed(42)
    
    true_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    noisy_values = [dp.add_laplace_noise(v, sensitivity=1.0) for v in true_values]
    
    print(f"  真实值: {true_values[:5]}...")
    print(f"  加噪后: {[round(v, 2) for v in noisy_values[:5]]}...")
    
    # 隐私搜索
    print("\n🔍 隐私搜索:")
    search = PrivacySearch(privacy)
    
    item = search.searchable_encrypt("用户喜欢简洁的界面", ["用户", "简洁", "界面"])
    print(f"  加密文本: {item['encrypted_text'][:30]}...")
    print(f"  关键词: {item['keywords']}")
    
    results = search.search("简洁界面", [item])
    print(f"  搜索'简洁界面': 找到 {len(results)} 条")
    
    print("\n✅ 隐私计算测试完成")
