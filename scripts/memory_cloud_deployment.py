#!/usr/bin/env python3
from pathlib import Path
"""
端侧部署 + 云端降级

支持：本地 Ollama → 云端 API → 纯 BM25 三级降级
"""

import json
import requests
from typing import Dict, List, Optional
from enum import Enum

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class ServiceMode(Enum):
    LOCAL = "local"       # 本地 Ollama
    CLOUD = "cloud"       # 云端 API
    BM25 = "bm25"         # 纯 BM25


class CloudDeployment:
    """云端部署管理器"""
    
    def __init__(self):
        self.config_file = MEMORY_DIR / "cloud_config.json"
        self.config = self._load_config()
        self.current_mode = self._detect_mode()
    
    def _load_config(self) -> Dict:
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {
            "ollama_url": "http://localhost:11434",
            "cloud_endpoints": {
                "openai": "https://api.openai.com/v1",
                "anthropic": "https://api.anthropic.com",
                "cohere": "https://api.cohere.ai"
            },
            "preferred_cloud": "openai",
            "api_keys": {}
        }
    
    def _save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def _detect_mode(self) -> ServiceMode:
        """检测当前可用服务"""
        # 1. 检测 Ollama
        try:
            resp = requests.get(
                f"{self.config['ollama_url']}/api/tags",
                timeout=3
            )
            if resp.status_code == 200:
                return ServiceMode.LOCAL
        except:
            pass
        
        # 2. 检测云端
        if self._test_cloud():
            return ServiceMode.CLOUD
        
        # 3. 降级 BM25
        return ServiceMode.BM25
    
    def _test_cloud(self) -> bool:
        """测试云端连接"""
        provider = self.config.get("preferred_cloud")
        if not provider or provider not in self.config["api_keys"]:
            return False
        
        # 简单测试
        try:
            if provider == "openai":
                resp = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.config['api_keys'][provider]}"},
                    timeout=5
                )
                return resp.status_code == 200
        except:
            pass
        return False
    
    def set_api_key(self, provider: str, api_key: str):
        """设置 API Key"""
        self.config["api_keys"][provider] = api_key
        self._save_config()
        self.current_mode = self._detect_mode()
    
    def set_ollama_url(self, url: str):
        """设置 Ollama URL"""
        self.config["ollama_url"] = url
        self._save_config()
        self.current_mode = self._detect_mode()
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取向量（自动选择服务）"""
        if self.current_mode == ServiceMode.LOCAL:
            return self._get_ollama_embedding(text)
        elif self.current_mode == ServiceMode.CLOUD:
            return self._get_cloud_embedding(text)
        else:
            return None  # BM25 模式不需要向量
    
    def _get_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """Ollama 向量"""
        try:
            resp = requests.post(
                f"{self.config['ollama_url']}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
        except:
            pass
        return None
    
    def _get_cloud_embedding(self, text: str) -> Optional[List[float]]:
        """云端向理"""
        provider = self.config.get("preferred_cloud")
        
        try:
            if provider == "openai":
                resp = requests.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.config['api_keys'][provider]}",
                        "Content-Type": "application/json"
                    },
                    json={"model": "text-embedding-3-small", "input": text},
                    timeout=30
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
        except:
            pass
        return None
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "mode": self.current_mode.value,
            "ollama_url": self.config["ollama_url"],
            "cloud_available": self.current_mode == ServiceMode.CLOUD,
            "bm25_fallback": self.current_mode == ServiceMode.BM25
        }
    
    def force_mode(self, mode: str):
        """强制指定模式"""
        if mode == "local":
            self.current_mode = ServiceMode.LOCAL
        elif mode == "cloud":
            self.current_mode = ServiceMode.CLOUD
        elif mode == "bm25":
            self.current_mode = ServiceMode.BM25


# 全局实例
_cloud = None

def get_cloud_deployment() -> CloudDeployment:
    global _cloud
    if _cloud is None:
        _cloud = CloudDeployment()
    return _cloud


if __name__ == "__main__":
    print("=" * 50)
    print("端侧部署测试")
    print("=" * 50)
    
    cloud = CloudDeployment()
    
    print(f"\n📊 当前模式: {cloud.current_mode.value}")
    print(f"📊 状态: {cloud.get_status()}")
    
    # 测试获取向量
    vec = cloud.get_embedding("测试文本")
    if vec:
        print(f"✅ 向量获取成功: {len(vec)} 维")
    else:
        print("⚠️ 向量获取失败（降级到 BM25）")
    
    print("\n✅ 端侧部署测试完成")
