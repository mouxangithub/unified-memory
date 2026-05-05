> 💾 **核心开发者** | 步骤 2/6 | 191.0s

---

<think>用户请求实现 Unified Memory v5 的备份恢复模块。用户提供了一个基础约束，提到：
- 备份频率：每小时增量，每日全量
- 存储...

用户似乎在输入约束时中断了。但根据请求，我需要实现一个完整的备份恢复模块。

让我基于最佳实践和常见需求来设计这个模块：

1. **增量备份**：只备份自上次备份以来的变更
2. **全量备份**：完整备份所有数据
3. **恢复功能**：从备份恢复数据
4. **备份元数据管理**：跟踪备份历史
5. **校验和验证**：确保备份完整性
6. **压缩存储**：节省空间
7. **并发控制**：多线程/多进程备份
8. **故障处理**：异常情况处理

我会提供一个完整的、生产级别的实现，包括：
- 核心备份恢复类
- 配置管理
- 存储后端抽象（支持本地/S3等）
- 元数据管理
- 校验和计算
- 恢复点管理
- 清理策略

让我开始实现完整的代码。
</think>

# Unified Memory v5 备份恢复模块

基于你的基础约束，我将实现一个完整的备份恢复系统。

## 项目结构

```
unified_memory_backup/
├── __init__.py
├── config.py
├── backup.py
├── restore.py
├── storage/
│   ├── __init__.py
│   ├── base.py
│   ├── local.py
│   └── s3.py
├── metadata.py
├── checksum.py
├── scheduler.py
└── main.py
```

## 完整实现

### config.py - 配置管理

```python
"""
Unified Memory v5 备份恢复配置模块
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional
import json


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class StorageBackend(Enum):
    LOCAL = "local"
    S3 = "s3"


@dataclass
class StorageConfig:
    backend: StorageBackend = StorageBackend.LOCAL
    base_path: str = "./backups"
    s3_bucket: Optional[str] = None
    s3_prefix: str = "unified-memory/backups"
    
    # 连接配置
    local_retention_days: int = 30
    remote_retention_days: int = 90


@dataclass
class BackupConfig:
    # 备份源配置
    memory_data_path: str = "./data/memory"
    
    # 频率配置
    incremental_interval_hours: int = 1
    full_backup_hour: int = 2  # 每天凌晨2点做全量
    
    # 备份文件配置
    compression_enabled: bool = True
    compression_algorithm: str = "gzip"  # gzip, zstd, lz4
    checksum_algorithm: str = "xxh64"  # md5, sha256, xxh64
    
    # 并发配置
    max_workers: int = 4
    chunk_size_mb: int = 64
    
    # 恢复配置
    allow_partial_restore: bool = True
    verify_after_restore: bool = True
    
    # 保留策略
    local_full_backups_to_keep: int = 7
    local_incremental_backups_to_keep: int = 24
    remote_full_backups_to_keep: int = 30
    remote_incremental_backups_to_keep: int = 90


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    backup_type: BackupType
    created_at: str
    status: str  # in_progress, completed, failed
    size_bytes: int = 0
    file_count: int = 0
    checksum: str = ""
    parent_backup_id: Optional[str] = None  # 增量备份的父备份
    files: List[dict] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at,
            "status": self.status,
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
            "checksum": self.checksum,
            "parent_backup_id": self.parent_backup_id,
            "files": self.files,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BackupMetadata":
        data["backup_type"] = BackupType(data["backup_type"])
        return cls(**data)


@dataclass
class RestoreConfig:
    """恢复配置"""
    backup_id: Optional[str] = None
    target_path: str = "./data/memory"
    overwrite_existing: bool = True
    parallel_restore: bool = True
    verify_checksums: bool = True
    
    # 选择性恢复
    specific_files: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
```

### storage/base.py - 存储后端抽象

