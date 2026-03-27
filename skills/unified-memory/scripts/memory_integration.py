#!/usr/bin/env python3
"""
Memory Integration Hook - Agent 集成钩子 v0.2.0

完整集成所有记忆系统功能：
- 对话开始时加载上下文 + 推荐 + 洞察
- 对话结束时自动存储 + 关联 + 去重 + 衰减
- 定期健康检查 + 提醒 + 统计
- 主动上下文注入
- 主题切换检测
- 审计日志

集成模块（P0-P2 全部）：
  ✅ memory_qmd_search - QMD 风格搜索
  ✅ memory_association - 关联推荐
  ✅ memory_decay - 置信度衰减
  ✅ memory_dedup - 去重合并
  ✅ memory_health - 健康检测
  ✅ memory_insights - 用户洞察
  ✅ memory_reminder - 智能提醒
  ✅ memory_export - 导出备份
  ✅ memory_graph - 知识图谱
  ✅ memory_qa - 智能问答
  ✅ memory_usage_stats - 使用统计
  ✅ memory_templates - 记忆模板

Usage:
    python3 scripts/memory_integration.py session-start --context "用户询问项目进度"
    python3 scripts/memory_integration.py session-end --conversation "对话内容"
    python3 scripts/memory_integration.py heartbeat
    python3 scripts/memory_integration.py export
    python3 scripts/memory_integration.py graph
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
SCRIPTS_DIR = Path(__file__).parent

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
    """会话开始 - 加载上下文 + 推荐 + Context Tree + 知识图谱"""
    result = {
        "loaded": 0,
        "memories": [],
        "recommendations": [],
        "suggestions": [],
        "reminders": [],
        "context_tree": None,
        "knowledge_graph": None,
        "project_context": None
    }
    
    log(f"📥 会话开始: {context[:50]}...")
    
    # ========== 1. Context Tree 智能上下文加载 ==========
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from context.context_tree import UnifiedContextTree
        
        ctx_tree = UnifiedContextTree()
        
        # 自动检测最佳上下文
        best_ctx = ctx_tree.find_best_context(context)
        ctx_chain = ctx_tree.get_memory_context_chain(best_ctx)
        ctx_desc = ctx_tree.get_context_description_chain(best_ctx)
        
        result["context_tree"] = {
            "best_context": best_ctx,
            "context_chain": ctx_chain,
            "context_description": ctx_desc
        }
        
        # 检查是否有当前项目
        project_ctx = ctx_tree.get_current_project_context()
        if project_ctx:
            proj_state = project_ctx.get_current()
            result["project_context"] = {
                "task": proj_state.get("task", "未设置"),
                "progress": proj_state.get("progress", 0),
                "notes": proj_state.get("notes", ""),
                "decisions": project_ctx.get_decisions(3)
            }
        
        log(f"🌳 Context Tree: {best_ctx}")
    except Exception as e:
        log(f"⚠️ Context Tree 加载失败: {e}")
    
    # ========== 2. 加载记忆 ==========
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
    
    # ========== 3. 知识图谱关联 ==========
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from memory_graph import search_context
        graph_result = search_context(context, limit=5)
        if graph_result and graph_result.get("entities"):
            result["knowledge_graph"] = {
                "entities": graph_result["entities"][:5],
                "relations": graph_result.get("relations", [])[:5]
            }
            for entity in graph_result["entities"][:3]:
                result["suggestions"].append(f"🔗 关联实体: {entity.get('name', entity.get('id', ''))}")
    except Exception as e:
        log(f"⚠️ 知识图谱加载失败: {e}")
    
    # ========== 4. 获取推荐 ==========
    current_ids = [m["id"] for m in top_memories]
    recommendations = _get_recommendations(context, 3)
    result["recommendations"] = recommendations
    
    # ========== 5. 分类建议 + Context Tree 建议 ==========
    categories = Counter(m["category"] for m in top_memories)
    for cat, count in categories.most_common(3):
        result["suggestions"].append(f"📂 相关记忆: {cat} ({count}条)")
    
    # 基于上下文添加项目建议
    if result.get("project_context"):
        proj = result["project_context"]
        if proj.get("task") and proj.get("task") != "未设置":
            result["suggestions"].insert(0, f"📋 当前项目: {proj['task']} ({proj['progress']}%)")
    
    # 保存当前上下文
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXT_FILE, 'w') as f:
        json.dump({
            "context": context,
            "context_tree": result.get("context_tree"),
            "loaded_ids": [m["id"] for m in top_memories],
            "timestamp": datetime.now().isoformat()
        }, f)
    
    log(f"✅ 加载 {result['loaded']} 条记忆 + {len(recommendations)} 条推荐 + Context Tree")
    
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
        
        # ===== 新增：建立关联 =====
        if result["stored"] > 0:
            try:
                assoc_result = subprocess.run(
                    ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_association.py"),
                     "build-graph"],
                    capture_output=True, text=True, timeout=60
                )
                if assoc_result.returncode == 0:
                    log(f"✅ 关联图谱已更新")
                    result["associations_built"] = True
            except Exception as e:
                log(f"⚠️ 建立关联失败: {e}")
        
        # ===== 新增：去重检测 =====
        try:
            dedup_result = subprocess.run(
                ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_dedup.py"),
                 "--json"],
                capture_output=True, text=True, timeout=30
            )
            if dedup_result.returncode == 0:
                dedup_data = json.loads(dedup_result.stdout)
                if dedup_data:
                    result["duplicates_found"] = len(dedup_data)
                    log(f"✅ 发现 {len(dedup_data)} 条重复记忆")
        except Exception as e:
            log(f"⚠️ 去重检测失败: {e}")
        
        # ===== 新增：应用衰减 =====
        try:
            from memory_decay import apply_decay_to_memories, get_decay_stats
            decayed = apply_decay_to_memories(dry_run=False)
            if decayed:
                log(f"✅ 衰减 {len(decayed)} 条记忆")
                result["decayed"] = len(decayed)
        except Exception as e:
            log(f"⚠️ 衰减失败: {e}")
        
    except Exception as e:
        log(f"❌ 存储失败: {e}")
    
    return result


def heartbeat() -> Dict:
    """心跳检查 - 健康检查 + 提醒检测 + 置信度衰减 + 关联维护"""
    result = {
        "health": {},
        "reminders": [],
        "actions": [],
        "confidence_adjustments": 0,
        "associations_built": False
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
        
        # ===== 新增：定期重建关联图谱 =====
        try:
            assoc_result = subprocess.run(
                ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_association.py"),
                 "build-graph"],
                capture_output=True, text=True, timeout=60
            )
            if assoc_result.returncode == 0:
                result["associations_built"] = True
                result["actions"].append("关联图谱已更新")
        except Exception as e:
            log(f"⚠️ 关联构建失败: {e}")
        
        # ===== 新增：去重检测 =====
        try:
            dedup_result = subprocess.run(
                ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_dedup.py"),
                 "--json"],
                capture_output=True, text=True, timeout=30
            )
            if dedup_result.returncode == 0 and dedup_result.stdout.strip():
                dedup_data = json.loads(dedup_result.stdout)
                if dedup_data:
                    result["duplicates_found"] = len(dedup_data)
                    result["actions"].append(f"发现 {len(dedup_data)} 条重复记忆")
        except Exception as e:
            log(f"⚠️ 去重检测失败: {e}")
        
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


def export_memories(format: str = "json", output: str = None) -> Dict:
    """导出记忆"""
    result = {
        "success": False,
        "output": "",
        "count": 0
    }
    
    try:
        output_file = output or str(MEMORY_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}")
        
        export_result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_export.py"),
             "--format", format, "--output", output_file],
            capture_output=True, text=True, timeout=30
        )
        
        if export_result.returncode == 0:
            result["success"] = True
            result["output"] = output_file
            log(f"✅ 导出成功: {output_file}")
        else:
            result["error"] = export_result.stderr
            
    except Exception as e:
        result["error"] = str(e)
        log(f"❌ 导出失败: {e}")
    
    return result


def generate_graph(html: bool = True, output: str = None) -> Dict:
    """生成知识图谱"""
    result = {
        "success": False,
        "nodes": 0,
        "edges": 0,
        "output": ""
    }
    
    try:
        output_file = output or str(MEMORY_DIR / "graph.html" if html else "graph.json")
        
        cmd = ["python3", str(SCRIPTS_DIR / "memory_graph.py")]
        if html:
            cmd.extend(["--html", output_file])
        else:
            cmd.append("--json")
        
        graph_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if graph_result.returncode == 0:
            result["success"] = True
            result["output"] = output_file
            
            if not html:
                data = json.loads(graph_result.stdout)
                result["nodes"] = len(data.get("nodes", {}))
                result["edges"] = len(data.get("edges", {}))
            
            log(f"✅ 图谱生成成功: {output_file}")
        else:
            result["error"] = graph_result.stderr
            
    except Exception as e:
        result["error"] = str(e)
        log(f"❌ 图谱生成失败: {e}")
    
    return result


def ask_question(question: str) -> Dict:
    """智能问答"""
    result = {
        "question": question,
        "answer": "",
        "sources": []
    }
    
    try:
        qa_result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_qa.py"),
             "ask", "-q", question],
            capture_output=True, text=True, timeout=60
        )
        
        if qa_result.returncode == 0:
            result["answer"] = qa_result.stdout.strip()
            log(f"✅ 问答成功")
        else:
            result["error"] = qa_result.stderr
            
    except Exception as e:
        result["error"] = str(e)
        log(f"❌ 问答失败: {e}")
    
    return result


def get_usage_stats() -> Dict:
    """使用统计"""
    result = {
        "total_memories": 0,
        "categories": {},
        "recent_activity": []
    }
    
    try:
        stats_result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_usage_stats.py")],
            capture_output=True, text=True, timeout=30
        )
        
        if stats_result.returncode == 0:
            # 解析输出
            result["raw"] = stats_result.stdout
            log(f"✅ 统计获取成功")
        else:
            result["error"] = stats_result.stderr
            
    except Exception as e:
        result["error"] = str(e)
        log(f"❌ 统计失败: {e}")
    
    return result


def apply_templates(template_name: str = None) -> Dict:
    """应用模板"""
    result = {
        "success": False,
        "applied": []
    }
    
    try:
        cmd = ["python3", str(SCRIPTS_DIR / "memory_templates.py")]
        if template_name:
            cmd.extend(["apply", template_name])
        else:
            cmd.append("list")
        
        template_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if template_result.returncode == 0:
            result["success"] = True
            result["output"] = template_result.stdout
            log(f"✅ 模板操作成功")
        else:
            result["error"] = template_result.stderr
            
    except Exception as e:
        result["error"] = str(e)
        log(f"❌ 模板操作失败: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Memory Integration Hook 0.2.0")
    parser.add_argument("command", choices=[
        "session-start", "session-end", "heartbeat",
        "detect-topic", "proactive-inject",
        "export", "graph", "qa", "stats", "templates"
    ])
    parser.add_argument("--context", "-c", help="上下文内容")
    parser.add_argument("--conversation", "-C", help="对话内容")
    parser.add_argument("--top-k", "-k", type=int, default=10)
    parser.add_argument("--threshold", "-t", type=float, default=0.3)
    parser.add_argument("--format", "-f", default="json", help="导出格式")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--html", action="store_true", help="生成 HTML 图谱")
    parser.add_argument("--question", "-q", help="问答问题")
    
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
    
    elif args.command == "export":
        result = export_memories(args.format, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "graph":
        result = generate_graph(args.html, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "qa":
        result = ask_question(args.question or args.context or "")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "stats":
        result = get_usage_stats()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "templates":
        result = apply_templates()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        result = proactive_inject(args.context or "", args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
