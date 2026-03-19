# unified-memory - 统一记忆系统 v0.5.0

> 专为 AI Agent 设计的智能记忆系统，分层缓存、知识合并、主动预测、自动维护

## 🎉 v0.5.0 更新

✨ **5 大核心优化**:

### 1. 时效性智能衰减
- 6 种记忆类型，不同半衰期（7天~365天）
- 过时记忆自动降权
- CLI: `memory_decay.py stats/preview/apply`

### 2. 关联推理增强
- 向量搜索 + 图谱路径扩展
- 上下文链：项目→参与人+任务+进度
- CLI: `memory_inference.py search/context`

### 3. 多 Agent 视角
- 支持小智/小刘独立视角
- 共享记忆 + 私有记忆
- CLI: `memory.py store --agent xiao-zhi`

### 4. 主动推送优化
- 项目截止提醒（提前3天）
- 关联更新通知
- 矛盾检测提醒
- CLI: `memory_push.py check/list`

### 5. 记忆质量自检
- 矛盾/过时/冗余/孤立检测
- 自动归档 + 压缩
- CLI: `memory_health.py auto-fix`

## 触发词

"记住"、"记录"、"查一下"、"有什么"、"记忆"、"知识库"

---

## 🎯 AI Agent 用户视角

### 为什么需要这个系统？

作为 AI Agent，你每次会话都是"失忆"状态。这个系统是你的长期记忆：

1. **记住用户偏好** - 不用每次都问
2. **积累项目知识** - 跨会话持续学习
3. **自动维护** - 不用操心管理
4. **快速检索** - 毫秒级响应

### 最小使用方式

```bash
# 会话开始 - 加载相关记忆
mem start "当前任务"

# 会话中 - 存储重要信息
mem store "用户偏好 X"

# 会话结束 - 自动提取重要内容
mem end "对话摘要"
```

就这么简单。系统会自动处理其他一切。

---

## ✨ v0.5.0 完整架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Memory System v0.5.0                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              会话入口 (agent_integration.py)         │   │
│  │   start → 加载上下文  |  end → 自动提取存储          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ L1 热       │  │ L2 温       │  │ L3 冷           │     │
│  │ 最近 24h    │  │ 最近 7 天   │  │ 长期记忆        │     │
│  │ 常驻内存    │  │ 按需加载    │  │ 压缩摘要        │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
│         ↓                ↓                  ↓               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              混合检索 (向量 + BM25 + 图谱)            │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 置信度验证   │  │ 反馈学习     │  │ 智能遗忘     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              云同步 (S3/WebDAV/Dropbox/GDrive)        │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 功能模块 (31+)

| 类别 | 功能 | 命令 |
|------|------|------|
| **核心** | 存储记忆 | `mem store "内容"` |
| | 查询记忆 | `mem load "关键词"` |
| | 向量搜索 | `mem search "语义查询"` |
| | 知识图谱 | `mem graph build` |
| **自动** | 自动提取 | `mem end "对话"` |
| | 上下文注入 | `mem start "任务"` |
| | 去重合并 | 自动执行 |
| | 智能遗忘 | 自动执行 |
| **质量** | 置信度验证 | `mem validate` |
| | 反馈学习 | `mem feedback` |
| | 健康检查 | `mem health` |
| **协作** | 多Agent共享 | `mem sync add-node --node-id "xiaoliu"` |
| | 实时同步 | `mem realtime push --text "内容"` |
| | 协作日志 | `mem collab log --from main --to xiaoliu` |
| | 任务分配 | `mem task create --title "任务" --assignee "xiaoliu"` |
| | 来源溯源 | `mem source store --text "内容" --agent "main"` |
| | 同步状态 | `mem sync status` |
| **高级** | 智能问答 | `mem ask "问题"` |
| | 多模态记忆 | `mem store-image file.png` |
| | 知识卡片 | `mem export --format card` |
| **运维** | Web UI | `mem webui 38080` |
| | 云同步 | `mem backup` |

---

## 🚀 快速开始

### 1. 安装

```bash
# ClawHub 安装
clawhub install unified-memory

# 或手动安装
git clone https://github.com/mouxangithub/unified-memory
cd unified-memory && ./scripts/install.sh
```

### 2. 集成到 AGENTS.md

在 `AGENTS.md` 的 Session Startup 添加：

