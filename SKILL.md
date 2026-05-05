# Unified Memory v5 — Skill for OpenClaw

> 🧠 AI Agent 统一记忆系统 | **自动记忆** | MCP 协议 | 一句话安装

---

## 🚀 一句话安装配置命令（发给 AI）

```
请帮我安装并配置 Unified Memory v5：
git clone https://github.com/mouxangithub/unified-memory.git && cd unified-memory && npm install && \
OLLAMA_BASE_URL=http://localhost:11434 && \
LLM_PROVIDER=ollama && LLM_MODEL=minimax-m2.7:cloud && \
EMBED_PROVIDER=ollama && EMBED_MODEL=nomic-embed-text:latest && \
VECTOR_ENGINE=lancedb && \
node src/gbrain_mcp_server.js
```

### 自动配置说明

运行后自动开启：
- ✅ **自动记忆** - 重要性评分 > 0.7 时自动存储
- ✅ **实体检测** - 自动识别文本中的实体
- ✅ **相似记忆关联** - 自动关联已有记忆

---

## ✨ 功能概述

| 功能 | 工具 | 说明 |
|------|------|------|
| 🧠 记忆存储 | `remember` | **自动评估重要性 > 0.7 时自动存储** |
| 🔍 语义搜索 | `search` | 混合搜索+过滤 |
| 📊 图谱查询 | `graph_stats` | 关联网络统计 |
| 🧹 记忆清理 | `cleanup` | 清理低价值记忆 |
| 💬 上下文 | `get_context` | 系统状态 |
| 🔬 重要性分析 | `auto_analyze` | **仅分析不存储** |

---

## 🧠 自动记忆功能

### 工作原理

```
用户输入 → 重要性评分 → 评分 > 0.7？→ ✅ 自动存储
                                      ↓ 否
                                  ❌ 不存储（返回分析）
```

### 重要性评分算法（7维度）

| 维度 | 权重 | 说明 |
|------|------|------|
| 内容长度 | +0.1 | 10-500词适当加分 |
| 决策/偏好信号 | +0.2 | "决定"、"偏好"、"需要"等 |
| 情感/情绪信号 | +0.15 | "重要"、"紧急"、"担心"等 |
| 事实/信息性内容 | +0.15 | 陈述句加分 |
| 项目/任务关联 | +0.15 | "项目"、"任务"、"计划"等 |
| 实体检测 | +0.1 | 检测到实体加分 |
| 问句 | -0.1 | 问句内容降低分数 |

### 示例

| 用户输入 | 评分 | 结果 |
|----------|------|------|
| "我决定了，下次去上海出差住浦东香格里拉" | 0.82 | ✅ 自动存储 |
| "我需要买咖啡豆，G7 曼特宁那个" | 0.78 | ✅ 自动存储 |
| "今天天气怎么样？" | 0.35 | ❌ 不存储 |
| "顺便帮我查一下明天是否下雨" | 0.42 | ❌ 不存储 |

### 手动控制

```javascript
// 手动指定重要性（跳过自动评估）
await remember({
  text: "用户偏好：喜欢冷萃咖啡",
  importance: 0.9,  // 强制存储
  auto: false       // 禁用自动评估
});

// 预分析（仅查看评分，不存储）
await auto_analyze({
  text: "用户决定去上海出差"
});
// 返回: { score: 0.75, reasons: ["决策信号", "项目相关"], suggestion: "建议存储" }
```

---

## 环境变量配置

创建 `.env` 文件：

```bash
# ─── LLM 配置 ───
LLM_PROVIDER=ollama
LLM_MODEL=minimax-m2.7:cloud
LLM_BASE_URL=http://localhost:11434

# ─── Embedding 配置 ───
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text:latest
EMBED_BASE_URL=http://localhost:11434
EMBED_DIMENSION=768

# ─── 存储配置 ───
VECTOR_ENGINE=lancedb
DATA_DIR=~/.openclaw/workspace/memory

# ─── 自动记忆配置 ───
AUTO_MEMORY_THRESHOLD=0.7  # 重要性阈值，默认 0.7
```

---

## OpenClaw MCP 配置

### 方式 1: mcp-config.json

```json
{
  "mcpServers": {
    "unified-memory-v5": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "minimax-m2.7:cloud",
        "EMBED_PROVIDER": "ollama",
        "EMBED_MODEL": "nomic-embed-text:latest",
        "VECTOR_ENGINE": "lancedb",
        "AUTO_MEMORY_THRESHOLD": "0.7"
      }
    }
  }
}
```

### 方式 2: SKILL.md 安装 (Hermes)

```bash
mkdir -p ~/.hermes/skills/memory/unified-memory
cp SKILL.md ~/.hermes/skills/memory/unified-memory/
```

---

## MCP 接口兼容

- ✅ **OpenClaw** - 直接配置 `mcp.servers`
- ✅ **Claude Desktop** - 配置 `mcpServers`
- ✅ **Hermes** - 安装 SKILL.md 到 `~/.hermes/skills/`
- ✅ **其他 MCP 客户端** - 通用 stdio 协议

---

## 高级功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **API Gateway** | `src/advanced/api_gateway/` | JWT/API Key认证、限流、OpenAPI |
| **Version Control** | `src/advanced/version_control/` | 乐观锁、冲突解决、差异计算 |
| **Cache Manager** | `src/advanced/cache_manager/` | L1/L2多级缓存、淘汰策略 |
| **Monitoring** | `src/advanced/monitoring/` | Prometheus指标、健康检查 |
| **Backup/Restore** | `src/advanced/backup_restore/` | 增量/全量备份、恢复 |
| **Archival** | `src/advanced/archival/` | 冷热分层、自动归档 |
| **Benchmark** | `src/advanced/benchmark/` | 性能基准测试、对比分析 |

---

## 快速使用

```javascript
// Node.js
const { exec } = require('child_process');

// 启动 MCP 服务器（自动记忆功能已内置）
exec('node src/gbrain_mcp_server.js', {
  env: {
    OLLAMA_BASE_URL: 'http://localhost:11434',
    AUTO_MEMORY_THRESHOLD: '0.7',
    ...process.env
  }
});
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.1.0 | 2026-05-05 | 🆕 自动记忆功能 - 重要性评分 > 0.7 自动存储 |
| v1.0.0 | 2026-04-20 | 初始版本 - 基础记忆、搜索、图谱功能 |

---

## 测试

```bash
npm test
```

---

## 许可证

MIT