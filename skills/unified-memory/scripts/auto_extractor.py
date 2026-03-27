#!/usr/bin/env python3
"""
Auto Extractor - 自动记忆提取器

功能:
- 从对话中自动提取重要信息
- 使用 LLM 识别记忆候选
- 自动分类和评分
- 敏感信息脱敏

Usage:
    auto_extractor.py extract --conversation "对话内容"
    auto_extractor.py extract --file conversation.txt
    auto_extractor.py batch --dir ./conversations/
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# Ollama 配置
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# 敏感信息模式
SENSITIVE_PATTERNS = {
    "password": [
        r'password["\s:=]+["\']?([^"\s,}]+)',
        r'passwd["\s:=]+["\']?([^"\s,}]+)',
        r'pwd["\s:=]+["\']?([^"\s,}]+)',
    ],
    "api_key": [
        r'api[_-]?key["\s:=]+["\']?([^"\s,}]+)',
        r'apikey["\s:=]+["\']?([^"\s,}]+)',
    ],
    "secret": [
        r'secret["\s:=]+["\']?([^"\s,}]+)',
        r'private[_-]?key["\s:=]+["\']?([^"\s,}]+)',
        r'token["\s:=]+["\']?([^"\s,}]+)',
    ],
    "credential": [
        r'credential["\s:=]+["\']?([^"\s,}]+)',
        r'auth["\s:=]+["\']?([^"\s,}]+)',
    ]
}

# 记忆分类
MEMORY_CATEGORIES = {
    "preference": ["偏好", "喜欢", "不喜欢", "想要", "prefer", "like", "want"],
    "fact": ["是", "有", "位于", "is", "has", "located", "成立于"],
    "decision": ["决定", "选择", "确认", "decide", "choose", "confirm"],
    "entity": ["项目", "公司", "团队", "project", "company", "team"],
    "task": ["任务", "待办", "需要", "task", "todo", "need"],
    "event": ["会议", "时间", "日期", "meeting", "time", "date"],
}


# ============================================================
# 敏感信息处理器
# ============================================================

class SensitiveFilter:
    """敏感信息过滤器"""
    
    def __init__(self):
        self.patterns = SENSITIVE_PATTERNS
        self.redacted_count = 0
    
    def sanitize(self, text: str) -> Tuple[str, List[Dict]]:
        """脱敏处理"""
        redactions = []
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    original = match.group(0)
                    sensitive_value = match.group(1) if len(match.groups()) > 0 else ""
                    
                    if sensitive_value and len(sensitive_value) > 2:
                        # 保留前2个和后1个字符
                        masked = sensitive_value[:2] + "***REDACTED***" + sensitive_value[-1:]
                        redacted = original.replace(sensitive_value, masked)
                        text = text.replace(original, redacted)
                        
                        redactions.append({
                            "category": category,
                            "original_length": len(sensitive_value),
                            "position": match.start()
                        })
                        self.redacted_count += 1
        
        return text, redactions
    
    def check_sensitive(self, text: str) -> bool:
        """检查是否包含敏感信息"""
        for patterns in self.patterns.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False


# ============================================================
# 自动记忆提取器
# ============================================================

class AutoExtractor:
    """自动记忆提取器"""
    
    def __init__(self):
        self.sensitive_filter = SensitiveFilter()
        self.extraction_count = 0
    
    def extract_from_conversation(self, conversation: str, use_llm: bool = True) -> List[Dict]:
        """从对话中提取记忆"""
        memories = []
        
        # 1. 规则提取（快速）
        rule_memories = self._extract_by_rules(conversation)
        memories.extend(rule_memories)
        
        # 2. LLM 提取（深度）
        if use_llm and HAS_REQUESTS:
            llm_memories = self._extract_by_llm(conversation)
            memories.extend(llm_memories)
        
        # 3. 去重和评分
        memories = self._deduplicate(memories)
        memories = self._score_memories(memories, conversation)
        
        # 4. 敏感信息脱敏
        for mem in memories:
            mem["text"], redactions = self.sensitive_filter.sanitize(mem["text"])
            if redactions:
                mem["has_sensitive"] = True
                mem["redactions"] = redactions
        
        self.extraction_count += len(memories)
        return memories
    
    def _extract_by_rules(self, conversation: str) -> List[Dict]:
        """基于规则提取"""
        memories = []
        
        # 提取偏好
        pref_patterns = [
            r'(?:我|用户)?(?:偏好|喜欢|想要)([^。！？\n]+)',
            r'(?:I|user)?\s*(?:prefer|like|want)\s+([^.!?\n]+)',
        ]
        
        for pattern in pref_patterns:
            matches = re.findall(pattern, conversation)
            for match in matches:
                text = match.strip()
                if len(text) > 5:
                    memories.append({
                        "text": text,
                        "category": "preference",
                        "source": "rule",
                        "importance": 0.6,
                        "extracted_at": datetime.now().isoformat()
                    })
        
        # 提取决策
        decision_patterns = [
            r'(?:决定|确认|选择)([^。！？\n]+)',
            r'(?:decide|confirm|choose)\s+([^.!?\n]+)',
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, conversation)
            for match in matches:
                text = match.strip()
                if len(text) > 5:
                    memories.append({
                        "text": text,
                        "category": "decision",
                        "source": "rule",
                        "importance": 0.8,
                        "extracted_at": datetime.now().isoformat()
                    })
        
        # 提取实体
        entity_patterns = [
            r'(?:项目|公司|团队)[：:]\s*([^\n]+)',
            r'(?:project|company|team)[::]\s*([^\n]+)',
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, conversation)
            for match in matches:
                text = match.strip()
                if len(text) > 2:
                    memories.append({
                        "text": text,
                        "category": "entity",
                        "source": "rule",
                        "importance": 0.5,
                        "extracted_at": datetime.now().isoformat()
                    })
        
        return memories
    
    def _extract_by_llm(self, conversation: str) -> List[Dict]:
        """使用 LLM 提取"""
        try:
            prompt = f"""分析以下对话，提取重要信息作为记忆。返回 JSON 数组格式：

