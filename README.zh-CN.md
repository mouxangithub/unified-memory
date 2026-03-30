# Unified Memory MCP Server

**中文**: OpenClaw 功能最丰富的记忆系统 MCP 服务器  
**English**: The most feature-rich Memory System MCP Server for OpenClaw

[![Version](https://img.shields.io/badge/version-3.8.4-blue.svg)](https://github.com/mouxangithub/unified-memory)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-supported-orange.svg)](https://openclaw.ai)

---

## 📖 快速开始 / Quick Start

### 中文

**安装**:
```bash
# 通过 Clawhub 安装
clawhub install unified-memory

# 或直接克隆仓库
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
```

**配置**:
在 `openclaw.json` 中添加:
```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/index.js"]
    }
  }
}
```

**使用**:
```bash
# 查看可用工具
mcporter list unified-memory

# 调用工具
mcporter call unified-memory memory_wal_status
```

### English

**Install**:
```bash
# Install via Clawhub
clawhub install unified-memory

# Or clone the repository directly
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
```

**Configure**:
Add to `openclaw.json`:
```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/unified-memory/src/index.js"]
    }
  }
}
```

**Usage**:
```bash
# List available tools
mcporter list unified-memory

# Call a tool
mcporter call unified-memory memory_wal_status
```

---

## 🚀 核心特性 / Core Features

### 中文

#### 1. **完整的数据可靠性** (WAL Protocol)
- ✅ Write-Ahead Log (WAL) 协议确保数据不丢失
- ✅ 崩溃自动恢复
- ✅ 校验和验证
- ✅ 导出/导入备份

#### 2. **证据链机制** (Evidence Chain)
- ✅ 记忆来源追踪 (transcript/message/manual/inference)
- ✅ 置信度评分 (0-1)
- ✅ 证据链可视化
- ✅ 来源过滤和搜索

#### 3. **自动整理** (Auto Organization)
- ✅ 自动层级迁移 (HOT/WARM/COLD)
- ✅ 基于年龄和重要性的压缩
- ✅ 旧记忆归档 (365+ 天)
- ✅ 层级压缩比例配置

#### 4. **Transcript-First 架构**
- ✅ Transcripts 作为唯一真相来源
- ✅ 记忆重建功能
- ✅ 证据链集成
- ✅ 来源过滤和搜索

#### 5. **Revision Lifecycle 管理**
- ✅ 生命周期阶段 (draft/review/approved/archived)
- ✅ 阶段过滤和更新
- ✅ 增强冲突检测
- ✅ 自动合并

#### 6. **Lane Memory 深度集成**
- ✅ 并行泳道 (primary/task/background/archive)
- ✅ 自定义创建
- ✅ 记忆移动和合并
- ✅ 统计和元数据支持

#### 7. **Token Budget 硬限制**
- ✅ 硬限制 (95%)
- ✅ 自动压缩 (85%)
- ✅ 警告 (70%)
- ✅ 类型分配和优先级分配

#### 8. **证据驱动召回**
- ✅ 证据权重系统
- ✅ 置信度乘数
- ✅ 类型和来源过滤
- ✅ 高置信度过滤

### English

#### 1. **Complete Data Reliability** (WAL Protocol)
- ✅ Write-Ahead Log (WAL) protocol ensures data durability
- ✅ Automatic crash recovery
- ✅ Checksum validation
- ✅ Export/Import backup

#### 2. **Evidence Chain Mechanism**
- ✅ Memory source tracking (transcript/message/manual/inference)
- ✅ Confidence scoring (0-1)
- ✅ Evidence chain visualization
- ✅ Source filtering and search

#### 3. **Auto Organization**
- ✅ Automatic tier migration (HOT/WARM/COLD)
- ✅ Compression based on age and importance
- ✅ Old memory archival (365+ days)
- ✅ Tier compression ratio configuration

#### 4. **Transcript-First Architecture**
- ✅ Transcripts as single source of truth
- ✅ Memory rebuild capability
- ✅ Evidence chain integration
- ✅ Source filtering and search

#### 5. **Revision Lifecycle Management**
- ✅ Lifecycle stages (draft/review/approved/archived)
- ✅ Stage filtering and updates
- ✅ Enhanced conflict detection
- ✅ Automatic merging

#### 6. **Lane Memory Deep Integration**
- ✅ Parallel swim lanes (primary/task/background/archive)
- ✅ Custom lane creation
- ✅ Memory movement and merging
- ✅ Statistics and metadata support

#### 7. **Token Budget Hard Limits**
- ✅ Hard limit enforcement (95%)
- ✅ Auto-compaction (85%)
- ✅ Warning threshold (70%)
- ✅ Type and priority allocation

#### 8. **Evidence-Driven Recall**
- ✅ Evidence weighting system
- ✅ Confidence multipliers
- ✅ Type and source filtering
- ✅ High-confidence filtering

---

## 📦 工具列表 / Tool List

### 中文

**总工具数**: 152 tools

#### WAL Protocol (6 tools)
- `memory_wal_write` - 写入 WAL 日志
- `memory_wal_replay` - 崩溃恢复重放
- `memory_wal_status` - WAL 状态查询
- `memory_wal_truncate` - 截断 WAL
- `memory_wal_export` - 导出备份
- `memory_wal_import` - 导入备份

#### Evidence Chain (5 + 10 = 15 tools)
- `memory_evidence_add` - 添加证据链
- `memory_evidence_get` - 获取证据链
- `memory_evidence_find_by_type` - 按类型搜索
- `memory_evidence_find_by_source` - 按来源搜索
- `memory_evidence_stats` - 统计信息
- `memory_evidence_recall` - 证据驱动召回
- `memory_evidence_index` - 索引证据
- `memory_evidence_score` - 计算分数
- `memory_evidence_rank` - 按证据排序
- `memory_evidence_filter_by_type` - 按类型过滤
- `memory_evidence_filter_by_source` - 按来源过滤
- `memory_evidence_high_confidence` - 高置信度过滤
- `memory_evidence_transcript_only` - 仅 transcript 证据
- `memory_evidence_summary` - 获取摘要
- `memory_evidence_statistics` - 获取统计

#### Auto Organization (5 tools)
- `memory_organize` - 跨层级整理
- `memory_compress_tier` - 压缩特定层级
- `memory_archive_old` - 归档旧记忆
- `memory_tier_stats` - 层级统计
- `memory_full_organize` - 完整整理

#### Transcript-First (11 tools)
- `memory_transcript_add` - 添加 transcript
- `memory_transcript_get` - 获取 transcript
- `memory_transcript_update` - 更新 transcript
- `memory_transcript_delete` - 删除 transcript
- `memory_transcript_list` - 列出 transcripts
- `memory_transcript_find_by_source` - 按来源搜索
- `memory_transcript_rebuild` - 重建记忆
- `memory_transcript_summary` - 获取摘要
- `memory_transcript_stats` - 统计信息
- `memory_transcript_verify` - 验证完整性
- `memory_transcript_compact` - 清理 transcript

#### Revision Lifecycle (3 tools)
- `memory_revision_lifecycle_summary` - 生命周期摘要
- `memory_revision_by_stage` - 按阶段获取
- `memory_revision_update_stage` - 更新阶段

#### Lane Memory (8 tools)
- `memory_lane_create` - 创建 lane
- `memory_lane_switch` - 切换 lane
- `memory_lane_current` - 获取当前 lane
- `memory_lane_list` - 列出 lanes
- `memory_lane_move` - 移动记忆
- `memory_lane_archive` - 归档 lane
- `memory_lane_merge` - 合并 lanes
- `memory_lane_delete` - 删除 lane

#### Token Budget (8 tools)
- `memory_token_budget_status` - 获取状态
- `memory_token_budget_enforce` - 执行限制
- `memory_token_budget_allocate` - 分配 tokens
- `memory_token_budget_record` - 记录使用
- `memory_token_budget_compress` - 压缩记忆
- `memory_token_budget_history` - 获取历史
- `memory_token_budget_reset` - 重置使用
- `memory_token_budget_config` - 获取/更新配置

#### Existing Tools (97 tools)
- Session State, Git-Notes, Budget, Cognitive Scheduler, Memory Lanes, Cloud Backup, Hybrid Search, Scope Isolation, Weibull Decay, Knowledge Graph, Pluggable Architecture, etc.

### English

**Total Tools**: 152 tools

#### WAL Protocol (6 tools)
- `memory_wal_write` - Write WAL log
- `memory_wal_replay` - Crash recovery replay
- `memory_wal_status` - WAL status query
- `memory_wal_truncate` - Truncate WAL
- `memory_wal_export` - Export backup
- `memory_wal_import` - Import backup

#### Evidence Chain (5 + 10 = 15 tools)
- `memory_evidence_add` - Add evidence chain
- `memory_evidence_get` - Get evidence chain
- `memory_evidence_find_by_type` - Search by type
- `memory_evidence_find_by_source` - Search by source
- `memory_evidence_stats` - Statistics
- `memory_evidence_recall` - Evidence-driven recall
- `memory_evidence_index` - Index evidence
- `memory_evidence_score` - Calculate score
- `memory_evidence_rank` - Rank by evidence
- `memory_evidence_filter_by_type` - Filter by type
- `memory_evidence_filter_by_source` - Filter by source
- `memory_evidence_high_confidence` - High confidence filter
- `memory_evidence_transcript_only` - Transcript evidence only
- `memory_evidence_summary` - Get summary
- `memory_evidence_statistics` - Get statistics

#### Auto Organization (5 tools)
- `memory_organize` - Cross-tier organization
- `memory_compress_tier` - Compress specific tier
- `memory_archive_old` - Archive old memories
- `memory_tier_stats` - Tier statistics
- `memory_full_organize` - Full organization

#### Transcript-First (11 tools)
- `memory_transcript_add` - Add transcript
- `memory_transcript_get` - Get transcript
- `memory_transcript_update` - Update transcript
- `memory_transcript_delete` - Delete transcript
- `memory_transcript_list` - List transcripts
- `memory_transcript_find_by_source` - Search by source
- `memory_transcript_rebuild` - Rebuild memories
- `memory_transcript_summary` - Get summary
- `memory_transcript_stats` - Statistics
- `memory_transcript_verify` - Verify integrity
- `memory_transcript_compact` - Compact transcript

#### Revision Lifecycle (3 tools)
- `memory_revision_lifecycle_summary` - Lifecycle summary
- `memory_revision_by_stage` - Get by stage
- `memory_revision_update_stage` - Update stage

#### Lane Memory (8 tools)
- `memory_lane_create` - Create lane
- `memory_lane_switch` - Switch lane
- `memory_lane_current` - Get current lane
- `memory_lane_list` - List lanes
- `memory_lane_move` - Move memory
- `memory_lane_archive` - Archive lane
- `memory_lane_merge` - Merge lanes
- `memory_lane_delete` - Delete lane

#### Token Budget (8 tools)
- `memory_token_budget_status` - Get status
- `memory_token_budget_enforce` - Enforce limits
- `memory_token_budget_allocate` - Allocate tokens
- `memory_token_budget_record` - Record usage
- `memory_token_budget_compress` - Compress memories
- `memory_token_budget_history` - Get history
- `memory_token_budget_reset` - Reset usage
- `memory_token_budget_config` - Get/update config

#### Existing Tools (97 tools)
- Session State, Git-Notes, Budget, Cognitive Scheduler, Memory Lanes, Cloud Backup, Hybrid Search, Scope Isolation, Weibull Decay, Knowledge Graph, Pluggable Architecture, etc.

---

## 📁 文件结构 / File Structure

### 中文

```
unified-memory/
├── src/
│   ├── index.js                    # 主入口文件 (15KB)
│   ├── wal.js                      # WAL 协议 (5.3KB)
│   ├── evidence.js                 # 证据链机制 (5.7KB)
│   ├── organize.js                 # 自动整理 (7.9KB)
│   ├── transcript_first.js         # Transcript-First 架构 (9.0KB)
│   ├── revision_manager_enhanced.js # Revision Lifecycle (10.9KB)
│   ├── lane_manager_enhanced.js    # Lane Memory (9.8KB)
│   ├── token_budget_enhanced.js    # Token Budget (10.9KB)
│   ├── evidence_recall.js          # 证据驱动召回 (10.9KB)
│   ├── budget.js                   # 预算计算 (4.3KB)
│   ├── config.js                   # 配置管理 (2.1KB)
│   └── utils/
│       └── token_estimator.js      # Token 估算器 (1.2KB)
├── docs/
│   ├── README.md                   # 本文件
│   ├── competitive-analysis.md     # 竞品分析
│   ├── v3.8.0-release-notes.md     # v3.8.0 发布说明
│   ├── v3.8.1-release-notes.md     # v3.8.1 发布说明
│   ├── v3.8.2-release-notes.md     # v3.8.2 发布说明
│   ├── v3.8.3-release-notes.md     # v3.8.3 发布说明
│   └── v3.8.4-release-notes.md     # v3.8.4 发布说明
├── package.json                    # 包配置
├── LICENSE                         # MIT 许可证
└── README.zh-CN.md                 # 中文文档 (本文件)
```

### English

```
unified-memory/
├── src/
│   ├── index.js                    # Main entry point (15KB)
│   ├── wal.js                      # WAL Protocol (5.3KB)
│   ├── evidence.js                 # Evidence Chain (5.7KB)
│   ├── organize.js                 # Auto Organization (7.9KB)
│   ├── transcript_first.js         # Transcript-First (9.0KB)
│   ├── revision_manager_enhanced.js # Revision Lifecycle (10.9KB)
│   ├── lane_manager_enhanced.js    # Lane Memory (9.8KB)
│   ├── token_budget_enhanced.js    # Token Budget (10.9KB)
│   ├── evidence_recall.js          # Evidence Recall (10.9KB)
│   ├── budget.js                   # Budget Calculator (4.3KB)
│   ├── config.js                   # Config Manager (2.1KB)
│   └── utils/
│       └── token_estimator.js      # Token Estimator (1.2KB)
├── docs/
│   ├── README.md                   # This file
│   ├── competitive-analysis.md     # Competitive Analysis
│   ├── v3.8.0-release-notes.md     # v3.8.0 Release Notes
│   ├── v3.8.1-release-notes.md     # v3.8.1 Release Notes
│   ├── v3.8.2-release-notes.md     # v3.8.2 Release Notes
│   ├── v3.8.3-release-notes.md     # v3.8.3 Release Notes
│   └── v3.8.4-release-notes.md     # v3.8.4 Release Notes
├── package.json                    # Package Config
├── LICENSE                         # MIT License
└── README.zh-CN.md                 # Chinese Documentation
```

---

## 🔄 版本历史 / Changelog

### 中文

#### v3.8.4 (2026-03-30) - Token Budget + Evidence Recall
- **新增**: Token Budget 硬限制 (8 tools)
- **新增**: 证据驱动召回 (10 tools)
- **总计**: 152 tools (+18)

#### v3.8.3 (2026-03-30) - Lane Memory
- **新增**: Lane Memory 深度集成 (8 tools)
- **总计**: 134 tools (+8)

#### v3.8.2 (2026-03-30) - Revision Lifecycle
- **新增**: Revision Lifecycle 深度化 (3 tools)
- **总计**: 126 tools (+3)

#### v3.8.1 (2026-03-30) - Transcript-First
- **新增**: Transcript-First 完整架构 (11 tools)
- **总计**: 123 tools (+11)

#### v3.8.0 (2026-03-30) - Core Improvements
- **新增**: WAL Protocol (6 tools)
- **新增**: Evidence Chain (5 tools)
- **新增**: Auto Organization (5 tools)
- **总计**: 112 tools (+15)

#### v3.7.0 (之前版本)
- **总计**: 97 tools

### English

#### v3.8.4 (2026-03-30) - Token Budget + Evidence Recall
- **Added**: Token Budget Hard Limits (8 tools)
- **Added**: Evidence-Driven Recall (10 tools)
- **Total**: 152 tools (+18)

#### v3.8.3 (2026-03-30) - Lane Memory
- **Added**: Lane Memory Deep Integration (8 tools)
- **Total**: 134 tools (+8)

#### v3.8.2 (2026-03-30) - Revision Lifecycle
- **Added**: Revision Lifecycle Enhancement (3 tools)
- **Total**: 126 tools (+3)

#### v3.8.1 (2026-03-30) - Transcript-First
- **Added**: Transcript-First Architecture (11 tools)
- **Total**: 123 tools (+11)

#### v3.8.0 (2026-03-30) - Core Improvements
- **Added**: WAL Protocol (6 tools)
- **Added**: Evidence Chain (5 tools)
- **Added**: Auto Organization (5 tools)
- **Total**: 112 tools (+15)

#### v3.7.0 (Previous Versions)
- **Total**: 97 tools

---

## 🤝 竞品对比 / Competitive Analysis

### 中文

| 功能 | Unified Memory | Smart Memory | Elite Longterm | Memory Tiering |
|------|----------------|--------------|----------------|----------------|
| **WAL 协议** | ✅ 完整 | ✅ 完整 | ✅ 完整 | ❌ 无 |
| **Transcript-First** | ✅ 完整 | ✅ 核心 | ⚠️ 部分 | ❌ 无 |
| **证据链机制** | ✅ 完整 | ✅ 完整 | ❌ 无 | ❌ 无 |
| **Revision Lifecycle** | ✅ 深度 | ✅ 深度 | ⚠️ 基础 | ❌ 无 |
| **Lane Memory** | ✅ 深度 | ✅ 深度 | ❌ 无 | ❌ 无 |
| **Token Budget** | ✅ 硬限制 | ⚠️ 统计 | ❌ 无 | ❌ 无 |
| **自动整理** | ✅ 完整 | ⚠️ 部分 | ❌ 无 | ✅ 完整 |
| **纯 Node.js** | ✅ 是 | ❌ Python | ❌ Python | ✅ 是 |
| **工具数** | **152** | ~80 | ~60 | ~30 |

**核心优势**:
- ✅ 功能最丰富 (152 tools)
- ✅ 纯 Node.js ESM (零 Python 依赖)
- ✅ 完整的数据可靠性
- ✅ 完整的可追溯性
- ✅ 完整的自动化管理

### English

| Feature | Unified Memory | Smart Memory | Elite Longterm | Memory Tiering |
|---------|----------------|--------------|----------------|----------------|
| **WAL Protocol** | ✅ Complete | ✅ Complete | ✅ Complete | ❌ None |
| **Transcript-First** | ✅ Complete | ✅ Core | ⚠️ Partial | ❌ None |
| **Evidence Chain** | ✅ Complete | ✅ Complete | ❌ None | ❌ None |
| **Revision Lifecycle** | ✅ Deep | ✅ Deep | ⚠️ Basic | ❌ None |
| **Lane Memory** | ✅ Deep | ✅ Deep | ❌ None | ❌ None |
| **Token Budget** | ✅ Hard Limit | ⚠️ Stats | ❌ None | ❌ None |
| **Auto Organization** | ✅ Complete | ⚠️ Partial | ❌ None | ✅ Complete |
| **Pure Node.js** | ✅ Yes | ❌ Python | ❌ Python | ✅ Yes |
| **Tool Count** | **152** | ~80 | ~60 | ~30 |

**Core Advantages**:
- ✅ Most feature-rich (152 tools)
- ✅ Pure Node.js ESM (zero Python dependency)
- ✅ Complete data reliability
- ✅ Complete traceability
- ✅ Complete automation

---

## 📚 文档索引 / Documentation Index

### 中文

- **[README.md](./README.md)** - 英文主文档
- **[README.zh-CN.md](./README.zh-CN.md)** - 中文主文档 (本文件)
- **[docs/competitive-analysis.md](./docs/competitive-analysis.md)** - 竞品分析报告
- **[docs/v3.8.0-release-notes.md](./docs/v3.8.0-release-notes.md)** - v3.8.0 发布说明
- **[docs/v3.8.1-release-notes.md](./docs/v3.8.1-release-notes.md)** - v3.8.1 发布说明
- **[docs/v3.8.2-release-notes.md](./docs/v3.8.2-release-notes.md)** - v3.8.2 发布说明
- **[docs/v3.8.3-release-notes.md](./docs/v3.8.3-release-notes.md)** - v3.8.3 发布说明
- **[docs/v3.8.4-release-notes.md](./docs/v3.8.4-release-notes.md)** - v3.8.4 发布说明

### English

- **[README.md](./README.md)** - English Main Documentation
- **[README.zh-CN.md](./README.zh-CN.md)** - Chinese Main Documentation (This File)
- **[docs/competitive-analysis.md](./docs/competitive-analysis.md)** - Competitive Analysis Report
- **[docs/v3.8.0-release-notes.md](./docs/v3.8.0-release-notes.md)** - v3.8.0 Release Notes
- **[docs/v3.8.1-release-notes.md](./docs/v3.8.1-release-notes.md)** - v3.8.1 Release Notes
- **[docs/v3.8.2-release-notes.md](./docs/v3.8.2-release-notes.md)** - v3.8.2 Release Notes
- **[docs/v3.8.3-release-notes.md](./docs/v3.8.3-release-notes.md)** - v3.8.3 Release Notes
- **[docs/v3.8.4-release-notes.md](./docs/v3.8.4-release-notes.md)** - v3.8.4 Release Notes

---

## 📄 许可证 / License

MIT License - See [LICENSE](./LICENSE) for details.

---

## 🙏 致谢 / Acknowledgments

感谢以下开源项目提供的灵感:
- Smart Memory (Transcript-First 架构)
- Elite Longterm Memory (WAL 协议)
- Memory Tiering (自动整理机制)

---

## 📧 联系方式 / Contact

- **GitHub**: https://github.com/mouxangithub/unified-memory
- **Clawhub**: https://clawhub.ai
- **OpenClaw**: https://openclaw.ai

---

**中文**: 功能最丰富的 OpenClaw 记忆系统 | 152 tools | 纯 Node.js ESM  
**English**: The Most Feature-Rich OpenClaw Memory System | 152 tools | Pure Node.js ESM
