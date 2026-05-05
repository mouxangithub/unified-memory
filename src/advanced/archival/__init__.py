"""
Unified Memory v5 归档模块
"""

from .archival_manager import ArchivalManager, ArchivePolicy, ArchiveTier
from .cold_storage import ColdStorageAdapter

__all__ = [
    'ArchivalManager',
    'ArchivePolicy',
    'ArchiveTier',
    'ColdStorageAdapter',
]

__version__ = "5.0.0"
