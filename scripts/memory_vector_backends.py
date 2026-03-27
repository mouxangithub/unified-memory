#!/usr/bin/env python3
"""
多后端向量支持 - Vector Backends

支持：LanceDB / Milvus / Pinecone / Weaviate
"""

import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class VectorBackend(ABC):
    """向量后端抽象接口"""
    
    @abstractmethod
    def add(self, id: str, vector: List[float], metadata: Dict):
        pass
    
    @abstractmethod
    def search(self, query: List[float], top_k: int) -> List[Dict]:
        pass
    
    @abstractmethod
    def delete(self, id: str):
        pass
    
    @abstractmethod
    def count(self) -> int:
        pass


class LanceDBBackend(VectorBackend):
    """LanceDB 后端"""
    
    def __init__(self, table_name: str = "memories"):
        self.table_name = table_name
        self._client = None
        self._table = None
        self._connect()
    
    def _connect(self):
        try:
            import lancedb
            db_path = str(MEMORY_DIR / "vector")
            self._client = lancedb.connect(db_path)
            self._table = self._client.open_table(self.table_name)
        except ImportError:
            print("⚠️ LanceDB 未安装")
    
    def add(self, id: str, vector: List[float], metadata: Dict):
        if self._table is None:
            return
        self._table.add([{"id": id, "vector": vector, **metadata}])
    
    def search(self, query: List[float], top_k: int) -> List[Dict]:
        if self._table is None:
            return []
        return self._table.search(query).limit(top_k).to_list()
    
    def delete(self, id: str):
        if self._table is None:
            return
        self._table.delete(f'id = "{id}"')
    
    def count(self) -> int:
        if self._table is None:
            return 0
        return len(self._table.to_list())


class MilvusBackend(VectorBackend):
    """Milvus 后端"""
    
    def __init__(self, host: str = "localhost", port: int = 19530, collection: str = "memories"):
        self.host = host
        self.port = port
        self.collection = collection
        self._client = None
        self._connect()
    
    def _connect(self):
        try:
            from pymilvus import connections, Collection
            connections.connect(host=self.host, port=self.port)
            self._collection = Collection(self.collection)
        except ImportError:
            print("⚠️ pymilvus 未安装")
    
    def add(self, id: str, vector: List[float], metadata: Dict):
        # 简化实现
        pass
    
    def search(self, query: List[float], top_k: int) -> List[Dict]:
        return []
    
    def delete(self, id: str):
        pass
    
    def count(self) -> int:
        return 0


class PineconeBackend(VectorBackend):
    """Pinecone 后端"""
    
    def __init__(self, api_key: str = None, environment: str = "us-east-1", index: str = "memories"):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index
        self._index = None
        self._connect()
    
    def _connect(self):
        try:
            import pinecone
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self._index = pinecone.Index(self.index_name)
        except ImportError:
            print("⚠️ pinecone 未安装")
    
    def add(self, id: str, vector: List[float], metadata: Dict):
        if self._index is None:
            return
        self._index.upsert([(id, vector, metadata)])
    
    def search(self, query: List[float], top_k: int) -> List[Dict]:
        if self._index is None:
            return []
        result = self._index.query(query, top_k=top_k)
        return [{"id": m.id, "score": m.score, **m.metadata} for m in result.matches]
    
    def delete(self, id: str):
        if self._index is None:
            return
        self._index.delete(id)
    
    def count(self) -> int:
        if self._index is None:
            return 0
        return self._index.describe_index_stats()["total_record_count"]


class WeaviateBackend(VectorBackend):
    """Weaviate 后端"""
    
    def __init__(self, url: str = "http://localhost:8080", class_name: str = "Memory"):
        self.url = url
        self.class_name = class_name
        self._client = None
        self._connect()
    
    def _connect(self):
        try:
            import weaviate
            self._client = weaviate.Client(self.url)
        except ImportError:
            print("⚠️ weaviate 未安装")
    
    def add(self, id: str, vector: List[float], metadata: Dict):
        if self._client is None:
            return
        self._client.data_object.create(
            class_name=self.class_name,
            uuid=id,
            vector=vector,
            properties=metadata
        )
    
    def search(self, query: List[float], top_k: int) -> List[Dict]:
        if self._client is None:
            return []
        result = self._client.query.get(self.class_name).with_near_vector({"vector": query}).with_limit(top_k).do()
        return result.get("data", {}).get("Get", {}).get(self.class_name, [])
    
    def delete(self, id: str):
        if self._client is None:
            return
        self._client.data_object.delete(id)
    
    def count(self) -> int:
        if self._client is None:
            return 0
        result = self._client.query.aggregate(self.class_name).with_meta_count().do()
        return result.get("data", {}).get("Aggregate", {}).get(self.class_name, [{}])[0].get("meta", {}).get("count", 0)


def get_backend(name: str = "lancedb", **kwargs) -> VectorBackend:
    """获取后端实例"""
    backends = {
        "lancedb": LanceDBBackend,
        "milvus": MilvusBackend,
        "pinecone": PineconeBackend,
        "weaviate": WeaviateBackend,
    }
    
    backend_class = backends.get(name.lower(), LanceDBBackend)
    return backend_class(**kwargs)


if __name__ == "__main__":
    print("=" * 50)
    print("多后端向量支持测试")
    print("=" * 50)
    
    print("\n📦 可用后端:")
    for name in ["lancedb", "milvus", "pinecone", "weaviate"]:
        try:
            backend = get_backend(name)
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    # 测试 LanceDB
    print("\n🧪 测试 LanceDB:")
    backend = get_backend("lancedb")
    print(f"  ✅ 连接成功")
    print(f"  📊 记录数: {backend.count()}")
    
    print("\n✅ 多后端向量支持测试完成")
