#!/usr/bin/env python3
"""
Code Sandbox - Docker 代码执行沙箱

功能:
- Docker 隔离执行
- 多语言支持（Python、JavaScript、TypeScript、Bash、Go）
- 资源限制（内存、CPU、超时）
- 安全隔离
- 本地降级执行

使用:
    from sandbox import CodeSandbox
    
    sandbox = CodeSandbox()
    
    # 执行 Python 代码
    result = sandbox.execute("print('Hello World')", language="python")
    print(result.output)
    
    # 执行带文件的代码
    result = sandbox.execute(
        code,
        language="python",
        files={"utils.py": "def helper(): ..."}
    )
    
    # 运行测试
    result = sandbox.test_code(code, test_code)
"""

import subprocess
import tempfile
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import shutil


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: str
    exit_code: int
    duration: float
    language: str = ""
    container_id: str = ""
    files: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "language": self.language,
            "files": self.files,
            "metrics": self.metrics
        }


class CodeSandbox:
    """代码执行沙箱"""
    
    # Docker 镜像映射
    IMAGES = {
        "python": "python:3.11-slim",
        "python3": "python:3.11-slim",
        "javascript": "node:18-slim",
        "js": "node:18-slim",
        "typescript": "node:18-slim",
        "ts": "node:18-slim",
        "bash": "alpine:latest",
        "shell": "alpine:latest",
        "go": "golang:1.21-alpine",
        "golang": "golang:1.21-alpine",
        "java": "openjdk:17-slim",
        "rust": "rust:slim",
        "ruby": "ruby:3.2-slim"
    }
    
    # 文件扩展名映射
    EXTENSIONS = {
        "python": ".py",
        "python3": ".py",
        "javascript": ".js",
        "js": ".js",
        "typescript": ".ts",
        "ts": ".ts",
        "bash": ".sh",
        "shell": ".sh",
        "go": ".go",
        "golang": ".go",
        "java": ".java",
        "rust": ".rs",
        "ruby": ".rb"
    }
    
    # 运行命令映射
    RUN_COMMANDS = {
        "python": ["python", "main.py"],
        "python3": ["python", "main.py"],
        "javascript": ["node", "main.js"],
        "js": ["node", "main.js"],
        "typescript": ["npx", "ts-node", "main.ts"],
        "ts": ["npx", "ts-node", "main.ts"],
        "bash": ["sh", "main.sh"],
        "shell": ["sh", "main.sh"],
        "go": ["go", "run", "main.go"],
        "golang": ["go", "run", "main.go"],
        "java": ["java", "Main.java"],
        "rust": ["rustc", "main.rs", "-o", "main", "&&", "./main"],
        "ruby": ["ruby", "main.rb"]
    }
    
    def __init__(self,
                 timeout: int = 60,
                 memory_limit: str = "256m",
                 cpu_limit: str = "1",
                 network_disabled: bool = True,
                 use_docker: bool = None):
        """
        初始化沙箱
        
        Args:
            timeout: 超时时间（秒）
            memory_limit: 内存限制
            cpu_limit: CPU 限制
            network_disabled: 是否禁用网络
            use_docker: 是否使用 Docker（None=自动检测）
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network_disabled = network_disabled
        
        # 检测 Docker 可用性
        if use_docker is None:
            self.use_docker = self._check_docker()
        else:
            self.use_docker = use_docker
        
        # 本地执行器可用性
        self._local_executors = self._detect_local_executors()
    
    def _check_docker(self) -> bool:
        """检查 Docker 是否可用"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _detect_local_executors(self) -> Dict[str, bool]:
        """检测本地可用的执行器"""
        executors = {
            "python": shutil.which("python3") or shutil.which("python"),
            "javascript": shutil.which("node"),
            "bash": shutil.which("bash") or shutil.which("sh"),
            "go": shutil.which("go"),
            "ruby": shutil.which("ruby")
        }
        return {k: bool(v) for k, v in executors.items()}
    
    def execute(self,
                code: str,
                language: str = "python",
                files: Dict[str, str] = None,
                env: Dict[str, str] = None,
                stdin: str = None,
                workdir_files: Dict[str, str] = None) -> ExecutionResult:
        """
        执行代码
        
        Args:
            code: 要执行的代码
            language: 语言
            files: 附加文件 {filename: content}
            env: 环境变量
            stdin: 标准输入
            workdir_files: 工作目录文件
        
        Returns:
            ExecutionResult
        """
        language = language.lower()
        
        if language not in self.IMAGES:
            return ExecutionResult(
                success=False,
                output="",
                error=f"不支持的语言: {language}。支持: {list(self.IMAGES.keys())}",
                exit_code=-1,
                duration=0,
                language=language
            )
        
        if self.use_docker:
            return self._docker_execute(code, language, files, env, stdin, workdir_files)
        else:
            return self._local_execute(code, language, files, env, stdin, workdir_files)
    
    def _docker_execute(self,
                        code: str,
                        language: str,
                        files: Dict[str, str],
                        env: Dict[str, str],
                        stdin: str,
                        workdir_files: Dict[str, str]) -> ExecutionResult:
        """Docker 执行"""
        
        start_time = time.time()
        container_id = ""
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                
                # 写入主代码文件
                ext = self.EXTENSIONS.get(language, ".txt")
                main_file = tmpdir / f"main{ext}"
                main_file.write_text(code, encoding="utf-8")
                
                # 写入附加文件
                if files:
                    for name, content in files.items():
                        (tmpdir / name).write_text(content, encoding="utf-8")
                
                # 写入工作目录文件
                if workdir_files:
                    for name, content in workdir_files.items():
                        (tmpdir / name).write_text(content, encoding="utf-8")
                
                # 获取镜像
                image = self.IMAGES.get(language)
                
                # 拉取镜像（如果不存在）
                pull_result = subprocess.run(
                    ["docker", "pull", image],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # 构建 Docker 命令
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{tmpdir}:/workspace",
                    "-w", "/workspace",
                    "--memory", self.memory_limit,
                    "--cpus", self.cpu_limit,
                ]
                
                # 网络设置
                if self.network_disabled:
                    docker_cmd.append("--network=none")
                
                # 环境变量
                if env:
                    for k, v in env.items():
                        docker_cmd.extend(["-e", f"{k}={v}"])
                
                # 容器名称（用于追踪）
                container_name = f"sandbox_{int(time.time())}"
                docker_cmd.extend(["--name", container_name])
                
                # 镜像和命令
                docker_cmd.append(image)
                docker_cmd.extend(self.RUN_COMMANDS.get(language, ["cat", "main.txt"]))
                
                # 执行
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    input=stdin
                )
                
                duration = time.time() - start_time
                
                # 收集生成的文件
                output_files = {}
                for f in tmpdir.iterdir():
                    if f.is_file() and f.name != f"main{ext}":
                        try:
                            output_files[f.name] = f.read_text(encoding="utf-8")
                        except:
                            pass
                
                return ExecutionResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode,
                    duration=duration,
                    language=language,
                    container_id=container_name,
                    files=output_files,
                    metrics={
                        "memory_limit": self.memory_limit,
                        "cpu_limit": self.cpu_limit,
                        "network_disabled": self.network_disabled
                    }
                )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行超时 ({self.timeout}s)",
                exit_code=-1,
                duration=self.timeout,
                language=language,
                container_id=container_id
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                duration=time.time() - start_time,
                language=language
            )
    
    def _local_execute(self,
                       code: str,
                       language: str,
                       files: Dict[str, str],
                       env: Dict[str, str],
                       stdin: str,
                       workdir_files: Dict[str, str]) -> ExecutionResult:
        """本地执行（降级方案）"""
        
        start_time = time.time()
        
        # 检查本地执行器
        if not self._local_executors.get(language):
            return ExecutionResult(
                success=False,
                output="",
                error=f"本地执行不支持: {language}。可用: {[k for k, v in self._local_executors.items() if v]}",
                exit_code=-1,
                duration=0,
                language=language
            )
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                
                # 写入代码
                ext = self.EXTENSIONS.get(language, ".txt")
                main_file = tmpdir / f"main{ext}"
                main_file.write_text(code, encoding="utf-8")
                
                # 写入附加文件
                if files:
                    for name, content in files.items():
                        (tmpdir / name).write_text(content, encoding="utf-8")
                
                # 构建命令
                if language in ["python", "python3"]:
                    cmd = ["python3" if shutil.which("python3") else "python", str(main_file)]
                elif language in ["javascript", "js"]:
                    cmd = ["node", str(main_file)]
                elif language in ["bash", "shell"]:
                    cmd = ["bash", str(main_file)]
                elif language in ["go", "golang"]:
                    cmd = ["go", "run", str(main_file)]
                elif language == "ruby":
                    cmd = ["ruby", str(main_file)]
                else:
                    cmd = ["cat", str(main_file)]
                
                # 执行
                process_env = os.environ.copy()
                if env:
                    process_env.update(env)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    input=stdin,
                    cwd=tmpdir,
                    env=process_env
                )
                
                return ExecutionResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode,
                    duration=time.time() - start_time,
                    language=language,
                    metrics={"mode": "local"}
                )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行超时 ({self.timeout}s)",
                exit_code=-1,
                duration=self.timeout,
                language=language
            )
        
        except FileNotFoundError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"找不到解释器: {e}",
                exit_code=-1,
                duration=0,
                language=language
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                duration=time.time() - start_time,
                language=language
            )
    
    def test_code(self,
                  code: str,
                  test_code: str = None,
                  language: str = "python",
                  test_framework: str = "pytest") -> ExecutionResult:
        """
        测试代码
        
        Args:
            code: 被测试的代码
            test_code: 测试代码
            language: 语言
            test_framework: 测试框架
        """
        
        if language == "python":
            # 合并代码和测试
            if test_framework == "pytest":
                full_code = f"{code}\n\n# Tests\n{test_code}"
            else:
                full_code = f"{code}\n\nif __name__ == '__main__':\n{test_code}"
            
            return self.execute(full_code, language)
        
        elif language in ["javascript", "js"]:
            # JavaScript 测试
            full_code = f"{code}\n\n// Tests\n{test_code}"
            return self.execute(full_code, language)
        
        return self.execute(code, language)
    
    def run_file(self,
                 file_path: str,
                 language: str = None,
                 **kwargs) -> ExecutionResult:
        """运行文件"""
        
        path = Path(file_path)
        
        if not path.exists():
            return ExecutionResult(
                success=False,
                output="",
                error=f"文件不存在: {file_path}",
                exit_code=-1,
                duration=0
            )
        
        # 自动检测语言
        if not language:
            ext = path.suffix.lower()
            ext_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".sh": "bash",
                ".go": "go",
                ".rb": "ruby"
            }
            language = ext_map.get(ext, "python")
        
        code = path.read_text(encoding="utf-8")
        
        return self.execute(code, language, **kwargs)
    
    def list_languages(self) -> List[str]:
        """列出支持的语言"""
        return list(self.IMAGES.keys())
    
    def get_executor_info(self) -> Dict[str, Any]:
        """获取执行器信息"""
        return {
            "docker_available": self.use_docker,
            "local_executors": self._local_executors,
            "supported_languages": self.list_languages(),
            "config": {
                "timeout": self.timeout,
                "memory_limit": self.memory_limit,
                "cpu_limit": self.cpu_limit,
                "network_disabled": self.network_disabled
            }
        }


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="代码沙箱")
    parser.add_argument("command", choices=["info", "run", "test", "demo"])
    parser.add_argument("--language", "-l", default="python", help="语言")
    parser.add_argument("--code", "-c", help="代码")
    parser.add_argument("--file", "-f", help="文件路径")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="超时")
    parser.add_argument("--docker", action="store_true", help="强制使用 Docker")
    parser.add_argument("--local", action="store_true", help="强制使用本地执行")
    
    args = parser.parse_args()
    
    # 创建沙箱
    use_docker = None
    if args.docker:
        use_docker = True
    elif args.local:
        use_docker = False
    
    sandbox = CodeSandbox(timeout=args.timeout, use_docker=use_docker)
    
    if args.command == "info":
        info = sandbox.get_executor_info()
        print("沙箱信息:")
        print(f"  Docker 可用: {info['docker_available']}")
        print(f"  本地执行器:")
        for lang, available in info['local_executors'].items():
            status = "✅" if available else "❌"
            print(f"    - {lang}: {status}")
        print(f"  支持的语言: {', '.join(info['supported_languages'])}")
        print(f"  配置: {info['config']}")
    
    elif args.command == "run":
        if args.file:
            result = sandbox.run_file(args.file, args.language)
        elif args.code:
            result = sandbox.execute(args.code, args.language)
        else:
            print("请提供 --code 或 --file")
            exit(1)
        
        print(f"成功: {result.success}")
        print(f"退出码: {result.exit_code}")
        print(f"耗时: {result.duration:.2f}s")
        print(f"输出:\n{result.output}")
        if result.error:
            print(f"错误:\n{result.error}")
    
    elif args.command == "test":
        code = args.code or "def add(a, b):\n    return a + b"
        test_code = """
def test_add():
    assert add(1, 2) == 3
    assert add(0, 0) == 0
    print('All tests passed!')
"""
        result = sandbox.test_code(code, test_code, args.language)
        print(f"测试{'通过' if result.success else '失败'}")
        print(f"输出: {result.output}")
        if result.error:
            print(f"错误: {result.error}")
    
    elif args.command == "demo":
        demos = {
            "python": "print('Hello from Python!')\nfor i in range(3):\n    print(f'Count: {i}')",
            "javascript": "console.log('Hello from JavaScript!');\nfor(let i = 0; i < 3; i++) {\n  console.log(`Count: ${i}`);\n}",
            "bash": "echo 'Hello from Bash!'\nfor i in 1 2 3; do\n  echo \"Count: $i\"\ndone"
        }
        
        for lang, code in demos.items():
            print(f"\n--- {lang.upper()} ---")
            result = sandbox.execute(code, lang)
            print(f"成功: {result.success}")
            print(f"输出: {result.output[:100]}")
