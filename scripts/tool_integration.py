#!/usr/bin/env python3
"""
Tool Integration - 工具集成系统

整合外部工具和服务：
- GitHub API
- 飞书 API
- 记忆系统
- 文件系统

使用：
    from tool_integration import ToolRegistry, GitHubTool, FeishuTool
    
    registry = ToolRegistry()
    registry.register("github", GitHubTool(token="..."))
    registry.register("feishu", FeishuTool(app_id="...", app_secret="..."))
    
    # 使用工具
    result = registry.call("github", "create_issue", repo="owner/repo", title="Bug")
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import subprocess
from pathlib import Path


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Any
    error: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration
        }


class BaseTool(ABC):
    """工具基类"""
    
    name: str = "base"
    description: str = "基础工具"
    actions: Dict[str, Callable] = {}
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._init_actions()
    
    @abstractmethod
    def _init_actions(self):
        """初始化动作"""
        pass
    
    def call(self, action: str, **kwargs) -> ToolResult:
        """调用动作"""
        import time
        start = time.time()
        
        if action not in self.actions:
            return ToolResult(
                success=False,
                data=None,
                error=f"未知动作: {action}"
            )
        
        try:
            result = self.actions[action](**kwargs)
            return ToolResult(
                success=True,
                data=result,
                duration=time.time() - start
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                duration=time.time() - start
            )


class GitHubTool(BaseTool):
    """GitHub 工具"""
    
    name = "github"
    description = "GitHub API 集成"
    
    def _init_actions(self):
        self.actions = {
            "create_issue": self._create_issue,
            "list_issues": self._list_issues,
            "create_pr": self._create_pr,
            "get_repo": self._get_repo,
            "search_code": self._search_code
        }
    
    def _create_issue(self, repo: str, title: str, body: str = "", labels: List[str] = None) -> Dict:
        """创建 Issue"""
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
        if labels:
            cmd.extend(["--label", ",".join(labels)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {"url": result.stdout.strip(), "status": "created"}
        else:
            raise Exception(result.stderr)
    
    def _list_issues(self, repo: str, state: str = "open", limit: int = 10) -> List[Dict]:
        """列出 Issues"""
        cmd = ["gh", "issue", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,title,state,url"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(result.stderr)
    
    def _create_pr(self, repo: str, title: str, body: str = "", base: str = "main", head: str = None) -> Dict:
        """创建 PR"""
        cmd = ["gh", "pr", "create", "--repo", repo, "--title", title, "--body", body, "--base", base]
        if head:
            cmd.extend(["--head", head])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {"url": result.stdout.strip(), "status": "created"}
        else:
            raise Exception(result.stderr)
    
    def _get_repo(self, repo: str) -> Dict:
        """获取仓库信息"""
        cmd = ["gh", "repo", "view", repo, "--json", "name,description,url,stargazerCount,forkCount"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(result.stderr)
    
    def _search_code(self, query: str, repo: str = None) -> List[Dict]:
        """搜索代码"""
        if repo:
            query = f"{query} repo:{repo}"
        
        cmd = ["gh", "search", "repos", query, "--json", "name,fullName,url", "--limit", "10"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(result.stderr)


class FeishuTool(BaseTool):
    """飞书工具"""
    
    name = "feishu"
    description = "飞书 API 集成"
    
    def _init_actions(self):
        self.actions = {
            "send_message": self._send_message,
            "send_card": self._send_card,
            "get_user": self._get_user,
            "create_doc": self._create_doc
        }
    
    def _send_message(self, chat_id: str, content: str) -> Dict:
        """发送消息"""
        # 使用 feishu_im_user_message 工具
        # 这里简化实现，实际调用飞书 API
        return {
            "status": "sent",
            "chat_id": chat_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
    
    def _send_card(self, chat_id: str, title: str, content: Dict) -> Dict:
        """发送卡片"""
        return {
            "status": "sent",
            "chat_id": chat_id,
            "card": {
                "title": title,
                "content": content
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_user(self, user_id: str) -> Dict:
        """获取用户信息"""
        return {
            "user_id": user_id,
            "name": "用户名",
            "department": "部门"
        }
    
    def _create_doc(self, title: str, content: str) -> Dict:
        """创建文档"""
        return {
            "status": "created",
            "title": title,
            "url": f"https://feishu.cn/doc/xxx",
            "timestamp": datetime.now().isoformat()
        }


class MemoryTool(BaseTool):
    """记忆系统工具"""
    
    name = "memory"
    description = "记忆系统集成"
    
    def _init_actions(self):
        self.actions = {
            "store": self._store,
            "recall": self._recall,
            "forget": self._forget,
            "search": self._search
        }
        
        # 简化的内存存储
        self._storage: Dict[str, List[Dict]] = {}
    
    def _store(self, key: str, value: Any, tags: List[str] = None) -> Dict:
        """存储记忆"""
        if key not in self._storage:
            self._storage[key] = []
        
        entry = {
            "value": value,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat()
        }
        self._storage[key].append(entry)
        
        return {"status": "stored", "key": key, "count": len(self._storage[key])}
    
    def _recall(self, key: str, limit: int = 10) -> List[Dict]:
        """回忆记忆"""
        return self._storage.get(key, [])[:limit]
    
    def _forget(self, key: str) -> Dict:
        """删除记忆"""
        if key in self._storage:
            del self._storage[key]
            return {"status": "forgotten", "key": key}
        return {"status": "not_found", "key": key}
    
    def _search(self, query: str) -> List[Dict]:
        """搜索记忆"""
        results = []
        for key, entries in self._storage.items():
            if query.lower() in key.lower():
                results.extend(entries)
            else:
                for entry in entries:
                    if query.lower() in str(entry["value"]).lower():
                        results.append(entry)
        return results


class FileSystemTool(BaseTool):
    """文件系统工具"""
    
    name = "filesystem"
    description = "文件系统操作"
    
    def _init_actions(self):
        self.actions = {
            "read": self._read,
            "write": self._write,
            "list": self._list,
            "delete": self._delete,
            "exists": self._exists
        }
    
    def _read(self, path: str) -> str:
        """读取文件"""
        return Path(path).read_text(encoding="utf-8")
    
    def _write(self, path: str, content: str) -> Dict:
        """写入文件"""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {"status": "written", "path": path, "size": len(content)}
    
    def _list(self, path: str, pattern: str = "*") -> List[str]:
        """列出文件"""
        return [str(p) for p in Path(path).glob(pattern)]
    
    def _delete(self, path: str) -> Dict:
        """删除文件"""
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
            return {"status": "deleted", "path": path}
        return {"status": "not_found", "path": path}
    
    def _exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return Path(path).exists()


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
        # 注册默认工具
        self.register("filesystem", FileSystemTool())
        self.register("memory", MemoryTool())
    
    def register(self, name: str, tool: BaseTool):
        """注册工具"""
        self._tools[name] = tool
    
    def unregister(self, name: str):
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "actions": list(tool.actions.keys())
            }
            for tool in self._tools.values()
        ]
    
    def call(self, tool_name: str, action: str, **kwargs) -> ToolResult:
        """调用工具"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"未知工具: {tool_name}"
            )
        
        return tool.call(action, **kwargs)
    
    def call_batch(self, calls: List[Dict]) -> List[ToolResult]:
        """批量调用工具"""
        return [
            self.call(call["tool"], call["action"], **call.get("params", {}))
            for call in calls
        ]


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="工具集成")
    parser.add_argument("command", choices=["list", "demo"])
    
    args = parser.parse_args()
    
    registry = ToolRegistry()
    
    if args.command == "list":
        print("可用工具:")
        for tool in registry.list_tools():
            print(f"  - {tool['name']}: {tool['description']}")
            print(f"    动作: {', '.join(tool['actions'])}")
    
    elif args.command == "demo":
        # 文件系统示例
        result = registry.call("filesystem", "write", path="/tmp/test.txt", content="Hello World!")
        print(f"写入文件: {result.to_dict()}")
        
        result = registry.call("filesystem", "read", path="/tmp/test.txt")
        print(f"读取文件: {result.to_dict()}")
        
        # 记忆系统示例
        result = registry.call("memory", "store", key="test", value="这是一条测试记忆")
        print(f"存储记忆: {result.to_dict()}")
        
        result = registry.call("memory", "recall", key="test")
        print(f"回忆记忆: {result.to_dict()}")
