#!/usr/bin/env python3
"""
插件化架构 - Plugin System

支持热插拔，可选模块动态加载
"""

import json
import importlib.util
import os
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Callable
from datetime import datetime

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
PLUGIN_DIR = MEMORY_DIR / "plugins"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)


class MemoryPlugin(Protocol):
    """插件接口"""
    
    name: str
    version: str
    
    def on_store(self, memory: Dict) -> Dict: ...
    def on_retrieve(self, query: str, memories: List[Dict]) -> List[Dict]: ...
    def on_compress(self, memories: List[Dict]) -> str: ...


class PluginManifest:
    """插件清单"""
    
    def __init__(self, name: str, version: str, description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.enabled = True
        self.loaded_at = None
        self.config = {}
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "loaded_at": self.loaded_at,
            "config": self.config
        }


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.manifest_file = PLUGIN_DIR / "manifest.json"
        self.plugins: Dict[str, Dict] = {}
        self.instances: Dict[str, any] = {}
        self._load_manifest()
        self._register_builtin()
    
    def _load_manifest(self):
        """加载插件清单"""
        if self.manifest_file.exists():
            with open(self.manifest_file, "r") as f:
                data = json.load(f)
                self.plugins = data.get("plugins", {})
    
    def _save_manifest(self):
        """保存插件清单"""
        with open(self.manifest_file, "w") as f:
            json.dump({"plugins": self.plugins}, f, indent=2)
    
    def _register_builtin(self):
        """注册内置插件"""
        builtins = {
            "bm25": {
                "name": "BM25",
                "version": "1.0.0",
                "description": "BM25 文本搜索",
                "type": "builtin",
                "enabled": True
            },
            "vector": {
                "name": "Vector Search",
                "version": "1.0.0",
                "description": "向量相似度搜索",
                "type": "builtin",
                "enabled": True
            },
            "feedback": {
                "name": "Feedback Learning",
                "version": "1.0.0",
                "description": "用户反馈学习",
                "type": "builtin",
                "enabled": True
            },
            "analytics": {
                "name": "Analytics",
                "version": "1.0.0",
                "description": "监控分析",
                "type": "builtin",
                "enabled": True
            },
            "auto_store": {
                "name": "Auto Store",
                "version": "1.0.0",
                "description": "自动存储",
                "type": "builtin",
                "enabled": True
            },
            "persistent_context": {
                "name": "Persistent Context",
                "version": "1.0.0",
                "description": "持久化上下文",
                "type": "builtin",
                "enabled": True
            },
        }
        
        for pid, pdata in builtins.items():
            if pid not in self.plugins:
                self.plugins[pid] = pdata
        
        self._save_manifest()
    
    def load(self, plugin_path: str) -> bool:
        """加载插件"""
        path = Path(plugin_path)
        if not path.exists():
            return False
        
        # 动态导入
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取插件类
            if hasattr(module, "Plugin"):
                plugin = module.Plugin()
                plugin_id = path.stem.replace("memory_", "").replace("_plugin", "")
                
                self.instances[plugin_id] = plugin
                self.plugins[plugin_id] = {
                    "name": plugin.name,
                    "version": plugin.version,
                    "type": "external",
                    "path": str(path),
                    "enabled": True,
                    "loaded_at": datetime.now().isoformat()
                }
                self._save_manifest()
                return True
        
        return False
    
    def unload(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id in self.instances:
            del self.instances[plugin_id]
        
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = False
            self._save_manifest()
            return True
        return False
    
    def enable(self, plugin_id: str):
        """启用插件"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = True
            self._save_manifest()
    
    def disable(self, plugin_id: str):
        """禁用插件"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = False
            self._save_manifest()
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return [
            {**p, "id": pid, "instance": pid in self.instances}
            for pid, p in self.plugins.items()
        ]
    
    def get_enabled(self) -> List[str]:
        """获取已启用的插件"""
        return [
            pid for pid, p in self.plugins.items()
            if p.get("enabled", False)
        ]
    
    def execute(self, plugin_id: str, method: str, *args, **kwargs):
        """执行插件方法"""
        if plugin_id not in self.instances:
            return None
        
        plugin = self.instances[plugin_id]
        if hasattr(plugin, method):
            return getattr(plugin, method)(*args, **kwargs)
        return None
    
    # ===== 插件管道 =====
    
    def on_store(self, memory: Dict) -> Dict:
        """存储管道"""
        result = memory
        for pid in self.get_enabled():
            result = self.execute(pid, "on_store", result)
        return result
    
    def on_retrieve(self, query: str, memories: List[Dict]) -> List[Dict]:
        """检索管道"""
        result = memories
        for pid in self.get_enabled():
            result = self.execute(pid, "on_retrieve", query, result) or result
        return result
    
    def on_compress(self, memories: List[Dict]) -> str:
        """压缩管道"""
        result = memories
        for pid in self.get_enabled():
            result = self.execute(pid, "on_compress", result) or result
        if isinstance(result, str):
            return result
        return ""


# 内置插件实现

class BM25Plugin:
    name = "BM25"
    version = "1.0.0"
    
    def on_store(self, memory: Dict) -> Dict:
        return memory
    
    def on_retrieve(self, query: str, memories: List[Dict]) -> List[Dict]:
        # 简单的 BM25 过滤
        return memories
    
    def on_compress(self, memories: List[Dict]) -> str:
        return ""


class FeedbackPlugin:
    name = "Feedback Learning"
    version = "1.0.0"
    
    def on_store(self, memory: Dict) -> Dict:
        return memory
    
    def on_retrieve(self, query: str, memories: List[Dict]) -> List[Dict]:
        # 根据置信度过滤
        return [m for m in memories if m.get("confidence", 0) > 0.3]
    
    def on_compress(self, memories: List[Dict]) -> str:
        return ""


# 全局实例
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


if __name__ == "__main__":
    print("=" * 50)
    print("插件系统测试")
    print("=" * 50)
    
    pm = PluginManager()
    
    # 列出插件
    print("\n📦 插件列表:")
    for p in pm.list_plugins():
        status = "✅" if p["enabled"] else "❌"
        print(f"  {status} {p['id']}: {p['name']} v{p['version']}")
    
    # 启用/禁用
    print("\n🔧 管理:")
    pm.disable("analytics")
    print("  禁用 analytics")
    pm.enable("analytics")
    print("  启用 analytics")
    
    # 执行管道
    print("\n🚀 执行存储管道:")
    result = pm.on_store({"id": "test", "text": "测试记忆"})
    print(f"  结果: {result}")
    
    print("\n✅ 插件系统测试完成")
