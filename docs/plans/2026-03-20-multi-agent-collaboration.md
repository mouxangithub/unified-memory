# 多 Agent 协作记忆系统设计

> 日期: 2026-03-20
> 目标: 让多个 AI Agent 高效协作

---

## 核心问题

1. **视角孤岛** - 各自存储，缺乏交叉验证
2. **协作上下文缺失** - 不知道谁做了什么
3. **任务分配盲区** - 没有智能分配机制
4. **实时同步延迟** - 变更感知不及时

---

## 解决方案

### 1. 协作记忆模型 (CollaborativeMemory)

```python
class CollaborativeMemory:
    content: str
    creator: AgentID  # 创建者
    editors: List[AgentEdit]  # 编辑历史
    confirmations: List[AgentConfirm]  # 确认列表
    perspective: Optional[AgentID]  # 视角归属
    shared_scope: List[AgentScope]  # 共享范围
    conflict_status: Optional[ConflictInfo]  # 冲突状态
    collaboration_score: float  # 协作质量分
```

### 2. Agent 能力画像 (AgentProfile)

```python
class AgentProfile:
    agent_id: str
    name: str
    skills: List[SkillScore]
    preferences: Dict
    workload: float
    expertise: List[str]
    collaboration_style: str  # 主动/被动/协商
    trust_scores: Dict[AgentID, float]
```

### 3. 冲突解决机制 (ConflictResolver)

```python
class ConflictResolver:
    strategies = ['latest_wins', 'higher_confidence', 'expert_wins', 'consensus', 'escalate']
    
    def detect(memories) -> List[Conflict]
    def resolve(conflict, strategy)
    def auto_resolve()  # 自动解决
```

### 4. 实时协作总线 (CollaborationBus)

```python
class CollaborationBus:
    def publish(event: CollaborationEvent)
    def subscribe(agent_id, topics)
    def sync_state() -> SyncState
    def broadcast_change(memory_id, change_type)
```

### 5. 任务队列 (TaskQueue)

```python
class TaskQueue:
    def add_task(task: Task)
    def assign(task, strategy)  # skill_match, load_balance, round_robin
    def handoff(task_id, from_agent, to_agent)
    def get_agent_tasks(agent_id)
```

### 6. 协作仪表盘 (WebUI Extension)

```
┌─────────────────────────────────────────┐
│           协作记忆仪表盘                  │
├─────────────────────────────────────────┤
│ 在线 Agent: 小智🟢 小刘🟢               │
│ 共享记忆: 31 条                          │
│ 待处理冲突: 0                            │
│ 任务队列: 3 个                           │
└─────────────────────────────────────────┘
```

---

## 实现计划

### Task 1: 协作记忆模型
- 创建 `scripts/memory_collab.py`
- 扩展 Memory 数据结构
- 添加编辑历史、确认机制

### Task 2: Agent 能力画像
- 创建 `scripts/agent_profile.py`
- 管理多个 Agent 的能力信息
- 支持能力查询和匹配

### Task 3: 冲突解决机制
- 创建 `scripts/conflict_resolver.py`
- 实现多种解决策略
- 自动检测和解决

### Task 4: 实时协作总线
- 创建 `scripts/collab_bus.py`
- 事件发布/订阅
- 变更广播

### Task 5: 任务队列
- 创建 `scripts/task_queue.py`
- 智能分配算法
- 任务移交机制

### Task 6: 协作仪表盘
- 扩展 `scripts/memory_webui.py`
- 新增协作视图
- 实时状态展示

### Task 7: 集成测试
- 测试多 Agent 协作流程
- 冲突解决验证
- 性能测试

### Task 8: 文档更新
- 更新 SKILL.md
- 添加协作使用指南

---

## 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `memory_collab.py` | 协作记忆模型 | 📝 待创建 |
| `agent_profile.py` | Agent 能力画像 | 📝 待创建 |
| `conflict_resolver.py` | 冲突解决 | 📝 待创建 |
| `collab_bus.py` | 协作总线 | 📝 待创建 |
| `task_queue.py` | 任务队列 | 📝 待创建 |
| `memory_webui.py` | 仪表盘扩展 | 📝 待修改 |

---

## 验收标准

1. 支持 2+ Agent 协作
2. 冲突自动检测和解决
3. 任务智能分配
4. 实时变更感知
5. 协作仪表盘可视化
