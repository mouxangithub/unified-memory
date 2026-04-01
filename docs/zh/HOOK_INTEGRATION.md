# Hook 集成指南

[English](./en/HOOK_INTEGRATION.md) | [概述](./README.md) | 中文

## 概述

Unified Memory 的 Hook 系统提供**完全透明的自动记忆捕获**。启用后，代理在每次对话结束后自动保存重要上下文 — 无需手动干预。

## Hook 工作原理

Hook 系统集成到两个关键生命周期点：

### 1. `before_prompt_build` — 上下文注入

在构建每个提示之前，Hook 系统会：

1. 根据当前上下文从存储中检索相关记忆
2. 将这些记忆作为 `<memory>` 块注入到提示中
3. 将已注入的记忆标记为"最近访问"以追踪重要性

```
用户查询 → Hook 拦截 → 检索相关记忆 → 注入到提示 → 继续执行
```

**注入格式：**

```markdown
<memory>
## 最近上下文
- [2026-03-28] 用户询问如何在 macOS 上设置 OpenClaw
- [2026-03-25] 讨论了深色模式终端的偏好
</memory>
```

### 2. `agent_end` — 自动提取

每次对话完成后，Hook 系统会：

1. 分析对话记录
2. 提取关键事实、决定、偏好和承诺
3. 创建带有重要性评分的语义块
4. 将块存储到统一记忆数据库

```
对话结束 → 分析记录 → 提取关键信息 → 评分并存储
```

## 配置选项

### 基础配置

```json
{
  "unified-memory": {
    "hook": "enabled",
    "config": {
      "before_prompt_build": {
        "enabled": true,
        "maxMemories": 10,
        "similarityThreshold": 0.7,
        "injectionFormat": "block"
      },
      "agent_end": {
        "enabled": true,
        "autoExtract": true,
        "minImportanceScore": 0.3,
        "maxChunksPerSession": 50
      }
    }
  }
}
```

### 高级选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `maxMemories` | number | 10 | 每次提示注入的最大记忆数 |
| `similarityThreshold` | number | 0.7 | 最低相似度分数 (0-1) |
| `minImportanceScore` | number | 0.3 | 保存块所需的最低分数 |
| `maxChunksPerSession` | number | 50 | 每次对话的最大块数 |
| `injectionFormat` | string | "block" | 记忆显示方式: "block", "inline", 或 "json" |
| `excludedContexts` | string[] | [] | 从提取中排除的模式 |

### 上下文排除示例

```json
{
  "config": {
    "agent_end": {
      "excludedContexts": [
        "password:*",
        "api_key:*",
        "secret:*"
      ]
    }
  }
}
```

## 性能影响

### 延迟开销

| 阶段 | 典型值 | 启用 Hook |
|------|--------|-----------|
| 提示构建 | 10-50ms | 15-80ms |
| 记忆检索 | — | 5-30ms |
| 存储写入 | — | 2-10ms |
| **总计** | **10-50ms** | **22-120ms** |

### 资源使用

- **CPU**: 检索期间额外 ~1-3%
- **内存**: 索引缓存约 5-20MB
- **存储**: 每个会话约 1-10KB
- **向量嵌入**: 每个块约 1KB（如使用语义搜索）

### 优化建议

1. **提高阈值** — 如果记忆库很大，可以减少检索时间
2. **限制 maxChunksPerSession** — 缩短提取时间
3. **使用 injectionFormat: "inline"** — 减少 token 开销

## Hook 运行时机

```
┌─────────────────────────────────────────────────────────┐
│                    会话生命周期                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  会话开始                                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │ before_prompt_build │ ◀── 每次提示前运行             │
│  │   (记忆注入)        │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │   Agent 处理中      │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │     agent_end       │ ◀── 每次会话结束后运行          │
│  │  (记忆提取)         │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  会话结束                                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 禁用 Hooks

要禁用基于 Hook 的捕获但保留 MCP 访问：

```json
{
  "unified-memory": {
    "hook": "disabled",
    "config": {
      "mcpEnabled": true
    }
  }
}
```

## 故障排除

**记忆没有被注入：**
- 检查 `before_prompt_build.enabled` 是否为 `true`
- 验证记忆存储中是否有条目
- 如果记忆存在但未匹配，降低 `similarityThreshold`

**提取效果不佳：**
- 增加 `maxChunksPerSession` 以便更彻底地提取
- 降低 `minImportanceScore` 以捕获低置信度记忆

**性能较慢：**
- 提高 `similarityThreshold` 以减少结果集
- 减少 `maxMemories` 以限制注入数量