对话内容：
{conversation[:2000]}

提取规则：
1. 只提取重要、持久的信息
2. 排除临时性、无关紧要的内容
3. 包含分类（preference/fact/decision/entity/task/event）
4. 评估重要性（0.0-1.0）

返回格式：
[
  {{"text": "记忆内容", "category": "分类", "importance": 0.7}}
]

只返回 JSON，不要其他内容。"""

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "")
                
                # 提取 JSON
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    memories = json.loads(json_match.group())
                    
                    for mem in memories:
                        mem["source"] = "llm"
                        mem["extracted_at"] = datetime.now().isoformat()
                    
                    return memories
        
        except Exception as e:
            print(f"⚠️ LLM 提取失败: {e}", file=sys.stderr)
        
        return []
    
    def _deduplicate(self, memories: List[Dict]) -> List[Dict]:
        """去重"""
        seen_texts = set()
        unique = []
        
        for mem in memories:
            text_key = mem.get("text", "")[:50].lower()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique.append(mem)
        
        return unique
    
    def _score_memories(self, memories: List[Dict], context: str) -> List[Dict]:
        """评分"""
        context_lower = context.lower()
        
        for mem in memories:
            text = mem.get("text", "").lower()
            
            # 基础分数
            base_score = mem.get("importance", 0.5)
            
            # 提升因素
            boost = 0
            
            # 出现在上下文中多次
            if context_lower.count(text) > 1:
                boost += 0.1
            
            # 关键词重要性
            if any(kw in text for kw in ["重要", "决定", "偏好", "important", "decide", "prefer"]):
                boost += 0.15
            
            # 分类权重
            category_weights = {
                "decision": 0.2,
                "preference": 0.15,
                "fact": 0.1,
                "entity": 0.05,
                "task": 0.1,
                "event": 0.08
            }
            boost += category_weights.get(mem.get("category", ""), 0)
            
            # 最终分数
            mem["importance"] = min(1.0, base_score + boost)
        
        return memories
    
    def auto_store(self, memories: List[Dict]) -> int:
        """自动存储记忆"""
        stored = 0
        
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            for mem in memories:
                # 生成 ID
                mem["id"] = f"auto_{int(datetime.now().timestamp() * 1000)}_{stored}"
                mem["created_at"] = datetime.now().isoformat()
                
                # 生成 embedding
                embedding = self._get_embedding(mem["text"])
                if embedding:
                    mem["embedding"] = embedding
                
                # 存储
                table.add([mem])
                stored += 1
            
            print(f"✅ 已存储 {stored} 条记忆")
        
        except Exception as e:
            print(f"⚠️ 存储失败: {e}", file=sys.stderr)
        
        return stored
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """生成 embedding"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": OLLAMA_EMBED_MODEL,
                    "prompt": text
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("embedding")
        
        except Exception as e:
            print(f"⚠️ Embedding 失败: {e}", file=sys.stderr)
        
        return None
    
    def stats(self) -> Dict:
        """统计"""
        return {
            "extraction_count": self.extraction_count,
            "redacted_count": self.sensitive_filter.redacted_count
        }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Auto Extractor")
    parser.add_argument("command", choices=["extract", "batch", "stats"])
    parser.add_argument("--conversation", "-c", help="对话内容")
    parser.add_argument("--file", "-f", help="对话文件")
    parser.add_argument("--dir", "-d", help="批量处理目录")
    parser.add_argument("--store", action="store_true", help="自动存储")
    parser.add_argument("--no-llm", action="store_true", help="禁用 LLM 提取")
    
    args = parser.parse_args()
    
    extractor = AutoExtractor()
    
    if args.command == "extract":
        conversation = args.conversation
        
        if args.file:
            try:
                conversation = Path(args.file).read_text()
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                sys.exit(1)
        
        if not conversation:
            print("❌ 请提供对话内容")
            sys.exit(1)
        
        memories = extractor.extract_from_conversation(
            conversation,
            use_llm=not args.no_llm
        )
        
        print(f"📋 提取到 {len(memories)} 条记忆:")
        for mem in memories:
            sensitive = " 🔒" if mem.get("has_sensitive") else ""
            print(f"  [{mem['category']}] {mem['text'][:50]}... (importance: {mem['importance']:.2f}){sensitive}")
        
        if args.store:
            extractor.auto_store(memories)
    
    elif args.command == "batch":
        if not args.dir:
            print("❌ 请指定 --dir")
            sys.exit(1)
        
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"❌ 目录不存在: {dir_path}")
            sys.exit(1)
        
        all_memories = []
        for file in dir_path.glob("*.txt"):
            conversation = file.read_text()
            memories = extractor.extract_from_conversation(conversation, use_llm=False)
            all_memories.extend(memories)
            print(f"📄 {file.name}: {len(memories)} 条记忆")
        
        print(f"\n📊 共提取 {len(all_memories)} 条记忆")
        
        if args.store:
            extractor.auto_store(all_memories)
    
    elif args.command == "stats":
        stats = extractor.stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
