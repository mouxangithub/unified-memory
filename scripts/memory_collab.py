#!/usr/bin/env python3
"""
Memory Collaboration - 多 Agent 协作记忆模型 v1.0

实现多 Agent 协作记忆，支持:
- 编辑历史追踪
- 确认机制
- 协作质量评分
- 冲突检测

Usage:
    memory_collab.py create "内容" --creator xiao-zhi
    memory_collab.py edit <id> --editor xiao-liu --content "新内容"
    memory_collab.py confirm <id> --agent xiao-liu --status confirmed
    memory_collab.py history <id>
    memory_collab.py stats
"""

import argparse
import json
import os
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
COLLAB_DB_DIR = MEMORY_DIR / "collab"

# 确保目录存在
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
COLLAB_DB_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 数据模型
# ============================================================

@dataclass
class AgentEdit:
    """编辑记录"""
    agent_id: str
    timestamp: str  # ISO format
    change_type: str  # create, update, delete
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentEdit':
        return cls(**data)


@dataclass
class AgentConfirm:
    """确认记录"""
    agent_id: str
    timestamp: str  # ISO format
    status: str  # confirmed, rejected, pending
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentConfirm':
        return cls(**data)


@dataclass
class CollaborativeMemory:
    """协作记忆"""
    id: str
    content: str
    creator: str  # AgentID
    editors: List[Dict] = field(default_factory=list)
    confirmations: List[Dict] = field(default_factory=list)
    perspective: Optional[str] = None  # AgentID
    shared_scope: List[str] = field(default_factory=list)  # ['all', 'team-alpha']
    conflict_status: Optional[Dict] = None
    collaboration_score: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CollaborativeMemory':
        return cls(**data)
    
    def add_edit(self, edit: AgentEdit):
        """添加编辑记录"""
        self.editors.append(edit.to_dict())
        self.updated_at = datetime.now().isoformat()
    
    def add_confirmation(self, confirm: AgentConfirm):
        """添加确认记录"""
        self.confirmations.append(confirm.to_dict())
        self.updated_at = datetime.now().isoformat()
    
    def get_unique_editors(self) -> List[str]:
        """获取参与编辑的唯一 Agent 列表"""
        return list(set(e['agent_id'] for e in self.editors))
    
    def get_confirmation_count(self, status: str = 'confirmed') -> int:
        """获取指定状态的确认数"""
        return len([c for c in self.confirmations if c['status'] == status])


# ============================================================
# 存储层
# ============================================================