```python
"""
存储后端抽象基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator, Optional
import os


@dataclass
class StorageObject:
    """存储对象信息"""
    key: str
    size: int
    last_modified: float
    etag: Optional[str] = None


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    def write(self, key: str, data: BinaryIO, metadata: Optional[dict] = None) -> None:
        """写入文件"""
        pass
    
    @abstractmethod
    def read(self, key: str) -> BinaryIO:
        """读取文件"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """删除文件"""
        pass
    
    @abstractmethod
    def list(self, prefix: str = "") -> Iterator[StorageObject]:
        """列出文件"""
        pass
    
    @abstractmethod
    def get_size(self, key: str) -> int:
        """获取文件大小"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str) -> dict:
        """获取文件元数据"""
        pass
    
    def ensure_directory(self, key: str) -> None:
        """确保目录存在"""
        pass
```

### storage/local.py - 本地存储实现

```python
"""
本地存储后端实现
"""
from pathlib import Path
from typing import BinaryIO, Iterator, Optional
import os
import shutil
import tempfile

from .base import StorageBackend, StorageObject


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储后端"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _full_path(self, key: str) -> Path:
        """获取完整路径"""
        return self.base_path / key.lstrip("/")
    
    def write(self, key: str, data: BinaryIO, metadata: Optional[dict] = None) -> None:
        full_path = self._full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            shutil.copyfileobj(data, f)
        
        # 保存元数据
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + ".meta")
            import json
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
    
    def read(self, key: str) -> BinaryIO:
        full_path = self._full_path(key)
        return open(full_path, "rb")
    
    def exists(self, key: str) -> bool:
        return self._full_path(key).exists()
    
    def delete(self, key: str) -> None:
        full_path = self._full_path(key)
        if full_path.exists():
            full_path.unlink()
        
        # 删除元数据文件
        meta_path = full_path.with_suffix(full_path.suffix + ".meta")
        if meta_path.exists():
            meta_path.unlink()
    
    def list(self, prefix: str = "") -> Iterator[StorageObject]:
        full_prefix = self._full_path(prefix)
        
        for root, dirs, files in os.walk(full_prefix):
            for filename in files:
                if filename.endswith(".meta"):
                    continue
                file_path = Path(root) / filename
                rel_key = str(file_path.relative_to(self.base_path))
                stat = file_path.stat()
                
                yield StorageObject(
                    key=rel_key,
                    size=stat.st_size,
                    last_modified=stat.st_mtime,
                )
    
    def get_size(self, key: str) -> int:
        return self._full_path(key).stat().st_size
    
    def get_metadata(self, key: str) -> dict:
        meta_path = self._full_path(key).with_suffix(".meta")
        if meta_path.exists():
            import json
            with open(meta_path) as f:
                return json.load(f)
        return {}
    
    def ensure_directory(self, key: str) -> None:
        self._full_path(key).parent.mkdir(parents=True, exist_ok=True)
```

### storage/s3.py - S3存储实现

