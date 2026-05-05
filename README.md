# 🧠 Unified Memory v5

> AI Agent 的统一记忆系统 | MCP 协议 | 开箱即用

**一行安装，即刻拥有记忆能力。**

---

## ⚡ 一句话安装（发给 AI）

```
请帮我安装 Unified Memory v5：
1. git clone https://github.com/mouxangithub/unified-memory.git
2. cd unified-memory && npm install
3. 启动服务：node src/gbrain_mcp_server.js
4. 配置 MCP 客户端连接
```

---

## ✨ 核心能力

| 功能 | 说明 |
|------|------|
| 🧠 **记忆存储** | 情景/语义/实体记忆，自动提取实体和关系 |
| 🔍 **语义搜索** | 向量 + BM25 混合搜索，RRF 融合 |
| 🔗 **关系图谱** | 记忆关联网络，发现隐藏联系 |
| 📊 **实体检测** | 自动识别人物/组织/地点/概念 |
| 🔌 **MCP 接口** | 标准协议，兼容 OpenClaw/Claude/Hermes |

---

## 🚀 快速开始

### 方式 1：直接运行

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
node src/gbrain_mcp_server.js
```

### 方式 2：配置到 AI 工具

**OpenClaw** (`openclaw.json`):
```json
{
  "mcp": {
    "servers": {
      "agent-brain": {
        "command": "node",
        "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"]
      }
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/gbrain_mcp_server.js"]
    }
  }
}
```

---

## 🛠️ 可用工具

| 工具 | 用途 |
|------|------|
| `remember` | 存储记忆，自动实体检测+关联 |
| `search` | 语义搜索，支持实体/项目/话题过滤 |
| `get_context` | 获取记忆系统状态 |
| `graph_stats` | 查看图谱统计 |
| `cleanup` | 清理低价值记忆 |

---

## 📁 项目结构

```
unified-memory/
├── src/
│   ├── gbrain_mcp_server.js     # MCP 服务器入口
│   ├── gbrain-integration.js    # GBrain 集成模块
│   ├── memory_graph.js          # 记忆关联网络
│   ├── entity_detection.js      # 实体检测
│   ├── typed_links.js           # 类型化链接
│   ├── source_attribution.js    # 来源追溯
│   ├── resolver.js               # 决策树
│   ├── memory_two_layer.js      # 两层页面格式
│   └── brain_cli.js             # CLI 工具
├── docs/
│   ├── ARCHITECTURE.md          # 系统架构
│   ├── MCP_INTERFACE.md         # MCP 接口规范
│   └── QUICK_START.md           # 快速安装
├── SKILL.md                     # OpenClaw Skill 定义
└── package.json
```

---

## 🔧 技术栈

- **运行时**: Node.js 18+
- **协议**: MCP (Model Context Protocol)
- **存储**: JSON 文件 (开发) / PostgreSQL (生产)
- **向量**: LanceDB (可选)
- **依赖**: @modelcontextprotocol/sdk

---

## 📦 发布版本

- **npm**: 即将发布
- **GitHub**: https://github.com/mouxangithub/unified-memory
- **ClawHub**: https://clawhub.ai/skill/unified-memory-v5

---

## 📖 文档

- [快速安装](QUICK_START.md) - 一句话发给 AI
- [架构设计](docs/ARCHITECTURE.md) - 核心模块说明
- [MCP 接口](docs/MCP_INTERFACE.md) - 工具/资源/提示模板

---

> "让 AI 拥有记忆，让记忆成为智能的基石。"
