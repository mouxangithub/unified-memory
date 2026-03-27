# MetaGPT × Agent-Collaboration-System 融合方案

> 日期: 2026-03-22
> 设计者: 小智
> 目标: 结合 MetaGPT 的成熟流程 + 我们的记忆驱动协作

---

## 一、为什么要融合？

### MetaGPT 的优势
- ✅ 成熟的多 Agent 协作 SOP（软件开发全流程）
- ✅ 固定角色分工明确（PM/架构师/工程师/QA）
- ✅ 开箱即用，文档完善
- ✅ 生产级稳定性

### MetaGPT 的不足
- ❌ **无记忆持久化** - Agent 不记得历史协作
- ❌ **无冲突解决机制** - 多 Agent 意见冲突时无处理
- ❌ **硬编码角色** - 无法动态调整能力
- ❌ **无实时同步** - 状态变更感知不及时

### 我们的补充
- ✅ unified-memory - 记忆持久化 + 向量搜索
- ✅ conflict_resolver - 智能冲突解决
- ✅ collab_bus - 实时事件驱动
- ✅ agent_profile - 动态能力画像

---

## 二、融合架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户需求输入                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  MetaGPT 核心流程层                           │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │  PM  │→ │架构师│→ │工程师│→ │  QA  │→ │交付  │          │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Agent-Collaboration 增强层 (我们提供)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ unified-     │  │ conflict-    │  │ collab-      │      │
│  │ memory       │  │ resolver     │  │ bus          │      │
│  │ (记忆层)      │  │ (冲突解决)    │  │ (实时同步)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                          │
│  │ agent-       │  (可选：动态角色替换)                      │
│  │ profile      │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   持久化存储层                                │
│  LanceDB (向量) + JSON (结构化) + 事件日志 (审计)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、具体融合方案

### 方案A: 记忆层注入 (最小改动)

**原理**: 给每个 MetaGPT Agent 注入 unified-memory

```python
# metagpt_agent_with_memory.py

from metagpt.roles import Role
from skills.unified_memory.scripts.memory_all_in_one import UnifiedMemory

class MemoryEnabledAgent(Role):
    def __init__(self, name, profile, memory_id):
        super().__init__(name, profile)
        self.memory = UnifiedMemory(agent_id=memory_id)
    
    async def _think(self):
        # 先回忆相关上下文
        context = self.memory.search(self.current_task)
        self.context_memory = context
        
        # 再执行原有逻辑
        await super()._think()
    
    async def _act(self):
        # 执行任务
        result = await super()._act()
        
        # 记住这次决策
        self.memory.store({
            "task": self.current_task,
            "decision": result,
            "timestamp": datetime.now()
        })
        
        return result
```

**优点**:
- 改动最小，不破坏 MetaGPT 原有流程
- 每个 Agent 有独立记忆
- 上下文连续性增强

**缺点**:
- Agent 间记忆不共享
- 冲突无法自动解决

---

### 方案B: 协作总线替换 (中等改动)

**原理**: 用 collab_bus 替换 MetaGPT 的消息传递

```python
# metagpt_with_collab_bus.py

from metagpt.context import Context
from skills.unified_memory.scripts.collab_bus import CollaborationBus, EventType

class BusEnabledContext(Context):
    def __init__(self):
        super().__init__()
        self.bus = CollaborationBus()
        
    async def publish_message(self, msg):
        # 包装为协作事件
        event = CollaborationEvent.create(
            event_type=EventType.MEMORY_CREATED,
            source_agent=msg.role,
            payload=msg.content
        )
        
        # 广播到总线
        await self.bus.broadcast(event)
        
        # 同时保留原有逻辑
        await super().publish_message(msg)
    
    async def subscribe(self, agent_id, topics):
        await self.bus.subscribe(agent_id, topics)
```

**优点**:
- 实时状态同步
- 支持多 Agent 订阅/广播
- 变更即时感知

**缺点**:
- 需要修改 MetaGPT 核心代码
- 可能影响原有稳定性

---

### 方案C: 冲突解决集成 (针对性增强)

**原理**: 在 MetaGPT 的 Review 阶段集成 conflict_resolver

