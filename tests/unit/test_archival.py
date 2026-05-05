"""
Archival 单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from archival.archival_manager import ArchivalManager, ArchiveTier, ArchivalConfig
from archival.cold_storage import LocalColdStorage


class TestArchivalConfig:
    def test_default_config(self):
        config = ArchivalConfig()
        assert config.default_tier == ArchiveTier.WARM
        assert config.auto_archive_enabled is True


class TestArchivalManager:
    def test_archive_memory(self):
        config = ArchivalConfig()
        manager = ArchivalManager(config)
        memory_data = {"id": "mem-123", "content": "Test", "created_at": datetime.now().isoformat()}
        archive = manager.archive_memory("mem-123", memory_data)
        assert archive.memory_id == "mem-123"
    
    def test_get_tier_for_age(self):
        config = ArchivalConfig()
        manager = ArchivalManager(config)
        assert manager.get_tier_for_age(1) == ArchiveTier.HOT
        assert manager.get_tier_for_age(10) == ArchiveTier.WARM
        assert manager.get_tier_for_age(60) == ArchiveTier.COLD
        assert manager.get_tier_for_age(400) == ArchiveTier.FROZEN
    
    def test_restore_memory(self):
        config = ArchivalConfig()
        manager = ArchivalManager(config)
        memory_data = {"id": "mem-123", "created_at": datetime.now().isoformat()}
        manager.archive_memory("mem-123", memory_data)
        restored = manager.restore_memory("mem-123")
        assert restored is not None
    
    def test_archive_stats(self):
        config = ArchivalConfig()
        manager = ArchivalManager(config)
        for i in range(5):
            manager.archive_memory(f"mem-{i}", {"id": f"mem-{i}", "created_at": datetime.now().isoformat()})
        stats = manager.get_archive_stats()
        assert stats["total_archives"] == 5


class TestColdStorage:
    def test_local_cold_storage(self, tmp_path):
        storage = LocalColdStorage(str(tmp_path))
        data = b"Test data"
        assert storage.store("archive/test", data) is True
        assert storage.retrieve("archive/test") == data
        assert storage.exists("archive/test") is True
        assert storage.delete("archive/test") is True
        assert storage.exists("archive/test") is False
