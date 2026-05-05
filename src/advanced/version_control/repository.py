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