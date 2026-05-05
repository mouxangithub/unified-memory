"""
Version Control 单元测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from version_control.models import MemoryVersion
from version_control.repository import VersionRepository


class TestVersionModels:
    def test_version_creation(self):
        version = MemoryVersion(memory_id="mem-123", version=1, content="Hello")
        assert version.memory_id == "mem-123"
        assert version.version == 1
        assert version.content == "Hello"
        assert version.created_at is not None
    
    def test_version_serialization(self):
        version = MemoryVersion(memory_id="mem-123", version=1, content="Test")
        data = version.to_dict()
        assert data["memory_id"] == "mem-123"
        restored = MemoryVersion.from_dict(data)
        assert restored.memory_id == version.memory_id


class TestDiffCalculator:
    def test_no_change(self):
        from version_control.diff import DiffCalculator
        calc = DiffCalculator()
        diff = calc.compute("Hello", "Hello")
        assert diff.added == []
        assert diff.removed == []
    
    def test_addition(self):
        from version_control.diff import DiffCalculator
        calc = DiffCalculator()
        diff = calc.compute("Hello", "Hello World")
        assert len(diff.added) > 0 or len(diff.modified) > 0


class TestVersionRepository:
    def test_repo_init(self):
        repo = VersionRepository(":memory:")
        assert repo.db_path == ":memory:"
    
    def test_save_version(self):
        repo = VersionRepository(":memory:")
        version = MemoryVersion(memory_id="mem-123", version=1, content="First")
        assert repo.save(version) is True
    
    def test_get_version(self):
        repo = VersionRepository(":memory:")
        version = MemoryVersion(memory_id="mem-123", version=1, content="First")
        repo.save(version)
        retrieved = repo.get("mem-123", 1)
        assert retrieved is not None
        assert retrieved.content == "First"
    
    def test_get_latest(self):
        repo = VersionRepository(":memory:")
        for i in range(1, 4):
            repo.save(MemoryVersion(memory_id="mem-123", version=i, content=f"v{i}"))
        latest = repo.get_latest("mem-123")
        assert latest.version == 3