```python
"""
S3 存储后端实现
"""
from io import BytesIO
from typing import BinaryIO, Iterator, Optional
import logging
import os

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .base import StorageBackend, StorageObject

logger = logging.getLogger(__name__)


class S3StorageBackend(StorageBackend):
    """AWS S3 存储后端"""
    
    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        
        self.s3_client = boto3.client(
            "s3",
            region_name=region_name or os.getenv("AWS_REGION"),
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    
    def _full_key(self, key: str) -> str:
        """获取完整的 S3 key"""
        if self.prefix:
            return f"{self.prefix}/{key.lstrip('/')}"
        return key.lstrip("/")
    
    def write(self, key: str, data: BinaryIO, metadata: Optional[dict] = None) -> None:
        full_key = self._full_key(key)
        
        # 转换为 bytes 以获取大小
        if hasattr(data, "read"):
            content = data.read()
            data = BytesIO(content)
        
        extra_args = {}
        if metadata:
            # S3 元数据限制
            safe_metadata = {
                k: str(v)[:1024] for k, v in metadata.items()
            }
            extra_args["Metadata"] = safe_metadata
        
        self.s3_client.upload_fileobj(
            data,
            self.bucket,
            full_key,
            ExtraArgs=extra_args,
        )
        logger.debug(f"Uploaded {full_key} to s3://{self.bucket}")
    
    def read(self, key: str) -> BinaryIO:
        full_key = self._full_key(key)
        
        response = self.s3_client.get_object(Bucket=self.bucket, Key=full_key)
        return response["Body"]
    
    def exists(self, key: str) -> bool:
        full_key = self._full_key(key)
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=full_key)
            return True
        except ClientError:
            return False
    
    def delete(self, key: str) -> None:
        full_key = self._full_key(key)
        self.s3_client.delete_object(Bucket=self.bucket, Key=full_key)
        logger.debug(f"Deleted s3://{self.bucket}/{full_key}")
    
    def list(self, prefix: str = "") -> Iterator[StorageObject]:
        full_prefix = self._full_key(prefix)
        
        paginator = self.s3_client.get_paginator("list_objects_v2")
        
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full_prefix):
            if "Contents" not in page:
                continue
            
            for obj in page["Contents"]:
                yield StorageObject(
                    key=obj["Key"],
                    size=obj["Size"],
                    last_modified=obj["LastModified"].timestamp(),
                    etag=obj.get("ETag", "").strip('"'),
                )
    
    def get_size(self, key: str) -> int:
        full_key = self._full_key(key)
        response = self.s3_client.head_object(Bucket=self.bucket, Key=full_key)
        return response["ContentLength"]
    
    def get_metadata(self, key: str) -> dict:
        full_key = self._full_key(key)
        response = self.s3_client.head_object(Bucket=self.bucket, Key=full_key)
        return response.get("Metadata", {})
    
    def ensure_directory(self, key: str) -> None:
        """S3 不需要目录操作，忽略"""
        pass
    
    def copy(self, source_key: str, dest_key: str) -> None:
        """复制对象"""
        self.s3_client.copy(
            {"Bucket": self.bucket, "Key": source_key},
            self.bucket,
            self._full_key(dest_key),
        )
```

### metadata.py - 备份元数据管理

