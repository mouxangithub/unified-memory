#!/usr/bin/env python3
"""
自我反思 - Memory Reflection

核心：LLM 定期反思记忆，发现模式、矛盾、建议
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
REFLECTION_DIR = MEMORY_DIR / "reflections"


class MemoryReflection:
    """
    记忆反思引擎
    
    定期运行，输出：
    1. 记忆说明的模式
    2. 发现的矛盾
    3. 用户下一步可能的行动
    """
    
    def __init__(self):
        REFLECTION_DIR.mkdir(parents=True, exist_ok=True)
        self.last_reflection_file = REFLECTION_DIR / "last_reflection.json"
        self.patterns_file = REFLECTION_DIR / "patterns.json"
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"patterns": [], "contradictions": []}
    
    def _save_patterns(self):
        with open(self.patterns_file, "w") as f:
            json.dump(self.patterns, f, indent=2, ensure_ascii=False)
    
    def reflect(self, memories: List[Dict], use_llm: bool = False) -> Dict:
        """
        反思记忆
        
        Args:
            memories: 记忆列表
            use_llm: 是否使用 LLM（需要 Ollama）
        
        Returns:
            反思结果
        """
        if not memories:
            return {"status": "no_memories"}
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "memories_count": len(memories),
            "patterns": [],
            "contradictions": [],
            "suggestions": [],
            "summary": ""
        }
        
        if use_llm:
            result = self._reflect_with_llm(memories)
        else:
            result = self._reflect_with_rules(memories)
        
        # 保存
        self._save_reflection(result)
        self.patterns = result
        self._save_patterns()
        
        return result
    
    def _reflect_with_rules(self, memories: List[Dict]) -> Dict:
        """
        基于规则的反思（无需 LLM）
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "memories_count": len(memories),
            "patterns": [],
            "contradictions": [],
            "suggestions": [],
            "method": "rules"
        }
        
        # ===== 1. 发现模式 =====
        
        # 按类别分组
        by_category = {}
        for mem in memories:
            cat = mem.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)
        
        # 发现频繁类别
        for cat, mems in by_category.items():
            if len(mems) >= 3:
                result["patterns"].append({
                    "type": "frequent_category",
                    "category": cat,
                    "count": len(mems),
                    "example": mems[0].get("text", "")[:50]
                })
        
        # 发现时间模式
        timestamps = []
        for mem in memories:
            ts = mem.get("timestamp", "")
            if ts:
                timestamps.append(ts)
        
        if timestamps:
            result["patterns"].append({
                "type": "temporal",
                "first_memory": min(timestamps),
                "last_memory": max(timestamps),
                "total_span_hours": (
                    datetime.fromisoformat(max(timestamps)) - 
                    datetime.fromisoformat(min(timestamps))
                ).total_seconds() / 3600
            })
        
        # ===== 2. 发现矛盾 =====
        
        # 检查相反的记忆
        decision_texts = [
            m.get("text", "").lower() 
            for m in by_category.get("decision", [])
        ]
        
        contradictions = self._find_contradictions(decision_texts)
        result["contradictions"] = contradictions
        
        # ===== 3. 生成建议 =====
        
        # 基于模式生成建议
        if by_category.get("preference"):
            prefs = by_category["preference"]
            if len(prefs) >= 3:
                result["suggestions"].append({
                    "type": "preference_consolidation",
                    "message": f"发现 {len(prefs)} 条偏好设置，建议整理为偏好文档"
                })
        
        if by_category.get("task"):
            tasks = by_category["task"]
            incomplete = [t for t in tasks if "完成" not in t.get("text", "")]
            if incomplete:
                result["suggestions"].append({
                    "type": "task_followup",
                    "message": f"有 {len(incomplete)} 个未完成任务需要跟进"
                })
        
        if contradictions:
            result["suggestions"].append({
                "type": "resolve_contradictions",
                "message": f"发现 {len(contradictions)} 个矛盾需要解决"
            })
        
        # ===== 4. 生成摘要 =====
        
        result["summary"] = self._generate_summary(result)
        
        return result
    
    def _reflect_with_llm(self, memories: List[Dict]) -> Dict:
        """
        使用 LLM 反思（需要 Ollama）
        """
        # 构建 prompt
        memories_text = "\n".join([
            f"- [{m.get('category', '?')}] {m.get('text', '')}"
            for m in memories[:50]
        ])
        
        prompt = f"""反思以下记忆，发现模式、矛盾和建议：

{memories_text}

请用 JSON 格式输出，包含：
- patterns: 发现的模式列表
- contradictions: 发现的矛盾列表
- suggestions: 建议列表
- summary: 一句话总结

JSON:"""
        
        try:
            import requests
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "deepseek-v3.2:cloud", "prompt": prompt},
                timeout=30
            )
            if resp.status_code == 200:
                result = resp.json()
                text = result.get("response", "{}")
                # 解析 JSON
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return {
                        **json.loads(json_match.group()),
                        "timestamp": datetime.now().isoformat(),
                        "method": "llm"
                    }
        except Exception as e:
            print(f"LLM reflection failed: {e}")
        
        # 降级到规则
        return self._reflect_with_rules(memories)
    
    def _find_contradictions(self, texts: List[str]) -> List[Dict]:
        """发现矛盾"""
        contradictions = []
        
        # 关键词矛盾
        conflict_pairs = [
            (["简单", "简洁"], ["复杂", "繁复"]),
            (["微服务", "单体"], ["不用微服务", "不用单体"]),
            (["快速", "快"], ["慢", "慢慢来"]),
        ]
        
        for pos_keywords, neg_keywords in conflict_pairs:
            pos_found = any(any(kw in t for kw in pos_keywords) for t in texts)
            neg_found = any(any(kw in t for kw in neg_keywords) for t in texts)
            
            if pos_found and neg_found:
                contradictions.append({
                    "type": "keyword_conflict",
                    "positive": pos_keywords,
                    "negative": neg_keywords,
                    "message": f"同时存在积极和消极的表述"
                })
        
        return contradictions
    
    def _generate_summary(self, reflection: Dict) -> str:
        """生成摘要"""
        patterns_count = len(reflection.get("patterns", []))
        contradictions_count = len(reflection.get("contradictions", []))
        suggestions_count = len(reflection.get("suggestions", []))
        
        summary_parts = []
        
        if patterns_count > 0:
            summary_parts.append(f"发现 {patterns_count} 个模式")
        if contradictions_count > 0:
            summary_parts.append(f"存在 {contradictions_count} 个矛盾")
        if suggestions_count > 0:
            summary_parts.append(f"给出 {suggestions_count} 条建议")
        
        if not summary_parts:
            return "记忆系统正常，无特殊情况"
        
        return "，".join(summary_parts)
    
    def _save_reflection(self, reflection: Dict):
        """保存反思结果"""
        with open(self.last_reflection_file, "w") as f:
            json.dump(reflection, f, indent=2, ensure_ascii=False)
    
    def get_last_reflection(self) -> Optional[Dict]:
        """获取上次反思"""
        if self.last_reflection_file.exists():
            with open(self.last_reflection_file, "r") as f:
                return json.load(f)
        return None
    
    def get_patterns(self) -> Dict:
        """获取发现的模式"""
        return self.patterns
    
    def get_stats(self) -> Dict:
        """获取统计"""
        last = self.get_last_reflection()
        return {
            "has_reflection": last is not None,
            "patterns_count": len(self.patterns.get("patterns", [])),
            "contradictions_count": len(self.patterns.get("contradictions", [])),
            "last_reflection": last.get("timestamp") if last else None
        }


