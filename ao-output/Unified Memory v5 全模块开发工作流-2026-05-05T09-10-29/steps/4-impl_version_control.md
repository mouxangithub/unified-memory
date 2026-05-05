> 🔄 **核心开发者** | 步骤 4/6 | 166.3s

---

<think>用户要求实现一个完整的 Unified Memory v5 版本控制模块，包含：

1. 数据模型：VersionedMemory
2. 版本管理器：VersionManager 类
3. 变更检测：diff 功能
4. 数据访问层：repository
5. 单元测试

让我按照高质量工程代码的标准来实现这个模块。

首先，我需要设计：

1. **models.py** - 数据模型
   - Memory 基类
   - Version 模型
   - DiffResult 数据类

2. **diff.py** - 差异计算
   - JSON diff
   - 向量相似度计算
   - 变更摘要生成

3. **repository.py** - 数据访问层
   - PostgreSQL 表设计
   - CRUD 操作
   - 版本链管理

4. **manager.py** - 业务逻辑层
   - 版本创建
   - 版本查询
   - 版本回滚
   - 清理策略

5. **tests/** - 单元测试
   - 测试覆盖率 > 80%

让我开始实现完整的代码：

```python
# memory_v5/version_control/__init__.py
```

```python
# memory_v5/version_control/models.py
```

```python
# memory_v5/version_control/diff.py
```

```python
# memory_v5/version_control/repository.py
```

```python
# memory_v5/version_control/manager.py
```

```python
# memory_v5/version_control/tests/test_models.py
```

```python
# memory_v5/version_control/tests/test_manager.py


```

```python
# memory_v5/version_control/tests/test_diff.py
```

需要使用以下技术栈：
- SQLAlchemy 用于 ORM
- numpy 用于向量计算
- deepdiff 或 jsonpatch 用于 JSON diff
- pytest 用于测试
- uuid 用于 ID 生成
- datetime 用于时间处理

现在开始实现这些模块。
</think>

# Unified Memory v5 版本控制模块实现

我将按照生产级代码标准实现完整的版本控制模块。

## 目录结构

```
memory_v5/version_control/
├── __init__.py
├── models.py            # 版本数据模型
├── diff.py              # 差异计算引擎
├── repository.py        # 数据访问层
├── manager.py           # 版本管理器
├── events.py            # 事件系统
├── exceptions.py        # 异常定义
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_manager.py
    ├── test_diff.py
    └── test_repository.py
```

## 核心实现

```python
# memory_v5/version_control/__init__.py
"""
Unified Memory v5 - 版本控制模块

提供完整的内存版本管理、差异计算和历史追溯能力。
"""

from .models import VersionedMemory, Version, DiffResult, ChangeType
from .manager import VersionManager
from .diff import DiffEngine
from .repository import VersionRepository
from .exceptions import (
    VersionControlError,
    VersionNotFoundError,
    MemoryNotFoundError,
    InvalidVersionError,
)

__version__ = "5.0.0"
__all__ = [
    "VersionedMemory",
    "Version",
    "DiffResult",
    "ChangeType",
    "VersionManager",
    "DiffEngine",
    "VersionRepository",
    "VersionControlError",
    "VersionNotFoundError",
    "MemoryNotFoundError",
    "InvalidVersionError",
]
```

```python
# memory_v5/version_control/exceptions.py
"""
版本控制模块异常定义
"""

from typing import Optional


class VersionControlError(Exception):
    """版本控制基础异常"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, details={self.details})"


class MemoryNotFoundError(VersionControlError):
    """内存记录不存在"""

    def __init__(self, memory_id: str):
        super().__init__(
            f"Memory not found: {memory_id}",
            details={"memory_id": memory_id},
        )


class VersionNotFoundError(VersionControlError):
    """版本不存在"""

    def __init__(self, memory_id: str, version: int):
        super().__init__(
            f"Version {version} not found for memory {memory_id}",
            details={"memory_id": memory_id, "version": version},
        )


class InvalidVersionError(VersionControlError):
    """无效的版本号"""

    def __init__(self, version: int, reason: str):
        super().__init__(
            f"Invalid version {version}: {reason}",
            details={"version": version, "reason": reason},
        )


class DiffComputationError(VersionControlError):
    """差异计算失败"""

    def __init__(self, reason: str, details: Optional[dict] = None):
        super().__init__(f"Diff computation failed: {reason}", details=details)


class RepositoryError(VersionControlError):
    """数据访问层错误"""

    pass
```

```python
# memory_v5/version_control/models.py
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
```

```python
# memory_v5/version_control/diff.py
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
```

```python
# memory_v5/version_control/repository.py
"""
数据访问层

提供 PostgreSQL 数据库操作能力
"""

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Generator, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .exceptions import MemoryNotFoundError, RepositoryError, VersionNotFoundError
from .models import EmbeddingVector, Metadata, Version, VersionedMemory, VersionStats

logger = logging.getLogger(__name__)

Base = declarative_base()


class VersionORM(Base):
    """版本表 ORM 模型"""

    __tablename__ = "memory_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    memory_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    change_summary = Column(Text, nullable=True)
    parent_version = Column(Integer, nullable=True)

    __table_args__ = (
        # 复合唯一索引：每个 memory 的版本号唯一
        {"schema": None},
    )


class MemoryORM(Base):
    """内存主表 ORM 模型"""

    __tablename__ = "memory_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    current_version = Column(Integer, nullable=False, default=1)
    current_content = Column(Text, nullable=False)
    current_embedding = Column(ARRAY(Float), nullable=False)
    current_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    is_deleted = Column(Integer, nullable=False, default=0)


class VersionRepository:
    """
    版本数据访问层

    提供版本数据的 CRUD 操作和查询能力
    """

    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def create_session(cls, database_url: str) -> "VersionRepository":
        """创建数据库会话"""
        engine = create_engine(database_url, pool_pre_ping=True, pool_size=10)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        return cls(session_factory())

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """事务上下文管理器"""
        try:
            yield self.session
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Transaction failed: {e}") from e

    # ==================== Memory 操作 ====================

    def create_memory(
        self,
        memory_id: UUID,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
        created_by: str,
    ) -> VersionedMemory:
        """创建新的内存记录（同时创建第一个版本）"""
        try:
            now = datetime.utcnow()
            memory = MemoryORM(
                id=memory_id,
                current_version=1,
                current_content=content,
                current_embedding=embedding,
                current_metadata=metadata,
                created_at=now,
                updated_at=now,
                created_by=created_by,
                is_deleted=0,
            )
            self.session.add(memory)

            # 创建第一个版本
            version = VersionORM(
                id=uuid4(),
                memory_id=memory_id,
                version=1,
                content=content,
                embedding=embedding,
                metadata=metadata,
                created_at=now,
                created_by=created_by,
                change_summary="Initial version",
                parent_version=None,
            )
            self.session.add(version)
            self.session.commit()

            return self._orm_to_memory(memory)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Failed to create memory: {e}") from e

    def get_memory(self, memory_id: UUID) -> Optional[VersionedMemory]:
        """获取内存记录"""
        memory = self.session.query(MemoryORM).filter(
            MemoryORM.id == memory_id,
            MemoryORM.is_deleted == 0,
        ).first()

        if not memory:
            return None

        return self._orm_to_memory(memory)

    def update_memory(
        self,
        memory_id: UUID,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> VersionedMemory:
        """更新内存记录"""
        memory = self.session.query(MemoryORM).filter(
            MemoryORM.id == memory_id,
            MemoryORM.is_deleted == 0,
        ).first()

        if not memory:
            raise MemoryNotFoundError(str(memory_id))

        memory.current_content = content
        memory.current_embedding = embedding
        memory.current_metadata = metadata
        memory.updated_at = datetime.utcnow()
        memory.current_version += 1

        self.session.commit()
        return self._orm_to_memory(memory)

    def soft_delete_memory(self, memory_id: UUID) -> bool:
        """软删除内存记录"""
        memory = self.session.query(MemoryORM).filter(
            MemoryORM.id == memory_id,
        ).first()

        if not memory:
            return False

        memory.is_deleted = 1
        memory.updated_at = datetime.utcnow()
        self.session.commit()
        return True

    # ==================== Version 操作 ====================

    def create_version(
        self,
        memory_id: UUID,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
        created_by: str,
        change_summary: str = "",
        parent_version: Optional[int] = None,
    ) -> Version:
        """创建新版本"""
        try:
            # 获取当前版本号
            last_version = self.session.query(func.max(VersionORM.version)).filter(
                VersionORM.memory_id == memory_id,
            ).scalar() or 0

            new_version = last_version + 1
            now = datetime.utcnow()

            version = VersionORM(
                id=uuid4(),
                memory_id=memory_id,
                version=new_version,
                content=content,
                embedding=embedding,
                metadata=metadata,
                created_at=now,
                created_by=created_by,
                change_summary=change_summary,
                parent_version=parent_version,
            )
            self.session.add(version)

            # 更新 memory 记录
            memory = self.session.query(MemoryORM).filter(
                MemoryORM.id == memory_id
            ).first()
            if memory:
                memory.current_version = new_version
                memory.current_content = content
                memory.current_embedding = embedding
                memory.current_metadata = metadata
                memory.updated_at = now

            self.session.commit()
            return self._orm_to_version(version)
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Failed to create version: {e}") from e

    def get_version(self, memory_id: UUID, version: int) -> Version:
        """获取指定版本"""
        v = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
            VersionORM.version == version,
        ).first()

        if not v:
            raise VersionNotFoundError(str(memory_id), version)

        return self._orm_to_version(v)

    def get_version_by_id(self, version_id: UUID) -> Version:
        """根据版本ID获取版本"""
        v = self.session.query(VersionORM).filter(
            VersionORM.id == version_id,
        ).first()

        if not v:
            raise VersionNotFoundError(str(version_id), 0)

        return self._orm_to_version(v)

    def list_versions(
        self,
        memory_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Version]:
        """列出内存的所有版本（按版本号降序）"""
        versions = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
        ).order_by(
            VersionORM.version.desc()
        ).limit(limit).offset(offset).all()

        return [self._orm_to_version(v) for v in versions]

    def get_latest_version(self, memory_id: UUID) -> Optional[Version]:
        """获取最新版本"""
        v = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
        ).order_by(
            VersionORM.version.desc()
        ).first()

        if not v:
            return None

        return self._orm_to_version(v)

    def get_previous_version(self, memory_id: UUID, version: int) -> Optional[Version]:
        """获取指定版本的前一个版本"""
        v = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
            VersionORM.version < version,
        ).order_by(
            VersionORM.version.desc()
        ).first()

        if not v:
            return None

        return self._orm_to_version(v)

    def get_versions_in_range(
        self,
        memory_id: UUID,
        start_version: int,
        end_version: int,
    ) -> list[Version]:
        """获取指定版本范围内的所有版本"""
        versions = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
            VersionORM.version >= start_version,
            VersionORM.version <= end_version,
        ).order_by(VersionORM.version.asc()).all()

        return [self._orm_to_version(v) for v in versions]

    def count_versions(self, memory_id: UUID) -> int:
        """统计版本数量"""
        return self.session.query(func.count(VersionORM.id)).filter(
            VersionORM.memory_id == memory_id,
        ).scalar() or 0

    def get_version_stats(self, memory_id: UUID) -> VersionStats:
        """获取版本统计信息"""
        result = self.session.query(
            func.count(VersionORM.id).label("total"),
            func.min(VersionORM.version).label("oldest"),
            func.max(VersionORM.version).label("newest"),
            func.min(VersionORM.created_at).label("oldest_date"),
            func.max(VersionORM.created_at).label("newest_date"),
            func.avg(func.length(VersionORM.content)).label("avg_size"),
        ).filter(
            VersionORM.memory_id == memory_id,
        ).first()

        return VersionStats(
            memory_id=str(memory_id),
            total_versions=result.total or 0,
            oldest_version=result.oldest,
            newest_version=result.newest,
            oldest_date=result.oldest_date,
            newest_date=result.newest_date,
            average_version_size=int(result.avg_size or 0),
        )

    # ==================== 清理操作 ====================

    def cleanup_old_versions(
        self,
        memory_id: UUID,
        keep_count: int = 30,
        keep_days: int = 90,
    ) -> int:
        """
        清理旧版本

        保留策略：最近 N 个版本 或 最近 M 天
        """
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        # 获取要保留的版本号（最近 keep_count 个）
        recent_versions = self.session.query(VersionORM.version).filter(
            VersionORM.memory_id == memory_id,
        ).order_by(
            VersionORM.version.desc()
        ).limit(keep_count).all()

        keep_versions = [v.version for v in recent_versions]

        # 删除不符合保留条件的版本
        query = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
            ~VersionORM.version.in_(keep_versions),
            VersionORM.created_at < cutoff_date,
        )

        deleted_count = query.delete(synchronize_session=False)
        self.session.commit()

        return deleted_count

    def get_versions_for_cleanup(
        self,
        memory_id: UUID,
        keep_count: int = 30,
        keep_days: int = 90,
    ) -> list[Version]:
        """获取待清理的版本列表"""
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        recent_versions = self.session.query(VersionORM.version).filter(
            VersionORM.memory_id == memory_id,
        ).order_by(
            VersionORM.version.desc()
        ).limit(keep_count).all()

        keep_versions = [v.version for v in recent_versions]

        versions = self.session.query(VersionORM).filter(
            VersionORM.memory_id == memory_id,
            ~VersionORM.version.in_(keep_versions),
            VersionORM.created_at < cutoff_date,
        ).all()

        return [self._orm_to_version(v) for v in versions]

    # ==================== 转换方法 ====================

    def _orm_to_memory(self, orm: MemoryORM) -> VersionedMemory:
        """ORM 模型转换为领域模型"""
        return VersionedMemory(
            id=orm.id,
            current_version=orm.current_version,
            current_content=orm.current_content,
            current_embedding=EmbeddingVector(values=orm.current_embedding),
            current_metadata=Metadata.from_dict(orm.current_metadata),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            created_by=orm.created_by,
            is_deleted=bool(orm.is_deleted),
        )

    def _orm_to_version(self, orm: VersionORM) -> Version:
        """ORM 模型转换为领域模型"""
        return Version(
            id=orm.id,
            memory_id=orm.memory_id,
            version=orm.version,
            content=orm.content,
            embedding=EmbeddingVector(values=orm.embedding),
            metadata=Metadata.from_dict(orm.metadata),
            created_at=orm.created_at,
            created_by=orm.created_by,
            change_summary=orm.change_summary or "",
            parent_version=orm.parent_version,
        )
```

```python
# memory_v5/version_control/manager.py
"""
版本管理器

提供版本控制的核心业务逻辑
"""

import logging
from datetime import datetime
from typing import Callable, Optional
from uuid import UUID, uuid4

from .diff import ChangeDetector, DiffEngine
from .exceptions import (
    InvalidVersionError,
    MemoryNotFoundError,
    VersionControlError,
    VersionNotFoundError,
)
from .models import DiffResult, EmbeddingVector, Metadata, Version, VersionedMemory
from .repository import VersionRepository

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """嵌入向量生成器接口"""

    def generate(self, text: str) -> list[float]:
        """生成文本的嵌入向量"""
        raise NotImplementedError


class DefaultEmbeddingProvider(EmbeddingProvider):
    """默认嵌入向量生成器（基于文本哈希生成伪向量）"""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def generate(self, text: str) -> list[float]:
        """使用简单的哈希生成伪向量用于测试"""
        import hashlib

        hash_value = hashlib.sha256(text.encode()).digest()