```python
# metagpt_with_conflict_resolver.py

from metagpt.roles.qa_engineer import QaEngineer
from skills.unified_memory.scripts.conflict_resolver import ConflictResolver

class ConflictAwareQA(QaEngineer):
    def __init__(self):
        super().__init__()
        self.resolver = ConflictResolver()
    
    async def review_code(self, code):
        # 检查代码与历史记忆是否有冲突
        conflicts = self.resolver.detect_conflicts([
            {"text": code, "id": "current"},
            *self.get_historical_decisions()
        ])
        
        if conflicts:
            # 自动解决或标记
            resolved = self.resolver.auto_resolve_all()
            
            # 无法自动解决的，返回给 PM 决策
            if resolved.get("needs_confirmation"):
                return {
                    "status": "conflict",
                    "conflicts": conflicts,
                    "suggestions": resolved["suggestions"]
                }
        
        # 无冲突，继续正常流程
        return await super().review_code(code)
```

**优点**:
- 针对性强，解决实际痛点
- 不影响 MetaGPT 主流程
- 可逐步迭代

**缺点**:
- 只解决了代码审查阶段的冲突
- 其他阶段（需求、设计）冲突未覆盖

---

### 方案D: 完全融合 (最大改动)

**原理**: 用 agent_profile 替换 MetaGPT 的硬编码角色

```python
# dynamic_role_factory.py

from skills.unified_memory.scripts.agent_profile import AgentProfileManager
from metagpt.roles import Role

class DynamicRoleFactory:
    def __init__(self):
        self.profile_mgr = AgentProfileManager()
    
    async def assign_role(self, task_type, task_requirements):
        # 根据任务需求，动态选择最合适的 Agent
        profiles = await self.profile_mgr.find_best_match(
            skills=task_requirements.get("skills", []),
            max_workload=0.8
        )
        
        if not profiles:
            # 无匹配，创建新角色
            return self.create_role_from_task(task_type)
        
        # 选择能力最匹配的
        best_match = profiles[0]
        
        # 动态实例化角色
        return DynamicRole(
            name=best_match.name,
            profile=best_match.expertise,
            memory_id=best_match.agent_id
        )

class DynamicRole(Role):
    async def _think(self):
        # 从记忆中获取相关上下文
        context = self.memory.search(self.current_task)
        
        # 结合上下文和能力画像决策
        decision = await self.make_decision(context, self.profile)
        
        # 广播决策到协作总线
        await self.bus.broadcast({
            "agent": self.name,
            "decision": decision,
            "confidence": self.profile.get_skill_confidence(self.current_task)
        })
        
        return decision
```

**优点**:
- 完全灵活，动态分配
- 角色可扩展
- 能力持续积累

**缺点**:
- 改动最大，风险最高
- 需要大量测试
- 可能失去 MetaGPT 的稳定性

---

## 四、推荐实施路径

### 阶段1: 记忆层注入 (1-2周)
- 实现方案A
- 每个 MetaGPT Agent 获得记忆能力
- 验证记忆持久化效果

### 阶段2: 冲突解决集成 (1周)
- 实现方案C
- 在 Review 阶段集成 conflict_resolver
- 测试冲突自动解决

### 阶段3: 协作总线替换 (2周)
- 实现方案B
- 替换消息传递机制
- 验证实时同步效果

### 阶段4: 动态角色 (可选，2-4周)
- 实现方案D
- 完全动态化角色分配
- 大规模测试和优化

---

## 五、文件结构

```
skills/metagpt-integration/
├── SKILL.md                    # 使用指南
├── scripts/
│   ├── metagpt_agent_with_memory.py    # 方案A
│   ├── metagpt_with_collab_bus.py      # 方案B
│   ├── metagpt_with_conflict_resolver.py # 方案C
│   ├── dynamic_role_factory.py         # 方案D
│   └── integration_test.py             # 集成测试
├── examples/
│   ├── software_dev_with_memory.md     # 示例：带记忆的软件开发
│   └── conflict_aware_review.md        # 示例：冲突感知审查
└── docs/
    ├── architecture.md                 # 架构说明
    └── migration_guide.md              # 迁移指南
```

---

## 六、预期效果

### 短期（方案A+C）
- MetaGPT Agent 有记忆，知道历史决策
- 代码审查能自动发现冲突
- 开发效率提升 20-30%

### 中期（方案A+B+C）
- 实时协作，状态同步
- 冲突自动解决率 > 80%
- 多 Agent 协作更顺畅

### 长期（方案D）
- 完全动态角色分配
- 能力持续积累和进化
- 成为真正的"记忆驱动 Agent 团队"

---

## 七、下一步行动

1. **刘总确认**: 选择哪个方案优先实施？
2. **小刘协助**: 负责测试和验证
3. **小智实施**: 编写集成代码
4. **逐步迭代**: 从方案A开始，逐步增强

---

*设计: 小智 | 2026-03-22*