```python
"""
备份元数据管理器
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
import logging

from config import BackupMetadata, BackupType

logger = logging.getLogger(__name__)


class MetadataStore:
    """备份元数据存储（SQLite）"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    checksum TEXT,
                    parent_backup_id TEXT,
                    files_json TEXT,
                    error_message TEXT,
                    FOREIGN KEY (parent_backup_id) REFERENCES backups(backup_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_created_at 
                ON backups(created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_status 
                ON backups(status)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save(self, metadata: BackupMetadata) -> None:
        """保存备份元数据"""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backups 
                    (backup_id, backup_type, created_at, status, size_bytes, 
                     file_count, checksum, parent_backup_id, files_json, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.backup_id,
                    metadata.backup_type.value,
                    metadata.created_at,
                    metadata.status,
                    metadata.size_bytes,
                    metadata.file_count,
                    metadata.checksum,
                    metadata.parent_backup_id,
                    json.dumps(metadata.files),
                    metadata.error_message,
                ))
                conn.commit()
        
        logger.debug(f"Saved metadata for backup {metadata.backup_id}")
    
    def get(self, backup_id: str) -> Optional[BackupMetadata]:
        """获取备份元数据"""
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM backups WHERE backup_id = ?",
                    (backup_id,)
                ).fetchone()
        
        if row is None:
            return None
        
        return self._row_to_metadata(row)
    
    def get_latest(self, backup_type: Optional[BackupType] = None) -> Optional[BackupMetadata]:
        """获取最新的备份"""
        with self._lock:
            with self._get_connection() as conn:
                if backup_type:
                    row = conn.execute("""
                        SELECT * FROM backups 
                        WHERE backup_type = ? AND status = 'completed'
                        ORDER BY created_at DESC LIMIT 1
                    """, (backup_type.value,)).fetchone()
                else:
                    row = conn.execute("""
                        SELECT * FROM backups 
                        WHERE status = 'completed'
                        ORDER BY created_at DESC LIMIT 1
                    """).fetchone()
        
        if row is None:
            return None
        
        return self._row_to_metadata(row)
    
    def get_chain_to_full(self, backup_id: str) -> List[BackupMetadata]:
        """获取从指定备份到最近全量备份的链"""
        chain = []
        current_id = backup_id
        
        with self._lock:
            with self._get_connection() as conn:
                while current_id:
                    row = conn.execute(
                        "SELECT * FROM backups WHERE backup_id = ?",
                        (current_id,)
                    ).fetchone()
                    
                    if row is None:
                        break
                    
                    chain.append(self._row_to_metadata(row))
                    current_id = row["parent_backup_id"]
        
        return list(reversed(chain))
    
    def get_all(self, limit: Optional[int] = None) -> List[BackupMetadata]:
        """获取所有备份"""
        with self._lock:
            with self._get_connection() as conn:
                query = "SELECT * FROM backups ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                rows = conn.execute(query).fetchall()
        
        return [self._row_to_metadata(row) for row in rows]
    
    def get_backup_ids_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[str]:
        """获取时间范围内的备份ID"""
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT backup_id FROM backups
                    WHERE created_at BETWEEN ? AND ?
                    AND status = 'completed'
                    ORDER BY created_at ASC
                """, (start_time.isoformat(), end_time.isoformat())).fetchall()
        
        return [row["backup_id"] for row in rows]
    
    def delete(self, backup_id: str) -> bool:
        """删除备份元数据"""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM backups WHERE backup_id = ?",
                    (backup_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
    
    def get_statistics(self) -> dict:
        """获取备份统计信息"""
        with self._lock:
            with self._get_connection() as conn:
                stats = {}
                
                # 总备份数
                row = conn.execute("SELECT COUNT(*) as count FROM backups").fetchone()
                stats["total_backups"] = row["count"]
                
                # 完成的备份数
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM backups WHERE status = 'completed'"
                ).fetchone()
                stats["completed_backups"] = row["count"]
                
                # 失败的备份数
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM backups WHERE status = 'failed'"
                ).fetchone()
                stats["failed_backups"] = row["count"]
                
                # 总大小
                row = conn.execute(
                    "SELECT SUM(size_bytes) as total FROM backups WHERE status = 'completed'"
                ).fetchone()
                stats["total_size_bytes"] = row["total"] or 0
                
                # 按类型统计
                rows = conn.execute("""
                    SELECT backup_type, COUNT(*) as count, SUM(size_bytes) as total
                    FROM backups WHERE status = 'completed'
                    GROUP BY backup_type
                """).fetchall()
                
                stats["by_type"] = {
                    row["backup_type"]: {
                        "count": row["count"],
                        "total_bytes": row["total"] or 0,
                    }
                    for row in rows
                }
                
                return stats
    
    def _row_to_metadata(self, row: sqlite3.Row) -> BackupMetadata:
        """将数据库行转换为元数据对象"""
        return BackupMetadata(
            backup_id=row["backup_id"],
            backup_type=BackupType(row["backup_type"]),
            created_at=row["created_at"],
            status=row["status"],
            size_bytes=row["size_bytes"],
            file_count=row["file_count"],
            checksum=row["checksum"],
            parent_backup_id=row["parent_backup_id"],
            files=json.loads(row["files_json"] or "[]"),
            error_message=row["error_message"],
        )
```

### checksum.py - 校验和计算

