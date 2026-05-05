"""
恢复管理器
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

from .backup_manager import BackupManager, BackupMetadata
from .config import RestoreConfig

logger = logging.getLogger(__name__)


class RestoreManager:
    """恢复管理器"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
    
    def restore(
        self,
        backup_id: str,
        target_path: Optional[str] = None,
        overwrite: bool = False
    ) -> bool:
        """恢复备份"""
        # 查找备份元数据
        metadata = None
        for m in self.backup_manager._backup_history:
            if m.backup_id == backup_id:
                metadata = m
                break
        
        if not metadata:
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        if metadata.status.value not in ["completed", "verified"]:
            logger.error(f"Backup not ready for restore: {metadata.status}")
            return False
        
        # 设置目标路径
        if target_path is None:
            target_path = self.backup_manager.config.data_path
        
        target = Path(target_path)
        
        # 检查目标目录
        if target.exists() and not overwrite:
            logger.error(f"Target path exists and overwrite=False: {target}")
            return False
        
        # 执行恢复
        try:
            backup_dir = Path(self.backup_manager.config.backup_path) / backup_id
            
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True)
            
            # 复制文件
            for file_path in metadata.files:
                src = backup_dir / file_path
                dst = target / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            
            logger.info(f"Restored backup {backup_id} to {target}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def restore_incremental_chain(self, backup_id: str, target_path: str) -> bool:
        """恢复增量备份链"""
        # 获取从当前备份到全量备份的链
        chain = []
        current_id = backup_id
        
        while current_id:
            metadata = None
            for m in self.backup_manager._backup_history:
                if m.backup_id == current_id:
                    metadata = m
                    break
            
            if not metadata:
                break
            
            chain.append(metadata)
            current_id = metadata.parent_backup_id
        
        # 反向恢复（从全量开始）
        chain.reverse()
        
        for metadata in chain:
            logger.info(f"Restoring {metadata.backup_id}...")
            if not self.restore(metadata.backup_id, target_path, overwrite=True):
                return False
        
        return True
