#!/usr/bin/env python3
"""
Agent Memory - AI Agent 专用记忆系统 v4.0

核心功能:
- 自动从对话提取记忆 (使用 LLM)
- 生成上下文摘要 (对话时加载)
- 维护用户画像 (USER_MODEL.md)
- Agent 自我认知 (AGENT_SELF.md)
- 能力边界记录

Usage:
    agent_memory.py extract --conversation "对话内容"
    agent_memory.py context --query "当前任务"
    agent_memory.py update-user
    agent_memory.py learn --type success|failure --content "内容"
    agent_memory.py status
"""

import argparse
import json
import os
import re
import sys
import uuid
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ONTOLOGY_DIR = MEMORY_DIR / "ontology"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

USER_MODEL_FILE = WORKSPACE / "USER_MODEL.md"
AGENT_SELF_FILE = WORKSPACE / "AGENT_SELF.md"
MEMORY_FILE = WORKSPACE / "MEMORY.md"

# Ollama 配置
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 确保目录存在
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ONTOLOGY_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LLM 调用 (Ollama)
# ============================================================

def call_llm(prompt: str, model: str = None) -> Optional[str]:
    """调用 Ollama LLM"""
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
    """调用 LLM 并解析 JSON 响应"""
    response = call_llm(prompt, model)
    if not response:
        return None
    
    # 尝试提取 JSON
    try:
        # 尝试直接解析
        return json.loads(response)
    except:
        pass
    
    # 尝试从 markdown 代码块提取
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # 尝试提取大括号内容
    brace_match = re.search(r'\{[\s\S]*\}', response)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except:
            pass
    
    return None


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


# ============================================================
# 记忆分类系统
# ============================================================

MEMORY_CATEGORIES = {
    "profile": "用户身份属性 (姓名、职业、位置等)",
    "preferences": "用户偏好习惯 (喜欢/不喜欢、习惯做法)",
    "entities": "持续存在的实体 (项目、设备、账号)",
    "events": "发生的事件 (会议、完成任务、发生的事)",
    "cases": "问题-解决方案对 (遇到什么问题、怎么解决的)",
    "patterns": "可复用的处理流程 (做事方法)",
}

# 合并策略
ALWAYS_MERGE = {"profile"}
MERGE_SUPPORTED = {"preferences", "entities", "patterns"}
APPEND_ONLY = {"events", "cases"}


# ============================================================
# 自动提取
# ============================================================

EXTRACTION_PROMPT = """你是一个记忆提取助手。从以下对话中提取值得记住的信息。

对话内容:
{conversation}

请提取以下类型的记忆:
1. profile - 用户身份信息 (姓名、职业、位置等)
2. preferences - 用户偏好 (喜欢/不喜欢、习惯做法)
3. entities - 重要实体 (项目名、设备、账号)
4. events - 重要事件 (会议、完成任务)
5. cases - 问题解决方案 (遇到什么问题、怎么解决的)
6. patterns - 处理模式 (可复用的方法)

返回 JSON 格式:
{{
  "memories": [
    {{
      "category": "preferences",
      "abstract": "一句话摘要",
      "detail": "详细说明",
      "importance": 0.7
    }}
  ]
}}

只提取真正有价值、对未来有用的信息。忽略寒暄、闲聊、无关细节。
"""


def extract_memories(conversation: str) -> List[Dict]:
    """从对话中提取记忆"""
    prompt = EXTRACTION_PROMPT.format(conversation=conversation[:4000])
    result = call_llm_json(prompt)
    
    if not result or "memories" not in result:
        return []
    
    return result["memories"]


# ============================================================
# 上下文生成
# ============================================================

CONTEXT_PROMPT = """基于以下记忆，生成针对当前查询的上下文摘要。

用户画像:
{user_model}

相关记忆:
{memories}

当前查询: {query}

生成简洁的上下文摘要 (不超过 200 字)，包含:
1. 用户相关背景
2. 相关项目/任务
3. 需要注意的偏好
4. 可能相关的过去经验

只输出摘要内容，不要其他说明。
"""


def generate_context(query: str, limit: int = 5) -> str:
    """生成上下文摘要"""
    # 加载用户画像
    user_model = ""
    if USER_MODEL_FILE.exists():
        with open(USER_MODEL_FILE, "r", encoding="utf-8") as f:
            user_model = f.read()
    
    # 搜索相关记忆
    memories = search_memories(query, limit)
    memories_text = "\n".join([f"- [{m['category']}] {m['text']}" for m in memories])
    
    prompt = CONTEXT_PROMPT.format(
        user_model=user_model[:1000],
        memories=memories_text[:2000],
        query=query
    )
    
    context = call_llm(prompt)
    return context or "无相关上下文"