# 全局实例
_reflection = None

def get_reflection() -> MemoryReflection:
    global _reflection
    if _reflection is None:
        _reflection = MemoryReflection()
    return _reflection


def reflect_memories(memories: List[Dict], use_llm: bool = False) -> Dict:
    """反思记忆的便捷函数"""
    return get_reflection().reflect(memories, use_llm)


if __name__ == "__main__":
    print("=" * 50)
    print("自我反思测试")
    print("=" * 50)
    
    reflection = MemoryReflection()
    
    # 测试数据
    memories = [
        {"id": "1", "text": "用户喜欢简洁的界面", "category": "preference", "timestamp": "2026-03-23T10:00:00"},
        {"id": "2", "text": "决定采用微服务架构", "category": "decision", "timestamp": "2026-03-23T11:00:00"},
        {"id": "3", "text": "用户喜欢蓝色", "category": "preference", "timestamp": "2026-03-23T12:00:00"},
        {"id": "4", "text": "项目需要快速完成", "category": "decision", "timestamp": "2026-03-23T13:00:00"},
        {"id": "5", "text": "不需要太复杂的设计", "category": "preference", "timestamp": "2026-03-23T14:00:00"},
    ]
    
    # 反思
    result = reflection.reflect(memories)
    
    print(f"\n📊 反思结果:")
    print(f"  记忆数: {result['memories_count']}")
    print(f"  方法: {result.get('method', 'unknown')}")
    
    print(f"\n🔍 发现模式:")
    for p in result.get("patterns", []):
        print(f"  - [{p['type']}] {p}")
    
    print(f"\n⚠️ 发现矛盾:")
    for c in result.get("contradictions", []):
        print(f"  - {c}")
    
    print(f"\n💡 建议:")
    for s in result.get("suggestions", []):
        print(f"  - [{s['type']}] {s['message']}")
    
    print(f"\n📝 摘要: {result.get('summary', '')}")
    
    print(f"\n📊 统计: {reflection.get_stats()}")
    
    print("\n✅ 自我反思测试完成")
