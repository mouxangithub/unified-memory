# Unified Memory - AI Agent Memory System

> **Version 0.4.0** | An intelligent memory system designed for AI Agents with hierarchical caching, knowledge merging, predictive loading, automatic maintenance, proactive injection, adaptive confidence, audit logging, and multi-agent sync.

[![ClawHub](https://img.shields.io/badge/ClawHub-Publish-green)](https://clawhub.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

English Documentation | [中文文档](./README_CN.md)

---

## ☁️ Cloud Sync (v0.2.2)

### Supported Cloud Storage

| Type | Description | Status |
|------|-------------|--------|
| **local** | Local filesystem backup | ✅ Implemented |
| **s3** | AWS S3 compatible (MinIO, Aliyun OSS, Tencent COS, etc.) | ✅ Implemented |
| **webdav** | WebDAV protocol (Nutstore, Nextcloud, etc.) | ✅ Implemented |
| **dropbox** | Dropbox cloud storage | ✅ Implemented |
| **gdrive** | Google Drive cloud storage | ✅ Implemented |

### Quick Setup

#### 1. Local Backup (Default)

```bash
# Enable local backup
python3 scripts/memory_cloud.py enable --storage local

# Create backup
python3 scripts/memory_cloud.py backup

# List backups
python3 scripts/memory_cloud.py list

# Restore backup
python3 scripts/memory_cloud.py restore --timestamp 20260318_120000
```

#### 2. AWS S3 / Compatible Storage

```bash
# Configure S3
python3 scripts/memory_cloud.py configure-s3 \
  --endpoint https://s3.amazonaws.com \
  --bucket my-memory-backup \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region us-east-1

# Create backup and upload
python3 scripts/memory_cloud.py backup
```

**Install**: `pip install boto3`

#### 3. WebDAV (Nutstore/Nextcloud)

```bash
# Configure WebDAV
python3 scripts/memory_cloud.py configure-webdav \
  --url https://dav.jianguoyun.com/dav/ \
  --username your@email.com \
  --password your-app-password

# Create backup
python3 scripts/memory_cloud.py backup
```

**Install**: `pip install webdavclient3`

#### 4. Dropbox

```bash
# Configure Dropbox
python3 scripts/memory_cloud.py configure-dropbox --token YOUR_ACCESS_TOKEN

# Create backup
python3 scripts/memory_cloud.py backup
```

**Install**: `pip install dropbox`

#### 5. Google Drive

```bash
# Configure Google Drive
python3 scripts/memory_cloud.py configure-gdrive \
  --credentials /path/to/credentials.json

# Create backup
python3 scripts/memory_cloud.py backup
```

**Install**: `pip install google-api-python-client google-auth-oauthlib`

### 📖 Detailed Usage Guide

See [examples/memory_cloud_usage.md](./examples/memory_cloud_usage.md) for:
- Complete setup guide for each provider
- Multi-device sync workflow
- Troubleshooting tips
- Security recommendations

---

## 🤖 Ollama Integration (Optional)

### ✨ Highlight: Works Without Ollama!

This system is designed with **graceful fallback** - it works perfectly even without Ollama!

| Mode | Ollama Status | Search Method | Functionality |
|------|---------------|---------------|---------------|
| **Full Mode** | ✅ Online | Vector semantic search | Full features |
| **Fallback Mode** | ❌ Offline | Keyword matching | Core features work |

### With vs Without Ollama

| Feature | With Ollama | Without Ollama |
|---------|-------------|----------------|
| **Search Quality** | Semantic understanding (finds related concepts) | Keyword matching (finds exact words) |
| **Auto Extraction** | AI-powered intelligent extraction | Rule-based extraction |
| **Memory Summarization** | LLM-generated summaries | Template-based summaries |
| **Importance Scoring** | ML-based scoring | Rule-based scoring |
| **Storage & CRUD** | ✅ Full support | ✅ Full support |
| **WebUI** | ✅ Full support | ✅ Full support |
| **Backup/Restore** | ✅ Full support | ✅ Full support |

### Ollama Configuration

```bash
# Set Ollama host (default: http://localhost:11434)
export OLLAMA_HOST=http://192.168.2.155:11434

# Required embedding model
ollama pull nomic-embed-text:latest

# Optional LLM for advanced features
ollama pull deepseek-v3.2:cloud
```

**Network Access**: If your Ollama is on another machine (e.g., NAS Docker), use LAN IP:
```bash
export OLLAMA_HOST=http://192.168.2.155:11434
```

---

## ✨ Features (31 Total)

### Core Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Hierarchical Cache** | 3-tier memory management (L1 Hot/L2 Warm/L3 Cold) | 90% reduction in access latency |
| **Knowledge Merging** | Combine similar memories into knowledge blocks | 75% token savings |
| **Predictive Loading** | Predict and preload relevant memories | Zero-delay response |
| **Cloud Sync** | Multi-cloud backup (S3/WebDAV/Dropbox/GDrive) | Data safety & multi-device sync |
| **Smart Q&A** | RAG-based question answering | Direct answers from memory |
| **Knowledge Graph** | Visual memory relationships | Intuitive understanding |

### All Features

| Category | Feature | Description |
|----------|---------|-------------|
| **Core** | Store | Vector semantic storage |
| | Search | Hybrid retrieval (Vector + BM25) |
| | Context | Auto-load relevant memories |
| **Intelligence** | Smart Q&A | RAG Q&A, direct answer generation |
| | Knowledge Graph | Memory relationship visualization |
| | User Insights | Preference analysis, trend suggestions |
| | Smart Reminders | Time-sensitive memory alerts |
| **Quality** | Health Check | System health score |
| | Deduplication | Auto-detect and merge duplicates |
| | Privacy Scan | Sensitive information detection |
| | Quality Report | Accuracy/timeliness/utilization |
| **Data** | Import/Export | JSON/CSV/Markdown |
| | Cloud Backup | 5 cloud storage support |
| | Restore | Restore from backup |
| **Visualization** | Web UI | Browser access (port 38080) |
| | Knowledge Graph | HTML visualization |
| | Knowledge Cards | Beautiful card export |
| | Memory Summary | Auto-generate summary |
| **Performance** | L1/L2/L3 Cache | Hot memory fast access |
| | Batch Preheat | Preload hotspots at startup |
| | Concurrent Query | Multi-condition parallel search |
| | Async Storage | Non-blocking writes |
| **Multimodal** | Image Memory | Store image descriptions |
| | Audio Memory | Speech-to-text |
| | File Memory | File information extraction |
| **Automation** | Auto Store | Smart importance detection |
| | Auto Extract | Extract memories from conversation |
| | Auto Dedup | Auto-merge duplicates |
| **Agent Integration** | Session Start Hook | Auto-load context |
| | Session End Hook | Auto-store important info |
| | Heartbeat Check | Periodic health check |

---

## 🚀 Quick Start

### Installation

```bash
# Install from ClawHub
clawhub install unified-memory

# Or manual install
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
./scripts/install.sh
```

### Basic Usage

```bash
# Quick commands
mem health                    # Health report
mem store "content"           # Store memory
mem load "query"              # Load memories
mem ask "question"            # Smart Q&A
mem webui 38080               # Start Web UI
mem backup                    # Cloud backup
mem insights analyze          # User insights
```

---

## 📖 Quick Command Reference

```bash
mem start "task"          # Session start, load context
mem end "content"         # Session end, store memory
mem heartbeat             # Heartbeat check
mem store "content"       # Quick store
mem load "query"          # Load memories
mem remind                # Check reminders
mem health                # Health report
mem webui 38080           # Web UI
mem ask "question"        # Smart Q&A
mem graph build           # Build knowledge graph
mem graph export          # Export HTML
mem insights analyze      # User insights
mem insights trends       # Behavior trends
mem backup                # Cloud backup
mem privacy               # Privacy scan
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Ollama (for embeddings and LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=deepseek-v3.2:cloud
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `L1_HOT_HOURS` | 24 | L1 time window |
| `L2_WARM_DAYS` | 7 | L2 time window |
| `L1_MAX_SIZE` | 20 | L1 max capacity |
| `L2_MAX_SIZE` | 100 | L2 max capacity |
| `SIMILARITY_THRESHOLD` | 0.85 | Knowledge merge threshold |
| `STALE_DAYS` | 30 | Outdated memory threshold |
| `FORGET_IMPORTANCE` | 0.1 | Forget below this importance |

---

## 📁 File Structure

```
~/.openclaw/workspace/
├── memory/
│   ├── vector/                # LanceDB vector database
│   ├── hierarchy/             # Hierarchical cache
│   ├── knowledge_blocks/      # Knowledge blocks
│   ├── memory_backup/         # Local backups
│   ├── cloud_config.json      # Cloud sync config
│   └── memory_graph.html      # Knowledge graph
└── skills/unified-memory/
    ├── scripts/
    │   ├── memory.py              # Main entry
    │   ├── memory_cloud.py        # Cloud sync
    │   ├── memory_qa.py           # Smart Q&A
    │   ├── memory_graph.py       # Knowledge graph
    │   ├── memory_insights.py    # Insights
    │   ├── memory_privacy.py     # Privacy
    │   ├── memory_perf.py        # Performance
    │   ├── memory_multimodal.py  # Multimodal
    │   ├── memory_auto.py        # Automation
    │   ├── memory_recommend.py   # Smart recommendations
    │   ├── memory_adaptive.py    # Adaptive confidence
    │   ├── memory_audit.py       # Audit logging
    │   ├── memory_sync.py       # Multi-agent sync
    │   ├── memory_summary.py    # Memory summaries
    │   ├── memory_integration.py # Agent integration
    │   └── mem                 # Quick command
    ├── README.md                 # English docs
    ├── README_CN.md              # Chinese docs
    ├── SKILL.md
    └── VERSION.md
```

---

## 🔧 Dependencies

### Required
- Python 3.8+
- `requests`

### Recommended
- `lancedb` - Vector database
- Ollama - Local embeddings and LLM

### Cloud Sync (Optional)
- `boto3` - AWS S3
- `webdavclient3` - WebDAV
- `dropbox` - Dropbox
- `google-api-python-client google-auth-oauthlib` - Google Drive

### Install

```bash
# Basic
pip install requests lancedb

# Cloud sync (as needed)
pip install boto3                          # S3
pip install webdavclient3                  # WebDAV
pip install dropbox                        # Dropbox
pip install google-api-python-client google-auth-oauthlib  # Google Drive
```

---

## 🗺️ Roadmap

### v0.3.2 (Current)
- ✅ Proactive context injection (主动上下文注入)
- ✅ Adaptive confidence with feedback (动态置信度自适应)
- ✅ Smart recommendations (智能关联推荐)
- ✅ Audit logging (可审计日志)
- ✅ Multi-agent sync (多Agent同步)
- ✅ Memory summaries (记忆摘要生成)
- ✅ Topic switch detection (主题切换检测)

### v0.2.2
- ✅ Multi-cloud sync (S3/WebDAV/Dropbox/GDrive)
- ✅ Bilingual documentation

### v0.3.0
- [ ] Team knowledge sharing
- [ ] Real-time sync

### v1.0.0
- [ ] Production-grade stability
- [ ] Full test coverage

---

## 🤝 Contributing

Contributions welcome! Please read [Contributing Guide](CONTRIBUTING.md).

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- Built for [OpenClaw](https://openclaw.ai) AI Agent framework
- Inspired by human memory systems
- Powered by [LanceDB](https://lancedb.github.io/lancedb/) vector database

---

**Made with ❤️ for AI Agents**

---

## 📚 Documentation Index

- [English Documentation](./README.md) (Current)
- [中文文档](./README_CN.md)
- [Version History](./VERSION.md)
- [Skill Description](./SKILL.md)
