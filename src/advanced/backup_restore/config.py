"""
备份恢复配置模块
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class StorageBackend(Enum):
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"


@dataclass
class BackupConfig:
    """备份配置"""
    # 源数据路径
    data_path: str = "./data"
    
    # 备份存储路径
    backup_path: str = "./backups"
    
    # 备份类型
    backup_type: BackupType = BackupType.INCREMENTAL
    
    # 备份间隔（小时）
    incremental_interval_hours: int = 1
    
    # 全量备份间隔（天）
    full_backup_interval_days: int = 7
    
    # 保留策略
    retention_days: int = 30
    
    # 压缩
    compression_enabled: bool = True
    compression_algorithm: str = "gzip"
    
    # 加密
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    
    # 并发
    max_concurrent_workers: int = 4
    
    # 校验
    checksum_algorithm: str = "xxh64"


@dataclass
class RestoreConfig:
    """恢复配置"""
    backup_id: str
    target_path: str = "./data"
    overwrite: bool = False
    verify_checksum: bool = True
    decrypt: bool = False
    decryption_key: Optional[str] = None
