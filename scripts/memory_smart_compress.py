#!/usr/bin/env python3
from pathlib import Path
"""
智能压缩 - Smart Compression

核心概念：
- 不是固定压缩率
- 而是保留"关键信息"
- 关键实体 + 关键关系 + 可溯源

灵感来自 RAG 的压缩技术
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class SmartCompressor:
    """智能压缩器"""
    
    def __init__(self):
        self.entity_patterns = self._init_entity_patterns()
    
    def _init_entity_patterns(self) -> Dict:
        """初始化实体模式"""
        return {
            "person": [
                r'[\u4e00-\u9fa5]{2,4}(?:先生|女士|总|经理|总监|工程师|设计师|产品经理|CEO|CTO|CFO)',
                r'(?:刘总|张总|王总|李总)',
            ],
            "project": [
                r'项目[：:][^\n]+',
                r'【[^\]]+】',
                r'(?:电商|社交|金融|医疗|教育)[网站系统平台]',
            ],
            "tool": [
                r'使用[^\s]+(?:框架|库|工具|服务)',
                r'(?:Python|Java|JS|React|Vue|Node)[^\s]*',
            ],
            "decision": [
                r'决定[^\n]+',
                r'采用[^\n]+',
                r'选择[^\n]+',
                r'应该[^\n]+',
            ],
            "metric": [
                r'\d+(?:%|%|倍|次|个|条)',
                r'(?:提升|增加|减少|降低)[^\d]+(\d+)',
            ]
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体"""
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            found = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                found.extend(matches)
            if found:
                entities[entity_type] = list(set(found))[:5]  # 最多5个
        
        return entities
    
    def extract_relations(self, text: str) -> List[str]:
        """提取关系"""
        relations = []
        
        # 动词关系
        action_patterns = [
            r'([\u4e00-\u9fa5]+)使用([\u4e00-\u9fa5]+)',
            r'([\u4e00-\u9fa5]+)决定([\u4e00-\u9fa5]+)',
            r'([\u4e00-\u9fa5]+)创建([\u4e00-\u9fa5]+)',
            r'([\u4e00-\u9fa5]+)完成([\u4e00-\u9fa5]+)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                relations.append(f"{m[0]} -> {m[1]}")
        
        return relations[:10]
    
    def compress(self, memories: List[Dict], target_size: int = 4000) -> Dict:
        """
        智能压缩
        
        保留：
        1. 关键实体
        2. 关键关系
        3. 时间顺序
        4. 可溯源
        """
        if not memories:
            return {"summary": "", "sources": []}
        
        # 按时间排序
        sorted_memories = sorted(
            memories,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # 提取所有实体和关系
        all_entities = {}
        all_relations = []
        sources = []
        
        for mem in sorted_memories:
            text = mem.get("text", "")
            
            # 提取实体
            entities = self.extract_entities(text)
            for et, ents in entities.items():
                if et not in all_entities:
                    all_entities[et] = []
                all_entities[et].extend(ents)
            
            # 提取关系
            relations = self.extract_relations(text)
            all_relations.extend(relations)
            
            # 记录来源
            sources.append({
                "id": mem.get("id", ""),
                "text": text[:100],
                "category": mem.get("category", "unknown"),
                "timestamp": mem.get("timestamp", "")
            })
        
        # 去重实体
        for et in all_entities:
            all_entities[et] = list(set(all_entities[et]))[:5]
        all_relations = list(set(all_relations))[:10]
        
        # 构建摘要
        parts = []
        
        # 1. 关键实体
        if all_entities:
            entity_text = []
            for et, ents in all_entities.items():
                if ents:
                    entity_text.append(f"{et}: {', '.join(ents)}")
            if entity_text:
                parts.append("【关键实体】\n" + "\n".join(entity_text))
        
        # 2. 关键关系
        if all_relations:
            parts.append("【关键关系】\n" + "\n".join(all_relations[:5]))
        
        # 3. 最新记忆
        recent = sorted_memories[:5]
        if recent:
            recent_text = "\n".join([
                f"- [{m.get('category', '?')}] {m.get('text', '')[:60]}..."
                for m in recent
            ])
            parts.append("【最新进展】\n" + recent_text)
        
        # 4. 决策记录
        decisions = [m for m in sorted_memories if m.get("category") == "decision"]
        if decisions:
            dec_text = "\n".join([
                f"- {d.get('text', '')[:60]}..."
                for d in decisions[:3]
            ])
            parts.append("【决策记录】\n" + dec_text)
        
        # 合并
        summary = "\n\n".join(parts)
        
        # 截断
        if len(summary) > target_size * 4:
            summary = summary[:target_size * 4]
        
        return {
            "summary": summary,
            "entities": all_entities,
            "relations": all_relations,
            "sources": sources[:20]  # 最多20个来源
        }
    
    def compress_for_context(self, memories: List[Dict], max_tokens: int = 4000) -> str:
        """
        为上下文压缩记忆
        
        直接返回压缩后的文本
        """
        result = self.compress(memories, max_tokens)
        return result["summary"]


def smart_compress(memories: List[Dict], target_size: int = 4000) -> Dict:
    """便捷函数"""
    compressor = SmartCompressor()
    return compressor.compress(memories, target_size)


if __name__ == "__main__":
    print("=" * 60)
    print("智能压缩测试")
    print("=" * 60)
    
    # 测试数据
    memories = [
        {
            "id": "mem_1",
            "text": "用户刘总说喜欢简洁的界面，我们决定采用微服务架构，使用Python开发",
            "category": "decision",
            "timestamp": "2026-03-23T10:00:00"
        },
        {
            "id": "mem_2",
            "text": "项目目标是做一个电商网站，预计3个月完成",
            "category": "fact",
            "timestamp": "2026-03-23T11:00:00"
        },
        {
            "id": "mem_3",
            "text": "用户希望界面响应时间<200ms，需要性能优化",
            "category": "preference",
            "timestamp": "2026-03-23T12:00:00"
        },
    ]
    
    compressor = SmartCompressor()
    
    # 提取实体
    print("\n📦 提取实体:")
    for mem in memories:
        entities = compressor.extract_entities(mem["text"])
        print(f"  {mem['id']}: {entities}")
    
    # 提取关系
    print("\n🔗 提取关系:")
    for mem in memories:
        relations = compressor.extract_relations(mem["text"])
        if relations:
            print(f"  {mem['id']}: {relations}")
    
    # 压缩
    print("\n📝 压缩结果:")
    result = compressor.compress(memories)
    print(result["summary"])
    
    print("\n✅ 智能压缩测试完成")
