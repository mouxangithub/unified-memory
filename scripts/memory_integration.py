#!/usr/bin/env python3
"""
Memory Integration Hook - Agent 集成钩子 v0.1.8

功能:
- 对话开始时加载上下文
- 对话结束时自动存储
- 定期健康检查
- 自动提醒检测
- 主动上下文注入 (NEW)
- 主题切换检测 (NEW)
- 智能推荐集成 (NEW)
- 置信度自适应 (NEW)
- 审计日志 (NEW)

集成到 OpenClaw Agent:
  1. 对话开始 → 加载相关上下文 + 推荐
  2. 对话进行 → 主题检测 + 主动注入
  3. 对话结束 → 提取并存储重要信息 + 审计
  4. 定时任务 → 健康检查 + 提醒 + 置信度衰减

Usage:
    python3 scripts/memory_integration.py session-start --context "用户询问项目进度"
    python3 scripts/memory_integration.py session-end --conversation "对话内容"
    python3 scripts/memory_integration.py heartbeat
    python3 scripts/memory_integration.py detect-topic --conversation "对话内容"
    python3 scripts/memory_integration.py proactive-inject --context "新主题"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
import subprocess

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CACHE_DIR = MEMORY_DIR / "cache"
LOG_FILE = MEMORY_DIR / "integration.log"
CONTEXT_FILE = MEMORY_DIR / "current_context.json"
TOPIC_HISTORY = MEMORY_DIR / "topic_history.json"

# Ollama 配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 敏感词
SENSITIVE_WORDS = [
    "password", "密码", "token", "密钥", "secret", "api_key",
    "信用卡", "银行卡", "身份证", "手机号", "验证码"
]


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")


def _load_memories() -> List[Dict]:
    """加载记忆"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        memories = []
        for i in range(len(data.get("id", []))):
            memories.append({
                "id": data["id"][i],
                "text": data["text"][i],
                "category": data.get("category", [""])[i] if i < len(data.get("category", [])) else "",
                "importance": data.get("importance", [0.5])[i] if i < len(data.get("importance", [])) else 0.5,
                "tags": data.get("tags", [[]])[i] if i < len(data.get("tags", [])) else [],
                "timestamp": data.get("timestamp", [""])[i] if i < len(data.get("timestamp", [])) else "",
                "vector": data.get("vector", [None])[i] if i < len(data.get("vector", [])) else None
            })
        return memories
    except Exception as e:
        log(f"❌ 加载记忆失败: {e}")
        return []


def _get_embedding(text: str) -> Optional[List[float]]:
    """获取嵌入向量"""
    try:
        import requests
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest"), "prompt": text},
            timeout=10
        )
        if response.ok:
            return response.json().get("embedding", [])
    except:
        pass
    return None


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算余弦相似度"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    
    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0


def _extract_important_info(conversation: str) -> List[Dict]:
    """提取重要信息"""
    extracted = []
    
    # 规则提取
    rules = [
        (r"偏好|喜欢|习惯", "preference"),
        (r"决定|选择|确定", "decision"),
        (r"项目|系统|平台", "entity"),
        (r"会议|提醒|记得", "event"),
    ]
    
    import re
    for pattern, category in rules:
        if re.search(pattern, conversation):
            # 提取句子
            sentences = re.split(r'[。！？\n]', conversation)
            for sentence in sentences:
                if re.search(pattern, sentence) and len(sentence) > 5:
                    extracted.append({
                        "text": sentence.strip(),
                        "category": category,
                        "importance": 0.5 if category == "entity" else 0.7
                    })
                    break
            break
    
    return extracted


def _detect_sensitive(text: str) -> List[str]:
    """检测敏感词"""
    found = []
    for word in SENSITIVE_WORDS:
        if word.lower() in text.lower():
            found.append(word)
    return found


def _get_recommendations(context: str, k: int = 3) -> List[Dict]:
    """获取推荐（调用 recommend 模块）"""
    try:
        result = subprocess.run(
            ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_recommend.py"),
             "context", "--query", context, "--k", str(k), "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("recommendations", [])
    except Exception as e:
        log(f"⚠️ 获取推荐失败: {e}")
    return []


def _record_audit(action: str, mem_id: str, text: str, source: str = "integration"):
    """记录审计日志"""
    try:
        subprocess.run(
            ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_audit.py"),
             "log", "--action", action, "--id", mem_id, "--text", text,
             "--source", source, "--json"],
            capture_output=True, timeout=10
        )
    except Exception as e:
        log(f"⚠️ 记录审计失败: {e}")


