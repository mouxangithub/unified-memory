#!/usr/bin/env python3
"""
LLM 智能提取 - Smart Memory Extraction

从对话中自动提取记忆
6类分类: profile/preferences/entities/events/cases/patterns
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SmartExtractor:
    """
    LLM 智能提取器
    
    使用规则 + 关键词自动分类
    （无需调用外部 LLM API）
    """
    
    # 分类关键词模式
    CATEGORY_PATTERNS = {
        "profile": [
            r"我是(.+?)。", r"我的(.+?)是(.+?)。",
            r"我从事(.+?工作)", r"我做(.+?的)",
        ],
        "preferences": [
            r"我喜欢(.+?)。", r"我偏好(.+?)。",
            r"不要(.+?)。", r"最好(.+?)。",
            r"用(.+?)而不是(.+?)", r"用(.+?)来(.+?)",
        ],
        "entities": [
            r"(.+?)是一个(.+?)。", r"(.+?)是(.+?)公司",
            r"(.+?)项目", r"(.+?)产品",
        ],
        "events": [
            r"昨天(.+?)。", r"今天(.+?)。",
            r"会议(.+?)。", r"讨论了(.+?)。",
            r"完成了(.+?)。", r"启动了(.+?)。",
        ],
        "cases": [
            r"遇到(.+?问题)", r"修复了(.+?bug)",
            r"踩了(.+?坑)", r"之前(.+?失败)",
            r"这个方案(.+?)不行", r"改为(.+?)才行",
        ],
        "patterns": [
            r"通常(.+?)。", r"一般(.+?)。",
            r"遇到(.+?)就(.+?)。", r"只要(.+?)就(.+?)。",
        ],
    }
    
    # 噪声模式（需要过滤的内容）
    NOISE_PATTERNS = [
        r"^你好$", r"^hi$", r"^嗨$", r"^hey$",
        r"^谢谢$", r"^thx$", r"^感谢",
        r"^对", r"^嗯", r"^好的",
        r"^哈哈", r"^哈哈哈",
        r"^[?\s]*$",  # 空白
        r"^随便", r"^无所谓",
        r"^可以吗", r"^行不行",
        r"^多少钱", r"^在吗",
    ]
    
    def __init__(self):
        self.categories = list(self.CATEGORY_PATTERNS.keys())
    
    def is_noise(self, text: str) -> bool:
        """判断是否为噪声"""
        text = text.strip().lower()
        
        for pattern in self.NOISE_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # 太短的内容
        if len(text) < 5:
            return True
        
        return False
    
    def extract_category(self, text: str) -> Tuple[str, float]:
        """
        提取分类
        
        Returns:
            (category, confidence)
        """
        text = text.strip()
        
        scores = {}
        for cat, patterns in self.CATEGORY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    score += len(matches)
            scores[cat] = score
        
        # 找最高分
        if not scores or max(scores.values()) == 0:
            return "other", 0.3
        
        best_cat = max(scores, key=scores.get)
        confidence = min(scores[best_cat] * 0.2, 1.0)
        
        return best_cat, max(confidence, 0.3)
    
    def extract_importance(self, text: str, category: str) -> float:
        """估算重要性"""
        base = 0.5
        
        # 类别权重
        weights = {
            "preferences": 0.8,  # 用户偏好重要
            "decisions": 0.8,    # 决策重要
            "cases": 0.85,       # 案例经验非常重要
            "patterns": 0.75,    # 模式重要
            "events": 0.5,       # 事件一般
            "entities": 0.6,     # 实体一般
            "other": 0.4,
        }
        
        importance = base + weights.get(category, 0.5) * 0.3
        
        # 关键词增强
        strong_words = ["必须", "绝对", "一定", "永远", "不要", "禁止", "重要"]
        for word in strong_words:
            if word in text:
                importance += 0.1
        
        return min(importance, 1.0)
    
    def extract(self, text: str) -> Optional[Dict]:
        """
        提取记忆
        
        Args:
            text: 输入文本
        
        Returns:
            提取的记忆字典，如果被过滤则返回 None
        """
        text = text.strip()
        
        # 过滤噪声
        if self.is_noise(text):
            return None
        
        # 提取分类
        category, confidence = self.extract_category(text)
        
        # 估算重要性
        importance = self.extract_importance(text, category)
        
        # 提取标签
        tags = self._extract_tags(text)
        
        return {
            "id": f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(text) % 10000}",
            "text": text,
            "category": category,
            "importance": importance,
            "confidence": confidence,
            "tags": tags,
            "extracted_at": datetime.now().isoformat(),
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 技术标签
        tech_keywords = ["Python", "JavaScript", "Docker", "Git", "API", "数据库", "微服务", "React", "Vue"]
        for kw in tech_keywords:
            if kw in text:
                tags.append(kw.lower())
        
        # 动作标签
        action_keywords = ["学习", "开发", "设计", "测试", "部署", "优化", "修复"]
        for kw in action_keywords:
            if kw in text:
                tags.append(kw)
        
        return tags[:5]  # 最多5个标签
    
    def extract_batch(self, texts: List[str]) -> List[Dict]:
        """批量提取"""
        results = []
        for text in texts:
            mem = self.extract(text)
            if mem:
                results.append(mem)
        return results


def smart_extract(text: str) -> Optional[Dict]:
    """便捷函数"""
    extractor = SmartExtractor()
    return extractor.extract(text)


if __name__ == "__main__":
    print("=" * 50)
    print("LLM 智能提取测试")
    print("=" * 50)
    
    extractor = SmartExtractor()
    
    test_texts = [
        "我喜欢用 Python 开发后端服务",
        "用户偏好简洁的界面设计",
        "我们决定采用微服务架构",
        "昨天开会讨论了产品路线图",
        "踩了个坑：Python 3.11 的 async 有 bug",
        "遇到 500 错误就检查日志",
        "这个项目使用 React + TypeScript",
        "你好",
        "谢谢",
        "好的",
    ]
    
    print("\n📝 提取结果:\n")
    
    for text in test_texts:
        result = extractor.extract(text)
        if result:
            print(f"  [{result['category']}] {result['text']}")
            print(f"       重要性: {result['importance']:.2f}, 置信度: {result['confidence']:.2f}")
        else:
            print(f"  [过滤] {text}")
    
    print("\n✅ LLM 智能提取测试完成")
