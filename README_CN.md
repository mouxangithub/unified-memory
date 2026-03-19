# Unified Memory - AI Agent 记忆系统

> **版本 0.4.0** | 专为 AI Agent 设计的智能记忆系统，支持分层缓存、知识合并、预测加载、自动维护、主动注入、自适应置信度、审计日志和多代理同步。

[![ClawHub](https://img.shields.io/badge/ClawHub-已发布-green)](https://clawhub.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**[English Documentation](./README.md)** | 中文文档

---

## 📦 云同步功能 (v0.2.2)

### 支持的云存储类型

| 类型 | 说明 | 状态 |
|------|------|------|
| **local** | 本地文件系统备份 | ✅ 已实现 |
| **s3** | AWS S3 兼容存储 (MinIO, 阿里云OSS, 腾讯云COS 等) | ✅ 已实现 |
| **webdav** | WebDAV 协议 (坚果云, Nextcloud 等) | ✅ 已实现 |
| **dropbox** | Dropbox 云存储 | ✅ 已实现 |
| **gdrive** | Google Drive 云存储 | ✅ 已实现 |

### 快速配置

#### 1. 本地备份（默认）

```bash
# 启用本地备份
python3 scripts/memory_cloud.py enable --storage local

# 创建备份
python3 scripts/memory_cloud.py backup

# 查看备份列表
python3 scripts/memory_cloud.py list

# 恢复备份
python3 scripts/memory_cloud.py restore --timestamp 20260318_120000
```

#### 2. AWS S3 / 兼容存储

```bash
# 配置 S3 (支持 MinIO, 阿里云OSS, 腾讯云COS 等)
python3 scripts/memory_cloud.py configure-s3 \
  --endpoint https://s3.amazonaws.com \
  --bucket my-memory-backup \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region us-east-1

# 创建备份并上传
python3 scripts/memory_cloud.py backup
```

**安装依赖**：
```bash
pip install boto3
```

#### 3. WebDAV (坚果云/Nextcloud)

```bash
# 配置 WebDAV
python3 scripts/memory_cloud.py configure-webdav \
  --url https://dav.jianguoyun.com/dav/ \
  --username your@email.com \
  --password your-app-password \
  --path /memory_backup

# 创建备份
python3 scripts/memory_cloud.py backup
```

**坚果云设置**：
1. 登录坚果云 → 账户信息 → 安全选项
2. 添加应用密码 → 生成第三方应用密码
3. 使用该密码作为 `--password`

**安装依赖**：
```bash
pip install webdavclient3
```

#### 4. Dropbox

```bash
# 配置 Dropbox
python3 scripts/memory_cloud.py configure-dropbox \
  --token YOUR_ACCESS_TOKEN

# 创建备份
python3 scripts/memory_cloud.py backup
```

**获取 Access Token**：
1. 访问 https://www.dropbox.com/developers/apps
2. 创建应用 → 选择 Dropbox API → Full Dropbox
3. 在 Settings 中生成 Access Token

**安装依赖**：
```bash
pip install dropbox
```

#### 5. Google Drive

```bash
# 配置 Google Drive
python3 scripts/memory_cloud.py configure-gdrive \
  --credentials /path/to/credentials.json \
  --token-file /path/to/token.json \
  --folder-id YOUR_FOLDER_ID

# 创建备份
python3 scripts/memory_cloud.py backup
```

**获取凭证**：
1. 访问 Google Cloud Console
2. 创建项目 → 启用 Google Drive API
3. 创建 OAuth 2.0 凭证 → 下载 credentials.json

**安装依赖**：
```bash
pip install google-api-python-client google-auth-oauthlib
```

### 📖 详细使用指南

查看 [examples/memory_cloud_usage.md](./examples/memory_cloud_usage.md) 获取：
- 各平台的完整配置教程
- 多设备同步工作流
- 故障排除指南
- 安全建议

### 云同步命令

```bash
# 查看同步状态
python3 scripts/memory_cloud.py status

# 创建备份
python3 scripts/memory_cloud.py backup

# 列出备份
python3 scripts/memory_cloud.py list

# 恢复备份
python3 scripts/memory_cloud.py restore --timestamp TIMESTAMP

# 禁用云同步
python3 scripts/memory_cloud.py disable
```

---

## 🤖 Ollama 集成（可选）

### ✨ 亮点：无 Ollama 也能用！

本系统采用**优雅降级**设计，即使没有 Ollama 也能完美运行！

| 模式 | Ollama 状态 | 搜索方式 | 功能完整性 |
|------|------------|---------|-----------|
| **完整模式** | ✅ 在线 | 向量语义搜索 | 全功能 |
| **降级模式** | ❌ 离线 | 关键词匹配 | 核心功能可用 |

### 有 Ollama vs 无 Ollama 对比

| 功能 | 有 Ollama | 无 Ollama |
|------|-----------|-----------|
| **搜索质量** | 语义理解（找到相关概念） | 关键词匹配（找精确词） |
| **自动提取** | AI 智能提取 | 规则提取 |
| **记忆摘要** | LLM 生成摘要 | 模板摘要 |
| **重要性评分** | ML 智能评分 | 规则评分 |
| **存储与 CRUD** | ✅ 完整支持 | ✅ 完整支持 |
| **WebUI 管理** | ✅ 完整支持 | ✅ 完整支持 |
| **备份/恢复** | ✅ 完整支持 | ✅ 完整支持 |

### Ollama 配置

```bash
# 设置 Ollama 主机（默认：http://localhost:11434）
export OLLAMA_HOST=http://192.168.2.155:11434

# 必需：embedding 模型
ollama pull nomic-embed-text:latest

# 可选：LLM 模型（高级功能）
ollama pull deepseek-v3.2:cloud
```

**网络访问**：如果 Ollama 在其他机器上（如 NAS Docker），使用局内网络 IP：
```bash
export OLLAMA_HOST=http://192.168.2.155:11434
```

---

## ✨ 功能总览

### 功能总数：31 个

| 类别 | 功能 | 说明 |
|------|------|------|
| **核心** | 存储记忆 | 向量语义存储 |
| | 搜索记忆 | 混合检索 (向量+BM25) |
| | 上下文加载 | 自动加载相关记忆 |
| **智能** | 智能问答 | RAG 问答，直接生成答案 |
| | 知识图谱 | 记忆关系可视化 |
| | 用户洞察 | 偏好分析、趋势建议 |
| | 智能提醒 | 时间敏感记忆提醒 |
| **质量** | 健康检测 | 系统健康评分 |
| | 对话去重 | 自动检测合并重复 |
| | 隐私扫描 | 敏感信息检测 |
| | 质量报告 | 准确率/时效性/利用率 |
| **数据** | 导入导出 | JSON/CSV/Markdown |
| | 云备份 | 5 种云存储支持 |
| | 恢复 | 从备份恢复 |
| **可视化** | Web UI | 浏览器访问 (端口 38080) |
| | 知识图谱 | HTML 可视化 |
| | 知识卡片 | 精美卡片导出 |
| | 记忆摘要 | 自动生成摘要 |
| **性能** | L1/L2/L3 缓存 | 热记忆快速访问 |
| | 批量预热 | 启动时预加载热点 |
| | 并发查询 | 多条件并行搜索 |
| | 异步存储 | 非阻塞写入 |
| **多模态** | 图片记忆 | 存储图片描述 |
| | 语音记忆 | 语音转文字 |
| | 文件记忆 | 文件信息提取 |
| **自动化** | 自动存储 | 智能判断重要性 |
| | 自动提取 | 从对话提取记忆 |
| | 自动去重 | 自动合并重复 |
| **Agent 集成** | 会话开始钩子 | 自动加载上下文 |
| | 会话结束钩子 | 自动存储重要信息 |
| | 心跳检查 | 定期健康检查 |

---

## 🚀 快速开始

### 安装

```bash
# 从 ClawHub 安装
clawhub install unified-memory

# 或手动安装
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
./scripts/install.sh
```

### 基础使用

```bash
# 查看状态
mem health

# 存储记忆
mem store "用户偏好使用飞书进行协作"

# 搜索记忆
mem load "飞书"

# 智能问答
mem ask "我的项目进展如何"

# 启动 Web UI
mem webui 38080
```

---

## 📖 详细文档

### 快捷命令 (mem)

```bash
mem start "任务"          # 会话开始，加载上下文
mem end "内容"            # 会话结束，存储记忆
mem heartbeat             # 心跳检查
mem store "内容"          # 快速存储
mem load "查询"           # 加载记忆
mem remind                # 检查提醒
mem health                # 健康报告
mem webui 38080           # Web UI
mem ask "问题"            # 智能问答
mem graph build           # 构建知识图谱
mem graph export          # 导出 HTML
mem insights analyze      # 用户洞察分析
mem insights trends       # 行为趋势
mem backup                # 云备份
mem privacy               # 隐私扫描
```

### 配置

#### 环境变量

```bash
# Ollama (用于 embedding 和 LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=deepseek-v3.2:cloud
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

#### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `L1_HOT_HOURS` | 24 | L1 热记忆时间窗口 |
| `L2_WARM_DAYS` | 7 | L2 温记忆时间窗口 |
| `L1_MAX_SIZE` | 20 | L1 最大容量 |
| `L2_MAX_SIZE` | 100 | L2 最大容量 |
| `SIMILARITY_THRESHOLD` | 0.85 | 知识合并相似度阈值 |
| `STALE_DAYS` | 30 | 过时记忆判定天数 |
| `FORGET_IMPORTANCE` | 0.1 | 遗忘重要性阈值 |

---

## 📁 文件结构

```
~/.openclaw/workspace/
├── memory/
│   ├── vector/                # LanceDB 向量数据库
│   ├── hierarchy/             # 分层缓存
│   ├── knowledge_blocks/      # 知识块
│   ├── predictions/           # 预测缓存
│   ├── validation/            # 验证状态
│   ├── feedback/              # 反馈数据
│   ├── archive/               # 归档记忆
│   ├── memory_backup/         # 本地备份
│   ├── cloud_config.json      # 云同步配置
│   └── memory_graph.html      # 知识图谱
└── skills/unified-memory/
    ├── scripts/
    │   ├── memory.py              # 统一入口
    │   ├── memory_cloud.py        # 云同步
    │   ├── memory_qa.py           # 智能问答
    │   ├── memory_graph.py        # 知识图谱
    │   ├── memory_insights.py     # 智能洞察
    │   ├── memory_privacy.py      # 隐私保护
    │   ├── memory_perf.py         # 性能优化
    │   ├── memory_multimodal.py   # 多模态
    │   ├── memory_auto.py         # 全自动化
    │   └── mem                    # 快捷命令
    ├── README.md                  # 英文文档
    ├── README_CN.md               # 中文文档
    ├── SKILL.md
    └── VERSION.md
```

---

## 🔧 依赖

### 必需
- Python 3.8+
- `requests` - HTTP 请求

### 推荐
- `lancedb` - 向量数据库
- Ollama - 本地 embedding 和 LLM

### 云同步可选
- `boto3` - AWS S3
- `webdavclient3` - WebDAV
- `dropbox` - Dropbox
- `google-api-python-client` - Google Drive

### 安装

```bash
# 基础依赖
pip install requests lancedb

# 云同步依赖 (按需安装)
pip install boto3              # S3
pip install webdavclient3      # WebDAV
pip install dropbox            # Dropbox
pip install google-api-python-client google-auth-oauthlib  # Google Drive
```

---

## 🗺️ 路线图

### v0.3.2 (当前)
- ✅ 多云同步支持 (S3/WebDAV/Dropbox/GDrive)
- ✅ 双语文档

### v0.3.0
- [ ] 团队知识共享
- [ ] 实时同步

### v1.0.0
- [ ] 生产级稳定性
- [ ] 完整测试覆盖

---

## 🤝 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md) 了解详情。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- 为 [OpenClaw](https://openclaw.ai) AI Agent 框架构建
- 灵感来源于人类记忆系统和认知架构
- 由 [LanceDB](https://lancedb.github.io/lancedb/) 向量数据库驱动

---

**用 ❤️ 为 AI Agent 打造**

---

## 📚 文档索引

- [English Documentation](./README.md)
- [中文文档](./README_CN.md) (当前)
- [版本历史](./VERSION.md)
- [技能说明](./SKILL.md)
