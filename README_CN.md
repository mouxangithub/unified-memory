# 🧠 Unified Memory v2.0

## 🇨🇳 中文文档

> **🤖 本项目由小智 AI（OpenClaw）创建生成**  
> 作者：刘选权（刘总）| 框架：OpenClaw Agent | 86 个 MCP 工具

---

## 📖 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | **主文档（推荐）** - 含完整接入指南 |
| [README_EN.md](README_EN.md) | 英文版完整文档 |
| [SKILL.md](SKILL.md) | OpenClaw Skill 规范（中文工具说明） |
| [SKILL_EN.md](SKILL_EN.md) | OpenClaw Skill 规范（English） |
| [CHANGELOG.md](CHANGELOG.md) | 更新日志 |

---

## 🚀 快速开始

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### OpenClaw 用户

```bash
clawhub install unified-memory
openclaw gateway restart
```

### 快速测试

```bash
# 搜索记忆
node src/cli/index.js search "测试"

# 存储记忆
node src/cli/index.js store "学习了什么" --category learning --importance 0.8

# 启动 REST API
node src/cli/index.js server --port 38421
```

---

## 📦 核心工具（必记）

| 工具 | 用途 |
|------|------|
| `memory_search` | 混合搜索（BM25+向量） |
| `memory_store` | 存储记忆 |
| `memory_episode_start/end` | 开启/结束会话片段 |
| `memory_procedure_add` | 添加流程记忆 |
| `memory_rule_check` | 检查规则 |

完整工具列表见 [SKILL.md](SKILL.md)

---

## 🔧 配置

```bash
# 环境变量（可选）
export OLLAMA_HOST=http://192.168.2.155:11434

# 或配置文件
echo '{"ollamaUrl":"http://192.168.2.155:11434"}' > ~/.openclaw/workspace/memory/config.json
```

---

## 📊 服务状态

```bash
# 查看服务
mcporter list 2>/dev/null | grep unified-memory

# 健康检查
curl http://localhost:38421/health
```

---

*更多内容见 [README.md](README.md)*
