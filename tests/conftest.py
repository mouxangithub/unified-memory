"""
pytest 配置和 fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def memory_data_dir(tmp_path):
    """创建临时内存数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def backup_dir(tmp_path):
    """创建临时备份目录"""
    backup = tmp_path / "backups"
    backup.mkdir()
    return backup

@pytest.fixture
def archive_dir(tmp_path):
    """创建临时归档目录"""
    archive = tmp_path / "archives"
    archive.mkdir()
    return archive
