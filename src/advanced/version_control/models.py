"""
版本控制数据模型

定义核心数据结构：VersionedMemory, Version, DiffResult
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class ChangeType(str, Enum):
    """变更类型枚举"""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class EmbeddingVector:
    """向量嵌入表示"""

    values: list[float]
    dimension: int = 1536

    def __post_init__(self):
        if not self.values:
            self.values = [0.0] * self.dimension
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimension}, "
                f"got {len(self.values)}"
            )

    def to_list(self) -> list[float]:
        return self.values

    @classmethod
    def zero(cls, dimension: int = 1536) -> "EmbeddingVector":
        return cls(values=[0.0] * dimension, dimension=dimension)

    def cosine_similarity(self, other: "EmbeddingVector") -> float:
        """计算余弦相似度"""
        import math

        dot_product = sum(a * b for a, b in zip(self.values, other.values))
        magnitude_a = math.sqrt(sum(a * a for a in self.values))
        magnitude_b = math.sqrt(sum(b * b for b in other.values))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)


@dataclass
class Metadata:
    """内存元数据"""

    tags: list[str] = field(default_factory=list)
    category: Optional[str] = None
    importance: int = 1  # 1-5
    source: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tags": self.tags,
            "category": self.category,
            "importance": self.importance,
            "source": self.source,
            **{k: v for k, v in self.extra.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metadata":
        return cls(
            tags=data.get("tags", []),
            category=data.get("category"),
            importance=data.get("importance", 1),
            source=data.get("source"),
            extra={k: v for k, v in data.items() if k not in ("tags", "category", "importance", "source")},
        )

    def merge(self, other: "Metadata") -> "Metadata":
        """合并元数据"""
        return Metadata(
            tags=list(set(self.tags + other.tags)),
            category=other.category or self.category,
            importance=max(self.importance, other.importance),
            source=other.source or self.source,
            extra={**self.extra, **other.extra},
        )


@dataclass
class FieldChange:
    """字段变更信息"""

    field: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None

    @property
    def has_changed(self) -> bool:
        return self.change_type != ChangeType.UNCHANGED


@dataclass
class DiffResult:
    """版本差异计算结果"""

    memory_id: str
    version_from: int
    version_to: int
    text_changes: list[FieldChange] = field(default_factory=list)
    semantic_similarity: float = 1.0
    summary: str = ""
    has_significant_change: bool = False
    computed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def changed_fields(self) -> list[str]:
        return [fc.field for fc in self.text_changes if fc.has_changed]

    @property
    def change_percentage(self) -> float:
        """计算变更比例"""
        total = len(self.text_changes)
        if total == 0:
            return 0.0
        changed = sum(1 for fc in self.text_changes if fc.has_changed)
        return (changed / total) * 100


@dataclass
class Version:
    """单个版本快照"""

    id: UUID
    memory_id: UUID
    version: int
    content: str
    embedding: EmbeddingVector
    metadata: Metadata
    created_at: datetime
    created_by: str
    change_summary: str
    parent_version: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "memory_id": str(self.memory_id),
            "version": self.version,
            "content": self.content,
            "embedding": self.embedding.to_list(),
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "change_summary": self.change_summary,
            "parent_version": self.parent_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Version":
        return cls(
            id=UUID(data["id"]),
            memory_id=UUID(data["memory_id"]),
            version=data["version"],
            content=data["content"],
            embedding=EmbeddingVector(values=data["embedding"]),
            metadata=Metadata.from_dict(data["metadata"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data["created_by"],
            change_summary=data.get("change_summary", ""),
            parent_version=data.get("parent_version"),
        )


@dataclass
class VersionedMemory:
    """带版本管理的内存记录"""

    id: UUID
    current_version: int
    current_content: str
    current_embedding: EmbeddingVector
    current_metadata: Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "current_version": self.current_version,
            "current_content": self.current_content,
            "current_embedding": self.current_embedding.to_list(),
            "current_metadata": self.current_metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionedMemory":
        return cls(
            id=UUID(data["id"]),
            current_version=data["current_version"],
            current_content=data["current_content"],
            current_embedding=EmbeddingVector(values=data["current_embedding"]),
            current_metadata=Metadata.from_dict(data["current_metadata"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            created_by=data["created_by"],
            is_deleted=data.get("is_deleted", False),
        )


@dataclass
class VersionStats:
    """版本统计信息"""

    memory_id: str
    total_versions: int
    oldest_version: Optional[int] = None
    newest_version: Optional[int] = None
    oldest_date: Optional[datetime] = None
    newest_date: Optional[datetime] = None
    average_version_size: int = 0

    @property
    def version_span(self) -> int:
        if self.oldest_version is None or self.newest_version is None:
            return 0
        return self.newest_version - self.oldest_version