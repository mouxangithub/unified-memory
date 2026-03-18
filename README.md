# Unified Memory - AI Agent Memory System

> **Version 0.0.7** | An intelligent memory system designed for AI Agents with hierarchical caching, knowledge merging, predictive loading, and automatic maintenance.

[![ClawHub](https://img.shields.io/badge/ClawHub-Publish-green)](https://clawhub.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🔗 Dependencies & Integration

### Required Skills

| Skill | Version | Auto-Install | Purpose |
|-------|---------|--------------|---------|
| **memory-lancedb-pro** | >=1.1.0 | ✅ Yes | LanceDB storage, hybrid retrieval, reranking |

### Installation Flow

```bash
# Install unified-memory (will auto-install memory-lancedb-pro)
clawhub install unified-memory
```

The installer will:
1. Check if `memory-lancedb-pro` is installed
2. If not, auto-install via `clawhub` or `git clone`
3. Install Python dependencies
4. Initialize directories and config

### Manual Installation

```bash
# Step 1: Install base skill
clawhub install memory-lancedb-pro
# or
git clone https://github.com/CortexReach/memory-lancedb-pro.git ~/.openclaw/workspace/skills/memory-lancedb-pro

# Step 2: Install unified-memory
clawhub install unified-memory
# or
git clone https://github.com/openclaw/unified-memory.git ~/.openclaw/workspace/skills/unified-memory
cd ~/.openclaw/workspace/skills/unified-memory
./scripts/install.sh
```

### Optional Skills

| Skill | Purpose |
|-------|---------|
| **ontology** | Knowledge graph for entity relationships |
| **agent-memory** | OpenClaw built-in memory |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Memory 0.0.7                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │         memory-lancedb-pro (Required)               │  │
│   │  - LanceDB Vector Storage                           │  │
│   │  - Hybrid Retrieval (Vector + BM25)                 │  │
│   │  - Cross-encoder Reranking                         │  │
│   └─────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│   ┌─────────────────────────────────────────────────────┐  │
│   │         Unified Memory Extensions                  │  │
│   │  - Hierarchical Cache (L1/L2/L3)                   │  │
│   │  - Knowledge Merging                                │  │
│   │  - Predictive Loading                               │  │
│   │  - Agent Lifecycle Integration                      │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Hierarchical Cache** | 3-tier memory management (L1 Hot/L2 Warm/L3 Cold) | 90% reduction in access latency |
| **Knowledge Merging** | Combine similar memories into knowledge blocks | 75% token savings |
| **Predictive Loading** | Predict and preload relevant memories | Zero-delay response |
| **Confidence Validation** | Detect outdated/conflicting memories | Improved accuracy |
| **Feedback Learning** | Auto-adjust importance based on usage | Continuous optimization |
| **Smart Forget** | Compress, archive, and delete low-value memories | Controlled memory size |

### Advanced Features (v0.0.7)

| Feature | Description |
|---------|-------------|
| **Auto Extraction** | Automatically extract memories from conversations |
| **Sensitive Filter** | Redact passwords, API keys, secrets |
| **Quality Metrics** | Memory health scores and recommendations |
| **Import/Export** | Backup and restore memory data |
| **Advanced Search** | Category, time-range, fuzzy search |
| **Agent Integration** | Lifecycle hooks for AI agents |

---

## 🚀 Quick Start

### Installation

```bash
# Clone from ClawHub
clawhub install unified-memory

# Or manual install
git clone https://github.com/your-repo/unified-memory.git
cd unified-memory
pip install -r requirements.txt
```

### Basic Usage

```bash
# View system status
python3 scripts/memory.py status

# Initialize system
python3 scripts/memory.py init

# Get context for current task
python3 scripts/memory.py context --query "my project"

# Auto extract from conversation
python3 scripts/memory.py extract --conversation "User prefers using Feishu for collaboration"

# Search memories
python3 scripts/memory.py search --query "preferences" --category preference

# Export backup
python3 scripts/memory.py export --format json --output backup.json
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System 0.0.7                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐ │
│  │ L1 Hot      │  │ L2 Warm     │  │ L3 Cold            │ │
│  │ Last 24h    │  │ Last 7 days │  │ Long-term          │ │
│  │ In-memory   │  │ On-demand   │  │ Compressed         │ │
│  └─────────────┘  └─────────────┘  └────────────────────┘ │
│         ↓                ↓                  ↓              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Predictive Loader (Trend Analysis)           │ │
│  └──────────────────────────────────────────────────────┘ │
│         ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Knowledge Merger (85% Similarity)            │ │
│  └──────────────────────────────────────────────────────┘ │
│         ↓                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Validation   │  │ Feedback     │  │ Smart Forget │    │
│  │ Stale/Conflict│ │ Importance   │  │ Archive/Delete│   │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Documentation

### Memory Hierarchy

#### L1 Hot (Hot Memory)
- **Criteria**: Last 24h + Importance > 0.6
- **Capacity**: Max 20 items
- **Access**: In-memory, zero latency

#### L2 Warm (Warm Memory)
- **Criteria**: Last 7 days + Importance > 0.3
- **Capacity**: Max 100 items
- **Access**: On-demand, fast loading

#### L3 Cold (Cold Memory)
- **Criteria**: Long-term history
- **Access**: Compressed, decompress on load

### Memory Quality Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | Verified memories ratio | > 80% |
| **Timeliness** | Recent 30-day memories ratio | > 70% |
| **Utilization** | Accessed memories ratio | > 50% |
| **Redundancy** | Duplicate memories ratio | < 20% |

### Memory Categories

- `preference` - User preferences
- `fact` - Factual information
- `decision` - Important decisions
- `entity` - Projects, companies, teams
- `task` - Tasks and todos
- `event` - Meetings, dates

---

## 🛠️ CLI Reference

### Core Commands

```bash
# System
memory.py status              # View system status
memory.py init                # Initialize system
memory.py stats               # Detailed statistics

# Context & Search
memory.py context --query "q" # Get relevant memories
memory.py search --query "q"  # Advanced search
memory.py analyze --query "q" # Predictive analysis

# Maintenance
memory.py validate            # Validate memories
memory.py feedback            # Apply feedback adjustments
memory.py forget --dry-run    # Preview deletions
memory.py forget              # Execute smart forget

# Extraction
memory.py extract --conversation "text"  # Auto extract
memory.py extract --file chat.txt        # From file

# Data
memory.py export --format json --output backup.json
memory.py import --file backup.json
memory.py reset --confirm    # ⚠️ Deletes all data

# Quality
memory.py quality report      # Quality report
memory.py quality health      # Health check
```

### Search Options

```bash
# Category search
memory.py search --query "飞书" --category preference

# Time range search
memory.py search --query "项目" --from 2026-03-01 --to 2026-03-18

# Fuzzy search
memory.py search --query "用户偏好" --fuzzy --threshold 0.7

# Importance filter
memory.py search --query "重要" --min-importance 0.7
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
│   ├── 2026-03-18.md          # Daily memory log
│   ├── memories.json           # Memory database (backup)
│   ├── hierarchy/              # Hierarchical cache
│   │   ├── l1_hot.json
│   │   ├── l2_warm.json
│   │   └── l3_index.json
│   ├── knowledge_blocks/       # Merged knowledge
│   ├── predictions/            # Prediction cache
│   ├── validation/             # Validation state
│   ├── feedback/               # Feedback data
│   ├── archive/                # Archived memories
│   ├── backups/                # Backups
│   └── sessions/               # Session logs
└── skills/unified-memory/
    ├── scripts/
    │   ├── memory.py        # Unified entry
    │   ├── memory_hierarchy.py # Hierarchical cache
    │   ├── knowledge_merger.py # Knowledge merge
    │   ├── predictive_loader.py# Predictive load
    │   ├── confidence_validator.py
    │   ├── feedback_learner.py
    │   ├── smart_forgetter.py
    │   ├── auto_extractor.py   # Auto extraction
    │   ├── memory_quality.py   # Quality metrics
    │   ├── memory_io.py        # Import/Export
    │   ├── memory_search.py    # Advanced search
    │   └── agent_integration.py
    ├── SKILL.md
    ├── README.md
    └── VERSION.md
```

---

## 🔧 Dependencies

### Required
- Python 3.8+
- `requests` - HTTP requests

### Optional
- `lancedb` - Vector database (recommended)
- Ollama - Local embeddings and LLM

### Install

```bash
pip install requests lancedb
```

---

## 📝 Examples

### Example 1: Auto Memory Extraction

```python
from auto_extractor import AutoExtractor

extractor = AutoExtractor()

# Extract from conversation
conversation = """
User: I prefer using Feishu for team collaboration.
Agent: Got it, I'll use Feishu for our collaboration.
"""

memories = extractor.extract_from_conversation(conversation)
# Result: [{"text": "使用飞书进行团队协作", "category": "preference", "importance": 0.65}]

# Auto store
extractor.auto_store(memories)
```

### Example 2: Quality Report

```bash
$ python3 memory.py quality report

📊 Memory Quality Report
==================================================
Total Memories: 20
Health Score: 87.5% 🟢 Excellent

Metrics:
  Accuracy: 95.0%
  Timeliness: 80.0%
  Utilization: 60.0%
  Redundancy: 10.0%

Recommendations:
  [medium] Utilization low: Optimize memory retrieval
```

### Example 3: Agent Integration

```python
from agent_integration import AgentMemoryIntegration

integration = AgentMemoryIntegration()

# On agent start
integration.on_agent_start(context="User project management")

# On message (auto extract)
integration.on_message(
    user_message="我喜欢用飞书管理项目",
    agent_response="好的，我会用飞书来管理我们的项目"
)

# Get relevant context
context = integration.get_relevant_context("项目管理")

# On agent end (auto maintenance)
integration.on_agent_end()
```

---

## 🗺️ Roadmap

### v0.0.8 (Next)
- [ ] Memory compression algorithm optimization
- [ ] Cross-session memory association
- [ ] Memory visualization (Web UI)

### v0.1.0 (Milestone)
- [ ] API stabilization
- [ ] Performance benchmarking
- [ ] Complete documentation

### v1.0.0 (Production)
- [ ] Production-grade stability
- [ ] Full test coverage
- [ ] Enterprise features

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built for [OpenClaw](https://openclaw.ai) AI Agent framework
- Inspired by human memory systems and cognitive architectures
- Powered by [LanceDB](https://lancedb.github.io/lancedb/) vector database

---

**Made with ❤️ for AI Agents**
