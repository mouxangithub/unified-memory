#!/usr/bin/env python3
"""
TaskRecovery - 任务恢复机制

功能:
- 断点续传
- 自动重试
- 状态持久化
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class TaskRecovery:
    def __init__(self, state_dir: str = None):
        self.state_dir = Path(state_dir or Path.home() / ".openclaw" / "workspace" / "memory" / "recovery")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.state_dir / "checkpoints.json"
        self.max_retries = 3
    
    def create_checkpoint(self, task_id: str, state: dict) -> bool:
        try:
            checkpoints = self._load()
            checkpoints[task_id] = {
                "task_id": task_id, "state": state,
                "created_at": datetime.now().isoformat(),
                "retry_count": 0
            }
            self._save(checkpoints)
            return True
        except:
            return False
    
    def resume(self, task_id: str) -> Optional[dict]:
        checkpoints = self._load()
        return checkpoints.get(task_id, {}).get("state")
    
    def retry(self, task_id: str) -> bool:
        checkpoints = self._load()
        if task_id not in checkpoints:
            return False
        if checkpoints[task_id]["retry_count"] >= self.max_retries:
            return False
        checkpoints[task_id]["retry_count"] += 1
        self._save(checkpoints)
        return True
    
    def complete(self, task_id: str):
        checkpoints = self._load()
        if task_id in checkpoints:
            checkpoints[task_id]["state"]["status"] = "completed"
            self._save(checkpoints)
    
    def list_incomplete(self) -> List[dict]:
        checkpoints = self._load()
        return [cp for cp in checkpoints.values() if cp["state"].get("status") != "completed"]
    
    def _load(self) -> dict:
        if self.checkpoint_file.exists():
            try:
                return json.loads(self.checkpoint_file.read_text())
            except:
                pass
        return {}
    
    def _save(self, checkpoints: dict):
        self.checkpoint_file.write_text(json.dumps(checkpoints, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    recovery = TaskRecovery()
    recovery.create_checkpoint("t1", {"step": 1, "status": "running"})
    print("检查点:", recovery.resume("t1"))