class CollaborativeMemoryStore:
    """协作记忆存储"""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else COLLAB_DB_DIR
        self.db_path.mkdir(parents=True, exist_ok=True)
        self._db = None
        self._table = None
        self._json_store = self.db_path / "collab_memories.jsonl"
    
    def _init_db(self):
        """初始化 LanceDB"""
        if self._db is not None:
            return
        
        try:
            import lancedb
            import pyarrow as pa
            
            self._db = lancedb.connect(str(self.db_path))
            
            # 尝试打开已存在的表
            try:
                self._table = self._db.open_table("collab_memories")
                return
            except Exception:
                pass
            
            # 创建新表
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("creator", pa.string()),
                pa.field("editors", pa.string()),  # JSON
                pa.field("confirmations", pa.string()),  # JSON
                pa.field("perspective", pa.string()),
                pa.field("shared_scope", pa.string()),  # JSON
                pa.field("conflict_status", pa.string()),  # JSON
                pa.field("collaboration_score", pa.float64()),
                pa.field("created_at", pa.string()),
                pa.field("updated_at", pa.string()),
            ])
            self._table = self._db.create_table("collab_memories", schema=schema)
            
        except Exception as e:
            print(f"⚠️ LanceDB 初始化失败，降级为 JSON 存储: {e}", file=sys.stderr)
            self._table = None
    
    def _load_from_json(self) -> List[CollaborativeMemory]:
        """从 JSONL 加载"""
        memories = []
        if self._json_store.exists():
            with open(self._json_store, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        memories.append(CollaborativeMemory.from_dict(data))
                    except:
                        continue
        return memories
    
    def create(self, content: str, creator: str, perspective: Optional[str] = None,
               shared_scope: List[str] = None) -> CollaborativeMemory:
        """创建协作记忆"""
        memory_id = f"collab_{uuid.uuid4().hex[:8]}"
        
        memory = CollaborativeMemory(
            id=memory_id,
            content=content,
            creator=creator,
            perspective=perspective,
            shared_scope=shared_scope or ['all']
        )
        
        # 记录创建编辑
        edit = AgentEdit(
            agent_id=creator,
            timestamp=datetime.now().isoformat(),
            change_type='create',
            old_value=None,
            new_value=content
        )
        memory.add_edit(edit)
        
        # 存储
        self._save(memory)
        
        return memory
    
    def _save(self, memory: CollaborativeMemory):
        """保存记忆 - 使用 JSONL 作为主存储确保一致性"""
        # 先更新 JSONL 文件（追加模式，读取时会取最新）
        self._update_json_store(memory)
        
        # LanceDB 作为可选索引
        self._init_db()
        
        if self._table is not None:
            try:
                import pyarrow as pa
                
                # LanceDB 不支持直接更新，但读取时会合并最新数据
                self._table.add([{
                    "id": memory.id,
                    "content": memory.content,
                    "creator": memory.creator,
                    "editors": json.dumps(memory.editors, ensure_ascii=False),
                    "confirmations": json.dumps(memory.confirmations, ensure_ascii=False),
                    "perspective": memory.perspective or "",
                    "shared_scope": json.dumps(memory.shared_scope, ensure_ascii=False),
                    "conflict_status": json.dumps(memory.conflict_status, ensure_ascii=False) if memory.conflict_status else "",
                    "collaboration_score": memory.collaboration_score,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                }])
            except Exception as e:
                print(f"⚠️ LanceDB 存储失败: {e}", file=sys.stderr)
    
    def _update_json_store(self, memory: CollaborativeMemory):
        """更新 JSONL 存储，保持最新版本"""
        # 读取现有记录
        memories = {}
        if self._json_store.exists():
            with open(self._json_store, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        memories[data['id']] = data
                    except:
                        continue
        
        # 更新或添加
        memories[memory.id] = memory.to_dict()
        
        # 写回文件
        with open(self._json_store, "w", encoding="utf-8") as f:
            for m in memories.values():
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
    
    def get(self, memory_id: str) -> Optional[CollaborativeMemory]:
        """获取记忆 - 优先从 JSONL 获取最新版本"""
        # 优先从 JSONL 获取（保证一致性）
        for m in self._load_from_json():
            if m.id == memory_id:
                return m
        
        return None
    
    def edit(self, memory_id: str, editor: str, new_content: str) -> Optional[CollaborativeMemory]:
        """编辑记忆，记录编辑历史"""
        memory = self.get(memory_id)
        if not memory:
            return None
        
        old_content = memory.content
        
        # 创建编辑记录
        edit = AgentEdit(
            agent_id=editor,
            timestamp=datetime.now().isoformat(),
            change_type='update',
            old_value=old_content,
            new_value=new_content
        )
        
        memory.content = new_content
        memory.add_edit(edit)
        
        # 检测冲突
        memory = self._detect_conflict(memory)
        
        # 重新计算协作分
        memory.collaboration_score = self.calculate_collaboration_score(memory_id)
        
        self._save(memory)
        
        return memory
    
    def confirm(self, memory_id: str, agent_id: str, status: str, 
                comment: Optional[str] = None) -> Optional[CollaborativeMemory]:
        """确认记忆"""
        memory = self.get(memory_id)
        if not memory:
            return None
        
        # 检查是否已确认过
        existing = [c for c in memory.confirmations if c['agent_id'] == agent_id]
        if existing:
            # 更新状态
            for c in memory.confirmations:
                if c['agent_id'] == agent_id:
                    c['status'] = status
                    c['timestamp'] = datetime.now().isoformat()
                    c['comment'] = comment
        else:
            # 新增确认
            confirm = AgentConfirm(
                agent_id=agent_id,
                timestamp=datetime.now().isoformat(),
                status=status,
                comment=comment
            )
            memory.add_confirmation(confirm)
        
        # 重新计算协作分
        memory.collaboration_score = self.calculate_collaboration_score(memory_id)
        
        # 解决冲突（如果有）
        memory = self._resolve_conflict(memory)
        
        self._save(memory)
        
        return memory
    
    def _detect_conflict(self, memory: CollaborativeMemory) -> CollaborativeMemory:
        """检测冲突"""
        # 获取最近的编辑者
        recent_editors = set()
        for edit in reversed(memory.editors[-5:]):  # 最近 5 次编辑
            recent_editors.add(edit['agent_id'])
        
        # 如果有多个编辑者且没有确认，标记为潜在冲突
        if len(recent_editors) > 1:
            confirmed_editors = {c['agent_id'] for c in memory.confirmations if c['status'] == 'confirmed'}
            unconfirmed = recent_editors - confirmed_editors
            
            if unconfirmed:
                memory.conflict_status = {
                    'detected': True,
                    'type': 'unconfirmed_edit',
                    'unconfirmed_agents': list(unconfirmed),
                    'timestamp': datetime.now().isoformat()
                }
        
        return memory
    
    def _resolve_conflict(self, memory: CollaborativeMemory) -> CollaborativeMemory:
        """尝试解决冲突"""
        if not memory.conflict_status or not memory.conflict_status.get('detected'):
            return memory
        
        # 检查所有编辑者是否都已确认
        recent_editors = set()
        for edit in reversed(memory.editors[-5:]):
            recent_editors.add(edit['agent_id'])
        
        confirmed_editors = {c['agent_id'] for c in memory.confirmations if c['status'] == 'confirmed'}
        
        if recent_editors.issubset(confirmed_editors):
            # 所有人都确认了，冲突解决
            memory.conflict_status = {
                'detected': False,
                'resolved_at': datetime.now().isoformat(),
                'resolution': 'all_confirmed'
            }
        
        return memory
    
    def get_collaboration_history(self, memory_id: str) -> List[Dict]:
        """获取协作历史"""
        memory = self.get(memory_id)
        if not memory:
            return []
        
        history = []
        
        # 编辑历史
        for edit in memory.editors:
            old_val = edit.get('old_value') or ''
            new_val = edit.get('new_value') or ''
            history.append({
                'type': 'edit',
                'agent': edit['agent_id'],
                'timestamp': edit['timestamp'],
                'action': edit['change_type'],
                'details': f"{edit['change_type']}: {old_val[:30]} → {new_val[:30]}" if edit['change_type'] != 'create' else f"创建: {new_val[:50]}"
            })
        
        # 确认历史
        for conf in memory.confirmations:
            history.append({
                'type': 'confirm',
                'agent': conf['agent_id'],
                'timestamp': conf['timestamp'],
                'action': conf['status'],
                'details': conf.get('comment', '')
            })
        
        # 按时间排序
        history.sort(key=lambda x: x['timestamp'])
        
        return history
    
    def calculate_collaboration_score(self, memory_id: str) -> float:
        """
        计算协作质量分
        
        公式: confirmed_count / (edit_count + 1) * participation_factor
        - 基础分 = 确认数 / (编辑数 + 1)
        - 参与因子 = min(1.0, 参与人数 / 3)
        """
        memory = self.get(memory_id)
        if not memory:
            return 0.0
        
        edit_count = len([e for e in memory.editors if e['change_type'] == 'update'])
        confirmed_count = memory.get_confirmation_count('confirmed')
        rejected_count = memory.get_confirmation_count('rejected')
        
        # 基础分
        base_score = confirmed_count / (edit_count + 1)
        
        # 参与因子
        participants = set()
        for e in memory.editors:
            participants.add(e['agent_id'])
        for c in memory.confirmations:
            participants.add(c['agent_id'])
        participation_factor = min(1.0, len(participants) / 3)
        
        # 拒绝惩罚
        reject_penalty = rejected_count * 0.1
        
        # 最终分数
        score = base_score * participation_factor - reject_penalty
        
        return max(0.0, min(1.0, score))
    
    def list_all(self, limit: int = 20) -> List[CollaborativeMemory]:
        """列出所有协作记忆"""
        memories = self._load_from_json()
        
        # 按更新时间排序（最新的在前）
        memories.sort(key=lambda m: m.updated_at, reverse=True)
        
        return memories[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        memories = self.list_all(limit=1000)
        
        if not memories:
            return {
                'total': 0,
                'agents': [],
                'avg_score': 0,
                'conflicts': 0
            }
        
        # 统计
        agents = Counter()
        total_edits = 0
        total_confirms = 0
        conflicts = 0
        scores = []
        
        for m in memories:
            agents[m.creator] += 1
            total_edits += len([e for e in m.editors if e['change_type'] == 'update'])
            total_confirms += m.get_confirmation_count('confirmed')
            if m.conflict_status and m.conflict_status.get('detected'):
                conflicts += 1
            scores.append(m.collaboration_score)
        
        return {
            'total': len(memories),
            'agents': list(agents.keys()),
            'agent_counts': dict(agents),
            'total_edits': total_edits,
            'total_confirms': total_confirms,
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'conflicts': conflicts
        }


# ============================================================
# CLI
# ============================================================

def cmd_create(args):
    """创建协作记忆"""
    store = CollaborativeMemoryStore()
    memory = store.create(
        content=args.content,
        creator=args.creator,
        perspective=args.perspective,
        shared_scope=args.scope.split(',') if args.scope else ['all']
    )
    
    print(f"✅ 已创建协作记忆")
    print(f"   ID: {memory.id}")
    print(f"   创建者: {memory.creator}")
    print(f"   内容: {memory.content[:50]}...")
    print(f"   共享范围: {memory.shared_scope}")


def cmd_edit(args):
    """编辑协作记忆"""
    store = CollaborativeMemoryStore()
    memory = store.edit(
        memory_id=args.id,
        editor=args.editor,
        new_content=args.content
    )
    
    if not memory:
        print(f"❌ 未找到记忆: {args.id}")
        return
    
    print(f"✅ 已编辑协作记忆")
    print(f"   ID: {memory.id}")
    print(f"   编辑者: {args.editor}")
    print(f"   新内容: {memory.content[:50]}...")
    print(f"   编辑次数: {len([e for e in memory.editors if e['change_type'] == 'update'])}")
    
    if memory.conflict_status and memory.conflict_status.get('detected'):
        print(f"   ⚠️ 检测到潜在冲突: {memory.conflict_status}")


def cmd_confirm(args):
    """确认协作记忆"""
    store = CollaborativeMemoryStore()
    memory = store.confirm(
        memory_id=args.id,
        agent_id=args.agent,
        status=args.status,
        comment=args.comment
    )
    
    if not memory:
        print(f"❌ 未找到记忆: {args.id}")
        return
    
    print(f"✅ 已确认协作记忆")
    print(f"   ID: {memory.id}")
    print(f"   确认者: {args.agent}")
    print(f"   状态: {args.status}")
    print(f"   协作分: {memory.collaboration_score:.2f}")
    
    if args.comment:
        print(f"   备注: {args.comment}")


def cmd_history(args):
    """查看协作历史"""
    store = CollaborativeMemoryStore()
    
    memory = store.get(args.id)
    if not memory:
        print(f"❌ 未找到记忆: {args.id}")
        return
    
    history = store.get_collaboration_history(args.id)
    
    print(f"📜 协作历史: {args.id}")
    print(f"   创建者: {memory.creator}")
    print(f"   当前内容: {memory.content[:60]}...")
    print()
    
    if not history:
        print("   暂无历史记录")
        return
    
    print("   时间线:")
    for h in history:
        ts = h['timestamp'].split('T')[1][:8] if 'T' in h['timestamp'] else h['timestamp']
        icon = '✏️' if h['type'] == 'edit' else '✅' if h['action'] == 'confirmed' else '❌' if h['action'] == 'rejected' else '⏳'
        print(f"   {ts} {icon} [{h['agent']}] {h['action']}")
        if h.get('details'):
            print(f"           {h['details'][:50]}")


def cmd_stats(args):
    """显示统计信息"""
    store = CollaborativeMemoryStore()
    stats = store.get_stats()
    
    print("📊 协作记忆统计")
    print()
    print(f"   总记忆数: {stats['total']}")
    print(f"   参与 Agent: {', '.join(stats['agents']) if stats['agents'] else '无'}")
    print(f"   总编辑数: {stats['total_edits']}")
    print(f"   总确认数: {stats['total_confirms']}")
    print(f"   平均协作分: {stats['avg_score']:.2f}")
    print(f"   活跃冲突: {stats['conflicts']}")
    
    if stats['agent_counts']:
        print()
        print("   Agent 贡献:")
        for agent, count in sorted(stats['agent_counts'].items(), key=lambda x: -x[1]):
            print(f"     - {agent}: {count} 条")


def cmd_list(args):
    """列出协作记忆"""
    store = CollaborativeMemoryStore()
    memories = store.list_all(limit=args.limit)
    
    if not memories:
        print("暂无协作记忆")
        return
    
    print(f"📋 协作记忆列表 (共 {len(memories)} 条)")
    print()
    
    for m in memories:
        status = ""
        if m.conflict_status and m.conflict_status.get('detected'):
            status = " ⚠️冲突"
        
        editors = len(set(e['agent_id'] for e in m.editors))
        confirms = m.get_confirmation_count('confirmed')
        
        print(f"   {m.id}")
        print(f"      [{m.creator}] {m.content[:40]}...")
        print(f"      编辑: {editors} | 确认: {confirms} | 分: {m.collaboration_score:.2f}{status}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Memory Collaboration - 多 Agent 协作记忆",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # create
    create_p = subparsers.add_parser("create", help="创建协作记忆")
    create_p.add_argument("content", help="记忆内容")
    create_p.add_argument("--creator", required=True, help="创建者 Agent ID")
    create_p.add_argument("--perspective", help="视角归属")
    create_p.add_argument("--scope", default="all", help="共享范围，逗号分隔")
    
    # edit
    edit_p = subparsers.add_parser("edit", help="编辑协作记忆")
    edit_p.add_argument("id", help="记忆 ID")
    edit_p.add_argument("--editor", required=True, help="编辑者 Agent ID")
    edit_p.add_argument("--content", required=True, help="新内容")
    
    # confirm
    confirm_p = subparsers.add_parser("confirm", help="确认协作记忆")
    confirm_p.add_argument("id", help="记忆 ID")
    confirm_p.add_argument("--agent", required=True, help="确认者 Agent ID")
    confirm_p.add_argument("--status", required=True, choices=['confirmed', 'rejected', 'pending'],
                          help="确认状态")
    confirm_p.add_argument("--comment", help="备注")
    
    # history
    history_p = subparsers.add_parser("history", help="查看协作历史")
    history_p.add_argument("id", help="记忆 ID")
    
    # stats
    subparsers.add_parser("stats", help="显示统计")
    
    # list
    list_p = subparsers.add_parser("list", help="列出协作记忆")
    list_p.add_argument("--limit", type=int, default=20)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "create":
            cmd_create(args)
        elif args.command == "edit":
            cmd_edit(args)
        elif args.command == "confirm":
            cmd_confirm(args)
        elif args.command == "history":
            cmd_history(args)
        elif args.command == "stats":
            cmd_stats(args)
        elif args.command == "list":
            cmd_list(args)
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
