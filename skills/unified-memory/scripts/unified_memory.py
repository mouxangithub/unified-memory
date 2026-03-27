#!/usr/bin/env python3
"""
Unified Memory - 统一记忆入口 v3.0
整合 Memory（文本+向量）+ Ontology（知识图谱），支持双写同步

核心功能:
- 文本搜索 (BM25 变体)
- 向量搜索 (LanceDB + 轻量 embedding)
- Ontology 图遍历
- 自动重要性评分
- 智能摘要

Usage:
    unified_memory.py store --text "内容" [--category fact]
    unified_memory.py query --text "搜索内容" [--limit 5]
    unified_memory.py graph --from ENTITY_ID [--depth 2]
    unified_memory.py score --text "内容"
    unified_memory.py summarize [--days 7]
    unified_memory.py clean [--days 30]
    unified_memory.py status
"""

import argparse
import json
import os
import re
import sys
import uuid
import requests
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set

# ============================================================
# Ollama Embedding 配置
# ============================================================
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

def get_ollama_embedding(text: str) -> Optional[List[float]]:
    """调用 Ollama 获取 embedding"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding")
    except Exception as e:
        print(f"⚠️ Ollama embedding 失败: {e}", file=sys.stderr)
        return None

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ONTOLOGY_DIR = MEMORY_DIR / "ontology"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MEMORY_FILE = WORKSPACE / "MEMORY.md"

# 确保目录存在
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ONTOLOGY_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# BM25 文本相似度 (轻量级，无需额外依赖)
# ============================================================

class BM25:
    """简单的 BM25 实现"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs: Dict[str, int] = Counter()
        self.doc_lens: List[int] = []
        self.avgdl: float = 0
        self.docs: List[Dict[str, Any]] = []
        self.doc_terms: List[Counter] = []
    
    def tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 中文按字符，英文按空格
        tokens = []
        # 匹配中文词
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                tokens.append(char)
        # 匹配英文单词
        en_words = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(en_words)
        return tokens
    
    def fit(self, docs: List[Dict[str, Any]]):
        """构建索引"""
        self.docs = docs
        self.doc_lens = []
        self.doc_terms = []
        
        for doc in docs:
            text = doc.get('text', '')
            tokens = self.tokenize(text)
            self.doc_lens.append(len(tokens))
            term_freq = Counter(tokens)
            self.doc_terms.append(term_freq)
            
            for term in term_freq:
                self.doc_freqs[term] += 1
        
        if self.doc_lens:
            self.avgdl = sum(self.doc_lens) / len(self.doc_lens)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float, Dict]]:
        """搜索"""
        if not self.docs or not self.avgdl:
            return []
        
        query_tokens = self.tokenize(query)
        scores = []
        N = len(self.docs)
        
        for i, (doc_len, doc_term_freq) in enumerate(zip(self.doc_lens, self.doc_terms)):
            score = 0.0
            for term in query_tokens:
                if term not in doc_term_freq:
                    continue
                
                # IDF
                df = self.doc_freqs.get(term, 0)
                if df == 0:
                    continue
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
                
                # TF
                tf = doc_term_freq[term]
                tf_norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
                
                score += idf * tf_norm
            
            if score > 0:
                scores.append((i, score, self.docs[i]))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


import math


# ============================================================
# 重要性评分系统
# ============================================================

class ImportanceScorer:
    """自动评估记忆重要性"""
    
    # 重要关键词
    IMPORTANT_PATTERNS = {
        'decision': ['决定', '决策', '选择', '确定', '选中', 'choose', 'decide', 'selected'],
        'critical': ['重要', '关键', '紧急', 'critical', 'urgent', '重要'],
        'preference': ['喜欢', '偏好', '习惯', 'prefer', 'like', '习惯'],
        'error': ['错误', '失败', '异常', 'error', 'fail', 'bug', '问题'],
        'success': ['完成', '成功', '解决', 'done', 'success', 'fixed', '✅'],
        'entity': ['项目', '任务', '人员', 'project', 'task', 'person'],
    }
    
    # 衰减因子
    DECAY_FACTOR = 0.95  # 每天衰减 5%
    BASE_SCORE = 0.5
    
    def score(self, text: str, timestamp: Optional[datetime] = None, 
              access_count: int = 0, entity_linked: bool = False) -> float:
        """
        计算重要性分数 (0-1)
        
        考虑因素:
        1. 内容关键词
        2. 时间衰减
        3. 访问频率
        4. 是否关联实体
        """
        score = self.BASE_SCORE
        text_lower = text.lower()
        
        # 1. 关键词加分
        for category, patterns in self.IMPORTANT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    score += 0.05
        
        # 2. 时间衰减
        if timestamp:
            days_old = (datetime.now() - timestamp).days
            decay = self.DECAY_FACTOR ** days_old
            score *= decay
        
        # 3. 访问频率加分
        score += min(0.2, access_count * 0.02)
        
        # 4. 关联实体加分
        if entity_linked:
            score += 0.1
        
        # 5. 长度惩罚（太长的文本可能不够精炼）
        if len(text) > 500:
            score *= 0.9
        
        return min(1.0, max(0.0, score))
    
    def categorize(self, text: str) -> str:
        """自动分类"""
        text_lower = text.lower()
        
        for category, patterns in self.IMPORTANT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return category
        
        return 'other'


