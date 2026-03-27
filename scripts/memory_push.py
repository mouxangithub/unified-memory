#!/usr/bin/env python3
"""
Memory Push - 智能推送和提醒系统 v0.4.1

核心功能:
- 项目截止日期提醒
- 关联记忆更新通知
- 矛盾记忆检测提醒
- 新关联发现通知

Usage:
    memory_push.py check              # 检查并生成推送
    memory_push.py mark-read <id>     # 标记已读
    memory_push.py list               # 列出未读推送
    memory_push.py list --all         # 列出所有推送
    memory_push.py clear              # 清理过期推送
    memory_push.py status             # 查看状态
"""

import argparse
import json
import os
import re
import sys
import uuid
import hashlib
import requests
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ONTOLOGY_DIR = MEMORY_DIR / "ontology"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
PUSH_QUEUE_DIR = MEMORY_DIR / "push_queue"
PUSH_STATE_FILE = PUSH_QUEUE_DIR / "push_state.json"

# Ollama 配置
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 确保目录存在
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
PUSH_QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 推送规则
# ============================================================
PUSH_RULES = {
    "project_deadline": {
        "advance_days": 3,
        "check_interval": "daily",
        "priority": "high",
        "template": "📅 项目截止提醒: {project_name} 将在 {days_left} 天后截止 ({deadline})"
    },
    "memory_update": {
        "notify_related": True,
        "related_threshold": 0.8,
        "priority": "medium",
        "template": "🔄 关联记忆更新: {related_topic} 有新信息 - {summary}"
    },
    "conflict_detected": {
        "require_confirm": True,
        "auto_resolve": False,
        "priority": "high",
        "template": "⚠️ 矛盾记忆检测: {conflict_desc} - 请确认正确信息"
    },
    "new_related": {
        "notify": True,
        "min_similarity": 0.85,
        "priority": "low",
        "template": "🔗 发现新关联: {entity_a} 与 {entity_b} 相似度 {similarity:.0%}"
    }
}


# ============================================================
# 推送消息类
# ============================================================

class PushMessage:
    """推送消息"""
    
    def __init__(self, msg_type: str, title: str, content: str,
                 priority: str = "medium", metadata: dict = None):
        self.id = self._generate_id(msg_type, content)
        self.type = msg_type
        self.title = title
        self.content = content
        self.priority = priority
        self.metadata = metadata or {}
        self.created = datetime.now().isoformat()
        self.read = False
        self.read_at = None
    
    def _generate_id(self, msg_type: str, content: str) -> str:
        """生成唯一ID (基于内容哈希，支持去重)"""
        hash_input = f"{msg_type}:{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "metadata": self.metadata,
            "created": self.created,
            "read": self.read,
            "read_at": self.read_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PushMessage':
        msg = cls(
            msg_type=data["type"],
            title=data["title"],
            content=data["content"],
            priority=data.get("priority", "medium"),
            metadata=data.get("metadata", {})
        )
        msg.id = data["id"]
        msg.created = data["created"]
        msg.read = data.get("read", False)
        msg.read_at = data.get("read_at")
        return msg
    
    def __str__(self) -> str:
        status = "✅" if self.read else "🔔"
        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        icon = priority_icons.get(self.priority, "⚪")
        return f"{status} {icon} [{self.id}] {self.title}: {self.content}"


# ============================================================
# 推送状态管理
# ============================================================