def search_memories(query: str, limit: int = 5) -> List[Dict]:
    """搜索记忆 (向量 + 文本)"""
    results = []
    
    # 1. 向量搜索
    embedding = get_embedding(query)
    if embedding:
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            vector_results = table.search(embedding).limit(limit).to_list()
            for r in vector_results:
                results.append({
                    "text": r.get("text", ""),
                    "category": r.get("category", "unknown"),
                    "importance": r.get("importance", 0.5),
                    "source": "vector"
                })
        except:
            pass
    
    # 2. 文本搜索
    text_results = search_text_memories(query, limit)
    for r in text_results:
        if not any(existing["text"] == r["text"] for existing in results):
            results.append(r)
    
    return results[:limit]


def search_text_memories(query: str, limit: int = 5) -> List[Dict]:
    """文本搜索记忆"""
    results = []
    query_lower = query.lower()
    
    for md_file in sorted(MEMORY_DIR.glob("*.md"), reverse=True):
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                if query_lower in line.lower():
                    # 解析记忆
                    match = re.match(r'- \[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\](?: \[I=([^\]]+)\])? (.+)', line.strip())
                    if match:
                        timestamp, category, scope, importance_str, text = match.groups()
                        results.append({
                            "text": text,
                            "category": category,
                            "importance": float(importance_str) if importance_str else 0.5,
                            "source": "text",
                            "file": md_file.name
                        })
                        if len(results) >= limit:
                            break
        if len(results) >= limit:
            break
    
    return results


# ============================================================
# 用户画像更新
# ============================================================

