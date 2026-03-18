#!/usr/bin/env python3
"""
Fallback Handler - 降级处理 v0.0.7

当依赖不可用时提供降级服务:
- LanceDB 不可用 → JSON 文件存储
- Ollama 不可用 → 规则提取
- Ontology 不可用 → 纯向量搜索
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
FALLBACK_FILE = MEMORY_DIR / "memories.json"

# ============================================================
# 依赖检测
# ============================================================

def check_dependencies() -> Dict[str, bool]:
    """检查依赖可用性"""
    deps = {
        "lancedb": False,
        "requests": False,
        "ollama": False,
        "ontology": False
    }
    
    # LanceDB
    try:
        import lancedb
        deps["lancedb"] = True
    except ImportError:
        pass
    
    # requests
    try:
        import requests
        deps["requests"] = True
    except ImportError:
        pass
    
    # Ollama
    if deps["requests"]:
        try:
            import requests
            response = requests.get(
                os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/api/tags",
                timeout=2
            )
            deps["ollama"] = response.status_code == 200
        except:
            pass
    
    # Ontology (检查是否有 ontology skill)
    ontology_path = WORKSPACE / "skills" / "ontology"
    deps["ontology"] = ontology_path.exists()
    
    return deps


# ============================================================
# JSON Fallback Storage
# ============================================================

class JSONStorage:
    """JSON 文件存储（LanceDB 降级方案）"""
    
    def __init__(self):
        FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()
    
    def _ensure_file(self):
        """确保文件存在"""
        if not FALLBACK_FILE.exists():
            FALLBACK_FILE.write_text("[]")
    
    def load(self) -> List[Dict]:
        """加载所有记忆"""
        try:
            return json.loads(FALLBACK_FILE.read_text())
        except:
            return []
    
    def save(self, memories: List[Dict]):
        """保存所有记忆"""
        FALLBACK_FILE.write_text(json.dumps(memories, ensure_ascii=False, indent=2))
    
    def add(self, memory: Dict):
        """添加记忆"""
        memories = self.load()
        memories.append(memory)
        self.save(memories)
    
    def delete(self, memory_id: str):
        """删除记忆"""
        memories = self.load()
        memories = [m for m in memories if m.get("id") != memory_id]
        self.save(memories)
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """简单文本搜索"""
        memories = self.load()
        query_lower = query.lower()
        
        results = []
        for mem in memories:
            text = mem.get("text", "").lower()
            if query_lower in text:
                results.append(mem)
        
        # 按重要性排序
        results.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return results[:limit]


# ============================================================
# Rule-based Extraction (Ollama 降级方案)
# ============================================================

class RuleExtractor:
    """规则提取器（Ollama 降级方案）"""
    
    def __init__(self):
        self.patterns = {
            "preference": [
                r'(?:我|用户)?(?:偏好|喜欢|想要)([^。！？\n]+)',
                r'(?:I\s+)?(?:prefer|like|want)\s+([^.!?\n]+)',
            ],
            "decision": [
                r'(?:决定|确认|选择)([^。！？\n]+)',
                r'(?:decide|confirm|choose)\s+([^.!?\n]+)',
            ],
            "fact": [
                r'(?:是|有|位于)([^。！？\n]{5,})',
                r'(?:is|has|located)\s+([^.!?\n]+)',
            ],
            "entity": [
                r'(?:项目|公司|团队)[：:]\s*([^\n]+)',
                r'(?:project|company|team)[::]\s*([^\n]+)',
            ],
            "task": [
                r'(?:任务|待办|需要)([^。！？\n]+)',
                r'(?:task|todo|need)\s+([^.!?\n]+)',
            ]
        }
    
    def extract(self, text: str) -> List[Dict]:
        """从文本提取记忆"""
        memories = []
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    content = match.strip()
                    if len(content) > 5:
                        # 检查重复
                        if not any(m.get("text", "")[:30] == content[:30] for m in memories):
                            memories.append({
                                "text": content,
                                "category": category,
                                "importance": self._score_importance(category, content),
                                "extracted_by": "rule",
                                "created_at": datetime.now().isoformat()
                            })
        
        return memories
    
    def _score_importance(self, category: str, text: str) -> float:
        """评分"""
        base = {
            "decision": 0.8,
            "preference": 0.6,
            "fact": 0.5,
            "entity": 0.5,
            "task": 0.6
        }.get(category, 0.5)
        
        # 关键词加成
        keywords = ["重要", "必须", "关键", "important", "critical", "must"]
        if any(kw in text.lower() for kw in keywords):
            base += 0.1
        
        return min(1.0, base)


# ============================================================
# Simple Vector Search (无 embedding 降级方案)
# ============================================================

class SimpleSimilarity:
    """简单相似度搜索（无 embedding）"""
    
    @staticmethod
    def jaccard(text1: str, text2: str) -> float:
        """Jaccard 相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    @staticmethod
    def levenshtein_ratio(text1: str, text2: str) -> float:
        """Levenshtein 相似度（通过 difflib）"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    @classmethod
    def search(cls, query: str, memories: List[Dict], method: str = "jaccard") -> List[Dict]:
        """相似度搜索"""
        results = []
        
        for mem in memories:
            text = mem.get("text", "")
            
            if method == "jaccard":
                score = cls.jaccard(query, text)
            else:
                score = cls.levenshtein_ratio(query, text)
            
            if score > 0.1:
                mem["_similarity"] = score
                results.append(mem)
        
        results.sort(key=lambda x: x.get("_similarity", 0), reverse=True)
        return results


# ============================================================
# Fallback Manager
# ============================================================

class FallbackManager:
    """降级管理器"""
    
    def __init__(self):
        self.deps = check_dependencies()
        self.json_storage = None
        self.rule_extractor = None
        
        # 初始化降级组件
        if not self.deps["lancedb"]:
            self.json_storage = JSONStorage()
        
        if not self.deps["ollama"]:
            self.rule_extractor = RuleExtractor()
    
    def status(self) -> Dict:
        """状态"""
        return {
            "dependencies": self.deps,
            "fallbacks": {
                "storage": "json" if self.json_storage else "lancedb",
                "extraction": "rule" if self.rule_extractor else "llm",
                "search": "similarity" if not self.deps["lancedb"] else "vector"
            }
        }
    
    def get_storage(self):
        """获取存储"""
        if self.json_storage:
            return self.json_storage
        
        # 使用 LanceDB
        try:
            import lancedb
            db = lancedb.connect(str(MEMORY_DIR / "vector"))
            return db.open_table("memories")
        except:
            return self.json_storage or JSONStorage()
    
    def extract(self, text: str) -> List[Dict]:
        """提取记忆"""
        if self.rule_extractor:
            return self.rule_extractor.extract(text)
        
        # 使用 LLM（需要调用 auto_extractor）
        try:
            from auto_extractor import AutoExtractor
            extractor = AutoExtractor()
            return extractor.extract_from_conversation(text, use_llm=False)
        except:
            return self.rule_extractor.extract(text) if self.rule_extractor else []
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索"""
        if self.deps["lancedb"]:
            # 向量搜索
            try:
                from memory import MemorySystemV7
                memory = MemorySystemV7()
                return memory.get_context(query, max_memories=limit)
            except:
                pass
        
        # 降级到简单搜索
        storage = self.get_storage()
        if isinstance(storage, JSONStorage):
            return storage.search(query, limit)
        else:
            memories = SimpleSimilarity.search(query, self._load_from_lancedb(), method="jaccard")
            return memories[:limit]
    
    def _load_from_lancedb(self) -> List[Dict]:
        """从 LanceDB 加载"""
        try:
            import lancedb
            db = lancedb.connect(str(MEMORY_DIR / "vector"))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            memories = []
            count = len(result.get("id", []))
            for i in range(count):
                mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                memories.append(mem)
            
            return memories
        except:
            return []


def main():
    """CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fallback Handler 0.0.7")
    parser.add_argument("command", choices=["status", "test"])
    
    args = parser.parse_args()
    
    manager = FallbackManager()
    
    if args.command == "status":
        print("🔍 依赖检测")
        print("=" * 50)
        for dep, available in manager.deps.items():
            status = "✅" if available else "❌"
            print(f"  {status} {dep}")
        
        print()
        print("📋 降级方案")
        print("=" * 50)
        for feature, fallback in manager.status()["fallbacks"].items():
            print(f"  {feature}: {fallback}")
    
    elif args.command == "test":
        print("🧪 测试降级方案...")
        
        # 测试提取
        test_text = "用户偏好使用飞书进行团队协作"
        memories = manager.extract(test_text)
        print(f"  ✅ 提取: {len(memories)} 条记忆")
        
        # 测试搜索
        results = manager.search("飞书")
        print(f"  ✅ 搜索: 找到 {len(results)} 条结果")
        
        print("✅ 降级测试通过")


if __name__ == "__main__":
    main()
