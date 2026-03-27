# 🧠 Unified Memory - 统一记忆系统

> AI Agent 专用记忆系统 v1.5.0 | 零依赖 | Context Tree + 知识图谱 + 工作流引擎

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

## 🎯 核心价值

**为什么需要统一记忆系统？**

AI Agent 每次会话从头开始 —— 记忆系统让 AI 记住：
- 用户的偏好和习惯
- 项目进展和决策
- 关键上下文和关系
- 历史交互模式

## ✨ 功能特性

### 1. Context Tree（上下文树）🆕
**双层架构**：记忆上下文 + 项目上下文

```
Layer 1: 记忆上下文
  qmd://notes, qmd://meetings, user:, project:

Layer 2: 项目上下文 (.context/)
  current.md + decisions/ + architecture.md
```

### 2. Knowledge Graph（知识图谱）🆕
自动提取实体和关系，构建记忆网络

```
实体类型: person, project, tool, action, time
关系类型: 喜欢, 使用, 决定, 创建, 完成
```

### 3. Smart Summarizer（智能摘要）
自动压缩历史日志，提取关键决策

```bash
mem summary compress --days 7    # 压缩 7 天日志
mem summary decisions --days 30 # 提取决策
```

### 4. Workflow Engine（工作流引擎）
SOP + DAG 混合引擎，支持 6 步软件工程流程

```bash
python3 workflow_engine.py demo --type hybrid
```

### 5. Project Templates（项目模板）
3 种项目模板，开箱即用

- `software-project` - 软件开发项目
- `content-creation` - 内容创作项目
- `research` - 研究项目

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
./scripts/install.sh
```

### 基础使用

```bash
# 初始化项目
mem init --template software-project "我的项目"

# 存储记忆
mem store "用户偏好深色主题" --tags "preference"

# 搜索
mem search "主题"

# 项目管理
mem ctx open "官网重构"
mem ctx update "完成首页" --progress 50
mem ctx decision "选择技术栈" "使用 Next.js"

# 健康检查
mem health
```

## 📁 项目结构

```
unified-memory/
├── SKILL.md                    # 技能说明
├── README.md                   # 本文档
├── CHANGELOG.md               # 变更日志
├── scripts/
│   ├── mem                     # 统一 CLI 入口
│   ├── context/
│   │   └── context_tree.py    # 🆕 统一上下文管理
│   ├── intelligence/
│   │   └── smart_summarizer.py # 智能摘要
│   ├── templates/
│   │   └── project_templates.py # 项目模板
│   ├── memory_graph.py         # 🆕 知识图谱
│   ├── workflow_engine.py       # 工作流引擎
│   ├── memory_integration.py    # 🆕 Agent 集成钩子
│   └── visualizer/
│       └── workflow_visualizer.py # HTML 可视化
```

## 🧩 模块详解

### mem - 统一 CLI

```bash
# 记忆
mem store "text" --tags "tag1,tag2"
mem search "query"
mem health

# 上下文
mem ctx init "项目名"
mem ctx open "项目名"
mem ctx update "任务" --progress 50
mem ctx decision "标题" "内容"
mem ctx status
mem ctx list

# 模板
mem init --template software-project "项目名"
mem template list

# 摘要
mem summary compress --days 7
mem summary decisions --days 30
```

### session_start 集成

Agent 会话启动时自动加载上下文：

```python
# 集成到 agent 流程
mem-int session-start --context "当前任务"

# 返回:
# - 相关记忆 (Top 10)
# - 最佳上下文路径
# - 项目状态
# - 知识图谱实体
# - 个性化建议
```

## 🆚 对比

| 特性 | Unified Memory | QMD | MetaGPT |
|------|---------------|-----|---------|
| **依赖数量** | 0 ✅ | ~5 | 70+ |
| **Context Tree** | ✅ 双层 | ✅ | ⚠️ |
| **知识图谱** | ✅ | ❌ | ❌ |
| **智能摘要** | ✅ | ✅ | ❌ |
| **多模态** | ✅ | ❌ | ⚠️ |
| **工作流引擎** | ✅ SOP+DAG | ❌ | ✅ |
| **零依赖** | ✅ | ❌ | ❌ |

## 📊 健康检查

```bash
$ mem health
🏥 系统健康检查

1️⃣ 向量库... ✅ (1 表)
2️⃣ Ollama... ✅ (2 模型)
3️⃣ Context Tree... ✅
4️⃣ Smart Summarizer... ✅

========================================
✅ 系统健康
```

## 🔗 链接

- **GitHub**: https://github.com/mouxangithub/unified-memory
- **文档**: [SKILL.md](./SKILL.md)
- **变更日志**: [CHANGELOG.md](./CHANGELOG.md)

## 📜 许可证

MIT License - 自由使用、修改、分发

---

*最后更新: 2026-03-23 | v1.5.0*
