#!/usr/bin/env python3
"""
Memory QA - 智能问答系统 v0.2.0

功能:
- RAG 检索增强生成
- 理解问题、生成答案
- 基于记忆回答用户问题

Usage:
    python3 scripts/memory_qa.py ask "我的项目进展如何？"
    python3 scripts/memory_qa.py chat  # 交互模式
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

try:
    import lancedb
    import requests
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def search_memories(query: str, top_k: int = 5) -> List[Dict]:
    """搜索相关记忆"""
    if not HAS_DEPS:
        return []
    
    try:
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        query_lower = query.lower()
        
        results = []
        for i in range(total):
            text = data["text"][i] if i < len(data.get("text", [])) else ""
            category = data["category"][i] if i < len(data.get("category", [])) else ""
            importance = float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5
            
            # 计算相关性分数
            score = 0
            text_lower = text.lower()
            
            # 词匹配
            for word in query_lower.split():
                if word in text_lower:
                    score += 2
            
            # 完全匹配加分
            if query_lower in text_lower:
                score += 5
            
            if score > 0:
                results.append({
                    "text": text,
                    "category": category,
                    "importance": importance,
                    "score": score + importance
                })
        
        # 排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"搜索失败: {e}")
        return []


def generate_answer(question: str, memories: List[Dict]) -> str:
    """使用 LLM 生成答案"""
    if not memories:
        return "抱歉，我没有找到相关的记忆来回答您的问题。"
    
    # 构建上下文
    context = "\n".join([f"- {m['text']}" for m in memories[:5]])
    
    prompt = f"""基于以下记忆回答用户问题。如果记忆中没有相关信息，请直接说明。

记忆内容：
{context}

用户问题：{question}

回答（简洁直接，不要提及"记忆"或"数据"）："""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_LLM_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        pass
    
    # 降级：直接返回记忆内容
    if len(memories) == 1:
        return memories[0]["text"]
    
    return f"根据记录：{memories[0]['text']}"


def ask(question: str) -> Dict:
    """智能问答"""
    start = datetime.now()
    
    # 1. 搜索相关记忆
    memories = search_memories(question, top_k=5)
    
    # 2. 生成答案
    answer = generate_answer(question, memories)
    
    elapsed = (datetime.now() - start).total_seconds() * 1000
    
    return {
        "question": question,
        "answer": answer,
        "sources": len(memories),
        "elapsed_ms": round(elapsed, 1)
    }


def chat_mode():
    """交互模式"""
    print("💬 Memory QA 智能问答")
    print("输入问题，输入 'exit' 退出\n")
    
    while True:
        try:
            question = input("❓ ").strip()
            if not question:
                continue
            if question.lower() in ['exit', 'quit', '退出']:
                break
            
            result = ask(question)
            print(f"\n💡 {result['answer']}")
            print(f"   (来源: {result['sources']} 条记忆, {result['elapsed_ms']}ms)\n")
            
        except KeyboardInterrupt:
            break
    
    print("\n👋 再见！")


def main():
    parser = argparse.ArgumentParser(description="Memory QA 0.2.0")
    parser.add_argument("command", choices=["ask", "chat"])
    parser.add_argument("question", nargs="?", help="问题")
    parser.add_argument("--top-k", "-k", type=int, default=5)
    
    args = parser.parse_args()
    
    if args.command == "ask":
        if not args.question:
            print("请提供问题")
            return
        result = ask(args.question)
        print(f"\n💡 {result['answer']}")
        print(f"\n📊 来源: {result['sources']} 条记忆")
        print(f"⏱️ 耗时: {result['elapsed_ms']}ms")
    
    elif args.command == "chat":
        chat_mode()


if __name__ == "__main__":
    main()