# ============================================================
# Ontology 图查询
# ============================================================

class OntologyGraph:
    """知识图谱操作"""
    
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
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """按类型获取实体"""
        return [e for e in self.entities.values() if e.get('type') == entity_type]
    
    def get_relations_from(self, entity_id: str) -> List[Dict]:
        """获取从该实体出发的关系"""
        return [r for r in self.relations if r['from'] == entity_id]
    
    def get_relations_to(self, entity_id: str) -> List[Dict]:
        """获取指向该实体的关系"""
        return [r for r in self.relations if r['to'] == entity_id]
    
    def traverse(self, start_id: str, depth: int = 2, relation_filter: str = None) -> Dict:
        """
        图遍历
        
        返回以 start_id 为中心的关系图
        """
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
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索实体"""
        results = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            props = entity.get('properties', {})
            name = props.get('name', '')
            text = json.dumps(props, ensure_ascii=False)
            
            if query_lower in text.lower() or query_lower in name.lower():
                results.append(entity)
                if len(results) >= limit:
                    break
        
        return results


# ============================================================
# 核心功能
# ============================================================

def get_today_memory_file():
    """获取今天的记忆文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    return MEMORY_DIR / f"{today}.md"


def init_vector_db():
    """初始化向量数据库"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        
        # 尝试打开已存在的表
        try:
            table = db.open_table("memories")
            return db, table
        except Exception:
            pass  # 表不存在，创建新表
        
        # 创建新表
        import pyarrow as pa
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field("category", pa.string()),
            pa.field("scope", pa.string()),
            pa.field("importance", pa.float64()),
            pa.field("timestamp", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), list_size=768)),
        ])
        table = db.create_table("memories", schema=schema)
        
        return db, table
    except Exception as e:
        print(f"⚠️ LanceDB 初始化失败: {e}", file=sys.stderr)
        return None, None


def store_to_vector(text: str, category: str, scope: str, importance: float, timestamp: str) -> bool:
    """存储到向量数据库"""
    try:
        _, table = init_vector_db()
        if table is None:
            return False
        
        embedding = get_ollama_embedding(text)
        if embedding is None:
            return False
        
        table.add([{
            "id": str(uuid.uuid4()),
            "text": text,
            "category": category,
            "scope": scope,
            "importance": importance,
            "timestamp": timestamp,
            "vector": embedding
        }])
        return True
    except Exception as e:
        print(f"⚠️ 向量存储失败: {e}", file=sys.stderr)
        return False


def search_vector(query: str, limit: int = 5) -> List[Dict]:
    """向量搜索"""
    try:
        _, table = init_vector_db()
        if table is None:
            return []
        
        embedding = get_ollama_embedding(query)
        if embedding is None:
            return []
        
        results = table.search(embedding).limit(limit).to_list()
        return results
    except Exception as e:
        print(f"⚠️ 向量搜索失败: {e}", file=sys.stderr)
        return []


def store_to_memory(text: str, category: str = "fact", scope: str = "default", 
                    importance: float = None) -> str:
    """存储到 Memory 系统"""
    today_file = get_today_memory_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 自动评分
    if importance is None:
        scorer = ImportanceScorer()
        importance = scorer.score(text)
    
    # 记录格式: [时间] [分类] [范围] [重要性] 内容
    entry = f"- [{timestamp}] [{category}] [{scope}] [I={importance:.2f}] {text}\n"
    
    with open(today_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # 存储到向量数据库
    vector_stored = store_to_vector(text, category, scope, importance, timestamp)
    
    status = "✅ 已写入 Memory"
    if vector_stored:
        status += " + 向量"
    status += f" (重要性: {importance:.2f}): {text[:50]}..."
    
    return status


def store_to_ontology(entity_type: str, properties: dict) -> Tuple[str, str]:
    """存储到 Ontology 图谱"""
    import uuid
    
    graph_file = ONTOLOGY_DIR / "graph.jsonl"
    
    entity_id = f"{entity_type.lower()}_{uuid.uuid4().hex[:8]}"
    entity = {
        "op": "create",
        "entity": {
            "id": entity_id,
            "type": entity_type,
            "properties": properties,
            "created": datetime.now().isoformat()
        }
    }
    
    with open(graph_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entity, ensure_ascii=False) + "\n")
    
    return entity_id, f"✅ 已创建 Ontology 实体: {entity_type} ({entity_id})"


def relate_entities(from_id: str, relation_type: str, to_id: str) -> str:
    """关联 Ontology 实体"""
    graph_file = ONTOLOGY_DIR / "graph.jsonl"
    
    relation = {
        "op": "relate",
        "from": from_id,
        "rel": relation_type,
        "to": to_id,
        "created": datetime.now().isoformat()
    }
    
    with open(graph_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(relation, ensure_ascii=False) + "\n")
    
    return f"✅ 已创建关系: {from_id} --[{relation_type}]--> {to_id}"


def load_all_memories() -> List[Dict[str, Any]]:
    """加载所有记忆"""
    memories = []
    
    for md_file in sorted(MEMORY_DIR.glob("*.md"), reverse=True):
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith('-'):
                    continue
                
                # 解析格式: [时间] [分类] [范围] [重要性?] 内容
                # 兼容多种格式
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
                else:
                    # 兼容旧格式: 纯文本行或 Markdown 标题
                    line_stripped = line.lstrip('- ')
                    if line_stripped and not line_stripped.startswith('#'):
                        memories.append({
                            'text': line_stripped,
                            'timestamp': datetime.now(),
                            'category': 'legacy',
                            'scope': 'default',
                            'importance': 0.5,
                            'file': md_file.name
                        })
    
    return memories


def unified_query(text: str, limit: int = 5) -> str:
    """统一查询 - 向量搜索 + 文本搜索 + 图谱搜索 (混合检索)"""
    results = []
    
    # 1. 向量搜索 (语义相似)
    vector_results = search_vector(text, limit)
    if vector_results:
        results.append("📐 向量搜索 (语义相似):")
        for i, r in enumerate(vector_results[:3], 1):
            importance = r.get('importance', 0.5)
            dist = r.get('_distance', 0)
            results.append(f"  {i}. [I={importance:.2f}] {r['text'][:50]}... (距离: {dist:.2f})")
    
    # 2. 加载所有记忆
    memories = load_all_memories()
    
    if memories:
        # 3. BM25 搜索 (关键词匹配)
        bm25 = BM25()
        bm25.fit(memories)
        search_results = bm25.search(text, limit)
        
        if search_results:
            results.append("\n📝 文本搜索 (BM25):")
            for i, (idx, score, doc) in enumerate(search_results, 1):
                importance = doc.get('importance', 0.5)
                results.append(f"  {i}. [I={importance:.2f}] {doc['text'][:60]}... (score: {score:.2f})")
    
    # 4. Ontology 图谱搜索
    graph = OntologyGraph(ONTOLOGY_DIR / "graph.jsonl")
    entity_results = graph.search(text, limit=3)
    
    if entity_results:
        results.append("\n🔗 Ontology 匹配:")
        for i, entity in enumerate(entity_results, 1):
            props = entity.get('properties', {})
            name = props.get('name', entity.get('id'))
            results.append(f"  {i}. [{entity.get('type')}] {name}")
    
    if results:
        return "🔍 统一查询结果:\n" + "\n".join(results)
    else:
        return "❌ 未找到相关内容"


def graph_traverse(entity_id: str, depth: int = 2) -> str:
    """图谱遍历"""
    graph = OntologyGraph(ONTOLOGY_DIR / "graph.jsonl")
    result = graph.traverse(entity_id, depth)
    
    if not result['center']:
        return f"❌ 未找到实体: {entity_id}"
    
    output = []
    center = result['center']
    props = center.get('properties', {})
    name = props.get('name', center.get('id'))
    
    output.append(f"🎯 中心实体: [{center.get('type')}] {name}")
    output.append(f"   ID: {center.get('id')}")
    
    if result['nodes']:
        output.append(f"\n📦 关联实体 ({len(result['nodes'])} 个):")
        for node in result['nodes'][:10]:
            node_props = node.get('properties', {})
            node_name = node_props.get('name', node.get('id'))
            output.append(f"   - [{node.get('type')}] {node_name}")
    
    if result['edges']:
        output.append(f"\n🔗 关系 ({len(result['edges'])} 条):")
        for edge in result['edges'][:10]:
            from_entity = graph.get_entity(edge['from'])
            to_entity = graph.get_entity(edge['to'])
            from_name = from_entity.get('properties', {}).get('name', edge['from']) if from_entity else edge['from']
            to_name = to_entity.get('properties', {}).get('name', edge['to']) if to_entity else edge['to']
            output.append(f"   - {from_name} --[{edge['rel']}]--> {to_name}")
    
    return "\n".join(output)


def score_text(text: str) -> str:
    """评估文本重要性"""
    scorer = ImportanceScorer()
    score = scorer.score(text)
    category = scorer.categorize(text)
    
    return f"""📊 重要性评分

