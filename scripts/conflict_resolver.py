#!/usr/bin/env python3
"""
Conflict Resolver - 记忆冲突检测和解决器 v2.0

功能:
- 自动检测冲突 (矛盾、重复、视角冲突、时序冲突)
- 多种解决策略
- 保留解决历史
- 与 memory_health.py 配合

Usage:
    python3 scripts/conflict_resolver.py detect        # 检测所有冲突
    python3 scripts/conflict_resolver.py list          # 列出所有冲突
    python3 scripts/conflict_resolver.py resolve <id> --strategy latest_wins
    python3 scripts/conflict_resolver.py auto-resolve  # 自动解决
    python3 scripts/conflict_resolver.py report        # 冲突报告
"""

import argparse
import json
import logging
import uuid
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
from collections import defaultdict

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CONFLICTS_DIR = MEMORY_DIR / "conflicts"
CONFLICTS_DIR.mkdir(parents=True, exist_ok=True)

CONFLICTS_FILE = CONFLICTS_DIR / "conflicts.json"
RESOLUTIONS_FILE = CONFLICTS_DIR / "resolutions.json"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("conflict_resolver")

# 矛盾词对 (用于检测内容矛盾)
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
    ("能", "不能"),
    ("支持", "不支持"),
    ("允许", "不允许"),
    ("开启", "关闭"),
    ("启用", "禁用"),
    ("增加", "减少"),
    ("添加", "删除"),
    ("创建", "销毁"),
    ("开始", "结束"),
    ("上线", "下线"),
]


class ConflictType(Enum):
    """冲突类型"""
    CONTRADICTION = "contradiction"      # 内容矛盾
    DUPLICATE = "duplicate"              # 重复
    PERSPECTIVE_CLASH = "perspective_clash"  # 视角冲突
    TEMPORAL = "temporal"                # 时序冲突


class ResolutionStrategy(Enum):
    """解决策略"""
    LATEST_WINS = "latest_wins"          # 最新获胜
    HIGHER_CONFIDENCE = "higher_confidence"  # 高置信度获胜
    EXPERT_WINS = "expert_wins"          # 专家获胜
    CONSENSUS = "consensus"              # 共识
    ESCALATE = "escalate"                # 升级


