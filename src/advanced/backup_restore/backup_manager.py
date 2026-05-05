"""
备份管理器
"""
import json
import logging
import shutil
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from .config import BackupConfig, BackupType
from .storage import LocalStorage

logger = logging.getLogger(__name__)


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    backup_type: BackupType
    created_at: str
    status: BackupStatus
    size_bytes: int = 0
    file_count: int = 0
    checksum: str = ""
    parent_backup_id: Optional[str] = None
    files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        data['backup_type'] = BackupType(data['backup_type'])
        data['status'] = BackupStatus(data['status'])
        return cls(**data)


class BackupManager:
    """备份管理器"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.storage = LocalStorage(config.backup_path)
        self._backup_history: List[BackupMetadata] = []
        self._load_history()
    
    def _load_history(self) -> None:
        """加载备份历史"""
        history_file = Path(self.config.backup_path) / "backup_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
                self._backup_history = [
                    BackupMetadata.from_dict(item) for item in data
                ]
    
    def _save_history(self) -> None:
        """保存备份历史"""
        history_file = Path(self.config.backup_path) / "backup_history.json"
        with open(history_file, 'w') as f:
            json.dump(
                [m.to_dict() for m in self._backup_history],
                f,
                indent=2
            )
    
    def create_backup(self, backup_type: Optional[BackupType] = None) -> BackupMetadata:
        """创建备份"""
        if backup_type is None:
            backup_type = self.config.backup_type
        
        # 生成备份ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}_{backup_type.value}"
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=datetime.now().isoformat(),
            status=BackupStatus.PENDING
        )
        
        try:
            metadata.status = BackupStatus.RUNNING
            logger.info(f"Starting backup {backup_id}")
            
            # 执行备份
            files = self._perform_backup(backup_id, backup_type)
            
            # 计算元数据
            metadata.files = files
            metadata.file_count = len(files)
            metadata.size_bytes = self._calculate_size(files)
            metadata.checksum = self._calculate_checksum(files)
            metadata.status = BackupStatus.COMPLETED
            
            # 获取父备份
            if backup_type == BackupType.INCREMENTAL:
                metadata.parent_backup_id = self._get_latest_full_backup_id()
            
            logger.info(f"Backup {backup_id} completed: {metadata.file_count} files, {metadata.size_bytes} bytes")
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"Backup {backup_id} failed: {e}")
        
        self._backup_history.append(metadata)
        self._save_history()
        
        return metadata
    
    def _perform_backup(self, backup_id: str, backup_type: BackupType) -> List[str]:
        """执行备份操作"""
        source = Path(self.config.data_path)
        dest = Path(self.config.backup_path) / backup_id
        
        if not source.exists():
            raise FileNotFoundError(f"Data path not found: {source}")
        
        # 创建备份目录
        dest.mkdir(parents=True, exist_ok=True)
        
        files = []
        
        if backup_type == BackupType.FULL:
            # 全量备份：复制所有文件
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(source)
                    dest_file = dest / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file)
                    files.append(str(rel_path))
        else:
            # 增量备份：只复制修改的文件
            last_backup = self._get_last_backup()
            if last_backup:
                # 获取上次备份后的修改文件
                files = self._get_incremental_files(source, last_backup)
                for rel_path in files:
                    src_file = source / rel_path
                    dst_file = dest / rel_path
                    if src_file.exists():
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
        
        return files
    
    def _get_incremental_files(self, source: Path, last_backup: BackupMetadata) -> List[str]:
        """获取增量文件列表"""
        files = []
        last_time = datetime.fromisoformat(last_backup.created_at)
        
        for file_path in source.rglob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > last_time:
                    files.append(str(file_path.relative_to(source)))
        
        return files
    
    def _get_latest_full_backup_id(self) -> Optional[str]:
        """获取最近的全量备份ID"""
        for backup in reversed(self._backup_history):
            if backup.backup_type == BackupType.FULL and backup.status == BackupStatus.COMPLETED:
                return backup.backup_id
        return None
    
    def _get_last_backup(self) -> Optional[BackupMetadata]:
        """获取最近的备份"""
        if self._backup_history:
            return self._backup_history[-1]
        return None
    
    def _calculate_size(self, files: List[str]) -> int:
        """计算备份大小"""
        total = 0
        backup_dir = Path(self.config.backup_path)
        for file in files:
            file_path = backup_dir / file
            if file_path.exists():
                total += file_path.stat().st_size
        return total
    
    def _calculate_checksum(self, files: List[str]) -> str:
        """计算校验和"""
        hasher = hashlib.xxh64()
        for file in sorted(files):
            hasher.update(file.encode())
        return hasher.hexdigest()
    
    def verify_backup(self, backup_id: str) -> bool:
        """验证备份"""
        for metadata in self._backup_history:
            if metadata.backup_id == backup_id:
                if metadata.status == BackupStatus.COMPLETED:
                    metadata.status = BackupStatus.VERIFIED
                    self._save_history()
                    return True
        return False
    
    def list_backups(self) -> List[BackupMetadata]:
        """列出所有备份"""
        return sorted(
            self._backup_history,
            key=lambda m: m.created_at,
            reverse=True
        )
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        backup_dir = Path(self.config.backup_path) / backup_id
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        self._backup_history = [
            m for m in self._backup_history if m.backup_id != backup_id
        ]
        self._save_history()
        return True
