#!/usr/bin/env python3
"""
Memory REST API - REST 接口 v0.1.4

功能:
- FastAPI REST API
- 记忆 CRUD 操作
- 搜索、摘要、导出接口
- OpenAPI 文档自动生成

Usage:
    uvicorn memory_api:app --host 0.0.0.0 --port 8000
    
Endpoints:
    GET  /memories          # 列表
    POST /memories          # 创建
    GET  /memories/{id}     # 获取
    PUT  /memories/{id}     # 更新
    DELETE /memories/{id}   # 删除
    POST /search            # 搜索
    POST /summary/{id}      # 摘要
    POST /export/{id}       # 导出
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import sys
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# FastAPI 应用
app = FastAPI(
    title="Unified Memory API",
    description="Intelligent memory system for AI Agents",
    version="0.1.4"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class MemoryCreate(BaseModel):
    text: str
    category: Optional[str] = "general"
    importance: Optional[float] = 0.5
    tags: Optional[List[str]] = []

class MemoryUpdate(BaseModel):
    text: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[float] = None
    tags: Optional[List[str]] = None

class MemoryResponse(BaseModel):
    id: str
    text: str
    category: str
    importance: float
    tags: List[str]
    created_at: str
    embedding: Optional[List[float]] = None

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    use_vector: Optional[bool] = True

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    elapsed_ms: float

# 数据库连接
def get_db():
    """获取数据库连接"""
    if not HAS_LANCEDB:
        return None
    try:
        return lancedb.connect(str(VECTOR_DB_DIR))
    except:
        return None

def get_table():
    """获取记忆表"""
    db = get_db()
    if not db:
        return None
    try:
        return db.open_table("memories")
    except:
        return None

def get_embedding(text: str) -> Optional[List[float]]:
    """获取向量"""
    if not HAS_REQUESTS:
        return None
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("embedding")
    except:
        pass
    return None

# API 端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Unified Memory API",
        "version": "0.1.4",
        "docs": "/docs",
        "endpoints": ["/memories", "/search", "/summary", "/export"]
    }

@app.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    category: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0)
):
    """列出记忆"""
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        result = table.to_lance().to_table().to_pydict()
        memories = []
        
        count = len(result.get("id", []))
        for i in range(count):
            mem = {
                "id": result["id"][i] if len(result["id"]) > i else "",
                "text": result["text"][i] if len(result["text"]) > i else "",
                "category": result["category"][i] if len(result["category"]) > i else "general",
                "importance": result["importance"][i] if len(result["importance"]) > i else 0.5,
                "tags": result["tags"][i] if len(result["tags"]) > i and result["tags"][i] else [],
                "created_at": result["created_at"][i] if len(result["created_at"]) > i else "",
                "embedding": result["embedding"][i] if len(result["embedding"]) > i else None
            }
            
            if category is None or mem["category"] == category:
                memories.append(mem)
        
        return memories[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """获取单个记忆"""
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        result = table.to_lance().to_table().to_pydict()
        count = len(result.get("id", []))
        
        for i in range(count):
            if result["id"][i] == memory_id:
                return {
                    "id": result["id"][i],
                    "text": result["text"][i],
                    "category": result["category"][i],
                    "importance": result["importance"][i],
                    "tags": result["tags"][i] if result["tags"][i] else [],
                    "created_at": result["created_at"][i],
                    "embedding": result["embedding"][i]
                }
        
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories", response_model=MemoryResponse)
async def create_memory(memory: MemoryCreate):
    """创建记忆"""
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        memory_id = str(uuid.uuid4())
        embedding = get_embedding(memory.text)
        created_at = datetime.now().isoformat()
        
        table.add([{
            "id": memory_id,
            "text": memory.text,
            "category": memory.category,
            "importance": memory.importance,
            "tags": memory.tags,
            "created_at": created_at,
            "embedding": embedding or []
        }])
        
        return {
            "id": memory_id,
            "text": memory.text,
            "category": memory.category,
            "importance": memory.importance,
            "tags": memory.tags,
            "created_at": created_at,
            "embedding": embedding
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, update: MemoryUpdate):
    """更新记忆"""
    # LanceDB 不支持直接更新，需要删除后重新添加
    raise HTTPException(status_code=501, detail="Update not implemented - use delete + create")

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        table.delete(f"id = '{memory_id}'")
        return {"deleted": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """搜索记忆"""
    import time
    start = time.time()
    
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        results = []
        
        # 文本搜索
        result = table.to_lance().to_table().to_pydict()
        count = len(result.get("id", []))
        query_lower = request.query.lower()
        
        for i in range(count):
            text = result["text"][i] if len(result["text"]) > i else ""
            if query_lower in text.lower():
                results.append({
                    "id": result["id"][i],
                    "text": text,
                    "category": result["category"][i],
                    "importance": result["importance"][i],
                    "score": text.lower().count(query_lower) / len(text) if text else 0
                })
        
        # 向量搜索（可选）
        if request.use_vector and HAS_REQUESTS:
            query_embedding = get_embedding(request.query)
            if query_embedding:
                # 简化版向量搜索
                pass  # TODO: 实现向量搜索
        
        elapsed_ms = (time.time() - start) * 1000
        
        return {
            "results": results[:request.top_k],
            "total": len(results),
            "elapsed_ms": round(elapsed_ms, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    table = get_table()
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        result = table.to_lance().to_table().to_pydict()
        total = len(result.get("id", []))
        
        categories = {}
        for cat in result.get("category", []):
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_memories": total,
            "categories": categories,
            "status": "healthy" if total > 0 else "empty"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 启动入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
