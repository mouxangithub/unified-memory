"""
存储后端抽象
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Iterator
import shutil


class StorageBackend(ABC):
    """存储后端基类"""
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查对象是否存在"""
        pass
    
    @abstractmethod
    def write(self, key: str, data: bytes) -> None:
        """写入数据"""
        pass
    
    @abstractmethod
    def read(self, key: str) -> bytes:
        """读取数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """删除对象"""
        pass
    
    @abstractmethod
    def list(self, prefix: str = "") -> Iterator[str]:
        """列出对象"""
        pass


class LocalStorage(StorageBackend):
    """本地存储后端"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _full_key(self, key: str) -> Path:
        return self.base_path / key
    
    def exists(self, key: str) -> bool:
        return self._full_key(key).exists()
    
    def write(self, key: str, data: bytes) -> None:
        path = self._full_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    
    def read(self, key: str) -> bytes:
        return self._full_key(key).read_bytes()
    
    def delete(self, key: str) -> None:
        path = self._full_key(key)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    
    def list(self, prefix: str = "") -> Iterator[str]:
        full_prefix = self.base_path / prefix
        for item in full_prefix.rglob("*"):
            if item.is_file():
                yield str(item.relative_to(self.base_path))