文本: {text[:50]}...

分数: {score:.2f}
分类: {category}

建议: {'📌 值得长期记住' if score > 0.6 else '📋 普通记录'}
"""


def extract_key_points(text: str) -> List[str]:
    """从文本中提取关键点"""
    points = []
    
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            points.append(line[2:])
        elif line.startswith('## '):
            points.append("  - " + line[3:])
        elif any(marker in line for marker in ['✅', '❌', '⚠️', '📌', '🔧']):
            if 10 < len(line) < 150:
                points.append("  - " + line)
        elif any(kw in line for kw in ['已完成', '创建', '修复', '决定', '选择', '重要']):
            if 10 < len(line) < 150:
                points.append("  - " + line)
    
    return points[:15]


def summarize_to_memory_md(days: int = 7) -> str:
    """摘要到 MEMORY.md"""
    today = datetime.now()
    summary_points = []
    
    for i in range(days):
        date = today - timedelta(days=i)
        date_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        
        if date_file.exists():
            with open(date_file, "r", encoding="utf-8") as f:
                content = f.read()
                points = extract_key_points(content)
                if points:
                    summary_points.append(f"### {date.strftime('%Y-%m-%d')}\n" + "\n".join(points))
    
    if not summary_points:
        return "⚠️ 没有可摘要的内容"
    
    # 读取现有 MEMORY.md
    existing = ""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
    
    summary_section = "\n\n## 最近活动\n\n" + "\n\n".join(summary_points) + "\n"
    
    # 更新
    if "## 最近活动" in existing:
        new_content = re.sub(r'## 最近活动\n.*', summary_section.strip(), existing, flags=re.DOTALL)
    else:
        new_content = existing + summary_section
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return f"✅ 已摘要 {len(summary_points)} 天的活动到 MEMORY.md"


def clean_old_memories(days: int = 30) -> str:
    """清理过期记忆"""
    cutoff = datetime.now() - timedelta(days=days)
    cleaned = []
    
    for md_file in MEMORY_DIR.glob("*.md"):
        try:
            date_str = md_file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                snapshot_dir = MEMORY_DIR / "snapshots"
                snapshot_dir.mkdir(exist_ok=True)
                import shutil
                shutil.move(str(md_file), str(snapshot_dir / md_file.name))
                cleaned.append(md_file.name)
        except ValueError:
            continue
    
    if cleaned:
        return f"🧹 已清理 {len(cleaned)} 个过期文件\n  - " + "\n  - ".join(cleaned)
    return "✅ 没有需要清理的文件"


def get_status() -> str:
    """获取系统状态"""
    memory_files = list(MEMORY_DIR.glob("*.md"))
    
    # 统计记忆
    memories = load_all_memories()
    total_lines = len(memories)
    
    # 重要性分布
    high_importance = len([m for m in memories if m.get('importance', 0) > 0.6])
    
    # Ontology
    graph = OntologyGraph(ONTOLOGY_DIR / "graph.jsonl")
    entity_count = len(graph.entities)
    relation_count = len(graph.relations)
    
    # 向量数据库
    vector_count = 0
    _, table = init_vector_db()
    if table is not None:
        try:
            vector_count = table.count_rows()
        except:
            pass
    
    # Ollama 状态
    ollama_status = "❌"
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.ok:
            ollama_status = "✅"
    except:
        pass
    
    return f"""📊 记忆系统状态 v3.1

