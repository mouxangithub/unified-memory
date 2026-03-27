# Agent Memory v4.0 - 使用指南

> 专为 AI Agent 设计的记忆系统

## 快速开始

### 1. 查看状态
```bash
python3 agent_memory.py status
```

### 2. 生成上下文（对话时使用）
```bash
python3 agent_memory.py context --query "当前任务"
```

这会自动加载：
- 用户画像 (USER_MODEL.md)
- 相关记忆（向量+文本搜索）
- 生成简洁的上下文摘要

### 3. 从对话提取记忆
```bash
python3 agent_memory.py extract --conversation "对话内容" --store
```

自动提取 6 类记忆：
- profile - 身份属性
- preferences - 偏好习惯
- entities - 项目/设备
- events - 重要事件
- cases - 问题解决方案
- patterns - 处理模式

### 4. 存储单条记忆
```bash
python3 agent_memory.py store --text "内容" --category preferences
```

### 5. 记录学习
```bash
# 记录成功经验
python3 agent_memory.py learn --type success --content "成功优化了记忆系统"

# 记录失败教训
python3 agent_memory.py learn --type failure --content "LanceDB 需要先 open_table 再 create_table"
```

### 6. 更新用户画像
```bash
python3 agent_memory.py update-user
```

## 自动化集成

### AGENTS.md 启动流程

已更新 Session Startup，自动加载：
1. `SOUL.md` - 角色定位
2. `USER.md` - 用户信息
3. `USER_MODEL.md` - 用户画像（自动维护）
4. `AGENT_SELF.md` - Agent 自我认知
5. `memory/YYYY-MM-DD.md` - 今日记忆

### 心跳集成

可以在 HEARTBEAT.md 中添加：
```bash
# 记忆维护
python3 agent_memory.py update-user
```

## 文件结构

```
~/.openclaw/workspace/
├── USER_MODEL.md      # 用户画像 (自动维护)
├── AGENT_SELF.md      # Agent 自我认知
├── MEMORY.md          # 长期记忆精选
├── memory/
│   ├── YYYY-MM-DD.md  # 日常记忆日志
│   ├── vector/        # LanceDB 向量
│   └── ontology/      # 知识图谱
└── skills/unified-memory/scripts/
    ├── agent_memory.py    # Agent 专用 (v4.0)
    └── unified_memory.py  # 通用版 (v3.1)
```

## LLM 配置

使用 Ollama：
```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_EMBED_MODEL=nomic-embed-text:latest
export OLLAMA_LLM_MODEL=deepseek-v3.2:cloud
```

## 工作流程示例

### 对话开始时
```python
# 1. 生成上下文
context = generate_context("用户的问题")

# 2. 上下文自动包含：
# - 用户是谁、偏好什么
# - 相关项目/任务
# - 过去的经验教训
```

### 对话结束时
```python
# 1. 提取记忆
memories = extract_memories(conversation)

# 2. 自动存储
for m in memories:
    store_memory(m)

# 3. 更新用户画像
update_user_model()
```

---

更新: 2026-03-18 v4.0
