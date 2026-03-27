#!/usr/bin/env python3
"""
SQLite 持久化存储 - Lightweight Persistence

无需向量数据库，支持全文搜索 FTS5
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SQLiteMemory:
    """
    SQLite 记忆存储
    
    优势：
    - 零依赖（Python 内置 sqlite3）
    - 轻量级（不比 LanceDB 重）
    - 支持 FTS5 全文搜索
    - 事务支持
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            WORKSPACE = Path.home() / ".openclaw" / "workspace"
            MEMORY_DIR = WORKSPACE / "memory"
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            db_path = str(MEMORY_DIR / "memory.db")
        
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_schema()
    
    def _connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def _init_schema(self):
        """初始化表结构"""
        cursor = self.conn.cursor()
        
        # 主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                category TEXT DEFAULT 'unknown',
                importance REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.8,
                tags TEXT DEFAULT '[]',
                project TEXT DEFAULT 'default',
                created_at TEXT,
                updated_at TEXT,
                accessed_at TEXT
            )
        """)
        
        # FTS5 全文搜索表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                text,
                content='memories',
                content_rowid='rowid'
            )
        """)
        
        # 触发器：保持 FTS 同步
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, text) VALUES (new.rowid, new.text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, text) VALUES('delete', old.rowid, old.text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, text) VALUES('delete', old.rowid, old.text);
                INSERT INTO memories_fts(rowid, text) VALUES (new.rowid, new.text);
            END
        """)
        
        self.conn.commit()
    
    # ===== CRUD =====
    
    def store(self, memory: Dict) -> bool:
        """存储记忆"""
        now = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, text, category, importance, confidence, tags, project, created_at, updated_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.get("id"),
            memory.get("text", ""),
            memory.get("category", "unknown"),
            memory.get("importance", 0.5),
            memory.get("confidence", 0.8),
            json.dumps(memory.get("tags", [])),
            memory.get("project", "default"),
            memory.get("created_at", now),
            now,
            now
        ))
        self.conn.commit()
        return True
    
    def get(self, memory_id: str) -> Optional[Dict]:
        """获取单条记忆"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Row 转 Dict"""
        return {
            "id": row["id"],
            "text": row["text"],
            "category": row["category"],
            "importance": row["importance"],
            "confidence": row["confidence"],
            "tags": json.loads(row["tags"]),
            "project": row["project"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "accessed_at": row["accessed_at"]
        }
    
    # ===== 搜索 =====
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        FTS5 全文搜索
        
        优势：比 LIKE 快，支持 relevance 排序
        """
        cursor = self.conn.cursor()
        
        # 使用 FTS5 MATCH
        cursor.execute("""
            SELECT memories.*, bm25(memories_fts) as rank
            FROM memories_fts
            JOIN memories ON memories.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(self._row_to_dict(row))
        
        return results
    
    def search_like(self, query: str, limit: int = 10) -> List[Dict]:
        """LIKE 搜索（备用）"""
        cursor = self.conn.cursor()
        pattern = f"%{query}%"
        
        cursor.execute("""
            SELECT * FROM memories
            WHERE text LIKE ? OR tags LIKE ?
            ORDER BY confidence DESC
            LIMIT ?
        """, (pattern, pattern, limit))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ===== 统计 =====
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有记忆"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def count(self) -> int:
        """计数"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]
    
    def get_stats(self) -> Dict:
        """统计"""
        cursor = self.conn.cursor()
        
        total = self.count()
        
        cursor.execute("""
            SELECT category, COUNT(*) as cnt
            FROM memories
            GROUP BY category
        """)
        by_category = {row["category"]: row["cnt"] for row in cursor.fetchall()}
        
        return {
            "total": total,
            "by_category": by_category
        }
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


# 全局实例
_sqlite = None

def get_sqlite_memory() -> SQLiteMemory:
    global _sqlite
    if _sqlite is None:
        _sqlite = SQLiteMemory()
    return _sqlite


if __name__ == "__main__":
    print("=" * 50)
    print("SQLite 存储测试")
    print("=" * 50)
    
    db = SQLiteMemory()
    
    # 存储测试
    print("\n📝 存储记忆:")
    db.store({
        "id": "mem_sqlite_1",
        "text": "用户喜欢简洁的界面设计",
        "category": "preference",
        "importance": 0.8
    })
    db.store({
        "id": "mem_sqlite_2",
        "text": "采用微服务架构方案",
        "category": "decision"
    })
    db.store({
        "id": "mem_sqlite_3",
        "text": "Python 编程语言很好用",
        "category": "fact"
    })
    
    print(f"  已存储 {db.count()} 条记忆")
    
    # FTS5 搜索
    print("\n🔍 FTS5 搜索 '界面':")
    results = db.search("界面")
    for r in results:
        print(f"  - {r['text']}")
    
    # LIKE 搜索
    print("\n🔍 LIKE 搜索 '微服务':")
    results = db.search_like("微服务")
    for r in results:
        print(f"  - {r['text']}")
    
    # 统计
    print(f"\n📊 统计: {db.get_stats()}")
    
    db.close()
    
    print("\n✅ SQLite 存储测试完成")
