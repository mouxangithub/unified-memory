#!/usr/bin/env python3
"""
标准化数据格式 - JSON-LD / Knowledge Cards

核心：采用 Schema.org 标准，兼容性强
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class StandardFormat:
    """标准化格式转换器"""
    
    SCHEMA_ORG_CONTEXT = "https://schema.org"
    
    @staticmethod
    def memory_to_jsonld(memory: Dict) -> Dict:
        """
        记忆转换为 JSON-LD 格式
        
        JSON-LD 是 W3C 标准，便于语义 web 和知识图谱集成
        """
        return {
            "@context": StandardFormat.SCHEMA_ORG_CONTEXT,
            "@type": "CreativeWork",  # 记忆是一种创意作品
            "@id": f"memory:{memory.get('id', '')}",
            "name": memory.get("text", "")[:100],
            "text": memory.get("text", ""),
            "description": f"{memory.get('category', 'unknown')} - {memory.get('text', '')[:50]}",
            "author": {
                "@type": "Person",
                "name": memory.get("author", "system")
            },
            "dateCreated": memory.get("timestamp", datetime.now().isoformat()),
            "dateModified": memory.get("updated_at", memory.get("timestamp")),
            "keywords": memory.get("tags", []),
            "version": memory.get("version", "1.0"),
            "inLanguage": "zh-CN",
            "encoding": {
                "@type": "MediaObject",
                "contentType": "text/plain",
                "encodingFormat": "utf-8"
            }
        }
    
    @staticmethod
    def memory_to_knowledge_card(memory: Dict) -> Dict:
        """
        记忆转换为 Knowledge Card 格式
        
        用于前端展示和搜索
        """
        return {
            "id": memory.get("id", ""),
            "type": "knowledge_card",
            "title": memory.get("text", "")[:50],
            "content": memory.get("text", ""),
            "category": memory.get("category", "unknown"),
            "tags": memory.get("tags", []),
            "confidence": memory.get("confidence", 0.8),
            "metadata": {
                "author": memory.get("author", "system"),
                "created": memory.get("timestamp"),
                "updated": memory.get("updated_at"),
                "project": memory.get("project", "default")
            },
            "highlight": memory.get("text", "")[:100],
            "source": "unified-memory"
        }
    
    @staticmethod
    def memory_to_rdf(memory: Dict) -> str:
        """
        记忆转换为 RDF Turtle 格式
        
        用于知识图谱 triple store
        """
        mem_id = memory.get("id", "")
        text = memory.get("text", "").replace('"', '\\"')
        category = memory.get("category", "unknown")
        timestamp = memory.get("timestamp", "")
        
        rdf = f"""@prefix memory: <http://unified-memory.org/> .
@prefix schema: <https://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

memory:{mem_id} a schema:CreativeWork ;
    schema:name "{text[:100]}"@zh ;
    schema:text "{text}"@zh ;
    schema:dateCreated "{timestamp}"^^xsd:dateTime ;
    memory:category "{category}" .
"""
        return rdf
    
    @staticmethod
    def memories_to_nq(memories: List[Dict]) -> str:
        """
        记忆转换为 N-Quads 格式
        
        用于 Apache Jena / RDF4J 导入
        """
        quads = []
        for mem in memories:
            mem_id = mem.get("id", "")
            text = mem.get("text", "").replace('"', '\\"')
            category = mem.get("category", "unknown")
            timestamp = mem.get("timestamp", "")
            
            quad = f'<http://unified-memory.org/{mem_id}> <http://schema.org/name> "{text[:100]}" .'
            quads.append(quad)
        
        return "\n".join(quads)
    
    @staticmethod
    def import_jsonld(data: Dict) -> Dict:
        """
        从 JSON-LD 导入记忆
        """
        return {
            "id": data.get("@id", "").replace("memory:", ""),
            "text": data.get("text", ""),
            "category": "imported",
            "author": data.get("author", {}).get("name", "imported"),
            "timestamp": data.get("dateCreated", ""),
            "tags": data.get("keywords", []),
            "format": "jsonld"
        }
    
    @staticmethod
    def export_all(memories: List[Dict], format: str = "jsonld") -> str:
        """
        批量导出
        
        format: jsonld / rdf / nq / card
        """
        if format == "jsonld":
            return json.dumps([
                StandardFormat.memory_to_jsonld(m) 
                for m in memories
            ], indent=2, ensure_ascii=False)
        
        elif format == "rdf":
            return "\n".join([
                StandardFormat.memory_to_rdf(m) 
                for m in memories
            ])
        
        elif format == "nq":
            return StandardFormat.memories_to_nq(memories)
        
        elif format == "card":
            return json.dumps([
                StandardFormat.memory_to_knowledge_card(m) 
                for m in memories
            ], indent=2, ensure_ascii=False)
        
        else:
            return json.dumps(memories, indent=2, ensure_ascii=False)


def to_jsonld(memory: Dict) -> Dict:
    """转换为 JSON-LD"""
    return StandardFormat.memory_to_jsonld(memory)


def to_knowledge_card(memory: Dict) -> Dict:
    """转换为 Knowledge Card"""
    return StandardFormat.memory_to_knowledge_card(memory)


def export_all(memories: List[Dict], format: str = "jsonld") -> str:
    """批量导出"""
    return StandardFormat.export_all(memories, format)


if __name__ == "__main__":
    print("=" * 50)
    print("标准化格式测试")
    print("=" * 50)
    
    # 测试数据
    memory = {
        "id": "mem_test",
        "text": "用户喜欢简洁的界面，决定采用微服务架构",
        "category": "decision",
        "author": "刘总",
        "timestamp": "2026-03-23T10:00:00",
        "tags": ["界面", "架构", "微服务"]
    }
    
    print("\n📝 JSON-LD:")
    jsonld = StandardFormat.memory_to_jsonld(memory)
    print(json.dumps(jsonld, indent=2, ensure_ascii=False)[:500])
    
    print("\n📝 Knowledge Card:")
    card = StandardFormat.memory_to_knowledge_card(memory)
    print(json.dumps(card, indent=2, ensure_ascii=False)[:500])
    
    print("\n📝 RDF Turtle:")
    rdf = StandardFormat.memory_to_rdf(memory)
    print(rdf[:300])
    
    print("\n✅ 标准化格式测试完成")
