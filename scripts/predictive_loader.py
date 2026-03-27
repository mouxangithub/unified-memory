#!/usr/bin/env python3
"""
Predictive Loader - 主动预测加载器 v7.0

功能:
- 分析对话趋势预测需要的记忆
- 提前加载相关记忆到 L1 缓存
- 减少首次查询延迟

Usage:
    predictive_loader.py analyze --context "当前对话内容"
    predictive_loader.py preload --keywords "项目,龙宫,电商"
    predictive_loader.py status
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from collections import Counter, defaultdict

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
PREDICTION_DIR = MEMORY_DIR / "predictions"

# Ollama 配置
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 预测参数
MAX_KEYWORDS = 5          # 最多提取关键词
MAX_PRELOAD = 3           # 最多预加载数量
MIN_CONFIDENCE = 0.6      # 最低预测置信度

# 文件路径
PREDICTION_CACHE_FILE = PREDICTION_DIR / "prediction_cache.json"
TOPIC_HISTORY_FILE = PREDICTION_DIR / "topic_history.json"

# 确保目录存在
PREDICTION_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 主动预测器
# ============================================================

class PredictiveLoader:
    """主动预测加载器"""
    
    def __init__(self):
        self.prediction_cache: Dict[str, List[str]] = {}
        self.topic_history: List[Dict] = []
        self.recent_keywords: List[str] = []
        self._load()
    
    def _load(self):
        """加载缓存数据"""
        try:
            if PREDICTION_CACHE_FILE.exists():
                self.prediction_cache = json.loads(PREDICTION_CACHE_FILE.read_text())
            if TOPIC_HISTORY_FILE.exists():
                self.topic_history = json.loads(TOPIC_HISTORY_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载预测缓存失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存缓存数据"""
        try:
            PREDICTION_CACHE_FILE.write_text(json.dumps(self.prediction_cache, ensure_ascii=False, indent=2))
            TOPIC_HISTORY_FILE.write_text(json.dumps(self.topic_history, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存预测缓存失败: {e}", file=sys.stderr)
    
    def extract_keywords(self, text: str) -> List[str]:
        """从文本提取关键词"""
        keywords = []
        
        # 1. 提取中文关键词（2-4字）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        keywords.extend(chinese_words[:MAX_KEYWORDS])
        
        # 2. 提取英文关键词
        english_words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)
        keywords.extend(english_words[:MAX_KEYWORDS])
        
        # 3. 提取项目名/实体名
        project_names = re.findall(r'[\u4e00-\u9fa5]{2,10}项目', text)
        keywords.extend(project_names[:2])
        
        # 去重并返回
        seen = set()
        unique = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique.append(kw)
        
        return unique[:MAX_KEYWORDS]
    
    def predict_topic(self, context: str) -> Dict:
        """预测对话主题"""
        keywords = self.extract_keywords(context)
        
        # 记录历史
        self.topic_history.append({
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "context_snippet": context[:100]
        })
        
        # 保留最近 20 条
        if len(self.topic_history) > 20:
            self.topic_history = self.topic_history[-20:]
        
        # 分析趋势
        all_keywords = []
        for record in self.topic_history[-5:]:
            all_keywords.extend(record.get("keywords", []))
        
        keyword_counts = Counter(all_keywords)
        trending = [kw for kw, _ in keyword_counts.most_common(3)]
        
        self._save()
        
        return {
            "current_keywords": keywords,
            "trending_keywords": trending,
            "confidence": self._calculate_confidence(keywords, trending)
        }
    
    def _calculate_confidence(self, current: List[str], trending: List[str]) -> float:
        """计算预测置信度"""
        if not current or not trending:
            return 0.0
        
        overlap = len(set(kw.lower() for kw in current) & set(kw.lower() for kw in trending))
        return min(1.0, overlap / min(len(current), len(trending)) + 0.3)
    
    def get_related_memories(self, keywords: List[str], memories: List[Dict]) -> List[Dict]:
        """获取与关键词相关的记忆"""
        related = []
        keyword_set = set(kw.lower() for kw in keywords)
        
        for mem in memories:
            text = mem.get("text", "").lower()
            tags = [t.lower() for t in mem.get("tags", [])]
            
            # 计算匹配度
            matches = sum(1 for kw in keyword_set if kw in text or kw in tags)
            if matches > 0:
                mem["relevance_score"] = matches / len(keyword_set)
                related.append(mem)
        
        # 按相关性排序
        related.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return related[:MAX_PRELOAD]
    
    def preload_to_l1(self, memory_ids: List[str]) -> bool:
        """预加载记忆到 L1"""
        try:
            hierarchy_file = MEMORY_DIR / "hierarchy" / "l1_hot.json"
            if not hierarchy_file.exists():
                return False
            
            l1_data = json.loads(hierarchy_file.read_text())
            
            # 标记为预加载
            for mem_id in memory_ids:
                if mem_id not in [m.get("id") for m in l1_data]:
                    l1_data.append({
                        "id": mem_id,
                        "preloaded": True,
                        "preloaded_at": datetime.now().isoformat()
                    })
            
            hierarchy_file.write_text(json.dumps(l1_data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"⚠️ 预加载失败: {e}", file=sys.stderr)
            return False
    
    def analyze_and_preload(self, context: str, memories: List[Dict]) -> Dict:
        """分析对话并预加载相关记忆"""
        # 1. 预测主题
        prediction = self.predict_topic(context)
        keywords = prediction["current_keywords"]
        
        # 2. 查找相关记忆
        related = self.get_related_memories(keywords, memories)
        
        # 3. 预加载
        preloaded_ids = [m.get("id") for m in related]
        success = self.preload_to_l1(preloaded_ids) if preloaded_ids else False
        
        # 缓存预测结果
        cache_key = "_".join(keywords[:2])
        self.prediction_cache[cache_key] = preloaded_ids
        self._save()
        
        return {
            "prediction": prediction,
            "related_memories": [{"id": m.get("id"), "text": m.get("text", "")[:50]} for m in related],
            "preloaded": success,
            "preloaded_count": len(preloaded_ids)
        }
    
    def status(self) -> Dict:
        """预测器状态"""
        return {
            "prediction_cache_size": len(self.prediction_cache),
            "topic_history_size": len(self.topic_history),
            "recent_predictions": list(self.prediction_cache.keys())[-5:],
            "trending_keywords": self._get_trending_keywords()
        }
    
    def _get_trending_keywords(self) -> List[str]:
        """获取趋势关键词"""
        all_keywords = []
        for record in self.topic_history[-10:]:
            all_keywords.extend(record.get("keywords", []))
        
        counts = Counter(all_keywords)
        return [kw for kw, _ in counts.most_common(5)]


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Predictive Loader v7.0")
    parser.add_argument("command", choices=["analyze", "preload", "status"])
    parser.add_argument("--context", help="当前对话内容")
    parser.add_argument("--keywords", help="关键词（逗号分隔）")
    
    args = parser.parse_args()
    loader = PredictiveLoader()
    
    if args.command == "analyze":
        if not args.context:
            print("❌ 请指定 --context")
            sys.exit(1)
        result = loader.predict_topic(args.context)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "preload":
        if args.keywords:
            keywords = [k.strip() for k in args.keywords.split(",")]
        elif args.context:
            keywords = loader.extract_keywords(args.context)
        else:
            print("❌ 请指定 --keywords 或 --context")
            sys.exit(1)
        
        print(f"🔑 关键词: {keywords}")
        print("⚠️ 需要记忆数据来完成预加载")
    
    elif args.command == "status":
        status = loader.status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