def update_user_model():
    """从记忆中更新用户画像"""
    # 收集所有 preferences 类型的记忆
    preferences = []
    entities = []
    profile = []
    
    for md_file in MEMORY_DIR.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r'- \[([^\]]+)\] \[([^\]]+)\].* (.+)', line.strip())
                if match:
                    _, category, text = match.groups()
                    if category == "preferences":
                        preferences.append(text)
                    elif category == "entities":
                        entities.append(text)
                    elif category == "profile":
                        profile.append(text)
    
    # 读取现有画像
    if USER_MODEL_FILE.exists():
        with open(USER_MODEL_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""
    
    # 更新偏好部分
    pref_section = "\n".join([f"- {p}" for p in set(preferences)])
    
    if "## 沟通偏好" in content:
        content = re.sub(
            r'## 沟通偏好\n.*?(?=\n## |\n---|\Z)',
            f"## 沟通偏好\n\n{pref_section}\n",
            content,
            flags=re.DOTALL
        )
    else:
        # 添加新部分
        content += f"\n\n## 沟通偏好\n\n{pref_section}\n"
    
    with open(USER_MODEL_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"✅ 已更新用户画像，偏好: {len(set(preferences))} 条"


# ============================================================
# Agent 学习
# ============================================================

def record_learning(learning_type: str, content: str, context: str = ""):
    """记录学习内容 (成功/失败)"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # 写入日常日志
    log_file = MEMORY_DIR / f"{today}.md"
    entry = f"- [{timestamp}] [learning] [{learning_type}] {content}"
    if context:
        entry += f" | 上下文: {context}"
    entry += "\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # 更新 AGENT_SELF.md
    if AGENT_SELF_FILE.exists():
        with open(AGENT_SELF_FILE, "r", encoding="utf-8") as f:
            self_content = f.read()
        
        if learning_type == "failure":
            # 添加到"不擅长"部分
            if "### ❌ 不擅长/需要改进" in self_content:
                failure_entry = f"| {content} | {today} | 待改进 |\n"
                # 找到表格并添加
                self_content = re.sub(
                    r'(### ❌ 不擅长/需要改进.*?\|.*?\n)(.*?)(\n---|\n##)',
                    r'\1\2' + failure_entry + r'\3',
                    self_content,
                    flags=re.DOTALL
                )
        elif learning_type == "success":
            # 添加到"擅长"部分或教训
            pass
        
        with open(AGENT_SELF_FILE, "w", encoding="utf-8") as f:
            f.write(self_content)
    
    return f"✅ 已记录学习: [{learning_type}] {content[:50]}..."


# ============================================================
# 存储记忆
# ============================================================

def store_memory(text: str, category: str = "fact", scope: str = "default",
                 importance: float = None) -> str:
    """存储记忆到文本 + 向量"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if importance is None:
        importance = score_importance(text, category)
    
    # 写入文本
    log_file = MEMORY_DIR / f"{today}.md"
    entry = f"- [{timestamp}] [{category}] [{scope}] [I={importance:.2f}] {text}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # 存储向量
    vector_stored = store_vector(text, category, scope, importance, timestamp)
    
    status = "✅ 已存储"
    if vector_stored:
        status += " (文本+向量)"
    else:
        status += " (文本)"
    
    return f"{status}: {text[:50]}..."


def store_vector(text: str, category: str, scope: str, importance: float, 
                 timestamp: str) -> bool:
    """存储到向量数据库"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        
        try:
            table = db.open_table("memories")
        except:
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
        
        embedding = get_embedding(text)
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


def score_importance(text: str, category: str) -> float:
    """评估记忆重要性"""
    base_scores = {
        "profile": 0.9,
        "preferences": 0.8,
        "entities": 0.7,
        "patterns": 0.85,
        "cases": 0.8,
        "events": 0.6,
        "fact": 0.5,
        "learning": 0.75,
    }
    
    score = base_scores.get(category, 0.5)
    
    # 关键词加分
    important_keywords = ["重要", "关键", "决定", "偏好", "失败", "成功", "必须", "不要"]
    for kw in important_keywords:
        if kw in text:
            score += 0.05
    
    return min(1.0, score)


# ============================================================
# 状态
# ============================================================

def get_status() -> str:
    """获取系统状态"""
    # 统计记忆
    memory_files = list(MEMORY_DIR.glob("*.md"))
    total_memories = 0
    categories = Counter()
    
    for md_file in memory_files:
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r'- \[([^\]]+)\] \[([^\]]+)\]', line)
                if match:
                    total_memories += 1
                    categories[match.group(2)] += 1
    
    # 向量数据库
    vector_count = 0
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
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
    
    return f"""📊 Agent Memory v4.0 状态

记忆存储:
  - 文件数: {len(memory_files)}
  - 总记忆: {total_memories} 条
  - 向量数: {vector_count}

分类统计:
{chr(10).join(f'  - {k}: {v} 条' for k, v in categories.most_common(6))}

用户画像: {'✅' if USER_MODEL_FILE.exists() else '❌'} USER_MODEL.md
Agent认知: {'✅' if AGENT_SELF_FILE.exists() else '❌'} AGENT_SELF.md

LLM 状态:
  - Ollama: {ollama_status} {OLLAMA_URL}
  - Embedding: {OLLAMA_EMBED_MODEL}
  - LLM: {OLLAMA_LLM_MODEL}

功能:
  ✅ 自动记忆提取 (LLM)
  ✅ 上下文生成
  ✅ 用户画像维护
  ✅ Agent 自我认知
  ✅ 学习记录
"""


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Agent Memory v4.0")
    subparsers = parser.add_subparsers(dest="command")
    
    # extract
    ext_p = subparsers.add_parser("extract", help="从对话提取记忆")
    ext_p.add_argument("--conversation", required=True, help="对话内容")
    ext_p.add_argument("--store", action="store_true", help="自动存储")
    
    # context
    ctx_p = subparsers.add_parser("context", help="生成上下文摘要")
    ctx_p.add_argument("--query", required=True, help="当前查询")
    ctx_p.add_argument("--limit", type=int, default=5)
    
    # store
    store_p = subparsers.add_parser("store", help="存储记忆")
    store_p.add_argument("--text", required=True)
    store_p.add_argument("--category", default="fact")
    store_p.add_argument("--scope", default="default")
    
    # update-user
    subparsers.add_parser("update-user", help="更新用户画像")
    
    # learn
    learn_p = subparsers.add_parser("learn", help="记录学习")
    learn_p.add_argument("--type", required=True, choices=["success", "failure", "pattern"])
    learn_p.add_argument("--content", required=True)
    learn_p.add_argument("--context", default="")
    
    # search
    search_p = subparsers.add_parser("search", help="搜索记忆")
    search_p.add_argument("--query", required=True)
    search_p.add_argument("--limit", type=int, default=5)
    
    # status
    subparsers.add_parser("status", help="查看状态")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "extract":
            memories = extract_memories(args.conversation)
            if args.store:
                for m in memories:
                    store_memory(
                        m.get("detail", m.get("abstract", "")),
                        m.get("category", "fact"),
                        importance=m.get("importance", 0.5)
                    )
                print(f"✅ 提取并存储了 {len(memories)} 条记忆")
            else:
                print(json.dumps(memories, ensure_ascii=False, indent=2))
        
        elif args.command == "context":
            context = generate_context(args.query, args.limit)
            print(context)
        
        elif args.command == "store":
            print(store_memory(args.text, args.category, args.scope))
        
        elif args.command == "update-user":
            print(update_user_model())
        
        elif args.command == "learn":
            print(record_learning(args.type, args.content, args.context))
        
        elif args.command == "search":
            results = search_memories(args.query, args.limit)
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['category']}] {r['text'][:60]}...")
        
        elif args.command == "status":
            print(get_status())
    
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
