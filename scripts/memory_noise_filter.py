#!/usr/bin/env python3
"""
噪声过滤 - Noise Filtering

过滤低质量内容：
- 问候语
- 确认回复
- 简单问答
- Agent 拒绝
- 元问题
"""

import re
from typing import List, Tuple


class NoiseFilter:
    """
    噪声过滤器
    
    规则：
    1. 模式匹配 - 匹配已知的噪声模式
    2. 长度检查 - 过滤过短或过长的内容
    3. 关键词检查 - 检测特定关键词
    """
    
    # 问候语模式
    GREETING_PATTERNS = [
        r"^(hi|hello|hey|你好|您好|嗨|嗨嗨|hi there|greetings)$",
        r"^喂",
        r"^早上好|^下午好|^晚上好",
        r"^good (morning|afternoon|evening|day)",
    ]
    
    # 确认回复模式
    CONFIRM_PATTERNS = [
        r"^(好的|好|行|可以|yes|yep|yeah|ok|okay|sure|certainly|当然|没问题)$",
        r"^收到",
        r"^明白",
        r"^了解",
        r"^👍|❤️|😊|😄",
        r"^[\s]*$",  # 空白
    ]
    
    # Agent 拒绝模式
    REFUSAL_PATTERNS = [
        r"抱歉，我无法",
        r"sorry, i can't",
        r"i'm sorry, but i cannot",
        r"作为一个.*?我无法",
        r"对不起，我不能",
        r"我无法提供",
        r"cannot provide",
        r"unable to",
    ]
    
    # 元问题模式
    META_PATTERNS = [
        r"你是谁",
        r"what are you",
        r"who are you",
        r"你的名字",
        r"what can you do",
        r"你能做什么",
        r"help me",
        r"help with",
    ]
    
    # 简单问答模式
    SIMPLE_QA_PATTERNS = [
        r"^(是|否|对|错|yes|no)$",
        r"^几点了",
        r"^今天几号",
        r"^天气怎么样",
        r"^\d+\+\d+=",  # 数学题
    ]
    
    def __init__(self):
        self.all_patterns = (
            self.GREETING_PATTERNS +
            self.CONFIRM_PATTERNS +
            self.REFUSAL_PATTERNS +
            self.META_PATTERNS +
            self.SIMPLE_QA_PATTERNS
        )
    
    def is_noise(self, text: str) -> bool:
        """
        判断是否为噪声
        
        Returns:
            True if noise, False if signal
        """
        text = text.strip().lower()
        
        # 空内容
        if not text:
            return True
        
        # 长度检查
        if len(text) < 3:
            return True
        
        if len(text) > 5000:  # 过长内容可能是转储
            return True
        
        # 模式匹配
        for pattern in self.all_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def get_noise_type(self, text: str) -> str:
        """获取噪声类型"""
        text = text.strip().lower()
        
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "greeting"
        
        for pattern in self.CONFIRM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "confirmation"
        
        for pattern in self.REFUSAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "refusal"
        
        for pattern in self.META_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "meta_question"
        
        for pattern in self.SIMPLE_QA_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "simple_qa"
        
        if len(text) < 3:
            return "too_short"
        
        if len(text) > 5000:
            return "too_long"
        
        return "unknown"
    
    def filter(self, texts: List[str]) -> List[Tuple[str, bool]]:
        """
        过滤列表
        
        Returns:
            List of (text, is_noise) tuples
        """
        return [(text, self.is_noise(text)) for text in texts]
    
    def filter_signals(self, texts: List[str]) -> List[str]:
        """
        只返回信号（过滤掉噪声）
        
        Returns:
            List of texts that are not noise
        """
        return [text for text in texts if not self.is_noise(text)]
    
    def filter_batch(self, texts: List[str]) -> dict:
        """
        批量过滤结果
        
        Returns:
            {
                "signals": [...],
                "noises": [...],
                "stats": {"greeting": N, "confirmation": N, ...}
            }
        """
        signals = []
        noises = []
        stats = {}
        
        for text in texts:
            if self.is_noise(text):
                noise_type = self.get_noise_type(text)
                noises.append(text)
                stats[noise_type] = stats.get(noise_type, 0) + 1
            else:
                signals.append(text)
        
        return {
            "signals": signals,
            "noises": noises,
            "stats": stats,
        }


# 全局实例
_filter = None

def get_noise_filter() -> NoiseFilter:
    global _filter
    if _filter is None:
        _filter = NoiseFilter()
    return _filter


if __name__ == "__main__":
    print("=" * 50)
    print("噪声过滤测试")
    print("=" * 50)
    
    filter = NoiseFilter()
    
    test_texts = [
        "你好",
        "好的",
        "谢谢",
        "👍",
        "",
        "   ",
        "抱歉，我无法帮助",
        "你是谁",
        "help me",
        "1+1=2",
        "用户喜欢用 Python 开发",
        "这个项目的技术方案是微服务架构",
        "我需要完成首页的设计工作",
        "今天天气不错",
        "请问你能做什么",
    ]
    
    print("\n📝 过滤结果:\n")
    
    for text in test_texts:
        is_noise = filter.is_noise(text)
        noise_type = filter.get_noise_type(text) if is_noise else "signal"
        
        status = "❌ 噪声" if is_noise else "✅ 信号"
        print(f"  {status} | {noise_type:15} | {text or '(空)'}")
    
    # 批量过滤
    print("\n📊 批量过滤:")
    result = filter.filter_batch(test_texts)
    
    print(f"  信号: {len(result['signals'])} 条")
    print(f"  噪声: {len(result['noises'])} 条")
    print(f"  统计: {result['stats']}")
    
    print("\n✅ 噪声过滤测试完成")