class PushState:
    """推送状态管理"""
    
    def __init__(self):
        self.state_file = PUSH_STATE_FILE
        self.messages: Dict[str, PushMessage] = {}
        self.last_check: Dict[str, str] = {}  # 类型 -> 最后检查时间
        self._load()
    
    def _load(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for msg_data in data.get("messages", []):
                        msg = PushMessage.from_dict(msg_data)
                        self.messages[msg.id] = msg
                    self.last_check = data.get("last_check", {})
            except Exception as e:
                print(f"⚠️ 加载推送状态失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存状态"""
        try:
            data = {
                "messages": [msg.to_dict() for msg in self.messages.values()],
                "last_check": self.last_check
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存推送状态失败: {e}", file=sys.stderr)
    
    def add_message(self, msg: PushMessage) -> bool:
        """添加推送消息 (去重)"""
        if msg.id in self.messages:
            return False  # 已存在，去重
        
        self.messages[msg.id] = msg
        self._save()
        return True
    
    def mark_read(self, msg_id: str) -> bool:
        """标记已读"""
        if msg_id in self.messages:
            self.messages[msg_id].read = True
            self.messages[msg_id].read_at = datetime.now().isoformat()
            self._save()
            return True
        return False
    
    def get_unread(self) -> List[PushMessage]:
        """获取未读消息"""
        return [msg for msg in self.messages.values() if not msg.read]
    
    def get_all(self, limit: int = 50) -> List[PushMessage]:
        """获取所有消息"""
        msgs = sorted(self.messages.values(), key=lambda m: m.created, reverse=True)
        return msgs[:limit]
    
    def cleanup_old(self, days: int = 30) -> int:
        """清理过期消息"""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for msg_id, msg in self.messages.items():
            if msg.read:
                try:
                    created = datetime.fromisoformat(msg.created)
                    if created < cutoff:
                        to_remove.append(msg_id)
                except:
                    pass
        
        for msg_id in to_remove:
            del self.messages[msg_id]
        
        if to_remove:
            self._save()
        
        return len(to_remove)
    
    def update_last_check(self, check_type: str):
        """更新最后检查时间"""
        self.last_check[check_type] = datetime.now().isoformat()
        self._save()
    
    def should_check(self, check_type: str, interval_hours: int = 24) -> bool:
        """判断是否应该检查"""
        if check_type not in self.last_check:
            return True
        
        try:
            last = datetime.fromisoformat(self.last_check[check_type])
            return datetime.now() - last > timedelta(hours=interval_hours)
        except:
            return True


# ============================================================
# Embedding 和向量搜索
# ============================================================

def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本向量"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding")
    except Exception as e:
        print(f"⚠️ Embedding 失败: {e}", file=sys.stderr)
        return None


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """计算余弦相似度"""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def search_vector(query: str, limit: int = 5) -> List[Dict]:
    """向量搜索"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        embedding = get_embedding(query)
        if embedding is None:
            return []
        
        results = table.search(embedding).limit(limit).to_list()
        return results
    except Exception as e:
        print(f"⚠️ 向量搜索失败: {e}", file=sys.stderr)
        return []


# ============================================================
# LLM 调用
# ============================================================

def call_llm(prompt: str, model: str = None) -> Optional[str]:
    """调用 LLM"""
    model = model or OLLAMA_LLM_MODEL
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"⚠️ LLM 调用失败: {e}", file=sys.stderr)
        return None


def call_llm_json(prompt: str, model: str = None) -> Optional[Dict]:
    """调用 LLM 并解析 JSON"""
    response = call_llm(prompt, model)
    if not response:
        return None
    
    # 尝试提取 JSON
    try:
        return json.loads(response)
    except:
        pass
    
    # 从 markdown 代码块提取
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    return None


# ============================================================
# 记忆加载
# ============================================================

def load_all_memories() -> List[Dict[str, Any]]:
    """加载所有记忆"""
    memories = []
    
    for md_file in sorted(MEMORY_DIR.glob("*.md"), reverse=True):
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith('-'):
                    continue
                
                # 解析格式
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


def load_ontology_graph() -> Tuple[Dict[str, Dict], List[Dict]]:
    """加载 Ontology 图谱"""
    graph_file = ONTOLOGY_DIR / "graph.jsonl"
    entities = {}
    relations = []
    
    if not graph_file.exists():
        return entities, relations
    
    with open(graph_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('op') == 'create':
                    entity = data.get('entity', {})
                    entities[entity.get('id')] = entity
                elif data.get('op') == 'relate':
                    relations.append({
                        'from': data.get('from'),
                        'rel': data.get('rel'),
                        'to': data.get('to'),
                        'created': data.get('created')
                    })
            except:
                continue
    
    return entities, relations


# ============================================================
# Memory Pusher 核心类
# ============================================================

class MemoryPusher:
    """智能推送管理器"""
    
    def __init__(self, silent: bool = False):
        self.state = PushState()
        self.silent = silent
        self.new_notifications: List[PushMessage] = []
    
    def check_and_push(self) -> List[PushMessage]:
        """检查并推送提醒"""
        self.new_notifications = []
        
        # 1. 项目截止日期提醒
        if self.state.should_check("deadline", 24):
            deadlines = self._check_deadlines()
            self.new_notifications.extend(deadlines)
            self.state.update_last_check("deadline")
        
        # 2. 关联记忆更新通知
        if self.state.should_check("related_updates", 12):
            related = self._check_related_updates()
            self.new_notifications.extend(related)
            self.state.update_last_check("related_updates")
        
        # 3. 矛盾检测提醒
        if self.state.should_check("conflicts", 48):
            conflicts = self._check_conflicts()
            self.new_notifications.extend(conflicts)
            self.state.update_last_check("conflicts")
        
        # 4. 新关联发现
        if self.state.should_check("new_related", 24):
            new_related = self._check_new_related()
            self.new_notifications.extend(new_related)
            self.state.update_last_check("new_related")
        
        # 添加到状态
        for msg in self.new_notifications:
            self.state.add_message(msg)
        
        return self.new_notifications
    
    def _check_deadlines(self) -> List[PushMessage]:
        """检查项目截止日期"""
        messages = []
        rule = PUSH_RULES["project_deadline"]
        advance_days = rule["advance_days"]
        
        # 从记忆中提取项目截止日期
        memories = load_all_memories()
        
        # 关键词模式
        deadline_patterns = [
            r'项目[：:]\s*(.+?)(?:截止|deadline|完成)',
            r'截止[日期]*[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'deadline[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s*(?:截止|完成|交付)',
        ]
        
        projects = {}  # project_name -> deadline
        
        for mem in memories:
            text = mem.get('text', '')
            
            # 检查是否包含项目信息
            if '项目' in text or 'deadline' in text.lower() or '截止' in text:
                for pattern in deadline_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # 尝试解析日期
                        date_str = match.group(1)
                        try:
                            # 尝试多种日期格式
                            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                                try:
                                    deadline = datetime.strptime(date_str.replace('/', '-'), "%Y-%m-%d")
                                    break
                                except:
                                    continue
                            else:
                                continue
                            
                            # 提取项目名
                            project_match = re.search(r'项目[：:]\s*(.+?)(?:\s|$|，|。)', text)
                            project_name = project_match.group(1) if project_match else date_str
                            
                            projects[project_name] = deadline
                        except:
                            pass
        
        # 检查即将到期的项目
        today = datetime.now().date()
        
        for project_name, deadline in projects.items():
            days_left = (deadline.date() - today).days
            
            if 0 < days_left <= advance_days:
                content = rule["template"].format(
                    project_name=project_name,
                    days_left=days_left,
                    deadline=deadline.strftime("%Y-%m-%d")
                )
                
                msg = PushMessage(
                    msg_type="project_deadline",
                    title="项目截止提醒",
                    content=content,
                    priority=rule["priority"],
                    metadata={
                        "project_name": project_name,
                        "deadline": deadline.isoformat(),
                        "days_left": days_left
                    }
                )
                messages.append(msg)
        
        if messages and not self.silent:
            print(f"📅 检查项目截止: 发现 {len(messages)} 个即将到期")
        
        return messages
    
    def _check_related_updates(self) -> List[PushMessage]:
        """检查关联记忆更新"""
        messages = []
        rule = PUSH_RULES["memory_update"]
        threshold = rule["related_threshold"]
        
        # 获取最近 24 小时的新记忆
        recent_cutoff = datetime.now() - timedelta(hours=24)
        memories = load_all_memories()
        recent_memories = [m for m in memories if m.get('timestamp', datetime.now()) > recent_cutoff]
        
        if not recent_memories:
            return messages
        
        # 加载图谱获取实体关联
        entities, relations = load_ontology_graph()
        
        # 对每个新记忆，检查是否有相关的实体
        for mem in recent_memories:
            text = mem.get('text', '')
            
            # 搜索相关实体
            for entity_id, entity in entities.items():
                props = entity.get('properties', {})
                entity_name = props.get('name', '')
                
                if entity_name and entity_name in text:
                    content = rule["template"].format(
                        related_topic=entity_name,
                        summary=text[:50] + "..."
                    )
                    
                    msg = PushMessage(
                        msg_type="memory_update",
                        title="关联记忆更新",
                        content=content,
                        priority=rule["priority"],
                        metadata={
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "memory_text": text
                        }
                    )
                    messages.append(msg)
                    break  # 每条记忆只关联一个实体
        
        if messages and not self.silent:
            print(f"🔄 检查关联更新: 发现 {len(messages)} 条相关更新")
        
        return messages
    
    def _check_conflicts(self) -> List[PushMessage]:
        """检查矛盾记忆"""
        messages = []
        rule = PUSH_RULES["conflict_detected"]
        
        memories = load_all_memories()
        
        # 使用 LLM 检测矛盾
        if len(memories) < 2:
            return messages
        
        # 只检查最近 30 天的高重要性记忆
        recent_cutoff = datetime.now() - timedelta(days=30)
        high_importance = [
            m for m in memories 
            if m.get('importance', 0) > 0.6 and m.get('timestamp', datetime.now()) > recent_cutoff
        ]
        
        if len(high_importance) < 2:
            return messages
        
        # 按关键词分组检测潜在矛盾
        conflict_keywords = {
            '喜欢': '不喜欢',
            '要': '不要',
            '需要': '不需要',
            '应该': '不应该',
            '正确': '错误',
            '同意': '反对',
        }
        
        for mem_a in high_importance[:20]:  # 限制检查数量
            text_a = mem_a.get('text', '')
            
            for positive, negative in conflict_keywords.items():
                if positive in text_a:
                    # 查找是否有矛盾的记录
                    for mem_b in high_importance:
                        if mem_b == mem_a:
                            continue
                        
                        text_b = mem_b.get('text', '')
                        if negative in text_b:
                            # 检查是否讨论同一主题
                            # 简单启发：共享关键词
                            keywords_a = set(re.findall(r'[\u4e00-\u9fa5]{2,}', text_a))
                            keywords_b = set(re.findall(r'[\u4e00-\u9fa5]{2,}', text_b))
                            
                            common = keywords_a & keywords_b
                            if len(common) >= 2:
                                content = rule["template"].format(
                                    conflict_desc=f"'{text_a[:30]}...' vs '{text_b[:30]}...'"
                                )
                                
                                msg = PushMessage(
                                    msg_type="conflict_detected",
                                    title="矛盾记忆检测",
                                    content=content,
                                    priority=rule["priority"],
                                    metadata={
                                        "memory_a": text_a,
                                        "memory_b": text_b,
                                        "common_keywords": list(common)
                                    }
                                )
                                messages.append(msg)
                                break
        
        if messages and not self.silent:
            print(f"⚠️ 检查矛盾: 发现 {len(messages)} 处潜在矛盾")
        
        return messages[:5]  # 限制推送数量
    
    def _check_new_related(self) -> List[PushMessage]:
        """检查新关联发现"""
        messages = []
        rule = PUSH_RULES["new_related"]
        min_similarity = rule["min_similarity"]
        
        entities, relations = load_ontology_graph()
        
        if len(entities) < 2:
            return messages
        
        # 检查未关联但相似的实体对
        entity_list = list(entities.values())
        existing_relations = set()
        
        for rel in relations:
            pair = tuple(sorted([rel['from'], rel['to']]))
            existing_relations.add(pair)
        
        # 对实体进行向量化比较
        checked_pairs = set()
        
        for i, entity_a in enumerate(entity_list[:10]):  # 限制检查数量
            props_a = entity_a.get('properties', {})
            name_a = props_a.get('name', '')
            
            if not name_a:
                continue
            
            embedding_a = get_embedding(name_a)
            if not embedding_a:
                continue
            
            for entity_b in entity_list[i+1:i+11]:
                props_b = entity_b.get('properties', {})
                name_b = props_b.get('name', '')
                
                if not name_b:
                    continue
                
                pair = tuple(sorted([entity_a.get('id'), entity_b.get('id')]))
                if pair in existing_relations or pair in checked_pairs:
                    continue
                
                checked_pairs.add(pair)
                
                embedding_b = get_embedding(name_b)
                if not embedding_b:
                    continue
                
                similarity = cosine_similarity(embedding_a, embedding_b)
                
                if similarity >= min_similarity:
                    content = rule["template"].format(
                        entity_a=name_a,
                        entity_b=name_b,
                        similarity=similarity
                    )
                    
                    msg = PushMessage(
                        msg_type="new_related",
                        title="发现新关联",
                        content=content,
                        priority=rule["priority"],
                        metadata={
                            "entity_a_id": entity_a.get('id'),
                            "entity_a_name": name_a,
                            "entity_b_id": entity_b.get('id'),
                            "entity_b_name": name_b,
                            "similarity": similarity
                        }
                    )
                    messages.append(msg)
        
        if messages and not self.silent:
            print(f"🔗 检查新关联: 发现 {len(messages)} 对潜在关联")
        
        return messages[:3]  # 限制推送数量
    
    def mark_read(self, msg_id: str) -> bool:
        """标记消息已读"""
        return self.state.mark_read(msg_id)
    
    def list_unread(self) -> List[PushMessage]:
        """列出未读消息"""
        return self.state.get_unread()
    
    def list_all(self, limit: int = 50) -> List[PushMessage]:
        """列出所有消息"""
        return self.state.get_all(limit)
    
    def clear_old(self, days: int = 30) -> int:
        """清理过期消息"""
        return self.state.cleanup_old(days)


# ============================================================
# 状态报告
# ============================================================

def get_status() -> str:
    """获取推送系统状态"""
    state = PushState()
    
    unread = state.get_unread()
    all_msgs = state.get_all()
    
    # 按类型统计
    type_counts = Counter(msg.type for msg in all_msgs)
    priority_counts = Counter(msg.priority for msg in unread)
    
    # 最后检查时间
    last_checks = []
    for check_type, last_time in state.last_check.items():
        try:
            last = datetime.fromisoformat(last_time)
            ago = datetime.now() - last
            hours_ago = ago.total_seconds() / 3600
            last_checks.append(f"  - {check_type}: {hours_ago:.1f} 小时前")
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
    
    return f"""📊 Memory Push v0.4.1 状态

推送队列:
  - 总消息: {len(all_msgs)} 条
  - 未读: {len(unread)} 条
  - 🔴 高优先级: {priority_counts.get('high', 0)}
  - 🟡 中优先级: {priority_counts.get('medium', 0)}
  - 🟢 低优先级: {priority_counts.get('low', 0)}

类型分布:
{chr(10).join(f'  - {k}: {v} 条' for k, v in type_counts.most_common(5))}

最后检查:
{chr(10).join(last_checks) if last_checks else '  (暂无记录)'}

配置:
  - 截止提醒: 提前 {PUSH_RULES['project_deadline']['advance_days']} 天
  - 关联阈值: {PUSH_RULES['memory_update']['related_threshold']}
  - 相似度阈值: {PUSH_RULES['new_related']['min_similarity']}

LLM 状态:
  - Ollama: {ollama_status} {OLLAMA_URL}
  - Embedding: {OLLAMA_EMBED_MODEL}
"""


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Memory Push v0.4.1")
    parser.add_argument("--silent", action="store_true", help="静默模式")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # check
    subparsers.add_parser("check", help="检查并生成推送")
    
    # mark-read
    read_p = subparsers.add_parser("mark-read", help="标记已读")
    read_p.add_argument("id", help="消息ID")
    
    # list
    list_p = subparsers.add_parser("list", help="列出推送")
    list_p.add_argument("--all", action="store_true", help="列出所有（包括已读）")
    list_p.add_argument("--limit", type=int, default=20, help="限制数量")
    
    # clear
    clear_p = subparsers.add_parser("clear", help="清理过期推送")
    clear_p.add_argument("--days", type=int, default=30, help="清理多少天前的")
    
    # status
    subparsers.add_parser("status", help="查看状态")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        pusher = MemoryPusher(silent=args.silent)
        
        if args.command == "check":
            notifications = pusher.check_and_push()
            if notifications:
                print(f"🔔 发现 {len(notifications)} 条新推送:\n")
                for msg in notifications:
                    print(f"  {msg}")
            else:
                print("✅ 暂无新推送")
        
        elif args.command == "mark-read":
            if pusher.mark_read(args.id):
                print(f"✅ 已标记为已读: {args.id}")
            else:
                print(f"❌ 未找到消息: {args.id}")
        
        elif args.command == "list":
            if args.all:
                messages = pusher.list_all(args.limit)
                print(f"📋 所有推送 ({len(messages)} 条):\n")
            else:
                messages = pusher.list_unread()
                print(f"📋 未读推送 ({len(messages)} 条):\n")
            
            for msg in messages:
                print(f"  {msg}")
        
        elif args.command == "clear":
            cleared = pusher.clear_old(args.days)
            print(f"🧹 已清理 {cleared} 条过期推送")
        
        elif args.command == "status":
            print(get_status())
    
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