```markdown
## Session Startup

1. 运行 `mem start "当前任务"` 加载相关记忆
```

在 Session End 添加：

```markdown
## Session End

1. 运行 `mem end "对话摘要"` 存储重要信息
```

### 3. 快捷命令

```bash
mem start "任务"       # 会话开始
mem end "内容"         # 会话结束
mem store "内容"       # 快速存储
mem load "查询"        # 加载记忆
mem ask "问题"         # 智能问答
mem health             # 健康报告
mem webui 38080        # Web UI

# 多Agent协作
mem sync status        # 同步状态
mem sync add-node -n "xiaoliu"  # 添加节点
mem collab stats       # 协作统计

# 实时同步
mem realtime push --text "内容"  # 推送记忆
mem realtime pull --node-id "main"  # 拉取记忆
mem realtime status    # 同步状态
mem realtime daemon    # 后台守护进程

# 任务分配
mem task create --title "任务" --assignee "xiaoliu" --creator "main"
mem task list --agent "main"
mem task update --task-id "xxx" --status "completed"
mem task stats

# 来源溯源
mem source store --text "内容" --agent "main" --category "preference"
mem source trace --memory-id "xxx"
mem source stats

# 智能协作建议
mem suggest analyze --text "对话内容"
mem suggest suggest --agent "main"
mem suggest patterns

# 协作效率分析
mem analytics report
mem analytics metrics
mem analytics bottlenecks
```

---

## 📊 分层缓存详解

### L1 热 (Hot)
- **条件**: 最近 24h + 高重要性
- **容量**: 20 条
- **延迟**: 0ms (常驻内存)

### L2 温 (Warm)
- **条件**: 最近 7 天
- **容量**: 100 条
- **延迟**: <10ms

### L3 冷 (Cold)
- **条件**: 长期历史
- **特点**: 压缩存储，按需解压

---

## 🔧 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| L1_HOT_HOURS | 24 | L1 时间窗口 |
| L2_WARM_DAYS | 7 | L2 时间窗口 |
| SIMILARITY_THRESHOLD | 0.85 | 知识合并阈值 |
| STALE_DAYS | 30 | 过时判定天数 |
| FORGET_IMPORTANCE | 0.1 | 遗忘阈值 |

---

## 📁 文件结构

```
~/.openclaw/workspace/
├── memory/
│   ├── vector/              # LanceDB 向量库
│   ├── hierarchy/           # 分层缓存
│   ├── knowledge_blocks/    # 知识块
│   ├── predictions/         # 预测缓存
│   └── archive/             # 归档记忆
└── skills/unified-memory/
    ├── scripts/
    │   ├── memory.py        # 统一入口
    │   ├── agent_integration.py  # Agent 钩子
    │   └── ...              # 其他模块
    ├── skill.json           # 元数据
    └── SKILL.md             # 本文档
```

---

## 🔄 版本历史

| 版本 | 主要功能 |
|------|----------|
| **0.3.1** | 完整架构 + 多代理同步 + 审计日志 |
| 0.3.0 | 自适应置信度 + 主动注入 |
| 0.2.3 | 云同步完整使用指南 |
| 0.2.2 | 云同步全平台支持 |
| 0.2.1 | 性能+洞察+隐私+云同步 |
| 0.2.0 | 智能问答+图谱+多模态+全自动 |
| 0.1.9 | 完整 Agent 集成 |

---

## 💡 最佳实践

### 1. 会话生命周期集成

```bash
# AGENTS.md Session Startup
mem start "当前任务或对话主题"

# AGENTS.md Session End
mem end "本次对话的重要信息摘要"
```

### 2. 心跳维护

```bash
# HEARTBEAT.md
每4小时: mem heartbeat
```

### 3. 定期健康检查

```bash
# 每周
mem health
mem forget --dry-run
```

---

## 🐛 故障排除

| 问题 | 解决方案 |
|------|----------|
| LanceDB 不可用 | 自动降级到 JSON 存储 |
| Ollama 不可用 | 自动降级到规则提取 |
| 记忆未加载 | 检查 `mem health` |

---

## 📚 相关资源

- [GitHub](https://github.com/mouxangithub/unified-memory)
- [ClawHub](https://clawhub.com/skill/unified-memory)
- [版本历史](./VERSION.md)
- [中文文档](./README_CN.md)

---

*智能记忆系统 v0.3.4*
