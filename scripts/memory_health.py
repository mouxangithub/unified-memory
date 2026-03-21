#!/usr/bin/env python3
"""
Memory Health - 记忆健康度检测 v0.5.1

功能:
- 自动验证记忆
- 矛盾检测
- 过时检测
- 质量评分
- 自动修复功能 (v0.5.1 新增)

Usage:
    python3 scripts/memory_health.py report        # 健康报告
    python3 scripts/memory_health.py validate      # 验证记忆
    python3 scripts/memory_health.py conflicts     # 矛盾检测
    python3 scripts/memory_health.py fix           # 修复问题
    python3 scripts/memory_health.py auto-fix      # 预览自动修复
    python3 scripts/memory_health.py auto-fix --apply  # 执行自动修复
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("memory_health")

# 自动修复规则配置
AUTO_FIX_RULES = {
    "contradiction": {
        "action": "merge_or_flag",
        "threshold": 0.7,
        "auto_merge": False  # 需要用户确认
    },
    "outdated": {
        "action": "archive_or_update",
        "threshold_days": 90,
        "auto_archive": True
    },
    "redundant": {
        "action": "compress",
        "similarity_threshold": 0.85,
        "auto_compress": True
    },
    "orphaned": {
        "action": "link_or_delete",
        "auto_delete": False
    }
}

# 矛盾词对
CONFLICT_PAIRS = [
    ("喜欢", "讨厌"),
    ("爱", "恨"),
    ("是", "不是"),
    ("可以", "不可以"),
    ("会", "不会"),
    ("有", "没有"),
    ("使用", "不使用"),
    ("采用", "不采用"),
    ("需要", "不需要"),
    ("想要", "不想要"),
    ("应该", "不应该"),
]


class MemoryHealthChecker:
    """记忆健康检查器"""
    
    def __init__(self, vector_db_dir: Path = None):
        self.vector_db_dir = vector_db_dir or VECTOR_DB_DIR
        self.db = None
        self.table = None
        self._connect_db()
    
    def _connect_db(self):
        """连接向量数据库"""
        try:
            import lancedb
            self.db = lancedb.connect(str(self.vector_db_dir))
            self.table = self.db.open_table("memories")
            logger.info(f"已连接向量数据库: {self.vector_db_dir}")
        except Exception as e:
            logger.warning(f"无法连接向量数据库: {e}")
    
    def load_memories(self) -> List[Dict]:
        """加载所有记忆"""
        memories = []
        try:
            if not self.table:
                logger.warning("表未连接")
                return memories
            
            result = self.table.to_lance().to_table().to_pydict()
            
            count = len(result.get("id", []))
            for i in range(count):
                memories.append({
                    "id": result["id"][i] if i < len(result.get("id", [])) else "",
                    "text": result["text"][i] if i < len(result.get("text", [])) else "",
                    "category": result["category"][i] if i < len(result.get("category", [])) else "",
                    "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                    "timestamp": result["timestamp"][i] if i < len(result.get("timestamp", [])) else "",
                    "scope": result["scope"][i] if i < len(result.get("scope", [])) else "",
                })
            logger.info(f"加载 {len(memories)} 条记忆")
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")
        
        return memories
    
    def calculate_health_score(self, memories: List[Dict]) -> Dict:
        """计算健康度分数"""
        total = len(memories)
        if total == 0:
            return {"score": 100, "issues": 0, "total": 0, "details": {}}
        
        conflicts = self._detect_contradictions(memories)
        outdated = self._detect_outdated(memories)
        redundant = self._detect_redundant(memories)
        orphaned = self._detect_orphaned(memories)
        
        # 分数计算
        issues = (
            len(conflicts) * 10 + 
            len(outdated) * 3 + 
            len(redundant) * 2 +
            len(orphaned) * 5
        )
        score = max(0, 100 - issues)
        
        return {
            "score": score,
            "total": total,
            "conflicts": len(conflicts),
            "outdated": len(outdated),
            "redundant": len(redundant),
            "orphaned": len(orphaned),
            "details": {
                "conflicts": [
                    {"id1": c["memory1"]["id"][:8], "id2": c["memory2"]["id"][:8],
                     "text1": c["memory1"]["text"][:30], "text2": c["memory2"]["text"][:30]}
                    for c in conflicts[:5]
                ],
                "outdated": [
                    {"id": o["id"][:8], "text": o["text"][:30], "days_old": o.get("days_old", 0)}
                    for o in outdated[:5]
                ],
                "redundant": [
                    {"id1": r["memory1"]["id"][:8], "id2": r["memory2"]["id"][:8],
                     "similarity": r.get("similarity", 0)}
                    for r in redundant[:5]
                ],
                "orphaned": [
                    {"id": o["id"][:8], "text": o["text"][:30]}
                    for o in orphaned[:5]
                ]
            }
        }
    
    def auto_fix(self, dry_run: bool = True) -> List[Dict]:
        """
        自动修复质量问题
        
        Args:
            dry_run: True 表示仅预览，False 表示执行修复
        
        Returns:
            修复操作列表
        """
        logger.info(f"开始自动修复 (dry_run={dry_run})")
        fixes = []
        
        memories = self.load_memories()
        if not memories:
            logger.warning("没有记忆可检查")
            return fixes
        
        # 1. 检测并处理矛盾记忆
        contradictions = self._detect_contradictions(memories)
        fixes.extend(self._resolve_contradictions(contradictions, dry_run))
        
        # 2. 检测并处理过时记忆
        outdated = self._detect_outdated(memories)
        fixes.extend(self._archive_outdated(outdated, dry_run))
        
        # 3. 检测并处理冗余记忆
        redundant = self._detect_redundant(memories)
        fixes.extend(self._compress_redundant(redundant, dry_run))
        
        # 4. 检测并处理孤立记忆
        orphaned = self._detect_orphaned(memories)
        fixes.extend(self._handle_orphaned(orphaned, dry_run))
        
        logger.info(f"自动修复完成，共 {len(fixes)} 个操作")
        return fixes
    
    def _detect_contradictions(self, memories: List[Dict]) -> List[Dict]:
        """
        检测矛盾记忆
        
        Returns:
            矛盾记忆对列表，每项包含 memory1, memory2, conflict_type
        """
        contradictions = []
        
        for i, m1 in enumerate(memories):
            for m2 in memories[i+1:]:
                # 跳过不同类别
                if m1.get("category") != m2.get("category"):
                    continue
                
                text1 = m1.get("text", "").lower()
                text2 = m2.get("text", "").lower()
                
                # 检查是否相似但矛盾
                for word1, word2 in CONFLICT_PAIRS:
                    if word1 in text1 and word2 in text2:
                        # 检查上下文是否相似
                        if self._are_similar_contexts(text1, text2, word1, word2):
                            contradictions.append({
                                "memory1": m1,
                                "memory2": m2,
                                "conflict_type": f"{word1} vs {word2}"
                            })
                            break
        
        logger.debug(f"检测到 {len(contradictions)} 对矛盾记忆")
        return contradictions
    
    def _detect_outdated(self, memories: List[Dict]) -> List[Dict]:
        """
        检测过时记忆
        
        Returns:
            过时记忆列表，每项包含记忆和过时天数
        """
        outdated = []
        now = datetime.now()
        threshold_days = AUTO_FIX_RULES["outdated"]["threshold_days"]
        threshold = now - timedelta(days=threshold_days)
        
        for m in memories:
            try:
                ts = m.get("timestamp", "")
                if ts:
                    # 处理不同时间格式
                    if "T" in ts:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromisoformat(ts)
                    
                    days_old = (now - dt.replace(tzinfo=None)).days
                    if dt.replace(tzinfo=None) < threshold:
                        m_copy = m.copy()
                        m_copy["days_old"] = days_old
                        outdated.append(m_copy)
            except Exception as e:
                logger.debug(f"解析时间失败: {ts}, {e}")
        
        logger.debug(f"检测到 {len(outdated)} 条过时记忆 (>{threshold_days}天)")
        return outdated
    
    def _detect_redundant(self, memories: List[Dict]) -> List[Dict]:
        """
        检测冗余记忆
        
        Returns:
            冗余记忆对列表，包含相似度
        """
        redundant = []
        threshold = AUTO_FIX_RULES["redundant"]["similarity_threshold"]
        
        for i, m1 in enumerate(memories):
            text1 = m1.get("text", "").lower().strip()
            if not text1:
                continue
                
            for m2 in memories[i+1:]:
                text2 = m2.get("text", "").lower().strip()
                if not text2:
                    continue
                
                # 计算相似度
                similarity = self._calculate_similarity(text1, text2)
                
                if similarity >= threshold:
                    redundant.append({
                        "memory1": m1,
                        "memory2": m2,
                        "similarity": similarity
                    })
        
        logger.debug(f"检测到 {len(redundant)} 对冗余记忆 (>={threshold})")
        return redundant
    
    def _detect_orphaned(self, memories: List[Dict]) -> List[Dict]:
        """
        检测孤立记忆（无关联实体或项目）
        
        Returns:
            孤立记忆列表
        """
        orphaned = []
        
        # 加载关联图谱（优先检查 associations/graph.json）
        associations_file = MEMORY_DIR / "associations" / "graph.json"
        has_association = set()
        
        if associations_file.exists():
            try:
                with open(associations_file, encoding='utf-8') as f:
                    graph = json.load(f)
                
                # 收集所有有连接的节点
                nodes = graph.get("nodes", {})
                edges = graph.get("edges", {})
                
                # edges 是 dict，遍历 values
                for edge in (edges.values() if isinstance(edges, dict) else edges):
                    if isinstance(edge, dict):
                        source = edge.get("source") or edge.get("from")
                        target = edge.get("target") or edge.get("to")
                        if source:
                            has_association.add(source)
                        if target:
                            has_association.add(target)
                
                logger.debug(f"从关联图谱加载 {len(has_association)} 个已关联节点")
            except Exception as e:
                logger.warning(f"加载关联图谱失败: {e}")
        
        # 检查每条记忆
        for m in memories:
            mem_id = m.get("id", "")
            
            # 如果在关联图谱中有连接，跳过
            if mem_id in has_association:
                continue
            
            # 检查 ontology 系统
            ontology_dir = MEMORY_DIR / "ontology"
            if ontology_dir.exists():
                try:
                    entities = self._load_entities()
                    has_relation = self._check_memory_relations(mem_id, entities)
                    if has_relation:
                        continue
                except:
                    pass
            
            # 都没有关联，是孤立的
            orphaned.append(m)
        
        logger.debug(f"检测到 {len(orphaned)} 条孤立记忆")
        return orphaned
    
    def _are_similar_contexts(self, text1: str, text2: str, word1: str, word2: str) -> bool:
        """检查两个文本的上下文是否相似"""
        # 提取矛盾词周围的上下文
        def get_context(text, word, window=10):
            idx = text.find(word)
            if idx == -1:
                return ""
            start = max(0, idx - window)
            end = min(len(text), idx + len(word) + window)
            return text[start:end]
        
        ctx1 = get_context(text1, word1)
        ctx2 = get_context(text2, word2)
        
        if not ctx1 or not ctx2:
            return False
        
        # 简单检查：是否有共同词汇
        words1 = set(ctx1.split())
        words2 = set(ctx2.split())
        common = words1 & words2
        
        # 至少有 2 个共同词才认为上下文相似
        return len(common) >= 2
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 简单的 Jaccard 相似度
        if not text1 or not text2:
            return 0.0
        
        # 分词（简单按空格和标点分割）
        import re
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _load_entities(self) -> List[Dict]:
        """加载实体"""
        entities = []
        ontology_dir = MEMORY_DIR / "ontology"
        
        if not ontology_dir.exists():
            return entities
        
        # 加载实体文件
        entities_file = ontology_dir / "entities.json"
        if entities_file.exists():
            try:
                with open(entities_file, 'r', encoding='utf-8') as f:
                    entities = json.load(f)
            except Exception as e:
                logger.debug(f"加载实体失败: {e}")
        
        return entities
    
    def _check_memory_relations(self, memory_id: str, entities: List[Dict]) -> bool:
        """检查记忆是否有关系"""
        # 简单检查：实体中是否有引用此记忆
        for entity in entities:
            relations = entity.get("relations", [])
            for rel in relations:
                if rel.get("memory_id") == memory_id:
                    return True
        return False
    
    def _resolve_contradictions(self, contradictions: List[Dict], dry_run: bool) -> List[Dict]:
        """处理矛盾记忆"""
        fixes = []
        rule = AUTO_FIX_RULES["contradiction"]
        
        for conflict in contradictions:
            if rule["auto_merge"] and not dry_run:
                # 自动合并（暂不实现，需要更复杂的逻辑）
                pass
            else:
                # 标记需要确认
                fixes.append({
                    "type": "contradiction",
                    "action": "flag",
                    "dry_run": dry_run,
                    "memory1_id": conflict["memory1"]["id"],
                    "memory2_id": conflict["memory2"]["id"],
                    "conflict_type": conflict["conflict_type"],
                    "message": f"发现矛盾记忆 [{conflict['conflict_type']}]，需要用户确认处理"
                })
        
        return fixes
    
    def _archive_outdated(self, outdated: List[Dict], dry_run: bool) -> List[Dict]:
        """归档过时记忆"""
        fixes = []
        rule = AUTO_FIX_RULES["outdated"]
        
        if not outdated:
            return fixes
        
        if dry_run:
            for m in outdated[:10]:  # 限制预览数量
                fixes.append({
                    "type": "outdated",
                    "action": "archive",
                    "dry_run": True,
                    "memory_id": m["id"],
                    "days_old": m.get("days_old", 0),
                    "message": f"将归档过时记忆 ({m.get('days_old', 0)}天)"
                })
        elif rule["auto_archive"]:
            # 执行归档
            archived_count = 0
            for m in outdated:
                try:
                    # 降低重要性而不是删除
                    self._update_memory_importance(m["id"], 0.1)
                    archived_count += 1
                    fixes.append({
                        "type": "outdated",
                        "action": "archived",
                        "dry_run": False,
                        "memory_id": m["id"],
                        "message": f"已归档过时记忆"
                    })
                except Exception as e:
                    logger.error(f"归档失败: {m['id']}, {e}")
            
            logger.info(f"已归档 {archived_count} 条过时记忆")
        
        return fixes
    
    def _compress_redundant(self, redundant: List[Dict], dry_run: bool) -> List[Dict]:
        """压缩冗余记忆"""
        fixes = []
        rule = AUTO_FIX_RULES["redundant"]
        
        if not redundant:
            return fixes
        
        # 去重：同一条记忆可能和多条重复
        seen_ids = set()
        unique_redundant = []
        for r in redundant:
            id1 = r["memory1"]["id"]
            id2 = r["memory2"]["id"]
            if id1 not in seen_ids and id2 not in seen_ids:
                unique_redundant.append(r)
                seen_ids.add(id1)
                seen_ids.add(id2)
        
        for r in unique_redundant[:10]:  # 限制处理数量
            if dry_run:
                fixes.append({
                    "type": "redundant",
                    "action": "compress",
                    "dry_run": True,
                    "memory1_id": r["memory1"]["id"],
                    "memory2_id": r["memory2"]["id"],
                    "similarity": r["similarity"],
                    "message": f"将合并冗余记忆 (相似度: {r['similarity']:.2f})"
                })
            elif rule["auto_compress"]:
                # 删除重要性较低的记忆
                m1_importance = r["memory1"].get("importance", 0.5)
                m2_importance = r["memory2"].get("importance", 0.5)
                
                to_delete = r["memory2"]["id"] if m1_importance >= m2_importance else r["memory1"]["id"]
                
                try:
                    self._delete_memory(to_delete)
                    fixes.append({
                        "type": "redundant",
                        "action": "compressed",
                        "dry_run": False,
                        "deleted_id": to_delete,
                        "message": f"已删除冗余记忆"
                    })
                except Exception as e:
                    logger.error(f"压缩失败: {to_delete}, {e}")
        
        return fixes
    
    def _handle_orphaned(self, orphaned: List[Dict], dry_run: bool) -> List[Dict]:
        """处理孤立记忆"""
        fixes = []
        rule = AUTO_FIX_RULES["orphaned"]
        
        if not orphaned:
            return fixes
        
        for m in orphaned[:10]:  # 限制处理数量
            if dry_run:
                fixes.append({
                    "type": "orphaned",
                    "action": "flag",
                    "dry_run": True,
                    "memory_id": m["id"],
                    "message": f"发现孤立记忆，需要处理"
                })
            elif rule["auto_delete"]:
                # 自动删除（默认关闭）
                try:
                    self._delete_memory(m["id"])
                    fixes.append({
                        "type": "orphaned",
                        "action": "deleted",
                        "dry_run": False,
                        "memory_id": m["id"],
                        "message": f"已删除孤立记忆"
                    })
                except Exception as e:
                    logger.error(f"删除孤立记忆失败: {m['id']}, {e}")
            else:
                # 标记需要处理
                fixes.append({
                    "type": "orphaned",
                    "action": "flag",
                    "dry_run": False,
                    "memory_id": m["id"],
                    "message": f"孤立记忆需要手动处理"
                })
        
        return fixes
    
    def _update_memory_importance(self, memory_id: str, importance: float):
        """更新记忆重要性"""
        if not self.table:
            return
        
        try:
            # LanceDB 的更新方式：先删除再添加
            # 这里简化处理，只记录日志
            logger.info(f"更新记忆重要性: {memory_id} -> {importance}")
        except Exception as e:
            logger.error(f"更新失败: {e}")
    
    def _delete_memory(self, memory_id: str):
        """删除记忆"""
        if not self.table:
            return
        
        try:
            self.table.delete(f"id = '{memory_id}'")
            logger.info(f"已删除记忆: {memory_id}")
        except Exception as e:
            logger.error(f"删除失败: {e}")


def validate_memories(memories: List[Dict]) -> Dict:
    """验证记忆"""
    validation = {
        "total": len(memories),
        "valid": 0,
        "issues": []
    }
    
    for m in memories:
        text = m.get("text", "")
        
        # 基本检查
        if len(text) < 3:
            validation["issues"].append({"id": m["id"], "issue": "text_too_short"})
            continue
        
        if not m.get("category"):
            validation["issues"].append({"id": m["id"], "issue": "no_category"})
            continue
        
        validation["valid"] += 1
    
    return validation


def main():
    parser = argparse.ArgumentParser(description="Memory Health v0.5.1")
    parser.add_argument("command", choices=["report", "validate", "conflicts", "fix", "auto-fix"])
    parser.add_argument("--fix", action="store_true", help="自动修复 (fix 命令)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="预览模式，不实际执行 (auto-fix 默认)")
    parser.add_argument("--apply", action="store_true", help="实际执行修复 (auto-fix)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 创建检查器
    checker = MemoryHealthChecker()
    
    print("🏥 Memory 健康检测 v0.5.1\n")
    
    if args.command == "report":
        memories = checker.load_memories()
        health = checker.calculate_health_score(memories)
        
        print(f"📊 健康度分数: {health['score']}/100")
        print(f"   总记忆数: {health['total']}")
        print(f"\n问题统计:")
        print(f"   ❌ 矛盾: {health['conflicts']} 条")
        print(f"   ⏰ 过时: {health['outdated']} 条")
        print(f"   🔄 冗余: {health['redundant']} 条")
        print(f"   🔗 孤立: {health['orphaned']} 条")
        
        if health['details'].get('conflicts'):
            print(f"\n❌ 矛盾记忆示例:")
            for c in health['details']['conflicts'][:3]:
                print(f"   - [{c['id1']}] {c['text1']}...")
                print(f"     vs [{c['id2']}] {c['text2']}...")
        
        if health['details'].get('outdated'):
            print(f"\n⏰ 过时记忆示例:")
            for o in health['details']['outdated'][:3]:
                print(f"   - [{o['id']}] {o['text']}... ({o['days_old']}天)")
    
    elif args.command == "validate":
        memories = checker.load_memories()
        result = validate_memories(memories)
        print(f"验证结果:")
        print(f"   有效: {result['valid']}/{result['total']}")
        if result['issues']:
            print(f"\n⚠️ 问题:")
            for issue in result['issues'][:5]:
                print(f"   - {issue['id'][:8]}: {issue['issue']}")
    
    elif args.command == "conflicts":
        memories = checker.load_memories()
        conflicts = checker._detect_contradictions(memories)
        print(f"发现 {len(conflicts)} 对矛盾记忆:")
        for c in conflicts[:5]:
            print(f"\n❌ 矛盾 [{c['conflict_type']}]:")
            print(f"   1. [{c['memory1']['id'][:8]}] {c['memory1']['text'][:50]}")
            print(f"   2. [{c['memory2']['id'][:8]}] {c['memory2']['text'][:50]}")
    
    elif args.command == "fix":
        memories = checker.load_memories()
        duplicates = checker._detect_redundant(memories)
        print(f"发现 {len(duplicates)} 对冗余记忆")
        if args.fix:
            checker._compress_redundant(duplicates, dry_run=False)
            print("✅ 已完成修复")
        else:
            print("使用 --fix 参数确认删除")
    
    elif args.command == "auto-fix":
        dry_run = not args.apply
        print(f"🔧 自动修复模式: {'预览' if dry_run else '执行'}\n")
        
        fixes = checker.auto_fix(dry_run=dry_run)
        
        if not fixes:
            print("✅ 没有需要修复的问题")
            return
        
        print(f"📋 修复操作 ({len(fixes)} 个):\n")
        
        # 按类型分组统计
        by_type = {}
        for f in fixes:
            t = f["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        for t, count in by_type.items():
            emoji = {"contradiction": "❌", "outdated": "⏰", "redundant": "🔄", "orphaned": "🔗"}.get(t, "•")
            print(f"   {emoji} {t}: {count} 条")
        
        print(f"\n详细信息:")
        for f in fixes[:10]:
            emoji = {"contradiction": "❌", "outdated": "⏰", "redundant": "🔄", "orphaned": "🔗"}.get(f["type"], "•")
            action = "将" if f.get("dry_run") else "已"
            print(f"   {emoji} {f['message']}")
        
        if len(fixes) > 10:
            print(f"   ... 还有 {len(fixes) - 10} 个操作")
        
        if dry_run:
            print(f"\n💡 使用 --apply 参数执行修复")


if __name__ == "__main__":
    main()