```python
"""
文件校验和计算模块
"""
import hashlib
import logging
import os
import xxhash
from pathlib import Path
from typing import BinaryIO, Generator, Optional

logger = logging.getLogger(__name__)


class ChecksumCalculator:
    """校验和计算器"""
    
    SUPPORTED_ALGORITHMS = {
        "md5": hashlib.md5,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "xxh64": xxhash.xxh64,
    }
    
    def __init__(self, algorithm: str = "xxh64", chunk_size: int = 8192):
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. "
                f"Supported: {list(self.SUPPORTED_ALGORITHMS.keys())}"
            )
        
        self.algorithm = algorithm
        self.chunk_size = chunk_size
    
    def hash_file(self, file_path: Path) -> str:
        """计算文件的校验和"""
        hasher = self._create_hasher()
        
        with open(file_path, "rb") as f:
            for chunk in self._read_chunks(f):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def hash_bytes(self, data: bytes) -> str:
        """计算字节数据的校验和"""
        hasher = self._create_hasher()
        hasher.update(data)
        return hasher.hexdigest()
    
    def hash_stream(self, stream: BinaryIO) -> str:
        """计算流数据的校验和"""
        hasher = self._create_hasher()
        
        while True:
            chunk = stream.read(self.chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def verify_file(self, file_path: Path, expected_checksum: str) -> bool:
        """验证文件校验和"""
        actual = self.hash_file(file_path)
        return actual == expected_checksum
    
    def compute_manifest(self, directory: Path) -> dict:
        """
        计算目录下所有文件的校验和清单
        返回: {relative_path: checksum}
        """
        manifest = {}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(directory))
                manifest[rel_path] = self.hash_file(file_path)
        
        return manifest
    
    def verify_manifest(self, directory: Path, manifest: dict) -> tuple[bool, list]:
        """
        验证目录下的文件是否符合清单
        返回: (是否全部通过, 失败文件列表)
        """
        failed = []
        
        for rel_path, expected_checksum in manifest.items():
            file_path = directory / rel_path
            
            if not file_path.exists():
                failed.append(f"{rel_path}: file missing")
                continue
            
            actual = self.hash_file(file_path)
            if actual != expected_checksum:
                failed.append(f"{rel_path}: checksum mismatch")
        
        # 检查多余文件
        current_files = {
            str(f.relative_to(directory))
            for f in directory.rglob("*")
            if f.is_file()
        }
        
        for rel_path in current_files:
            if rel_path not in manifest:
                failed.append(f"{rel_path}: unexpected file")
        
        return len(failed) == 0, failed
    
    def _create_hasher(self):
        """创建哈希对象"""
        if self.algorithm == "xxh64":
            return xxhash.xxh64()
        return self.SUPPORTED_ALGORITHMS[self.algorithm]()
    
    def _read_chunks(self, file: BinaryIO) -> Generator[bytes, None, None]:
        """分块读取文件"""
        while True:
            chunk = file.read(self.chunk_size)
            if not chunk:
                break
            yield chunk


class BackupChecksumCalculator:
    """备份文件校验和计算器"""
    
    def __init__(self, algorithm: str = "xxh64", chunk_size: int = 8192):
        self.checksum_calc = ChecksumCalculator(algorithm, chunk_size)
    
    def calculate_backup_checksum(self, backup_file: Path) -> dict:
        """
        计算备份文件的校验和信息
        返回包含文件校验和和分块校验和的信息
        """
        info = {
            "file_checksum": self.checksum_calc.hash_file(backup_file),
            "file_size": backup_file.stat().st_size,
        }
        
        # 计算分块校验和用于大文件验证
        chunk_checksums = []
        with open(backup_file, "rb") as f:
            for i, chunk in enumerate(self.checksum_calc._read_chunks(f)):
                chunk_hash = self.checksum_calc.hash_bytes(chunk)
                chunk_checksums.append({
                    "chunk_index": i,
                    "checksum": chunk_hash,
                    "size": len(chunk),
                })
        
        info["chunks"] = chunk_checksums
        return info
    
    def verify_backup(self, backup_file: Path, expected_info: dict) -> bool:
        """验证备份文件的完整性"""
        if not backup_file.exists():
            return False
        
        actual_checksum = self.checksum_calc.hash_file(backup_file)
        return actual_checksum == expected_info["file_checksum"]
```

### backup.py - 核心备份逻辑

