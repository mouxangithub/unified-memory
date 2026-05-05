"""
Backup/Restore 单元测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backup_restore.config import BackupConfig, BackupType
from backup_restore.backup_manager import BackupManager, BackupStatus
from backup_restore.storage import LocalStorage


class TestBackupConfig:
    def test_default_config(self):
        config = BackupConfig()
        assert config.backup_type == BackupType.INCREMENTAL
        assert config.incremental_interval_hours == 1
        assert config.retention_days == 30


class TestLocalStorage:
    def test_write_read(self, tmp_path):
        storage = LocalStorage(str(tmp_path))
        storage.write("test.txt", b"Hello World")
        assert storage.read("test.txt") == b"Hello World"
    
    def test_exists(self, tmp_path):
        storage = LocalStorage(str(tmp_path))
        storage.write("test.txt", b"Hello")
        assert storage.exists("test.txt") is True
        assert storage.exists("nonexistent.txt") is False
    
    def test_delete(self, tmp_path):
        storage = LocalStorage(str(tmp_path))
        storage.write("test.txt", b"Hello")
        storage.delete("test.txt")
        assert storage.exists("test.txt") is False


class TestBackupManager:
    def test_create_backup(self, tmp_path, memory_data_dir):
        (memory_data_dir / "test.txt").write_text("Hello")
        config = BackupConfig(data_path=str(memory_data_dir), backup_path=str(tmp_path), backup_type=BackupType.FULL)
        manager = BackupManager(config)
        result = manager.create_backup(BackupType.FULL)
        assert result.status == BackupStatus.COMPLETED
        assert result.file_count >= 1
    
    def test_list_backups(self, tmp_path, memory_data_dir):
        config = BackupConfig(data_path=str(memory_data_dir), backup_path=str(tmp_path))
        manager = BackupManager(config)
        manager.create_backup()
        backups = manager.list_backups()
        assert len(backups) >= 1
