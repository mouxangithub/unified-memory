#!/usr/bin/env python3
"""
Intelligence Engine - 智能分类与关联引擎

功能:
- 自动分类 (基于内容语义)
- 自动打标签 (提取关键词)
- 智能关联 (发现相关记忆)
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    tags: List[str]
    related_ids: List[str]


class IntelligenceEngine:
    """智能分类引擎"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.llm_provider = llm_provider
        
        # 预定义分类
        self.categories = {
            "技术": ["代码", "bug", "API", "开发", "部署", "测试", "框架", "数据库", "服务器"],
            "产品": ["需求", "设计", "用户", "体验", "功能", "迭代", "路线图", "PRD"],
            "运营": ["数据", "增长", "推广", "转化", "留存", "活跃", "渠道"],
            "管理": ["会议", "团队", "计划", "目标", "复盘", "绩效", "招聘"],
            "学习": ["教程", "笔记", "总结", "经验", "技巧", "最佳实践"],
            "生活": ["日常", "心情", "健康", "旅行", "美食", "电影", "音乐"],
            "项目": ["进度", "里程碑", "风险", "资源", "验收", "交付"],
            "其他": []
        }
        
        # 关键词提取停用词
        self.stopwords = set([
            "的", "是", "在", "了", "和", "与", "或", "有", "这", "那",
            "我", "你", "他", "她", "它", "们", "的", "地", "得",
            "就", "也", "都", "会", "能", "要", "不", "没", "很",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can"
        ])
    
    def classify(self, text: str) -> ClassificationResult:
        """智能分类"""
        # 1. 关键词匹配分类
        category, confidence = self._classify_by_keywords(text)
        
        # 2. 提取标签
        tags = self._extract_tags(text)
        
        # 3. 查找相关记忆
        related_ids = self._find_related(text)
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            tags=tags,
            related_ids=related_ids
        )
    
    def _classify_by_keywords(self, text: str) -> Tuple[str, float]:
        """关键词匹配分类"""
        scores = {}
        
        for category, keywords in self.categories.items():
            if category == "其他":
                continue
            
            score = 0
            for kw in keywords:
                if kw.lower() in text.lower():
                    score += 1
            
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return "其他", 0.5
        
        # 最高分
        best = max(scores, key=scores.get)
        max_score = scores[best]
        
        # 置信度 = 匹配数 / 最大可能匹配数
        confidence = min(1.0, max_score / 5)
        
        return best, confidence
    
    def _extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """提取标签"""
        # 1. 提取中英文词汇
        # 中文: 连续汉字
        chinese = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        # 英文: 连续字母
        english = re.findall(r'[a-zA-Z]{3,}', text)
        
        # 2. 合并并过滤
        words = chinese + english
        words = [w for w in words if w.lower() not in self.stopwords]
        
        # 3. 计算词频
        counter = Counter(words)
        
        # 4. 返回高频词
        tags = [w for w, _ in counter.most_common(max_tags)]
        
        return tags
    
    def _find_related(self, text: str, limit: int = 5) -> List[str]:
        """查找相关记忆"""
        try:
            # 使用向量搜索
            from unified_memory import UnifiedMemory
            um = UnifiedMemory()
            results = um.search(text, limit=limit, mode="hybrid")
            
            return [r.get("id") for r in results if r.get("id")]
        except:
            # 降级：使用 BM25
            try:
                from resilience.error_fallback import ErrorFallback
                fallback = ErrorFallback()
                result = fallback.search_with_fallback(text, limit=limit)
                
                if result.success and result.data:
                    return [r.get("id") for r in result.data if r.get("id")]
            except:
                pass
        
        return []
    
    def smart_tag(self, text: str, existing_tags: List[str] = None) -> List[str]:
        """智能打标签 (合并现有标签和自动提取)"""
        auto_tags = self._extract_tags(text)
        
        if existing_tags:
            # 合并，去重
            all_tags = list(set(existing_tags + auto_tags))
            return all_tags
        
        return auto_tags
    
    def suggest_category(self, text: str) -> List[Tuple[str, float]]:
        """建议分类 (返回多个候选)"""
        scores = {}
        
        for category, keywords in self.categories.items():
            if category == "其他":
                continue
            
            score = sum(1 for kw in keywords if kw.lower() in text.lower())
            if score > 0:
                scores[category] = score
        
        # 排序
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_cats[:3]


# CLI 入口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="智能分类引擎")
    parser.add_argument("text", help="要分类的文本")
    parser.add_argument("--tags", "-t", nargs="*", help="现有标签")
    
    args = parser.parse_args()
    
    engine = IntelligenceEngine()
    
    print("🔍 智能分析中...\n")
    
    result = engine.classify(args.text)
    
    print(f"分类: {result.category} ({result.confidence:.0%})")
    print(f"标签: {', '.join(result.tags)}")
    print(f"相关记忆: {len(result.related_ids)} 条")
    
    # 分类建议
    suggestions = engine.suggest_category(args.text)
    if suggestions:
        print(f"\n分类建议:")
        for cat, score in suggestions:
            print(f"  - {cat}: {score}")


if __name__ == "__main__":
    main()
