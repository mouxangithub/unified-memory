"""
备份元数据管理
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from .backup_manager import BackupMetadata, BackupStatus, BackupType


class MetadataStore:
    """备份元数据存储"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    checksum TEXT,
                    parent_backup_id TEXT,
                    files_json TEXT,
                    error_message TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON backups(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON backups(status)")
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save(self, metadata: BackupMetadata) -> None:
        """保存元数据"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO backups 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.backup_id,
                metadata.backup_type.value,
                metadata.created_at,
                metadata.status.value,
                metadata.size_bytes,
                metadata.file_count,
                metadata.checksum,
                metadata.parent_backup_id,
                json.dumps(metadata.files),
                metadata.error_message,
            ))
            conn.commit()
    
    def get(self, backup_id: str) -> Optional[BackupMetadata]:
        """获取元数据"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM backups WHERE backup_id = ?",
                (backup_id,)
            ).fetchone()
        
        if row:
            return self._row_to_metadata(row)
        return None
    
    def get_latest(self, backup_type: Optional[BackupType] = None) -> Optional[BackupMetadata]:
        """获取最新备份"""
        with self._get_connection() as conn:
            if backup_type:
                row = conn.execute("""
                    SELECT * FROM backups 
                    WHERE backup_type = ? AND status IN ('completed', 'verified')
                    ORDER BY created_at DESC LIMIT 1
                """, (backup_type.value,)).fetchone()
            else:
                row = conn.execute("""
                    SELECT * FROM backups 
                    WHERE status IN ('completed', 'verified')
                    ORDER BY created_at DESC LIMIT 1
                """).fetchone()
        
        if row:
            return self._row_to_metadata(row)
        return None
    
    def get_all(self, limit: Optional[int] = None) -> List[BackupMetadata]:
        """获取所有备份"""
        with self._get_connection() as conn:
            query = "SELECT * FROM backups ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            rows = conn.execute(query).fetchall()
        
        return [self._row_to_metadata(row) for row in rows]
    
    def delete(self, backup_id: str) -> bool:
        """删除元数据"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM backups WHERE backup_id = ?",
                (backup_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def _row_to_metadata(self, row: sqlite3.Row) -> BackupMetadata:
        return BackupMetadata(
            backup_id=row["backup_id"],
            backup_type=BackupType(row["backup_type"]),
            created_at=row["created_at"],
            status=BackupStatus(row["status"]),
            size_bytes=row["size_bytes"],
            file_count=row["file_count"],
            checksum=row["checksum"],
            parent_backup_id=row["parent_backup_id"],
            files=json.loads(row["files_json"] or "[]"),
            error_message=row["error_message"],
        )
