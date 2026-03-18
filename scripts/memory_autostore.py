#!/usr/bin/env python3
"""
Memory Auto-Store - 自动存储记忆 v0.1.6

功能:
- 对话后自动提取重要信息
- 自动存入记忆系统
- 支持敏感信息过滤

Usage:
    python3 scripts/memory_autostore.py --conversation "对话内容"
    python3 scripts/memory_autostore.py --file conversation.txt
    python3 scripts/memory_autostore.py --watch  # 监听模式
"""

import argparse
import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 敏感词过滤
SENSITIVE_WORDS = [
    "password", "密码", "token", "密钥", "secret", "api_key",
    "信用卡", "银行卡", "身份证", "手机号", "验证码"
]

# 重要信息模式
IMPORTANT_PATTERNS = [
    # 用户偏好
    (r"(喜欢|偏好|爱|习惯用|用.{0,5}进行)", "preference"),
    # 项目信息
    (r"项目.*?(名称|类型|进度|状态|负责人)", "project"),
    # 决策
    (r"(决定|确定|选择|采用|使用)", "decision"),
    # 事件
    (r"(会议|生日|截止|安排|计划|预约)", "event"),
    # 学习
    (r"(学到|学会|掌握|了解|发现)", "learning"),
    # 技能
    (r"(技能|能力|可以|能|会)", "skill"),
]

try:
    import lancedb
    import requests
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


def get_embedding(text: str) -> Optional[List[float]]:
    """获取向量"""
    if not HAS_LANCEDB:
        return None
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("embedding")
    except:
        pass
    return None


def is_sensitive(text: str) -> bool:
    """检查是否包含敏感信息"""
    text_lower = text.lower()
    for word in SENSITIVE_WORDS:
        if word.lower() in text_lower:
            return True
    return False


def extract_important_info(text: str) -> List[Dict]:
    """提取重要信息"""
    results = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
        
        # 跳过敏感信息
        if is_sensitive(line):
            continue
        
        # 模式匹配
        for pattern, category in IMPORTANT_PATTERNS:
            if re.search(pattern, line):
                # 提取核心内容
                content = line
                if '：' in line:
                    content = line.split('：', 1)[1].strip()
                elif ':' in line:
                    content = line.split(':', 1)[1].strip()
                
                if len(content) > 3:
                    results.append({
                        "text": content,
                        "category": category,
                        "source": "auto-extract"
                    })
                break
    
    return results


def extract_with_llm(text: str) -> List[Dict]:
    """使用 LLM 提取（可选）"""
    try:
        prompt = f"""从以下对话中提取重要信息，输出JSON数组：
[
  {{"text": "核心内容", "category": "preference|project|decision|event|learning|skill"}}
]

对话内容：
{text[:1000]}

输出："""
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud"),
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "")
            # 尝试解析 JSON
            try:
                import re
                json_match = re.search(r'\[.*\]', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
    except:
        pass
    
    return []


def store_memory(text: str, category: str = "general", importance: float = 0.5) -> bool:
    """存储记忆"""
    if not HAS_LANCEDB:
        print("❌ LanceDB 未安装")
        return False
    
    try:
        # 获取向量
        embedding = get_embedding(text)
        
        # 连接数据库
        db = lancedb.connect(str(VECTOR_DB_DIR))
        
        # 确保表存在
        try:
            table = db.open_table("memories")
        except:
            # 创建表
            schema = {
                "id": "string",
                "text": "string",
                "category": "string", 
                "importance": "float",
                "timestamp": "string",
                "vector": "float32"
            }
            table = db.create_table("memories", schema=schema)
        
        # 生成 ID
        import uuid
        memory_id = str(uuid.uuid4())
        
        # 存储
        table.add([{
            "id": memory_id,
            "text": text,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "vector": embedding or []
        }])
        
        return True
    except Exception as e:
        print(f"❌ 存储失败: {e}")
        return False


def auto_store(conversation: str, use_llm: bool = True) -> Dict:
    """自动存储对话中的重要信息"""
    results = {
        "extracted": [],
        "stored": 0,
        "skipped": 0
    }
    
    # 1. 规则提取
    extracted = extract_important_info(conversation)
    results["extracted"].extend(extracted)
    
    # 2. LLM 提取（可选）
    if use_llm:
        llm_extracted = extract_with_llm(conversation)
        for item in llm_extracted:
            if item not in results["extracted"]:
                results["extracted"].append(item)
    
    # 3. 存储
    for item in results["extracted"]:
        text = item.get("text", "")
        category = item.get("category", "general")
        
        if text and len(text) > 5:
            if store_memory(text, category, 0.6):
                results["stored"] += 1
                print(f"✅ 已存储: {text[:40]}... [{category}]")
            else:
                results["skipped"] += 1
        else:
            results["skipped"] += 1
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Memory Auto-Store 0.1.6")
    parser.add_argument("--conversation", "-c", help="对话内容")
    parser.add_argument("--file", "-f", help="对话文件")
    parser.add_argument("--watch", "-w", action="store_true", help="监听模式")
    parser.add_argument("--no-llm", action="store_true", help="不使用 LLM 提取")
    
    args = parser.parse_args()
    
    conversation = ""
    
    if args.conversation:
        conversation = args.conversation
    elif args.file:
        with open(args.file, 'r') as f:
            conversation = f.read()
    else:
        print("请提供对话内容或文件")
        sys.exit(1)
    
    print(f"📝 处理对话 ({len(conversation)} 字符)...")
    
    results = auto_store(conversation, use_llm=not args.no_llm)
    
    print(f"\n📊 结果:")
    print(f"   提取: {len(results['extracted'])} 条")
    print(f"   存储: {results['stored']} 条")
    print(f"   跳过: {results['skipped']} 条")


if __name__ == "__main__":
    main()