```python
"""
核心备份模块
"""
import archive as tarfile
import compressed as gzip
import datetime
import io
import logging
import os
import re
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import json

from config import (
    BackupConfig,
    BackupMetadata,
    BackupType,
    StorageConfig,
)
from checksum import ChecksumCalculator, BackupChecksumCalculator
from storage.base import StorageBackend
from storage.local import LocalStorageBackend
from metadata import MetadataStore

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """备份结果"""
    success: bool
    backup_id: str
    backup_type: BackupType
    size_bytes: int
    file_count: int
    checksum: str
    duration_seconds: float
    error_message: Optional[str] = None


class IncrementalBackupTracker:
    """增量备份追踪器 - 记录文件变更"""
    
    def __init__(self, tracker_file: Path):
        self.tracker_file = tracker_file
        self.file_hashes: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._load()
    
    def _load(self) -> None:
        """从文件加载追踪状态"""
        if self.tracker_file.exists():
            with open(self.tracker_file) as f:
                data = json.load(f)
                self.file_hashes = data.get("file_hashes", {})
    
    def save(self) -> None:
        """保存追踪状态"""
        with self._lock:
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_file, "w") as f:
                json.dump({
                    "file_hashes": self.file_hashes,
                    "last_updated": datetime.datetime.now().isoformat(),
                }, f, indent=2)
    
    def get_changed_files(
        self,
        data_path: Path,
        checksum_calc: ChecksumCalculator,
    ) -> Set[str]:
        """
        获取变更的文件集合
        返回变更文件的相对路径集合
        """
        changed = set()
        
        for file_path in data_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            rel_path = str(file_path.relative_to(data_path))
            
            try:
                current_hash = checksum_calc.hash_file(file_path)
                
                if rel_path not in self.file_hashes:
                    changed.add(rel_path)
                    logger.debug(f"New file: {rel_path}")
                elif self.file_hashes[rel_path] != current_hash:
                    changed.add(rel_path)
                    logger.debug(f"Modified file: {rel_path}")
            except Exception as e:
                logger.warning(f"Error checking {rel_path}: {e}")
        
        # 检查被删除的文件（从追踪中移除）
        current_files = {
            str(f.relative_to(data_path))
            for f in data_path.rglob("*")
            if f.is_file()
        }
        
        for tracked_file in list(self.file_hashes.keys()):
            if tracked_file not in current_files:
                del self.file_hashes[tracked_file]
                logger.debug(f"Deleted file: {tracked_file}")
        
        return changed
    
    def update_hashes(self, files: List[str], data_path: Path, checksum_calc: ChecksumCalculator) -> None:
        """更新文件哈希"""
        for rel_path in files:
            file_path = data_path / rel_path
            try:
                self.file_hashes[rel_path] = checksum_calc.hash_file(file_path)
            except Exception as e:
                logger.warning(f"Error hashing {rel_path}: {e}")


class UnifiedMemoryBackup:
    """Unified Memory 备份主类"""
    
    def __init__(
        self,
        backup_config: BackupConfig,
        storage_config: StorageConfig,
        metadata_store: MetadataStore,
    ):
        self.config = backup_config
        self.storage_config = storage_config
        self.metadata_store = metadata_store
        
        # 初始化存储后端
        self.storage = self._create_storage_backend()
        
        # 校验和计算器
        self.checksum_calc = ChecksumCalculator(
            algorithm=backup_config.checksum_algorithm
        )
        self.backup_checksum_calc = BackupChecksumCalculator(
            algorithm=backup_config.checksum_algorithm
        )
        
        # 增量备份追踪器
        self.tracker_file = Path(f"{storage_config.base_path}/.tracker/state.json")
        self.tracker = IncrementalBackupTracker(self.tracker_file)
        
        # 确保目录存在
        Path(storage_config.base_path).mkdir(parents=True, exist_ok=True)
    
    def _create_storage_backend(self) -> StorageBackend:
        """创建存储后端"""
        if self.storage_config.backend.value == "local":
            return LocalStorageBackend(self.storage_config.base_path)
        else:
            from storage.s3 import S3StorageBackend
            return S3StorageBackend(
                bucket=self.storage_config.s3_bucket or "",
                prefix=self.storage_config.s3_prefix,
            )
    
    def create_backup(self, backup_type: Optional[BackupType] = None) -> BackupResult:
        """
        创建备份
        
        Args:
            backup_type: 备份类型，如果不指定则根据时间自动判断
            
        Returns:
            BackupResult: 备份结果
        """
        start_time = datetime.datetime.now()
        backup_id = f"backup-{start_time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # 自动判断备份类型
        if backup_type is None:
            backup_type = self._determine_backup_type(start_time)
        
        logger.info(f"Starting {backup_type.value} backup: {backup_id}")
        
        # 创建元数据记录
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=start_time.isoformat(),
            status="in_progress",
        )
        self.metadata_store.save(metadata)
        
        try:
            # 执行备份
            if backup_type == BackupType.FULL:
                result = self._create_full_backup(backup_id)
            else:
                # 获取最新的全量备份作为增量备份的父备份
                latest_full = self.metadata_store.get_latest(BackupType.FULL)
                metadata.parent_backup_id = latest_full.backup_id if latest_full else None
                result = self._create_incremental_backup(backup_id)
            
            # 更新元数据
            metadata.status = "completed"
            metadata.size_bytes = result.size_bytes
            metadata.file_count = result.file_count
            metadata.checksum = result.checksum
            self.metadata_store.save(metadata)
            
            # 更新追踪器
            self.tracker.save()
            
            duration = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(
                f"Backup completed: {backup_id} "
                f"({result.file_count} files, {result.size_bytes} bytes, {duration:.1f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Backup failed: {backup_id}")
            metadata.status = "failed"
            metadata.error_message = str(e)
            self.metadata_store.save(metadata)
            
            return BackupResult(
                success=False,
                backup_id=backup_id,
                backup_type=backup_type,
                size_bytes=0,
                file_count=0,
                checksum="",
                duration_seconds=(datetime.datetime.now() - start_time).total_seconds(),
                error_message=str(e),
            )
    
    def _determine_backup_type(self, now: datetime.datetime) -> BackupType:
        """根据当前时间判断备份类型"""
        if now.hour == self.config.full_backup_hour and now.minute < 30:
            return BackupType.FULL
        return BackupType.INCREMENTAL
    
    def _create_full_backup(self, backup_id: str) -> BackupResult:
        """创建全量备份"""
        data_path = Path(self.config.memory_data_path)
        
        if not data_path.exists():
            raise ValueError(f"Data path does not exist: {data_path}")
        
        # 创建临时备份文件
        temp_file = Path(f"/tmp/{backup_id}.tar.gz")
        
        try:
            # 创建压缩归档
            with gzip.open(temp_file, "wb") as tar_gz:
                with tarfile.open(fileobj=tar_gz, mode="w") as tar:
                    tar.add(data_path, arcname="data")
            
            # 计算校验和
            checksum = self.checksum_calc.hash_file(temp_file)
            
            # 统计信息
            file_count = sum(1 for _ in data_path.rglob("*") if _.is_file())
            size_bytes = temp_file.stat().st_size
            
            # 上传到存储
            storage_key = f"backups/{backup_id}/backup.tar.gz"
            with open(temp_file, "rb") as f:
                self.storage.write(storage_key, f, {
                    "backup_id": backup_id,
                    "backup_type": "full",
                    "checksum": checksum,
                })
            
            # 更新追踪器
            self.tracker.update_hashes(
                files=[
                    str(f.relative_to(data_path))
                    for f in data_path.rglob("*")
                    if f.is_file()
                ],
                data_path=data_path,
                checksum_calc=self.checksum_calc,
            )
            
            return BackupResult(
                success=True,
                backup_id=backup_id,
                backup_type=BackupType.FULL,
                size_bytes=size_bytes,
                file_count=file_count,
                checksum=checksum,
                duration_seconds=0,
            )
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def _create_incremental_backup(self, backup_id: str) -> BackupResult:
        """创建增量备份"""
        data_path = Path(self.config.memory_data_path)
        
        if not data_path.exists():
            raise ValueError(f"Data path does not exist: {data_path}")
        
        # 获取变更的文件
        changed_files = self.tracker.get_changed_files(data_path, self.checksum_calc)
        
        if not changed_files:
            logger.info("No changes detected, skipping incremental backup")
            return BackupResult(
                success=True,
                backup_id=backup_id,
                backup_type=BackupType.INCREMENTAL,
                size_bytes=0,
                file_count=0,
                checksum="",
                duration_seconds=0,
            )
        
        logger.info(f"Incremental backup: {len(changed_files)} changed files")
        
        # 创建变更文件列表
        manifest = {
            "backup_id": backup_id,
            "backup_type": "incremental",
            "files": [],
        }
        
        temp_dir = Path(f"/tmp/{backup_id}-files")
        temp_dir.mkdir(exist_ok=True)
        
        try:
