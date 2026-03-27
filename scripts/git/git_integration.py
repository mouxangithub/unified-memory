#!/usr/bin/env python3
"""
Git Integration - Git 仓库集成

功能:
- 追踪 Git 仓库
- 同步代码变更
- 搜索代码历史
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class GitIntegration:
    """Git 集成"""
    
    def __init__(self):
        self.tracked_repos = []
        self.repo_file = Path.home() / ".openclaw" / "workspace" / "memory" / "git_repos.json"
        self._load_tracked()
    
    def _load_tracked(self):
        """加载已追踪的仓库"""
        if self.repo_file.exists():
            import json
            self.tracked_repos = json.loads(self.repo_file.read_text())
    
    def _save_tracked(self):
        """保存已追踪的仓库"""
        import json
        self.repo_file.parent.mkdir(parents=True, exist_ok=True)
        self.repo_file.write_text(json.dumps(self.tracked_repos, ensure_ascii=False, indent=2))
    
    def track_repo(self, repo_path: str) -> Dict:
        """
        追踪 Git 仓库
        
        Returns:
            {
                "commits": 150,
                "files": 45,
                "memory_id": "git_xxx"
            }
        """
        path = Path(repo_path).resolve()
        
        if not (path / ".git").exists():
            raise ValueError(f"不是 Git 仓库: {path}")
        
        # 获取仓库信息
        result = {
            "path": str(path),
            "tracked_at": datetime.now().isoformat(),
            "commits": 0,
            "files": 0,
            "memory_id": None
        }
        
        # 获取提交数
        try:
            output = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True
            )
            result["commits"] = int(output.stdout.strip())
        except:
            pass
        
        # 获取文件数
        try:
            output = subprocess.run(
                ["git", "ls-files"],
                cwd=path,
                capture_output=True,
                text=True
            )
            files = output.stdout.strip().split("\n")
            result["files"] = len([f for f in files if f])
        except:
            pass
        
        # 添加到追踪列表
        if str(path) not in [r["path"] for r in self.tracked_repos]:
            self.tracked_repos.append(result)
            self._save_tracked()
        
        # 存储到记忆系统
        result["memory_id"] = self._store_repo_memory(result)
        
        return result
    
    def sync_changes(self) -> Dict:
        """
        同步所有仓库的变更
        
        Returns:
            {
                "new_commits": 10,
                "changed_files": 25
            }
        """
        result = {
            "synced_at": datetime.now().isoformat(),
            "new_commits": 0,
            "changed_files": 0,
            "repos": []
        }
        
        for repo in self.tracked_repos:
            repo_path = Path(repo["path"])
            
            if not repo_path.exists():
                continue
            
            # 拉取最新
            try:
                subprocess.run(
                    ["git", "fetch"],
                    cwd=repo_path,
                    capture_output=True
                )
                
                # 获取新提交
                output = subprocess.run(
                    ["git", "log", "--oneline", f"HEAD..origin/HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                new_commits = len([l for l in output.stdout.strip().split("\n") if l])
                result["new_commits"] += new_commits
                
                if new_commits > 0:
                    # 存储新提交
                    self._store_commits(repo_path, new_commits)
                
                result["repos"].append({
                    "path": str(repo_path),
                    "new_commits": new_commits
                })
                
            except Exception as e:
                result["repos"].append({
                    "path": str(repo_path),
                    "error": str(e)
                })
        
        return result
    
    def search_code(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索代码历史
        
        Args:
            query: 搜索关键词
            limit: 返回数量
        
        Returns:
            匹配的代码提交
        """
        results = []
        
        for repo in self.tracked_repos:
            repo_path = Path(repo["path"])
            
            if not repo_path.exists():
                continue
            
            try:
                # 搜索提交信息
                output = subprocess.run(
                    ["git", "log", "--all", "--grep", query, "--oneline", f"-{limit}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                for line in output.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(" ", 1)
                        if len(parts) >= 2:
                            results.append({
                                "repo": str(repo_path),
                                "commit": parts[0],
                                "message": parts[1]
                            })
                
                # 搜索代码内容
                output = subprocess.run(
                    ["git", "log", "-p", "--all", "-S", query, f"-{limit}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                if output.stdout:
                    results.append({
                        "repo": str(repo_path),
                        "type": "code_search",
                        "query": query,
                        "preview": output.stdout[:500]
                    })
                
            except:
                continue
        
        return results[:limit]
    
    def _store_repo_memory(self, repo_info: Dict) -> str:
        """存储仓库信息到记忆"""
        try:
            from unified_interface import UnifiedMemory
            um = UnifiedMemory()
            
            text = f"[Git 仓库]\n"
            text += f"路径: {repo_info['path']}\n"
            text += f"提交数: {repo_info['commits']}\n"
            text += f"文件数: {repo_info['files']}\n"
            
            return um.quick_store(text, category="git")
        except:
            return None
    
    def _store_commits(self, repo_path: Path, count: int):
        """存储新提交到记忆"""
        try:
            from unified_interface import UnifiedMemory
            um = UnifiedMemory()
            
            # 获取最近的提交
            output = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%h %s"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            text = f"[Git 新提交]\n"
            text += f"仓库: {repo_path.name}\n"
            text += f"数量: {count}\n\n"
            text += output.stdout
            
            um.quick_store(text, category="git")
        except:
            pass
    
    def list_tracked(self) -> List[Dict]:
        """列出已追踪的仓库"""
        return self.tracked_repos


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Git 集成")
    parser.add_argument("--track", help="追踪仓库")
    parser.add_argument("--sync", action="store_true", help="同步变更")
    parser.add_argument("--search", help="搜索代码")
    parser.add_argument("--list", action="store_true", help="列出已追踪")
    
    args = parser.parse_args()
    
    git = GitIntegration()
    
    if args.track:
        result = git.track_repo(args.track)
        print(f"✅ 已追踪:")
        print(f"   路径: {result['path']}")
        print(f"   提交: {result['commits']}")
        print(f"   文件: {result['files']}")
    
    elif args.sync:
        result = git.sync_changes()
        print(f"✅ 同步完成:")
        print(f"   新提交: {result['new_commits']}")
        for repo in result['repos']:
            print(f"   - {repo}")
    
    elif args.search:
        results = git.search_code(args.search)
        print(f"🔍 搜索结果: {len(results)} 条")
        for r in results:
            print(f"  - {r}")
    
    elif args.list:
        repos = git.list_tracked()
        print(f"📦 已追踪仓库: {len(repos)} 个")
        for r in repos:
            print(f"  - {r['path']} ({r['commits']} commits)")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