@dataclass
class Conflict:
    """冲突记录"""
    conflict_id: str
    conflict_type: ConflictType
    memory_ids: List[str]
    description: str
    detected_at: datetime
    severity: str  # low, medium, high
    suggested_resolution: Optional[str]
    status: str  # detected, resolving, resolved, escalated
    
    def to_dict(self) -> Dict:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "memory_ids": self.memory_ids,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "severity": self.severity,
            "suggested_resolution": self.suggested_resolution,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conflict":
        return cls(
            conflict_id=data["conflict_id"],
            conflict_type=ConflictType(data["conflict_type"]),
            memory_ids=data["memory_ids"],
            description=data["description"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
            severity=data["severity"],
            suggested_resolution=data.get("suggested_resolution"),
            status=data["status"]
        )


@dataclass
class Resolution:
    """解决记录"""
    conflict_id: str
    strategy: ResolutionStrategy
    winner_id: Optional[str]
    merged_content: Optional[str]
    resolved_by: str  # agent_id or "auto" or "user"
    resolved_at: datetime
    notes: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "conflict_id": self.conflict_id,
            "strategy": self.strategy.value,
            "winner_id": self.winner_id,
            "merged_content": self.merged_content,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat(),
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Resolution":
        return cls(
            conflict_id=data["conflict_id"],
            strategy=ResolutionStrategy(data["strategy"]),
            winner_id=data.get("winner_id"),
            merged_content=data.get("merged_content"),
            resolved_by=data["resolved_by"],
            resolved_at=datetime.fromisoformat(data["resolved_at"]),
            notes=data.get("notes")
        )


class ConflictResolver:
    """冲突解决器"""
    
    def __init__(self, memory_store=None, agent_profiles: Optional[Dict] = None):
        self.memory_store = memory_store
        self.agent_profiles = agent_profiles or {}
        self.conflicts: List[Conflict] = []
        self.resolutions: List[Resolution] = []
        self._load_data()
    
    def _load_data(self):
        """加载冲突和解决数据"""
        try:
            if CONFLICTS_FILE.exists():
                with open(CONFLICTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conflicts = [Conflict.from_dict(c) for c in data]
                logger.info(f"加载了 {len(self.conflicts)} 个冲突记录")
        except Exception as e:
            logger.warning(f"加载冲突数据失败: {e}")
        
        try:
            if RESOLUTIONS_FILE.exists():
                with open(RESOLUTIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.resolutions = [Resolution.from_dict(r) for r in data]
                logger.info(f"加载了 {len(self.resolutions)} 个解决记录")
        except Exception as e:
            logger.warning(f"加载解决数据失败: {e}")
    
    def _save_data(self):
        """保存冲突和解决数据"""
        try:
            with open(CONFLICTS_FILE, 'w', encoding='utf-8') as f:
                json.dump([c.to_dict() for c in self.conflicts], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存冲突数据失败: {e}")
        
        try:
            with open(RESOLUTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in self.resolutions], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存解决数据失败: {e}")
    
    def load_memories(self) -> List[Dict]:
        """加载所有记忆"""
        memories = []
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            count = len(result.get("id", []))
            for i in range(count):
                memories.append({
                    "id": result["id"][i] if i < len(result.get("id", [])) else "",
                    "text": result["text"][i] if i < len(result.get("text", [])) else "",
                    "category": result["category"][i] if i < len(result.get("category", [])) else "",
                    "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                    "timestamp": result["timestamp"][i] if i < len(result.get("timestamp", [])) else "",
                    "scope": result["scope"][i] if i < len(result.get("scope", [])) else "",
                    "agent_id": result.get("agent_id", [""])[i] if i < len(result.get("agent_id", [])) else "",
                    "confidence": float(result.get("confidence", [0.5])[i]) if i < len(result.get("confidence", [])) else 0.5,
                })
            logger.info(f"加载了 {len(memories)} 条记忆")
        except Exception as e:
            logger.warning(f"无法加载向量数据库: {e}")
        
        return memories
    
    def detect_all(self) -> List[Conflict]:
        """检测所有冲突"""
        memories = self.load_memories()
        if not memories:
            logger.warning("没有记忆可检测")
            return []
        
        all_conflicts = []
        
        # 检测各类冲突
        all_conflicts.extend(self.detect_contradiction(memories))
        all_conflicts.extend(self.detect_duplicate(memories))
        all_conflicts.extend(self.detect_perspective_clash(memories))
        all_conflicts.extend(self.detect_temporal(memories))
        
        # 保存新检测到的冲突
        new_conflicts = [c for c in all_conflicts if c.conflict_id not in [x.conflict_id for x in self.conflicts]]
        self.conflicts.extend(new_conflicts)
        self._save_data()
        
        logger.info(f"检测到 {len(new_conflicts)} 个新冲突，总计 {len(self.conflicts)} 个")
        return all_conflicts
    
    def detect_contradiction(self, memories: List[Dict]) -> List[Conflict]:
        """检测矛盾记忆"""
        conflicts = []
        
        for i, m1 in enumerate(memories):
            for m2 in memories[i+1:]:
                # 跳过不同类别
                if m1.get("category") != m2.get("category"):
                    continue
                
                text1 = m1.get("text", "").lower()
                text2 = m2.get("text", "").lower()
                
                # 检查矛盾词对
                for word1, word2 in CONFLICT_PAIRS:
                    if word1 in text1 and word2 in text2:
                        if self._are_similar_contexts(text1, text2, word1, word2):
                            conflict_id = str(uuid.uuid4())[:8]
                            conflict = Conflict(
                                conflict_id=conflict_id,
                                conflict_type=ConflictType.CONTRADICTION,
                                memory_ids=[m1["id"], m2["id"]],
                                description=f"内容矛盾: '{word1}' vs '{word2}'",
                                detected_at=datetime.now(),
                                severity=self._calculate_severity(m1, m2, "contradiction"),
                                suggested_resolution=f"建议: 选择更可信或更新的版本",
                                status="detected"
                            )
                            conflicts.append(conflict)
                            break
        
        logger.info(f"检测到 {len(conflicts)} 个矛盾记忆")
        return conflicts
    
    def detect_duplicate(self, memories: List[Dict]) -> List[Conflict]:
        """检测重复记忆"""
        conflicts = []
        threshold = 0.85  # 相似度阈值
        
        for i, m1 in enumerate(memories):
            text1 = m1.get("text", "").lower().strip()
            if not text1:
                continue
            
            for m2 in memories[i+1:]:
                text2 = m2.get("text", "").lower().strip()
                if not text2:
                    continue
                
                similarity = self._calculate_similarity(text1, text2)
                
                if similarity >= threshold:
                    conflict_id = str(uuid.uuid4())[:8]
                    conflict = Conflict(
                        conflict_id=conflict_id,
                        conflict_type=ConflictType.DUPLICATE,
                        memory_ids=[m1["id"], m2["id"]],
                        description=f"重复记忆 (相似度: {similarity:.2f})",
                        detected_at=datetime.now(),
                        severity="low",
                        suggested_resolution="建议: 保留重要性更高的版本",
                        status="detected"
                    )
                    conflicts.append(conflict)
        
        logger.info(f"检测到 {len(conflicts)} 个重复记忆")
        return conflicts
    
    def detect_perspective_clash(self, memories: List[Dict]) -> List[Conflict]:
        """检测视角冲突"""
        conflicts = []
        
        # 按主题分组
        by_topic = defaultdict(list)
        for m in memories:
            topic = m.get("category", "general")
            by_topic[topic].append(m)
        
        # 检测同一主题下不同 Agent 的观点
        for topic, mems in by_topic.items():
            agent_views = defaultdict(list)
            for m in mems:
                agent_id = m.get("agent_id", "unknown")
                agent_views[agent_id].append(m)
            
            # 检查不同 Agent 之间的冲突
            agents = list(agent_views.keys())
            for i, a1 in enumerate(agents):
                for a2 in agents[i+1:]:
                    if a1 == a2 or a1 == "unknown" or a2 == "unknown":
                        continue
                    
                    # 检查是否有明显不同的观点
                    for m1 in agent_views[a1]:
                        for m2 in agent_views[a2]:
                            similarity = self._calculate_similarity(
                                m1.get("text", ""), 
                                m2.get("text", "")
                            )
                            # 相似但不完全相同，可能是不同视角
                            if 0.5 < similarity < 0.85:
                                conflict_id = str(uuid.uuid4())[:8]
                                conflict = Conflict(
                                    conflict_id=conflict_id,
                                    conflict_type=ConflictType.PERSPECTIVE_CLASH,
                                    memory_ids=[m1["id"], m2["id"]],
                                    description=f"视角冲突: {a1} vs {a2} (主题: {topic})",
                                    detected_at=datetime.now(),
                                    severity="medium",
                                    suggested_resolution="建议: 合并不同视角或保留多个观点",
                                    status="detected"
                                )
                                conflicts.append(conflict)
        
        logger.info(f"检测到 {len(conflicts)} 个视角冲突")
        return conflicts
    
    def detect_temporal(self, memories: List[Dict]) -> List[Conflict]:
        """检测时序冲突"""
        conflicts = []
        
        # 按内容分组，检查时间线
        by_content = defaultdict(list)
        for m in memories:
            # 提取关键内容（简化处理）
            text = m.get("text", "")
            keywords = tuple(sorted([w for w in text.lower().split() if len(w) > 3][:3]))
            by_content[keywords].append(m)
        
        # 检查时间冲突
        for keywords, mems in by_content.items():
            if len(mems) < 2:
                continue
            
            # 按时间排序
            timed_mems = []
            for m in mems:
                ts = m.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        timed_mems.append((dt, m))
                    except:
                        pass
            
            if len(timed_mems) >= 2:
                timed_mems.sort(key=lambda x: x[0])
                # 检查是否有明显的时间矛盾描述
                for i in range(len(timed_mems) - 1):
                    m1, m2 = timed_mems[i][1], timed_mems[i+1][1]
                    # 如果旧记忆说"即将"，新记忆也说"即将"，可能是时序冲突
                    if "即将" in m1.get("text", "") and "即将" in m2.get("text", ""):
                        conflict_id = str(uuid.uuid4())[:8]
                        conflict = Conflict(
                            conflict_id=conflict_id,
                            conflict_type=ConflictType.TEMPORAL,
                            memory_ids=[m1["id"], m2["id"]],
                            description="时序冲突: 时间描述不一致",
                            detected_at=datetime.now(),
                            severity="low",
                            suggested_resolution="建议: 使用最新的时间描述",
                            status="detected"
                        )
                        conflicts.append(conflict)
        
        logger.info(f"检测到 {len(conflicts)} 个时序冲突")
        return conflicts
    
    def _are_similar_contexts(self, text1: str, text2: str, word1: str, word2: str) -> bool:
        """检查两个文本的上下文是否相似"""
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
        
        words1 = set(ctx1.split())
        words2 = set(ctx2.split())
        common = words1 & words2
        
        return len(common) >= 2
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 (Jaccard)"""
        import re
        
        if not text1 or not text2:
            return 0.0
        
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_severity(self, m1: Dict, m2: Dict, conflict_type: str) -> str:
        """计算冲突严重程度"""
        # 基于重要性判断
        imp1 = m1.get("importance", 0.5)
        imp2 = m2.get("importance", 0.5)
        avg_importance = (imp1 + imp2) / 2
        
        if conflict_type == "contradiction":
            if avg_importance > 0.8:
                return "high"
            elif avg_importance > 0.5:
                return "medium"
            else:
                return "low"
        
        return "medium"
    
    def resolve(self, conflict: Conflict, strategy: ResolutionStrategy, 
                resolved_by: str = "auto") -> Resolution:
        """解决冲突"""
        memories = self.load_memories()
        
        # 获取冲突相关的记忆
        conflict_memories = [m for m in memories if m["id"] in conflict.memory_ids]
        
        if len(conflict_memories) < 2:
            raise ValueError("冲突相关的记忆不足")
        
        winner_id = None
        merged_content = None
        notes = None
        
        if strategy == ResolutionStrategy.LATEST_WINS:
            winner_id, notes = self._resolve_latest_wins(conflict_memories)
        elif strategy == ResolutionStrategy.HIGHER_CONFIDENCE:
            winner_id, notes = self._resolve_higher_confidence(conflict_memories)
        elif strategy == ResolutionStrategy.EXPERT_WINS:
            winner_id, notes = self._resolve_expert_wins(conflict_memories)
        elif strategy == ResolutionStrategy.CONSENSUS:
            winner_id, merged_content, notes = self._resolve_consensus(conflict_memories)
        elif strategy == ResolutionStrategy.ESCALATE:
            self.escalate(conflict, "无法自动解决，需要用户决策")
            return Resolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                winner_id=None,
                merged_content=None,
                resolved_by=resolved_by,
                resolved_at=datetime.now(),
                notes="已升级给用户"
            )
        
        # 创建解决记录
        resolution = Resolution(
            conflict_id=conflict.conflict_id,
            strategy=strategy,
            winner_id=winner_id,
            merged_content=merged_content,
            resolved_by=resolved_by,
            resolved_at=datetime.now(),
            notes=notes
        )
        
        # 更新冲突状态
        conflict.status = "resolved"
        self.resolutions.append(resolution)
        self._save_data()
        
        logger.info(f"冲突 {conflict.conflict_id} 已解决，策略: {strategy.value}")
        return resolution
    
    def _resolve_latest_wins(self, memories: List[Dict]) -> Tuple[Optional[str], str]:
        """最新获胜策略"""
        latest = None
        latest_time = None
        
        for m in memories:
            ts = m.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if latest_time is None or dt > latest_time:
                        latest_time = dt
                        latest = m
                except:
                    pass
        
        if latest:
            return latest["id"], f"选择最新记忆 ({latest_time})"
        return memories[0]["id"], "默认选择第一个"
    
    def _resolve_higher_confidence(self, memories: List[Dict]) -> Tuple[Optional[str], str]:
        """高置信度获胜策略"""
        winner = max(memories, key=lambda m: m.get("confidence", 0.5))
        return winner["id"], f"选择置信度最高的记忆 ({winner.get('confidence', 0.5):.2f})"
    
    def _resolve_expert_wins(self, memories: List[Dict]) -> Tuple[Optional[str], str]:
        """专家获胜策略"""
        # 查找专家评分最高的记忆
        expert_scores = []
        for m in memories:
            agent_id = m.get("agent_id", "unknown")
            expertise = self.agent_profiles.get(agent_id, {}).get("expertise_score", 0.5)
            expert_scores.append((expertise, m))
        
        winner = max(expert_scores, key=lambda x: x[0])[1]
        return winner["id"], f"选择专家评分最高的记忆 (Agent: {winner.get('agent_id', 'unknown')})"
    
    def _resolve_consensus(self, memories: List[Dict]) -> Tuple[Optional[str], Optional[str], str]:
        """共识策略 - 尝试合并内容"""
        texts = [m.get("text", "") for m in memories]
        # 简单合并：取最长的文本作为基础
        merged = max(texts, key=len)
        
        # 保存所有记忆ID，标记为已合并
        winner_id = memories[0]["id"]
        return winner_id, merged, f"合并了 {len(memories)} 条记忆的内容"
    
    def auto_resolve(self, conflicts: Optional[List[Conflict]] = None) -> List[Resolution]:
        """自动解决（选择最佳策略）"""
        if conflicts is None:
            conflicts = [c for c in self.conflicts if c.status == "detected"]
        
        resolutions = []
        
        for conflict in conflicts:
            # 根据冲突类型选择最佳策略
            if conflict.conflict_type == ConflictType.CONTRADICTION:
                # 矛盾使用高置信度策略
                strategy = ResolutionStrategy.HIGHER_CONFIDENCE
            elif conflict.conflict_type == ConflictType.DUPLICATE:
                # 重复使用最新策略
                strategy = ResolutionStrategy.LATEST_WINS
            elif conflict.conflict_type == ConflictType.PERSPECTIVE_CLASH:
                # 视角冲突使用共识策略
                strategy = ResolutionStrategy.CONSENSUS
            elif conflict.conflict_type == ConflictType.TEMPORAL:
                # 时序冲突使用最新策略
                strategy = ResolutionStrategy.LATEST_WINS
            else:
                strategy = ResolutionStrategy.ESCALATE
            
            try:
                resolution = self.resolve(conflict, strategy, "auto")
                resolutions.append(resolution)
            except Exception as e:
                logger.error(f"自动解决冲突 {conflict.conflict_id} 失败: {e}")
        
        logger.info(f"自动解决了 {len(resolutions)} 个冲突")
        return resolutions
    
    def escalate(self, conflict: Conflict, reason: str):
        """升级给用户"""
        conflict.status = "escalated"
        self._save_data()
        logger.warning(f"冲突 {conflict.conflict_id} 已升级: {reason}")
    
    def get_conflict_report(self) -> Dict:
        """获取冲突报告"""
        total = len(self.conflicts)
        resolved = len([c for c in self.conflicts if c.status == "resolved"])
        escalated = len([c for c in self.conflicts if c.status == "escalated"])
        pending = len([c for c in self.conflicts if c.status == "detected"])
        
        by_type = defaultdict(int)
        for c in self.conflicts:
            by_type[c.conflict_type.value] += 1
        
        by_severity = defaultdict(int)
        for c in self.conflicts:
            by_severity[c.severity] += 1
        
        recent_conflicts = sorted(
            [c for c in self.conflicts if c.status == "detected"],
            key=lambda x: x.detected_at,
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "total_conflicts": total,
                "resolved": resolved,
                "escalated": escalated,
                "pending": pending,
                "resolution_rate": resolved / total if total > 0 else 0
            },
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "recent_pending": [
                {
                    "id": c.conflict_id,
                    "type": c.conflict_type.value,
                    "description": c.description,
                    "severity": c.severity,
                    "detected_at": c.detected_at.isoformat()
                }
                for c in recent_conflicts
            ]
        }
    
    def list_conflicts(self, status: Optional[str] = None) -> List[Conflict]:
        """列出冲突"""
        if status:
            return [c for c in self.conflicts if c.status == status]
        return self.conflicts


def main():
    parser = argparse.ArgumentParser(description="记忆冲突解决器 v2.0")
    parser.add_argument("command", choices=["detect", "list", "resolve", "auto-resolve", "report"])
    parser.add_argument("--id", help="冲突ID (用于 resolve)")
    parser.add_argument("--strategy", choices=[s.value for s in ResolutionStrategy],
                       default="latest_wins", help="解决策略")
    parser.add_argument("--status", choices=["detected", "resolving", "resolved", "escalated"],
                       help="过滤状态 (用于 list)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    resolver = ConflictResolver()
    
    if args.command == "detect":
        print("🔍 开始检测冲突...\n")
        conflicts = resolver.detect_all()
        
        by_type = defaultdict(int)
        for c in conflicts:
            by_type[c.conflict_type.value] += 1
        
        print(f"检测到 {len(conflicts)} 个新冲突:")
        for ctype, count in by_type.items():
            emoji = {
                "contradiction": "❌",
                "duplicate": "🔄",
                "perspective_clash": "👥",
                "temporal": "⏰"
            }.get(ctype, "•")
            print(f"   {emoji} {ctype}: {count}")
    
    elif args.command == "list":
        conflicts = resolver.list_conflicts(args.status)
        status_filter = f" [{args.status}]" if args.status else ""
        print(f"\n📋 冲突列表{status_filter} ({len(conflicts)} 个):\n")
        
        for c in conflicts:
            emoji = {
                ConflictType.CONTRADICTION: "❌",
                ConflictType.DUPLICATE: "🔄",
                ConflictType.PERSPECTIVE_CLASH: "👥",
                ConflictType.TEMPORAL: "⏰"
            }.get(c.conflict_type, "•")
            
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(c.severity, "⚪")
            
            print(f"{emoji} {c.conflict_id} {severity_emoji}")
            print(f"   类型: {c.conflict_type.value}")
            print(f"   描述: {c.description}")
            print(f"   记忆: {', '.join(c.memory_ids)}")
            print(f"   状态: {c.status}")
            print(f"   检测时间: {c.detected_at.strftime('%Y-%m-%d %H:%M')}")
            if c.suggested_resolution:
                print(f"   建议: {c.suggested_resolution}")
            print()
    
    elif args.command == "resolve":
        if not args.id:
            print("❌ 请指定冲突ID (--id)")
            sys.exit(1)
        
        conflict = next((c for c in resolver.conflicts if c.conflict_id == args.id), None)
        if not conflict:
            print(f"❌ 未找到冲突: {args.id}")
            sys.exit(1)
        
        strategy = ResolutionStrategy(args.strategy)
        print(f"🔧 解决冲突 {args.id}，策略: {strategy.value}\n")
        
        try:
            resolution = resolver.resolve(conflict, strategy, "user")
            print(f"✅ 已解决")
            print(f"   获胜记忆: {resolution.winner_id}")
            if resolution.merged_content:
                print(f"   合并内容: {resolution.merged_content[:100]}...")
            if resolution.notes:
                print(f"   备注: {resolution.notes}")
        except Exception as e:
            print(f"❌ 解决失败: {e}")
            sys.exit(1)
    
    elif args.command == "auto-resolve":
        print("🤖 开始自动解决...\n")
        resolutions = resolver.auto_resolve()
        
        if not resolutions:
            print("✅ 没有需要解决的冲突")
        else:
            print(f"✅ 自动解决了 {len(resolutions)} 个冲突:")
            for r in resolutions:
                print(f"   • {r.conflict_id}: {r.strategy.value}")
    
    elif args.command == "report":
        report = resolver.get_conflict_report()
        
        print("\n📊 冲突解决报告\n")
        print(f"{'='*50}")
        
        summary = report["summary"]
        print(f"\n📈 总体统计:")
        print(f"   总冲突数: {summary['total_conflicts']}")
        print(f"   已解决: {summary['resolved']}")
        print(f"   已升级: {summary['escalated']}")
        print(f"   待处理: {summary['pending']}")
        print(f"   解决率: {summary['resolution_rate']*100:.1f}%")
        
        print(f"\n📊 按类型分布:")
        for ctype, count in report["by_type"].items():
            print(f"   • {ctype}: {count}")
        
        print(f"\n🔴 按严重程度分布:")
        for sev, count in report["by_severity"].items():
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
            print(f"   {emoji} {sev}: {count}")
        
        if report["recent_pending"]:
            print(f"\n⏳ 最近待处理冲突:")
            for c in report["recent_pending"][:5]:
                print(f"   • [{c['id']}] {c['description']}")


if __name__ == "__main__":
    main()
