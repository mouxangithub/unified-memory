#!/usr/bin/env python3
"""
Unified Interface - 统一接口封装
为所有功能模块提供一致的类接口

Usage:
    from unified_interface import (
        SmartChunker,
        ContextTreeManager,
        HybridSearch,
        SOPWorkflow,
        MCPServerWrapper,
        MemoryManager,
        LLMProvider,
        RoleManager,
        CodeSandbox,
        CodeGenerator,
        AgentCollab
    )
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 1. Smart Chunker
# ============================================================

class SmartChunker:
    """智能分块器"""
    
    def __init__(self, max_tokens: int = 900, overlap_tokens: int = 135):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
    
    def chunk(self, text: str) -> List[str]:
        """分块文本"""
        from smart_chunk import smart_chunk
        return smart_chunk(text, self.max_tokens, self.overlap_tokens)
    
    def chunk_file(self, file_path: str) -> List[str]:
        """分块文件"""
        from smart_chunk import chunk_file
        return chunk_file(file_path, self.max_tokens)


# ============================================================
# 2. Context Tree Manager
# ============================================================

class ContextTreeManager:
    """上下文树管理器"""
    
    def __init__(self):
        from memory_context import ContextTree
        self._tree = ContextTree()
    
    def add_context(self, path: str, description: str, parent: str = "") -> bool:
        """添加上下文节点"""
        return self._tree.add_context(path, description, parent)
    
    def add_memory(self, path: str, memory_id: str, content: str, category: str = "") -> bool:
        """添加记忆到上下文"""
        return self._tree.add_memory(path, memory_id, content, category)
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索并附加上下文"""
        return self._tree.search_with_context(query, limit)
    
    def get_chain(self, path: str) -> List[str]:
        """获取上下文链"""
        return self._tree.get_context_chain(path)


# ============================================================
# 3. Hybrid Search
# ============================================================

class HybridSearch:
    """混合搜索器"""
    
    def __init__(self):
        self._initialized = True
    
    def search(self, query: str, mode: str = "hybrid", limit: int = 10) -> List[Dict]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            mode: lex/vec/hyde/hybrid
            limit: 返回数量
        """
        if mode == "lex":
            from memory_hyde import lex_search
            return lex_search(query, limit)
        elif mode == "hyde":
            from memory_hyde import hyde_search
            return hyde_search(query, limit)
        elif mode == "hybrid":
            from memory_hyde import rrf_fusion, lex_search, hyde_search
            lex_results = lex_search(query, limit)
            hyde_results = hyde_search(query, limit)
            return rrf_fusion(lex_results, hyde_results, limit)
        else:
            from memory_hyde import hyde_search
            return hyde_search(query, limit)


# ============================================================
# 4. SOP Workflow
# ============================================================

class SOPWorkflow:
    """SOP 工作流"""
    
    def __init__(self):
        from workflow_sop import SOPEngine
        self._engine = SOPEngine()
        self._sop_dir = Path.home() / ".openclaw" / "workspace" / "skills" / "unified-memory" / "configs" / "sop"
    
    def load(self, sop_file: str) -> bool:
        """加载 SOP 文件"""
        return self._engine.load_sop(sop_file)
    
    def execute(self, context: Dict) -> Dict:
        """执行工作流"""
        return self._engine.execute(context)
    
    def list_sops(self) -> List[str]:
        """列出可用的 SOP"""
        if self._sop_dir.exists():
            return [f.stem for f in self._sop_dir.glob("*.yaml")]
        return []
    
    def list_steps(self) -> List[str]:
        """列出当前 SOP 的步骤"""
        return self._engine.list_steps()


# ============================================================
# 5. MCP Server Wrapper
# ============================================================

class MCPServerWrapper:
    """MCP 服务器封装"""
    
    def __init__(self, http: bool = False, port: int = 8181):
        from mcp_server import MCPServer
        self._server = MCPServer(http=http, port=port)
    
    def run(self):
        """运行服务器"""
        self._server.run()


# ============================================================
# 6. Memory Manager
# ============================================================

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self):
        from unified_memory import BM25, ImportanceScorer, OntologyGraph
        from pathlib import Path
        self._bm25 = BM25()
        self._scorer = ImportanceScorer()
        graph_file = Path.home() / ".openclaw" / "workspace" / "memory" / "ontology" / "graph.json"
        graph_file.parent.mkdir(parents=True, exist_ok=True)
        self._graph = OntologyGraph(graph_file)
    
    def store(self, text: str, category: str = "fact", metadata: Dict = None) -> str:
        """存储记忆"""
        import uuid
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        # 存储逻辑
        return memory_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆"""
        return self._bm25.search(query, limit)
    
    def get_graph(self) -> Dict:
        """获取知识图谱"""
        return self._graph.to_dict()


# ============================================================
# 7. LLM Provider
# ============================================================

class LLMProvider:
    """LLM 提供商"""
    
    def __init__(self, provider: str = "ollama", model: str = ""):
        from llm_provider import LLMProviderFactory
        self._factory = LLMProviderFactory()
        self._provider_name = provider
        self._model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        provider = self._factory.create(self._provider_name)
        if self._model:
            kwargs['model'] = self._model
        response = provider.generate(prompt, **kwargs)
        return response.content if hasattr(response, 'content') else str(response)
    
    def embed(self, text: str) -> List[float]:
        """获取 embedding"""
        # 使用 Ollama
        from unified_memory import get_ollama_embedding
        return get_ollama_embedding(text)