def session_start(context: str, top_k: int = 10) -> Dict:
    """会话开始 - 加载上下文 + 推荐"""
    result = {
        "loaded": 0,
        "memories": [],
        "recommendations": [],
        "suggestions": [],
        "reminders": []
    }
    
    log(f"📥 会话开始: {context[:50]}...")
    
    memories = _load_memories()
    if not memories:
        return result
    
    # 获取上下文嵌入
    context_vec = _get_embedding(context)
    
    # 计算相似度
    scored = []
    for mem in memories:
        if mem.get("vector"):
            sim = _cosine_similarity(context_vec, mem["vector"])
            scored.append((mem, sim))
    
    # 排序并取 top_k
    scored.sort(key=lambda x: x[1], reverse=True)
    top_memories = [m for m, s in scored[:top_k]]
    
    result["loaded"] = len(top_memories)
    result["memories"] = [
        {
            "id": m["id"],
            "text": m["text"],
            "category": m["category"],
            "importance": m["importance"],
            "_score": 2  # 简化评分
        }
        for m in top_memories
    ]
    
    # 获取推荐
    current_ids = [m["id"] for m in top_memories]
    recommendations = _get_recommendations(context, 3)
    result["recommendations"] = recommendations
    
    # 分类建议
    categories = Counter(m["category"] for m in top_memories)
    for cat, count in categories.most_common(3):
        result["suggestions"].append(f"相关记忆: {cat} ({count}条)")
    
    # 保存当前上下文
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXT_FILE, 'w') as f:
        json.dump({
            "context": context,
            "loaded_ids": [m["id"] for m in top_memories],
            "timestamp": datetime.now().isoformat()
        }, f)
    
    log(f"✅ 加载 {result['loaded']} 条记忆 + {len(recommendations)} 条推荐")
    
    return result


def session_end(conversation: str) -> Dict:
    """会话结束 - 提取并存储重要信息 + 审计"""
    result = {
        "extracted": 0,
        "stored": 0,
        "skipped": 0,
        "sensitive_detected": [],
        "audit_logged": False
    }
    
    log(f"📤 会话结束: 处理对话...")
    
    # 提取重要信息
    extracted = _extract_important_info(conversation)
    result["extracted"] = len(extracted)
    
    # 检测敏感信息
    sensitive = _detect_sensitive(conversation)
    result["sensitive_detected"] = sensitive
    
    if sensitive:
        log(f"⚠️ 检测到敏感词: {sensitive}")
    
    # 存储
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        for item in extracted:
            # 去重检查
            existing = table.search(item["text"]).limit(1).to_list()
            if existing and existing[0].get("text", "") == item["text"]:
                result["skipped"] += 1
                continue
            
            # 生成向量
            vector = _get_embedding(item["text"]) or []
            
            # 存储
            try:
                table.add([{
                    "id": f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(item['text']) % 10000}",
                    "text": item["text"],
                    "category": item["category"],
                    "importance": item["importance"],
                    "tags": [],
                    "timestamp": datetime.now().isoformat(),
                    "vector": vector
                }])
                result["stored"] += 1
                
                # 记录审计
                _record_audit("store", f"mem_{hash(item['text']) % 10000}", item["text"], "session_end")
                
            except Exception as e:
                result["skipped"] += 1
                log(f"⚠️ 存储失败: {e}")
        
        result["audit_logged"] = True
        log(f"✅ 存储 {result['stored']}/{result['extracted']} 条记忆")
        
    except Exception as e:
        log(f"❌ 存储失败: {e}")
    
    return result


def heartbeat() -> Dict:
    """心跳检查 - 健康检查 + 提醒检测 + 置信度衰减"""
    result = {
        "health": {},
        "reminders": [],
        "actions": [],
        "confidence_adjustments": 0
    }
    
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        
        # 简单健康检查
        result["health"] = {
            "total": total,
            "status": "healthy" if total > 0 else "empty"
        }
        
        # 检查提醒文件
        reminder_file = MEMORY_DIR / "reminders.json"
        if reminder_file.exists():
            with open(reminder_file) as f:
                reminders = json.load(f)
            
            now = datetime.now()
            threshold = now + timedelta(hours=24)
            
            for r in reminders:
                try:
                    event_date = datetime.fromisoformat(r.get("date", ""))
                    if now < event_date <= threshold:
                        result["reminders"].append(r)
                except:
                    pass
        
        if result["reminders"]:
            result["actions"].append(f"有 {len(result['reminders'])} 个即将到来的提醒")
        
        # 应用置信度衰减（可选）
        try:
            decay_result = subprocess.run(
                ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_adaptive.py"),
                 "decay", "--days", "30", "--json"],
                capture_output=True, text=True, timeout=30
            )
            if decay_result.returncode == 0:
                decay_data = json.loads(decay_result.stdout)
                result["confidence_adjustments"] = len(decay_data)
                if decay_data:
                    result["actions"].append(f"置信度衰减: {len(decay_data)} 条记忆")
        except Exception as e:
            log(f"⚠️ 置信度衰减失败: {e}")
        
        log(f"💓 心跳: {total} 条记忆, {len(result['reminders'])} 个提醒, {result['confidence_adjustments']} 次衰减")
        
    except Exception as e:
        result["health"]["error"] = str(e)
        log(f"❌ 心跳失败: {e}")
    
    return result


