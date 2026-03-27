---
name: unified-memory
version: 1.5.1
description: 统一记忆系统 - AI Agent 专用记忆系统，支持 Context Tree、智能摘要、知识图谱、工作流引擎。零依赖，完整对标 QMD/MetaGPT
author: mouxangithub
tags: [memory, context-tree, knowledge-graph, workflow-engine, vector-search]
triggers:
  - 记忆
  - 上下文
  - 智能摘要
  - 知识图谱
  - memory
  - context
---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
./scripts/install.sh
```

### 基础使用

```bash
# 初始化项目（带模板）
mem init --template software-project "我的项目" --desc "项目描述"

# 存储记忆
mem store "重要决策：使用微服务架构" --tags "架构,决策"

# 搜索记忆
mem search "架构"

# 项目上下文
mem ctx open "官网重构"
mem ctx update "完成首页设计" --progress 50
mem ctx decision "选择配色" "使用深蓝色调"

# 健康检查
mem health
```

---

## 📖 核心架构

### 分层上下文系统

```
Layer 1: 记忆上下文 (qmd://, user:, project:)
  └─ 自动分类: 个人笔记、会议记录、项目知识

Layer 2: 项目上下文 (.context/ 目录)
  ├─ current.md    # 当前状态 + 进度
  ├─ decisions/    # 决策日志
  ├─ architecture.md
  └─ summary.md
```

### 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **Context Tree** | `context/context_tree.py` | 统一分层上下文管理 |
| **Smart Summarizer** | `intelligence/smart_summarizer.py` | 自动压缩历史、提取决策 |
| **Workflow Engine** | `workflow_engine.py` | SOP + DAG 混合工作流 |
| **Knowledge Graph** | `memory_graph.py` | 实体关系图谱 |
| **Project Templates** | `templates/project_templates.py` | 3种项目模板 |
| **Visualizer** | `visualizer/workflow_visualizer.py` | HTML 可视化仪表盘 |

---

## 🔧 CLI 命令

### mem - 统一入口

```bash
# 记忆操作
mem store "内容" --tags "标签"     # 存储记忆
mem search "查询"                   # 搜索记忆
mem health                         # 健康检查

# 项目上下文
mem ctx init "项目名" --desc "描述"  # 初始化项目
mem ctx open "项目名"                # 打开项目
mem ctx update "任务" --progress 50  # 更新进度
mem ctx decision "标题" "内容"       # 记录决策
mem ctx status                       # 查看状态
mem ctx list                         # 列出项目

# 模板
mem init --template software-project "项目名"  # 快速创建
mem template list                                # 查看模板

# 智能摘要
mem summary compress --days 7     # 压缩日志
mem summary decisions --days 30   # 提取决策
```

---

## 📊 session_start 集成

每次会话启动时自动加载：

```python
mem_int session-start --context "当前任务"
```

**加载内容**：
- ✅ 相关记忆（向量相似度 Top 10）
- ✅ 最佳上下文（自动检测 qmd:// / user: / project:）
- ✅ 项目状态（进度、决策）
- ✅ 知识图谱关联实体
- ✅ 个性化建议

---

## 🆚 对比优势

| 维度 | 我们 | QMD | MetaGPT |
|------|------|-----|---------|
| **依赖** | 0 ✅ | ~5 | 70+ |
| **Context Tree** | ✅ 双层 | ✅ | ⚠️ |
| **智能摘要** | ✅ | ✅ | ❌ |
| **多模态 OCR/STT** | ✅ | ❌ | ⚠️ |
| **知识图谱** | ✅ | ❌ | ❌ |
| **零依赖** | ✅ | ❌ | ❌ |

---

## 🧠 Context Tree 详解

### 记忆上下文前缀

| 前缀 | 用途 | 示例 |
|------|------|------|
| `qmd://notes` | 个人笔记 | `qmd://notes/projects` |
| `qmd://meetings` | 会议记录 | `qmd://docs` |
| `user:` | 用户偏好 | `user:刘总` |
| `project:` | 项目知识 | `project:官网重构` |

### 项目 .context/ 结构

```
projects/
└── 官网重构/
    └── .context/
        ├── current.md       # 当前任务 + 进度
        ├── decisions/       # 决策日志
        │   └── 20260323-选择配色.md
        ├── architecture.md  # 架构文档
        └── summary.md       # 项目摘要
```

---

## 🌳 知识图谱

自动从记忆中提取实体和关系：

```bash
mem graph build --format html --output /tmp/graph.html
```

**实体类型**: person, project, tool, action, time
**关系类型**: 喜欢、使用、决定、创建、完成

---

## 📝 更新日志

### v1.5.0 (2026-03-23)
- ✅ Context Tree 统一架构（记忆上下文 + 项目上下文）
- ✅ session_start 深度集成（Context Tree + Knowledge Graph）
- ✅ mem ctx open/list 命令
- ✅ mem init --template 快捷命令
- ✅ Smart Summarizer 定时脚本
- ✅ Knowledge Graph search_context() 函数
- ✅ Visualizer HTML 可视化

### v1.4.0 (2026-03-23)
- 全面对标 QMD/MetaGPT
- 新增 OCR/STT 多模态支持
- 新增智能分类 + 自动标签
- 新增 Web UI + API 服务

---

*Author: mouxangithub | License: MIT*
*GitHub: https://github.com/mouxangithub/unified-memory*