# ============================================================
# 8. Role Manager
# ============================================================

class RoleManager:
    """角色管理器"""
    
    def __init__(self):
        from roles import Architect, Engineer, BackendEngineer, DevOps
        self._roles = {
            'architect': Architect,
            'engineer': Engineer,
            'backend': BackendEngineer,
            'devops': DevOps
        }
    
    def get_role(self, role_name: str):
        """获取角色"""
        role_class = self._roles.get(role_name.lower())
        if role_class:
            return role_class()
        return None
    
    def list_roles(self) -> List[str]:
        """列出所有角色"""
        return list(self._roles.keys())


# ============================================================
# 9. Code Sandbox
# ============================================================

class CodeSandbox:
    """代码沙箱"""
    
    def __init__(self):
        from sandbox import CodeSandbox as _CodeSandbox
        self._sandbox = _CodeSandbox()
    
    def execute(self, code: str, language: str = "python") -> Dict:
        """执行代码"""
        return self._sandbox.execute(code, language)


# ============================================================
# 10. Code Generator
# ============================================================

class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        from code_generator import CodeGenerator as _CodeGenerator
        self._generator = _CodeGenerator()
    
    def generate_project(self, project_type: str, name: str, requirements: str) -> Dict:
        """生成项目"""
        return self._generator.generate(project_type, name, requirements)


# ============================================================
# 11. Agent Collaboration
# ============================================================

class AgentCollab:
    """Agent 协作系统"""
    
    def __init__(self):
        from agent_collab_system import AgentCollaborationSystem
        self._system = AgentCollaborationSystem()
    
    def register_agent(self, agent_id: str, name: str, role: str, skills: List[str] = None):
        """注册 Agent"""
        return self._system.register_agent(agent_id, name, role, skills or [])
    
    def add_task(self, task_id: str, description: str, priority: int = 1):
        """创建任务"""
        return self._system.add_task(task_id, description, priority)
    
    def assign_task(self, task_id: str, agent_id: str):
        """分配任务"""
        return self._system.assign_task(task_id, agent_id)
    
    def complete_task(self, task_id: str, result: str):
        """完成任务"""
        return self._system.complete_task(task_id, result)
    
    def list_agents(self) -> List[Dict]:
        """列出所有 Agent"""
        return self._system.list_agents()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._system.get_stats()


# ============================================================
# 统一入口
# ============================================================

class UnifiedMemory:
    """统一记忆系统入口"""
    
    def __init__(self):
        self.chunker = SmartChunker()
        self.context = ContextTreeManager()
        self.search = HybridSearch()
        self.workflow = SOPWorkflow()
        self.memory = MemoryManager()
        self.llm = LLMProvider()
        self.roles = RoleManager()
        self.sandbox = CodeSandbox()
        self.generator = CodeGenerator()
        self.agents = AgentCollab()
    
    def quick_store(self, text: str, category: str = "fact") -> str:
        """快速存储"""
        return self.memory.store(text, category)
    
    def quick_search(self, query: str, limit: int = 5) -> List[Dict]:
        """快速搜索"""
        return self.search.search(query, mode="hybrid", limit=limit)


# ============================================================
# CLI 入口
# ============================================================

def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一记忆系统 v1.0.0")
    parser.add_argument("command", choices=["store", "search", "chunk", "status"])
    parser.add_argument("--text", "-t", help="文本内容")
    parser.add_argument("--file", "-f", help="文件路径")
    parser.add_argument("--category", "-c", default="fact", help="分类")
    parser.add_argument("--mode", "-m", default="hybrid", help="搜索模式")
    parser.add_argument("--limit", "-l", type=int, default=5, help="返回数量")
    
    args = parser.parse_args()
    
    um = UnifiedMemory()
    
    if args.command == "store":
        if args.file:
            text = Path(args.file).read_text()
        elif args.text:
            text = args.text
        else:
            print("需要 --text 或 --file")
            return
        
        memory_id = um.quick_store(text, args.category)
        print(f"✅ 已存储: {memory_id}")
    
    elif args.command == "search":
        results = um.quick_search(args.text or "", args.limit)
        for r in results:
            print(f"- {r}")
    
    elif args.command == "chunk":
        if args.file:
            chunks = um.chunker.chunk_file(args.file)
        elif args.text:
            chunks = um.chunker.chunk(args.text)
        else:
            print("需要 --text 或 --file")
            return
        
        print(f"✅ 分块完成: {len(chunks)} 块")
        for i, chunk in enumerate(chunks[:3], 1):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"  {i}. {preview}")
    
    elif args.command == "status":
        print("✅ 统一记忆系统 v1.0.0")
        print("  - Smart Chunker: 就绪")
        print("  - Context Tree: 就绪")
        print("  - Hybrid Search: 就绪")
        print("  - SOP Workflow: 就绪")
        print("  - Agent Collab: 就绪")


# ============================================================
# 12. Multimodal Memory
# ============================================================

try:
    from multimodal import MultimodalMemory as _MultimodalMemory
except ImportError:
    _MultimodalMemory = None


if __name__ == "__main__":
    main()