Memory (文本):
  - 文件数: {len(memory_files)}
  - 总记录: {total_lines} 条
  - 高重要性: {high_importance} 条 (>0.6)
  - 长期记忆: {'✅' if MEMORY_FILE.exists() else '❌'} MEMORY.md

Vector (向量):
  - 向量数: {vector_count}
  - Embedding: {OLLAMA_EMBED_MODEL}
  - Ollama: {ollama_status} {OLLAMA_URL}

Ontology (图谱):
  - 实体数: {entity_count}
  - 关系数: {relation_count}
  - 类型分布: {dict(Counter(e.get('type') for e in graph.entities.values()))}

功能:
  ✅ 向量语义搜索 (Ollama)
  ✅ BM25 关键词搜索
  ✅ 混合检索
  ✅ 图谱遍历
  ✅ 自动重要性评分
  ✅ 智能摘要 + 过期清理
"""


def main():
    parser = argparse.ArgumentParser(description="Unified Memory v3.0")
    subparsers = parser.add_subparsers(dest="command")
    
    # store
    store_p = subparsers.add_parser("store", help="存储记忆")
    store_p.add_argument("--text", required=True)
    store_p.add_argument("--category", default="fact")
    store_p.add_argument("--scope", default="default")
    
    # query
    query_p = subparsers.add_parser("query", help="统一搜索")
    query_p.add_argument("--text", required=True)
    query_p.add_argument("--limit", type=int, default=5)
    
    # graph
    graph_p = subparsers.add_parser("graph", help="图谱操作")
    graph_p.add_argument("--traverse", dest="entity_id", help="遍历图谱")
    graph_p.add_argument("--depth", type=int, default=2)
    graph_p.add_argument("--list-entities", action="store_true", help="列出所有实体")
    graph_p.add_argument("--type", help="按类型筛选")
    
    # score
    score_p = subparsers.add_parser("score", help="重要性评分")
    score_p.add_argument("--text", required=True)
    
    # summarize
    sum_p = subparsers.add_parser("summarize", help="摘要")
    sum_p.add_argument("--days", type=int, default=7)
    
    # clean
    clean_p = subparsers.add_parser("clean", help="清理")
    clean_p.add_argument("--days", type=int, default=30)
    
    # status
    subparsers.add_parser("status", help="状态")
    
    # ontology
    ont_p = subparsers.add_parser("ontology", help="Ontology 操作")
    ont_sub = ont_p.add_subparsers(dest="ont_cmd")
    
    ont_create = ont_sub.add_parser("create", help="创建实体")
    ont_create.add_argument("--type", required=True)
    ont_create.add_argument("--props", required=True)
    
    ont_relate = ont_sub.add_parser("relate", help="创建关系")
    ont_relate.add_argument("--from", dest="from_id", required=True)
    ont_relate.add_argument("--rel", required=True)
    ont_relate.add_argument("--to", required=True)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "store":
            print(store_to_memory(args.text, args.category, args.scope))
        
        elif args.command == "query":
            print(unified_query(args.text, args.limit))
        
        elif args.command == "graph":
            if args.entity_id:
                print(graph_traverse(args.entity_id, args.depth))
            elif args.list_entities:
                graph = OntologyGraph(ONTOLOGY_DIR / "graph.jsonl")
                entities = graph.get_entities_by_type(args.type) if args.type else list(graph.entities.values())
                for e in entities[:20]:
                    props = e.get('properties', {})
                    print(f"  [{e.get('type')}] {props.get('name', e.get('id'))} ({e.get('id')})")
            else:
                print("用法: --traverse ENTITY_ID 或 --list-entities")
        
        elif args.command == "score":
            print(score_text(args.text))
        
        elif args.command == "summarize":
            print(summarize_to_memory_md(args.days))
        
        elif args.command == "clean":
            print(clean_old_memories(args.days))
        
        elif args.command == "status":
            print(get_status())
        
        elif args.command == "ontology":
            if args.ont_cmd == "create":
                props = json.loads(args.props)
                entity_id, msg = store_to_ontology(args.type, props)
                store_to_memory(f"【Ontology】创建: {args.type} {props.get('name', entity_id)}", "entity", "ontology")
                print(msg)
            elif args.ont_cmd == "relate":
                msg = relate_entities(args.from_id, args.rel, args.to)
                store_to_memory(f"【Ontology】关联: {args.from_id} --[{args.rel}]--> {args.to}", "relation", "ontology")
                print(msg)
    
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
