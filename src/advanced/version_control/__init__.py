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