"""
归档管理器
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


class ArchiveTier(Enum):
    """归档层级"""
    HOT = "hot"       # 经常访问
    WARM = "warm"     # 偶尔访问
    COLD = "cold"     # 很少访问
    FROZEN = "frozen" # 几乎不访问


@dataclass
class ArchivePolicy:
    """归档策略"""
    name: str
    tier: ArchiveTier
    
    # 触发条件
    max_age_days: int = 30
    min_access_count: int = 0
    max_size_mb: Optional[int] = None
    
    # 归档操作
    compress: bool = True
    encryption: bool = False
    delete_after_archive: bool = False
    
    # 保留期
    retention_days: int = 365
    
    def should_archive(self, memory: Dict[str, Any]) -> bool:
        """判断是否应该归档"""
        # 检查年龄
        created_at = memory.get("created_at", "")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
                age_days = (datetime.now() - created).days
                if age_days < self.max_age_days:
                    return False
            except:
                pass
        
        # 检查访问次数
        access_count = memory.get("access_count", 0)
        if access_count > self.min_access_count:
            return False
        
        return True


class MemoryArchive:
    """记忆归档"""
    
    def __init__(
        self,
        memory_id: str,
        tier: ArchiveTier,
        archived_at: str,
        original_size: int,
        archived_size: int,
        checksum: str,
    ):
        self.memory_id = memory_id
        self.tier = tier
        self.archived_at = archived_at
        self.original_size = original_size
        self.archived_size = archived_size
        self.checksum = checksum
        self.restore_requested = False


@dataclass
class ArchivalConfig:
    """归档配置"""
    # 存储路径
    archive_path: str = "./archives"
    
    # 默认策略
    default_tier: ArchiveTier = ArchiveTier.WARM
    
    # 自动归档
    auto_archive_enabled: bool = True
    archive_check_interval_hours: int = 24
    
    # 分层阈值（天）
    hot_threshold_days: int = 7
    warm_threshold_days: int = 30
    cold_threshold_days: int = 90
    frozen_threshold_days: int = 365


class ArchivalManager:
    """归档管理器"""
    
    def __init__(self, config: ArchivalConfig):
        self.config = config
        self._archives: Dict[str, MemoryArchive] = {}
        self._policies: Dict[ArchiveTier, ArchivePolicy] = {}
        self._init_default_policies()
    
    def _init_default_policies(self) -> None:
        """初始化默认策略"""
        self._policies[ArchiveTier.HOT] = ArchivePolicy(
            name="hot",
            tier=ArchiveTier.HOT,
            max_age_days=7,
        )
        self._policies[ArchiveTier.WARM] = ArchivePolicy(
            name="warm",
            tier=ArchiveTier.WARM,
            max_age_days=30,
        )
        self._policies[ArchiveTier.COLD] = ArchivePolicy(
            name="cold",
            tier=ArchiveTier.COLD,
            max_age_days=90,
            compress=True,
        )
        self._policies[ArchiveTier.FROZEN] = ArchivePolicy(
            name="frozen",
            tier=ArchiveTier.FROZEN,
            max_age_days=365,
            compress=True,
            retention_days=2555,
        )
    
    def get_tier_for_age(self, age_days: int) -> ArchiveTier:
        """根据年龄确定层级"""
        if age_days < self.config.hot_threshold_days:
            return ArchiveTier.HOT
        elif age_days < self.config.warm_threshold_days:
            return ArchiveTier.WARM
        elif age_days < self.config.cold_threshold_days:
            return ArchiveTier.COLD
        else:
            return ArchiveTier.FROZEN
    
    def archive_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> MemoryArchive:
        """归档记忆"""
        created_at = memory_data.get("created_at", datetime.now().isoformat())
        
        try:
            created = datetime.fromisoformat(created_at)
            age_days = (datetime.now() - created).days
        except:
            age_days = 0
        
        tier = self.get_tier_for_age(age_days)
        
        archive = MemoryArchive(
            memory_id=memory_id,
            tier=tier,
            archived_at=datetime.now().isoformat(),
            original_size=len(str(memory_data)),
            archived_size=len(str(memory_data)),  # 简化，实际应压缩
            checksum=self._calculate_checksum(memory_data),
        )
        
        self._archives[memory_id] = archive
        logger.info(f"Archived {memory_id} to {tier.value} tier")
        
        return archive
    
    def restore_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """恢复记忆"""
        archive = self._archives.get(memory_id)
        
        if not archive:
            logger.warning(f"Archive not found for {memory_id}")
            return None
        
        archive.restore_requested = True
        logger.info(f"Restore requested for {memory_id}")
        
        # 实际恢复逻辑需要访问存储
        return {"memory_id": memory_id, "restored": True}
    
    def get_archive_stats(self) -> Dict[str, Any]:
        """获取归档统计"""
        stats = {
            "total_archives": len(self._archives),
            "by_tier": {
                tier.value: 0 for tier in ArchiveTier
            },
            "total_original_size": 0,
            "total_archived_size": 0,
            "restore_requests": 0,
        }
        
        for archive in self._archives.values():
            stats["by_tier"][archive.tier.value] += 1
            stats["total_original_size"] += archive.original_size
            stats["total_archived_size"] += archive.archived_size
            if archive.restore_requested:
                stats["restore_requests"] += 1
        
        return stats
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """计算校验和"""
        import hashlib
        return hashlib.xxh64(str(data).encode()).hexdigest()
    
    def get_all_archives(self, tier: Optional[ArchiveTier] = None) -> List[MemoryArchive]:
        """获取所有归档"""
        if tier:
            return [a for a in self._archives.values() if a.tier == tier]
        return list(self._archives.values())
