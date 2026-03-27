#!/usr/bin/env python3
"""
Memory Inference - 关联推理增强 v0.4.1

功能:
- 向量搜索 + 图谱路径扩展的联合推理
- 实体上下文链获取
- 智能缓存优化

Usage:
    python3 scripts/memory_inference.py search "项目进度"
    python3 scripts/memory_inference.py context "项目A"
    python3 scripts/memory_inference.py related "EvoMap" --depth 2
    python3 scripts/memory_inference.py chain "person_xxx" --type person
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from collections import defaultdict
import hashlib

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ONTOLOGY_DIR = MEMORY_DIR / "ontology"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
GRAPH_FILE = ONTOLOGY_DIR / "graph.jsonl"

# 添加统一内存模块路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from unified_memory import OntologyGraph, search_vector, load_all_memories, BM25
except ImportError:
    print("⚠️ 无法导入 unified_memory 模块，使用内置实现")
    OntologyGraph = None
    search_vector = None
    load_all_memories = None
    BM25 = None


class CacheManager:
    """简单缓存管理器"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """获取缓存值"""
        key = self._make_key(*args, **kwargs)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["time"] < timedelta(seconds=self.ttl):
                return entry["data"]
            else:
                del self.cache[key]
        return None
    
    def set(self, data: Any, *args, **kwargs):
        """设置缓存值"""
        key = self._make_key(*args, **kwargs)
        self.cache[key] = {
            "data": data,
            "time": datetime.now()
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        now = datetime.now()
        valid = sum(1 for v in self.cache.values() if now - v["time"] < timedelta(seconds=self.ttl))
        return {
            "total": len(self.cache),
            "valid": valid,
            "expired": len(self.cache) - valid
        }


class MemoryInference:
    """记忆关联推理引擎"""
    
    # 关系类型权重
    RELATION_WEIGHTS = {
        "participates_in": 1.0,    # 参与
        "owns": 1.0,               # 拥有
        "depends_on": 0.9,         # 依赖
        "related_to": 0.8,         # 相关
        "uses": 0.8,               # 使用
        "prefers": 0.9,            # 偏好
        "works_on": 0.9,           # 工作于
        "manages": 0.9,            # 管理
        "created": 0.85,           # 创建
        "completed": 0.85,         # 完成
        "updated": 0.7,            # 更新
        "mentioned_in": 0.6,       # 提及
    }
    
    # 实体类型优先级
    ENTITY_PRIORITY = {
        "project": 1.0,
        "task": 0.95,
        "person": 0.9,
        "decision": 0.9,
        "preference": 0.85,
        "event": 0.8,
        "tool": 0.75,
        "fact": 0.7,
    }
    
    def __init__(self, cache_ttl: int = 300):
        """
        初始化推理引擎
        
        Args:
            cache_ttl: 缓存有效期（秒）
        """
        self.cache = CacheManager(cache_ttl)
        self.graph = self._init_graph()
        self.memories = []
        self._load_memories()
    
    def _init_graph(self) -> Optional[Any]:
        """初始化知识图谱"""
        if OntologyGraph is not None:
            return OntologyGraph(GRAPH_FILE)
        
        # 内置简单实现
        return SimpleOntologyGraph(GRAPH_FILE)
    
    def _load_memories(self):
        """加载记忆数据"""
        if load_all_memories is not None:
            self.memories = load_all_memories()
        else:
            self.memories = self._load_memories_builtin()
    
    def _load_memories_builtin(self) -> List[Dict]:
        """内置记忆加载实现"""
        memories = []
        import re
        
        for md_file in sorted(MEMORY_DIR.glob("*.md"), reverse=True):
            with open(md_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith('-'):
                        continue
                    
                    match = re.match(r'- \[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\](?: \[I=([^\]]+)\])? (.+)', line)
                    if match:
                        timestamp_str, category, scope, importance_str, text = match.groups()
                        try:
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp = datetime.now()
                        
                        importance = float(importance_str) if importance_str else 0.5
                        
                        memories.append({
                            'text': text,
                            'timestamp': timestamp,
                            'category': category,
                            'scope': scope,
                            'importance': importance,
                            'file': md_file.name
                        })
        
        return memories
    
    def infer_related(self, query: str, top_k: int = 5, max_depth: int = 2) -> Dict:
        """
        向量搜索 + 图谱路径扩展联合推理
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            max_depth: 图谱扩展深度
            
        Returns:
            {
                "vector_results": [...],      # 向量搜索结果
                "graph_expansion": [...],     # 图谱扩展结果
                "merged": [...],              # 合并去重后结果
                "stats": {...}                # 统计信息
            }
        """
        # 检查缓存
        cached = self.cache.get("infer_related", query, top_k, max_depth)
        if cached:
            return cached
        
        start_time = time.time()
        
        # 1. 向量搜索获取基础结果
        vector_results = self._vector_search(query, top_k * 2)
        
        # 2. 图谱路径扩展
        graph_expansion = []
        seen_entity_ids = set()
        
        for result in vector_results:
            entity_id = result.get("entity_id") or self._find_entity_id(result.get("text", ""))
            if entity_id and entity_id not in seen_entity_ids:
                seen_entity_ids.add(entity_id)
                paths = self._expand_from_entity(entity_id, max_depth)
                graph_expansion.extend(paths)
        
        # 3. 合并去重
        merged = self._merge_results(vector_results, graph_expansion, top_k)
        
        result = {
            "vector_results": vector_results[:top_k],
            "graph_expansion": graph_expansion[:top_k],
            "merged": merged,
            "stats": {
                "vector_count": len(vector_results),
                "expansion_count": len(graph_expansion),
                "merged_count": len(merged),
                "time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        # 写入缓存
        self.cache.set(result, "infer_related", query, top_k, max_depth)
        
        return result
    
    def _vector_search(self, query: str, limit: int = 10) -> List[Dict]:
        """向量搜索"""
        results = []
        
        # 尝试使用统一内存的向量搜索
        if search_vector is not None:
            try:
                vector_results = search_vector(query, limit)
                for r in vector_results:
                    # LanceDB 返回的是距离，需要转换为相似度分数 (0-1)
                    distance = r.get("_distance", 0.0)
                    # 距离越小越相似，用 1 / (1 + distance) 转换
                    score = 1.0 / (1.0 + distance) if distance >= 0 else 1.0
                    results.append({
                        "id": r.get("id"),
                        "text": r.get("text", ""),
                        "category": r.get("category", "unknown"),
                        "importance": r.get("importance", 0.5),
                        "score": score,
                        "source": "vector",
                        "entity_id": self._find_entity_id(r.get("text", ""))
                    })
                return results
            except Exception as e:
                print(f"⚠️ 向量搜索失败: {e}", file=sys.stderr)
        
        # 回退到 BM25 搜索
        if BM25 is not None and self.memories:
            bm25 = BM25()
            bm25.fit(self.memories)
            search_results = bm25.search(query, limit)
            
            for idx, score, doc in search_results:
                results.append({
                    "id": f"bm25_{idx}",
                    "text": doc.get("text", ""),
                    "category": doc.get("category", "unknown"),
                    "importance": doc.get("importance", 0.5),
                    "score": score,
                    "source": "bm25",
                    "entity_id": self._find_entity_id(doc.get("text", ""))
                })
        
        return results
    
    def _find_entity_id(self, text: str) -> Optional[str]:
        """从文本中查找关联的实体ID"""
        if not self.graph:
            return None
        
        # 搜索图谱中的实体
        text_lower = text.lower()
        for entity_id, entity in self.graph.entities.items():
            props = entity.get("properties", {})
            name = props.get("name", "")
            if name and name.lower() in text_lower:
                return entity_id
        
        return None
    
    def _expand_from_entity(self, entity_id: str, max_depth: int = 2) -> List[Dict]:
        """从实体出发进行图谱扩展"""
        if not self.graph or not hasattr(self.graph, 'traverse'):
            return []
        
        try:
            result = self.graph.traverse(entity_id, max_depth)
            expansion = []
            
            # 添加关联实体
            for node in result.get("nodes", []):
                props = node.get("properties", {})
                weight = self.ENTITY_PRIORITY.get(node.get("type"), 0.5)
                expansion.append({
                    "entity_id": node.get("id"),
                    "type": node.get("type"),
                    "name": props.get("name", node.get("id")),
                    "text": props.get("description", ""),
                    "weight": weight,
                    "source": "graph_expansion",
                    "relation_depth": self._calculate_depth(node.get("id"), result.get("edges", []), entity_id)
                })
            
            return expansion
        except Exception as e:
            print(f"⚠️ 图谱扩展失败: {e}", file=sys.stderr)
            return []
    
    def _calculate_depth(self, node_id: str, edges: List[Dict], start_id: str) -> int:
        """计算节点到起始节点的最短距离"""
        if node_id == start_id:
            return 0
        
        # BFS 计算最短距离
        visited = {start_id}
        frontier = [(start_id, 0)]
        
        while frontier:
            current, depth = frontier.pop(0)
            if depth >= 3:  # 最大深度限制
                break
            
            for edge in edges:
                if edge["from"] == current:
                    neighbor = edge["to"]
                    if neighbor == node_id:
                        return depth + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        frontier.append((neighbor, depth + 1))
                elif edge["to"] == current:
                    neighbor = edge["from"]
                    if neighbor == node_id:
                        return depth + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        frontier.append((neighbor, depth + 1))
        
        return 3  # 默认最大深度
    
    def _merge_results(self, vector_results: List[Dict], graph_expansion: List[Dict], top_k: int) -> List[Dict]:
        """合并去重并排序结果"""
        merged_map = {}
        
        # 添加向量结果
        for r in vector_results:
            key = r.get("text", r.get("name", ""))
            merged_map[key] = {
                "text": r.get("text", ""),
                "entity_id": r.get("entity_id"),
                "category": r.get("category", "unknown"),
                "importance": r.get("importance", 0.5),
                "vector_score": r.get("score", 0),
                "graph_weight": 0,
                "sources": ["vector"]
            }
        
        # 添加图谱扩展结果
        for r in graph_expansion:
            key = r.get("text", r.get("name", ""))
            if key in merged_map:
                merged_map[key]["graph_weight"] = r.get("weight", 0)
                merged_map[key]["entity_id"] = r.get("entity_id")
                merged_map[key]["sources"].append("graph")
            else:
                merged_map[key] = {
                    "text": r.get("text", r.get("name", "")),
                    "entity_id": r.get("entity_id"),
                    "type": r.get("type"),
                    "category": r.get("type", "unknown"),
                    "importance": r.get("weight", 0.5),
                    "vector_score": 0,
                    "graph_weight": r.get("weight", 0),
                    "sources": ["graph"]
                }
        
        # 计算综合分数并排序
        scored_results = []
        for item in merged_map.values():
            # 归一化向量分数 (BM25 分数可能很大，向量分数是 0-1)
            vector_score = item["vector_score"]
            # 如果分数 > 1，说明是 BM25 分数，需要归一化
            if vector_score > 1:
                vector_score = min(1.0, vector_score / 10.0)  # 简单归一化
            # 如果分数 < 0，说明是距离值，转换为相似度
            elif vector_score < 0:
                vector_score = 1.0 / (1.0 + abs(vector_score))
            
            # 综合分数 = 向量分数 * 0.4 + 图谱权重 * 0.4 + 重要性 * 0.2
            combined_score = (
                vector_score * 0.4 +
                item["graph_weight"] * 0.4 +
                item["importance"] * 0.2
            )
            item["combined_score"] = round(combined_score, 3)
            item["vector_score_normalized"] = round(vector_score, 3)
            scored_results.append(item)
        
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return scored_results[:top_k]
    
    def get_context_chain(self, entity_id: str, entity_type: Optional[str] = None) -> List[Dict]:
        """
        获取实体上下文链
        
        根据实体类型返回不同的上下文链:
        - 项目 → 参与人 + 任务 + 进度
        - 人物 → 偏好 + 项目 + 近期对话
        - 任务 → 负责人 + 截止日期 + 依赖
        
        Args:
            entity_id: 实体ID (或实体名称，会自动查找匹配的实体)
            entity_type: 实体类型（可选，自动检测）
            
        Returns:
            上下文链列表
        """
        # 检查缓存
        cached = self.cache.get("context_chain", entity_id, entity_type)
        if cached:
            return cached
        
        if not self.graph:
            return []
        
        # 尝试精确匹配实体ID
        entity = self.graph.get_entity(entity_id) if hasattr(self.graph, 'get_entity') else None
        
        # 如果精确匹配失败，尝试按名称模糊查找
        if not entity:
            entity = self._find_entity_by_name(entity_id)
            if entity:
                entity_id = entity.get("id")
        
        # 获取实体类型
        if not entity_type:
            if entity:
                entity_type = entity.get("type", "unknown")
        
        # 根据类型获取上下文链
        if entity_type == "project":
            chain = self._get_project_context(entity_id)
        elif entity_type == "person":
            chain = self._get_person_context(entity_id)
        elif entity_type == "task":
            chain = self._get_task_context(entity_id)
        else:
            chain = self._get_generic_context(entity_id)
        
        # 写入缓存
        self.cache.set(chain, "context_chain", entity_id, entity_type)
        
        return chain
    
    def _find_entity_by_name(self, name: str) -> Optional[Dict]:
        """按名称模糊查找实体"""
        if not self.graph or not hasattr(self.graph, 'entities'):
            return None
        
        name_lower = name.lower()
        best_match = None
        best_score = 0
        
        for entity_id, entity in self.graph.entities.items():
            props = entity.get("properties", {})
            entity_name = props.get("name", "")
            
            # 完全匹配
            if entity_name.lower() == name_lower:
                return entity
            
            # 包含匹配
            if name_lower in entity_name.lower() or entity_name.lower() in name_lower:
                # 计算匹配分数
                score = len(name_lower) / max(len(entity_name), 1)
                if score > best_score:
                    best_score = score
                    best_match = entity
        
        return best_match
    
    def _get_project_context(self, project_id: str) -> List[Dict]:
        """获取项目上下文链"""
        context = []
        
        # 获取项目实体
        project = self.graph.get_entity(project_id) if hasattr(self.graph, 'get_entity') else None
        if project:
            props = project.get("properties", {})
            context.append({
                "type": "project",
                "role": "center",
                "name": props.get("name", project_id),
                "status": props.get("status", "unknown"),
                "priority": props.get("priority", "normal")
            })
        
        # 获取参与人
        if hasattr(self.graph, 'get_relations_to'):
            for rel in self.graph.get_relations_to(project_id):
                if rel.get("rel") in ["participates_in", "works_on", "manages"]:
                    person = self.graph.get_entity(rel.get("from"))
                    if person:
                        person_props = person.get("properties", {})
                        context.append({
                            "type": "person",
                            "role": rel.get("rel"),
                            "name": person_props.get("name", rel.get("from")),
                            "entity_id": rel.get("from")
                        })
        
        # 获取关联任务
        if hasattr(self.graph, 'get_relations_from'):
            for rel in self.graph.get_relations_from(project_id):
                if rel.get("rel") in ["has_task", "includes"]:
                    task = self.graph.get_entity(rel.get("to"))
                    if task:
                        task_props = task.get("properties", {})
                        context.append({
                            "type": "task",
                            "role": "subtask",
                            "name": task_props.get("name", rel.get("to")),
                            "status": task_props.get("status", "unknown"),
                            "entity_id": rel.get("to")
                        })
        
        return context
    
    def _get_person_context(self, person_id: str) -> List[Dict]:
        """获取人物上下文链"""
        context = []
        
        # 获取人物实体
        person = self.graph.get_entity(person_id) if hasattr(self.graph, 'get_entity') else None
        if person:
            props = person.get("properties", {})
            context.append({
                "type": "person",
                "role": "center",
                "name": props.get("name", person_id)
            })
        
        # 获取偏好
        if hasattr(self.graph, 'get_relations_from'):
            for rel in self.graph.get_relations_from(person_id):
                if rel.get("rel") in ["prefers", "likes"]:
                    pref = self.graph.get_entity(rel.get("to"))
                    if pref:
                        pref_props = pref.get("properties", {})
                        context.append({
                            "type": "preference",
                            "role": rel.get("rel"),
                            "name": pref_props.get("name", rel.get("to")),
                            "entity_id": rel.get("to")
                        })
        
        # 获取参与的项目
        if hasattr(self.graph, 'get_relations_from'):
            for rel in self.graph.get_relations_from(person_id):
                if rel.get("rel") in ["participates_in", "works_on", "manages"]:
                    project = self.graph.get_entity(rel.get("to"))
                    if project:
                        proj_props = project.get("properties", {})
                        context.append({
                            "type": "project",
                            "role": rel.get("rel"),
                            "name": proj_props.get("name", rel.get("to")),
                            "status": proj_props.get("status", "unknown"),
                            "entity_id": rel.get("to")
                        })
        
        return context
    
    def _get_task_context(self, task_id: str) -> List[Dict]:
        """获取任务上下文链"""
        context = []
        
        # 获取任务实体
        task = self.graph.get_entity(task_id) if hasattr(self.graph, 'get_entity') else None
        if task:
            props = task.get("properties", {})
            context.append({
                "type": "task",
                "role": "center",
                "name": props.get("name", task_id),
                "status": props.get("status", "unknown"),
                "deadline": props.get("deadline", "unknown")
            })
        
        # 获取负责人
        if hasattr(self.graph, 'get_relations_to'):
            for rel in self.graph.get_relations_to(task_id):
                if rel.get("rel") in ["owns", "assigned_to"]:
                    person = self.graph.get_entity(rel.get("from"))
                    if person:
                        person_props = person.get("properties", {})
                        context.append({
                            "type": "person",
                            "role": "owner",
                            "name": person_props.get("name", rel.get("from")),
                            "entity_id": rel.get("from")
                        })
        
        # 获取依赖
        if hasattr(self.graph, 'get_relations_from'):
            for rel in self.graph.get_relations_from(task_id):
                if rel.get("rel") in ["depends_on", "blocked_by"]:
                    dep = self.graph.get_entity(rel.get("to"))
                    if dep:
                        dep_props = dep.get("properties", {})
                        context.append({
                            "type": "task",
                            "role": "dependency",
                            "name": dep_props.get("name", rel.get("to")),
                            "entity_id": rel.get("to")
                        })
        
        return context
    
    def _get_generic_context(self, entity_id: str) -> List[Dict]:
        """获取通用上下文链"""
        context = []
        
        # 获取实体
        entity = self.graph.get_entity(entity_id) if hasattr(self.graph, 'get_entity') else None
        if entity:
            props = entity.get("properties", {})
            context.append({
                "type": entity.get("type", "unknown"),
                "role": "center",
                "name": props.get("name", entity_id)
            })
        
        # 获取所有关系
        if hasattr(self.graph, 'get_relations_from'):
            for rel in self.graph.get_relations_from(entity_id):
                target = self.graph.get_entity(rel.get("to"))
                if target:
                    target_props = target.get("properties", {})
                    context.append({
                        "type": target.get("type", "unknown"),
                        "role": rel.get("rel"),
                        "name": target_props.get("name", rel.get("to")),
                        "entity_id": rel.get("to")
                    })
        
        if hasattr(self.graph, 'get_relations_to'):
            for rel in self.graph.get_relations_to(entity_id):
                source = self.graph.get_entity(rel.get("from"))
                if source:
                    source_props = source.get("properties", {})
                    context.append({
                        "type": source.get("type", "unknown"),
                        "role": f"reverse:{rel.get('rel')}",
                        "name": source_props.get("name", rel.get("from")),
                        "entity_id": rel.get("from")
                    })
        
        return context
    
    def find_related_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        查找与查询相关的实体
        
        Args:
            query: 查询文本
            entity_type: 实体类型过滤
            limit: 返回数量
            
        Returns:
            相关实体列表
        """
        # 先进行推理搜索
        inference_result = self.infer_related(query, top_k=limit * 2)
        
        # 提取实体
        entities = []
        seen = set()
        
        for item in inference_result.get("merged", []):
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in seen:
                if entity_type and item.get("type") != entity_type:
                    continue
                
                seen.add(entity_id)
                entities.append({
                    "entity_id": entity_id,
                    "name": item.get("text", entity_id)[:50],
                    "type": item.get("type", "unknown"),
                    "score": item.get("combined_score", 0),
                    "sources": item.get("sources", [])
                })
                
                if len(entities) >= limit:
                    break
        
        return entities
    
    def get_stats(self) -> Dict:
        """获取推理引擎统计"""
        return {
            "cache": self.cache.stats(),
            "graph_entities": len(self.graph.entities) if self.graph else 0,
            "graph_relations": len(self.graph.relations) if self.graph and hasattr(self.graph, 'relations') else 0,
            "memories_loaded": len(self.memories)
        }


