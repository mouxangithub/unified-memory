"""
版本控制模块异常定义
"""

from typing import Optional


class VersionControlError(Exception):
    """版本控制基础异常"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, details={self.details})"


class MemoryNotFoundError(VersionControlError):
    """内存记录不存在"""

    def __init__(self, memory_id: str):
        super().__init__(
            f"Memory not found: {memory_id}",
            details={"memory_id": memory_id},
        )


class VersionNotFoundError(VersionControlError):
    """版本不存在"""

    def __init__(self, memory_id: str, version: int):
        super().__init__(
            f"Version {version} not found for memory {memory_id}",
            details={"memory_id": memory_id, "version": version},
        )


class InvalidVersionError(VersionControlError):
    """无效的版本号"""

    def __init__(self, version: int, reason: str):
        super().__init__(
            f"Invalid version {version}: {reason}",
            details={"version": version, "reason": reason},
        )


class DiffComputationError(VersionControlError):
    """差异计算失败"""

    def __init__(self, reason: str, details: Optional[dict] = None):
        super().__init__(f"Diff computation failed: {reason}", details=details)


class RepositoryError(VersionControlError):
    """数据访问层错误"""

    pass