def detect_topic_switch(conversation: str, threshold: float = 0.3) -> Dict:
    """检测主题切换"""
    result = {
        "switched": False,
        "current_topic": "",
        "previous_topic": "",
        "confidence": 0.0
    }
    
    # 加载历史主题
    if TOPIC_HISTORY.exists():
        with open(TOPIC_HISTORY) as f:
            history = json.load(f)
        previous_topic = history.get("last_topic", "")
    else:
        previous_topic = ""
    
    # 提取当前主题关键词
    keywords = {
        "飞书": "协作工具",
        "微信": "通讯工具",
        "项目": "项目管理",
        "EvoMap": "进化网络",
        "记忆": "记忆系统",
        "龙宫": "龙宫项目",
        "电商": "电商业务",
        "会议": "会议安排"
    }
    
    current_topic = ""
    for kw, topic in keywords.items():
        if kw in conversation:
            current_topic = topic
            break
    
    result["current_topic"] = current_topic
    result["previous_topic"] = previous_topic
    
    # 判断是否切换
    if current_topic and previous_topic and current_topic != previous_topic:
        result["switched"] = True
        result["confidence"] = 1.0
        log(f"🔄 主题切换: {previous_topic} → {current_topic}")
    
    # 更新历史
    TOPIC_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(TOPIC_HISTORY, 'w') as f:
        json.dump({
            "last_topic": current_topic,
            "timestamp": datetime.now().isoformat()
        }, f)
    
    return result


def proactive_inject(context: str, k: int = 5) -> Dict:
    """主动上下文注入"""
    result = {
        "injected": False,
        "memories": [],
        "reason": ""
    }
    
    # 检测主题切换
    topic_result = detect_topic_switch(context)
    
    if not topic_result["switched"]:
        result["reason"] = "无主题切换，无需注入"
        return result
    
    # 加载新主题相关记忆
    memories = _load_memories()
    if not memories:
        result["reason"] = "无记忆可注入"
        return result
    
    context_vec = _get_embedding(context)
    
    scored = []
    for mem in memories:
        if mem.get("vector"):
            sim = _cosine_similarity(context_vec, mem["vector"])
            scored.append((mem, sim))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    
    result["memories"] = [
        {
            "id": m["id"],
            "text": m["text"],
            "category": m["category"],
            "relevance": round(s, 3)
        }
        for m, s in scored[:k]
    ]
    
    result["injected"] = True
    result["reason"] = f"主题切换 {topic_result['previous_topic']} → {topic_result['current_topic']}"
    
    # 更新上下文文件
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXT_FILE, 'w') as f:
        json.dump({
            "context": context,
            "loaded_ids": [m["id"] for m in scored[:k]],
            "timestamp": datetime.now().isoformat(),
            "proactive": True
        }, f)
    
    log(f"💉 主动注入: {len(result['memories'])} 条记忆 (主题: {topic_result['current_topic']})")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Memory Integration Hook 0.1.8")
    parser.add_argument("command", choices=[
        "session-start", "session-end", "heartbeat",
        "detect-topic", "proactive-inject"
    ])
    parser.add_argument("--context", "-c", help="上下文内容")
    parser.add_argument("--conversation", "-C", help="对话内容")
    parser.add_argument("--top-k", "-k", type=int, default=10)
    parser.add_argument("--threshold", "-t", type=float, default=0.3)
    
    args = parser.parse_args()
    
    if args.command == "session-start":
        result = session_start(args.context or "", args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "session-end":
        result = session_end(args.conversation or "")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "heartbeat":
        result = heartbeat()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "detect-topic":
        result = detect_topic_switch(args.conversation or "", args.threshold)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "proactive-inject":
        result = proactive_inject(args.context or "", args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
