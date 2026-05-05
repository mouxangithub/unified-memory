"""
差异计算引擎

提供 JSON diff 和向量相似度计算能力
"""

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .models import ChangeType, DiffResult, EmbeddingVector, FieldChange, Metadata


class DiffEngine:
    """差异计算引擎"""

    SEMANTIC_CHANGE_THRESHOLD = 0.85  # 向量相似度低于此值认为有显著语义变化
    MIN_DIFF_THRESHOLD = 0.3  # 文本变化比例超过此值认为有显著变化

    def __init__(self, semantic_threshold: float = 0.85, min_diff_threshold: float = 0.3):
        self.semantic_threshold = semantic_threshold
        self.min_diff_threshold = min_diff_threshold

    def compute_diff(
        self,
        content_from: str,
        content_to: str,
        embedding_from: EmbeddingVector,
        embedding_to: EmbeddingVector,
        metadata_from: Metadata,
        metadata_to: Metadata,
        memory_id: str,
        version_from: int,
        version_to: int,
    ) -> DiffResult:
        """
        计算两个版本之间的完整差异

        Args:
            content_from: 源版本内容
            content_to: 目标版本内容
            embedding_from: 源版本向量
            embedding_to: 目标版本向量
            metadata_from: 源版本元数据
            metadata_to: 目标版本元数据
            memory_id: 内存ID
            version_from: 源版本号
            version_to: 目标版本号

        Returns:
            DiffResult: 差异计算结果
        """
        # 计算文本差异
        text_changes = self._compute_text_diff(content_from, content_to, metadata_from, metadata_to)

        # 计算向量相似度
        semantic_similarity = embedding_from.cosine_similarity(embedding_to)

        # 判断是否有显著变化
        has_significant_change = self._detect_significant_change(
            text_changes, semantic_similarity
        )

        # 生成变更摘要
        summary = self._generate_summary(
            text_changes, semantic_similarity, content_from, content_to
        )

        return DiffResult(
            memory_id=memory_id,
            version_from=version_from,
            version_to=version_to,
            text_changes=text_changes,
            semantic_similarity=semantic_similarity,
            summary=summary,
            has_significant_change=has_significant_change,
            computed_at=datetime.utcnow(),
        )

    def _compute_text_diff(
        self,
        content_from: str,
        content_to: str,
        metadata_from: Metadata,
        metadata_to: Metadata,
    ) -> list[FieldChange]:
        """计算文本和元数据的差异"""
        changes = []

        # 内容差异
        content_change = self._compute_content_diff(content_from, content_to)
        changes.append(content_change)

        # 元数据差异
        changes.extend(self._compute_metadata_diff(metadata_from, metadata_to))

        return changes

    def _compute_content_diff(self, content_from: str, content_to: str) -> FieldChange:
        """计算内容差异"""
        if content_from == content_to:
            return FieldChange(
                field="content",
                change_type=ChangeType.UNCHANGED,
                old_value=content_from,
                new_value=content_to,
            )

        # 计算变化行数
        from_lines = content_from.splitlines(keepends=True)
        to_lines = content_to.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, from_lines, to_lines)
        changes_count = sum(
            1 for tag in matcher.get_opcodes() if tag[0] in ("replace", "delete", "insert")
        )

        change_type = ChangeType.UPDATED if changes_count > 0 else ChangeType.UNCHANGED

        return FieldChange(
            field="content",
            change_type=change_type,
            old_value=content_from,
            new_value=content_to,
        )

    def _compute_metadata_diff(
        self, metadata_from: Metadata, metadata_to: Metadata
    ) -> list[FieldChange]:
        """计算元数据差异"""
        changes = []

        # 标签变化
        if set(metadata_from.tags) != set(metadata_to.tags):
            changes.append(
                FieldChange(
                    field="metadata.tags",
                    change_type=ChangeType.UPDATED,
                    old_value=metadata_from.tags,
                    new_value=metadata_to.tags,
                )
            )

        # 分类变化
        if metadata_from.category != metadata_to.category:
            changes.append(
                FieldChange(
                    field="metadata.category",
                    change_type=ChangeType.UPDATED,
                    old_value=metadata_from.category,
                    new_value=metadata_to.category,
                )
            )

        # 重要性变化
        if metadata_from.importance != metadata_to.importance:
            changes.append(
                FieldChange(
                    field="metadata.importance",
                    change_type=ChangeType.UPDATED,
                    old_value=metadata_from.importance,
                    new_value=metadata_to.importance,
                )
            )

        return changes

    def _detect_significant_change(
        self, text_changes: list[FieldChange], semantic_similarity: float
    ) -> bool:
        """检测是否有显著变化"""
        # 语义变化检测
        if semantic_similarity < self.semantic_threshold:
            return True

        # 文本变化检测
        content_change = next((c for c in text_changes if c.field == "content"), None)
        if content_change and content_change.change_type == ChangeType.UPDATED:
            # 使用编辑距离计算变化比例
            if content_change.old_value and content_change.new_value:
                ratio = difflib.SequenceMatcher(
                    None,
                    content_change.old_value,
                    content_change.new_value,
                ).ratio()
                if ratio < (1 - self.min_diff_threshold):
                    return True

        return False

    def _generate_summary(
        self,
        text_changes: list[FieldChange],
        semantic_similarity: float,
        content_from: str,
        content_to: str,
    ) -> str:
        """生成变更摘要"""
        summary_parts = []

        # 分析内容变化
        content_change = next((c for c in text_changes if c.field == "content"), None)
        if content_change and content_change.change_type == ChangeType.UPDATED:
            lines_added = content_to.count("\n") - content_from.count("\n")
            if lines_added > 0:
                summary_parts.append(f"+{lines_added} lines")
            elif lines_added < 0:
                summary_parts.append(f"{lines_added} lines")

            # 计算字符变化
            char_diff = len(content_to) - len(content_from)
            if abs(char_diff) > 100:
                summary_parts.append(f"{'+' if char_diff > 0 else ''}{char_diff} chars")

        # 元数据变化
        for change in text_changes:
            if change.field.startswith("metadata.") and change.change_type == ChangeType.UPDATED:
                field_name = change.field.split(".")[-1]
                summary_parts.append(f"meta.{field_name} updated")

        # 语义变化
        if semantic_similarity < self.semantic_threshold:
            summary_parts.append(f"semantic change ({semantic_similarity:.2f})")

        if not summary_parts:
            return "minor update"

        return ", ".join(summary_parts)

    def compute_similarity(self, vec1: EmbeddingVector, vec2: EmbeddingVector) -> float:
        """计算两个向量的相似度"""
        return vec1.cosine_similarity(vec2)

    def compute_text_hash(self, text: str) -> str:
        """计算文本的哈希值（用于快速比较）"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def compute_unified_diff(
        self, content_from: str, content_to: str, from_label: str = "v1", to_label: str = "v2"
    ) -> str:
        """生成标准的 unified diff 格式"""
        from_lines = content_from.splitlines(keepends=True)
        to_lines = content_to.splitlines(keepends=True)

        diff = difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"{from_label}",
            tofile=f"{to_label}",
            lineterm="",
        )
        return "".join(diff)


@dataclass
class ChangeDetector:
    """变更检测器 - 用于实时监控变化"""

    engine: DiffEngine
    history: list[DiffResult] = field(default_factory=list)
    max_history: int = 100

    def detect_change(
        self,
        old_content: str,
        new_content: str,
        old_embedding: EmbeddingVector,
        new_embedding: EmbeddingVector,
        memory_id: str,
        version: int,
    ) -> DiffResult:
        """检测变更并记录"""
        prev_version = version - 1
        diff = self.engine.compute_diff(
            old_content,
            new_content,
            old_embedding,
            new_embedding,
            Metadata(),
            Metadata(),
            memory_id,
            prev_version,
            version,
        )

        self.history.append(diff)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

        return diff

    def get_change_frequency(self, window: int = 10) -> float:
        """获取变更频率"""
        if len(self.history) < 2:
            return 0.0

        recent = self.history[-window:]
        significant_changes = sum(1 for d in recent if d.has_significant_change)
        return significant_changes / len(recent)

    def get_change_trend(self) -> str:
        """获取变更趋势"""
        if len(self.history) < 3:
            return "stable"

        recent_similarity = [d.semantic_similarity for d in self.history[-3:]]
        if all(s > 0.95 for s in recent_similarity):
            return "stable"
        elif all(s < 0.8 for s in recent_similarity):
            return "volatile"
        else:
            return "evolving"