class SimpleOntologyGraph:
    """内置简单图谱实现（当 unified_memory 不可用时）"""
    
    def __init__(self, graph_file: Path):
        self.graph_file = graph_file
        self.entities: Dict[str, Dict] = {}
        self.relations: List[Dict] = []
        self._load()
    
    def _load(self):
        """加载图谱"""
        if not self.graph_file.exists():
            return
        
        with open(self.graph_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('op') == 'create':
                        entity = data.get('entity', {})
                        self.entities[entity.get('id')] = entity
                    elif data.get('op') == 'relate':
                        self.relations.append({
                            'from': data.get('from'),
                            'rel': data.get('rel'),
                            'to': data.get('to'),
                            'created': data.get('created')
                        })
                except:
                    continue
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_relations_from(self, entity_id: str) -> List[Dict]:
        """获取从该实体出发的关系"""
        return [r for r in self.relations if r['from'] == entity_id]
    
    def get_relations_to(self, entity_id: str) -> List[Dict]:
        """获取指向该实体的关系"""
        return [r for r in self.relations if r['to'] == entity_id]
    
    def traverse(self, start_id: str, depth: int = 2, relation_filter: str = None) -> Dict:
        """图遍历"""
        result = {
            'center': self.entities.get(start_id),
            'nodes': [],
            'edges': []
        }
        
        if start_id not in self.entities:
            return result
        
        visited = {start_id}
        frontier = [start_id]
        
        for _ in range(depth):
            new_frontier = []
            for node_id in frontier:
                # 出边
                for rel in self.get_relations_from(node_id):
                    if relation_filter and rel['rel'] != relation_filter:
                        continue
                    
                    target_id = rel['to']
                    result['edges'].append({
                        'from': node_id,
                        'rel': rel['rel'],
                        'to': target_id
                    })
                    
                    if target_id in self.entities and target_id not in visited:
                        visited.add(target_id)
                        new_frontier.append(target_id)
                        result['nodes'].append(self.entities[target_id])
                
                # 入边
                for rel in self.get_relations_to(node_id):
                    if relation_filter and rel['rel'] != relation_filter:
                        continue
                    
                    source_id = rel['from']
                    result['edges'].append({
                        'from': source_id,
                        'rel': rel['rel'],
                        'to': node_id
                    })
                    
                    if source_id in self.entities and source_id not in visited:
                        visited.add(source_id)
                        new_frontier.append(source_id)
                        result['nodes'].append(self.entities[source_id])
            
            frontier = new_frontier
        
        return result


def print_search_results(result: Dict, query: str):
    """打印搜索结果"""
    print(f"\n🔍 联合推理搜索: \"{query}\"")
    print(f"   向量结果: {result['stats']['vector_count']} 条")
    print(f"   图谱扩展: {result['stats']['expansion_count']} 条")
    print(f"   合并结果: {result['stats']['merged_count']} 条")
    print(f"   耗时: {result['stats']['time_ms']} ms\n")
    
    print("📊 Top 合并结果:")
    for i, item in enumerate(result['merged'][:5], 1):
        sources = "+".join(item.get('sources', ['unknown']))
        score = item.get('combined_score', 0)
        text = item.get('text', '')[:60]
        print(f"   {i}. [{sources}] {text}... (score: {score:.3f})")
    
    if result['graph_expansion']:
        print("\n🔗 图谱扩展发现:")
        for item in result['graph_expansion'][:3]:
            name = item.get('name', item.get('text', 'unknown'))
            type_ = item.get('type', 'unknown')
            print(f"   - [{type_}] {name}")


def print_context_chain(chain: List[Dict], entity_id: str):
    """打印上下文链"""
    print(f"\n📋 实体上下文链: {entity_id}\n")
    
    if not chain:
        print("   未找到上下文信息")
        return
    
    center = None
    for item in chain:
        if item.get('role') == 'center':
            center = item
            break
    
    if center:
        print(f"🎯 {center.get('type', 'Entity').upper()}: {center.get('name', entity_id)}")
        if center.get('status'):
            print(f"   状态: {center['status']}")
        if center.get('priority'):
            print(f"   优先级: {center['priority']}")
        print()
    
    related = [i for i in chain if i.get('role') != 'center']
    
    if related:
        print("🔗 关联信息:")
        for item in related:
            type_ = item.get('type', 'unknown')
            role = item.get('role', 'related')
            name = item.get('name', 'unnamed')
            
            extra = ""
            if item.get('status'):
                extra += f" [{item['status']}]"
            
            print(f"   - [{type_}/{role}] {name}{extra}")


def main():
    parser = argparse.ArgumentParser(description="Memory Inference v0.4.1")
    parser.add_argument("command", choices=["search", "context", "related", "chain", "stats", "cache-clear"])
    parser.add_argument("query", nargs="?", help="查询内容或实体ID")
    parser.add_argument("--depth", "-d", type=int, default=2, help="图谱扩展深度")
    parser.add_argument("--type", "-t", help="实体类型")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量限制")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    parser.add_argument("--cache-ttl", type=int, default=300, help="缓存有效期(秒)")
    
    args = parser.parse_args()
    
    # 初始化推理引擎
    inference = MemoryInference(cache_ttl=args.cache_ttl)
    
    if args.command == "search":
        if not args.query:
            print("❌ 请提供查询内容")
            sys.exit(1)
        
        result = inference.infer_related(args.query, top_k=args.limit, max_depth=args.depth)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_search_results(result, args.query)
    
    elif args.command == "context":
        if not args.query:
            print("❌ 请提供实体ID")
            sys.exit(1)
        
        chain = inference.get_context_chain(args.query, args.type)
        
        if args.json:
            print(json.dumps(chain, ensure_ascii=False, indent=2))
        else:
            print_context_chain(chain, args.query)
    
    elif args.command == "related":
        if not args.query:
            print("❌ 请提供查询内容")
            sys.exit(1)
        
        entities = inference.find_related_entities(args.query, args.type, args.limit)
        
        if args.json:
            print(json.dumps(entities, ensure_ascii=False, indent=2))
        else:
            print(f"\n🔗 相关实体: \"{args.query}\"\n")
            for i, e in enumerate(entities, 1):
                sources = "+".join(e.get('sources', []))
                print(f"   {i}. [{e.get('type', 'unknown')}] {e.get('name', 'unnamed')} (score: {e.get('score', 0):.3f})")
                print(f"      ID: {e.get('entity_id')} | 来源: {sources}")
    
    elif args.command == "chain":
        # chain 是 context 的别名
        if not args.query:
            print("❌ 请提供实体ID")
            sys.exit(1)
        
        chain = inference.get_context_chain(args.query, args.type)
        
        if args.json:
            print(json.dumps(chain, ensure_ascii=False, indent=2))
        else:
            print_context_chain(chain, args.query)
    
    elif args.command == "stats":
        stats = inference.get_stats()
        
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("\n📊 Memory Inference 引擎统计")
            print(f"   缓存: {stats['cache']['valid']} 有效 / {stats['cache']['total']} 总计")
            print(f"   图谱实体: {stats['graph_entities']}")
            print(f"   图谱关系: {stats['graph_relations']}")
            print(f"   加载记忆: {stats['memories_loaded']}")
    
    elif args.command == "cache-clear":
        inference.cache.clear()
        print("✅ 缓存已清空")


if __name__ == "__main__":
    main()
