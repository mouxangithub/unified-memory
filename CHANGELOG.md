# Changelog

## v2.7.0 (2026-03-28)

### Web UI Dashboard ⭐ NEW
- `npm run dashboard` — Launch monitoring dashboard on port 3849
- Real-time stats: total memories, 7d growth, access counts
- Memory distribution: by category, scope, tier, importance, tags
- System health: Ollama, LanceDB, memory file, storage usage
- 14-day growth trend chart (Chart.js bar chart)
- Scope donut chart
- Management actions: cleanup old memories, export JSON
- Auto-refresh every 5 seconds via AJAX
- Lightweight HTTP server (no Express dependency required)

### REST API Endpoints (Dashboard)
- `GET /` — Dashboard UI
- `GET /api/stats` — Memory statistics
- `GET /api/health` — System health check
- `GET /api/memories` — All memories
- `GET /api/export` — Download memories JSON
- `POST /api/manage` — Management actions (cleanup)

---

### Identity Memory Type ⭐ NEW

#### Extended Category System
- New `identity` category family: `identity`, `preference`, `habit`, `requirement`, `skill`, `goal`
- Identity memories always use `importance >= 0.9` (highest priority)
- Identity category documented in `src/storage.js`

#### Identity Extraction Tools (`src/tools/identity_tools.js`)
- `memory_identity_extract` — Rule-based extraction from text
  - "我喜欢/爱/偏好..." → preference (like)
  - "我讨厌/厌恶/不喜欢..." → preference (dislike)
  - "我是/叫/职业..." → identity
  - "我习惯/通常/经常..." → habit
  - "我需要/必须/希望..." → requirement
  - "我会/能/擅长..." → skill
  - "我的目标..." → goal
- `memory_identity_update` — Store extracted identities with importance 0.9+
- `memory_identity_get` — Get user's identity profile summary

#### Auto-Store Integration (`src/tools/autostore.js`)
- Identity patterns run first (priority over general patterns)
- Identity items auto-tagged `identity-auto`
- Identity importance defaults to 0.9 (vs 0.6 for general)

#### Tool Registration
- All 3 identity tools registered in `src/index.js` as MCP tools

### Files Changed
- `src/storage.js` — identity category documentation
- `src/tools/autostore.js` — IDENTITY_PATTERNS + extractIdentityInfo()
- `src/tools/identity_tools.js` — NEW (3 tools + extraction engine)
- `src/index.js` — 3 new tool registrations + import
- `package.json` — version 2.7.0

## v2.6.0 (2026-03-28)

### Phase 3 — Complete

#### Multi-Scope Isolation ⭐ NEW
- **LanceDB query-level scope filtering** — scope filter applied at DB query level (not post-filter), ensuring true multi-tenant isolation
- Scope B-tree index on `scope` column for zero-cost scope filtering before ANN search
- `memory_search` and `memory_vector` tools expose `scope` parameter
- `hybridSearch()` and `vectorSearch()` both透传 scope parameter

#### Plugin Interface ⭐ NEW
- `phase3_memory_search` — OpenClaw Memory Plugin spec search
- `phase3_memory_get` — OpenClaw Memory Plugin memory get
- `phase3_memory_write` — OpenClaw Memory Plugin memory write

#### QMD Search Backend ⭐ NEW
- `memory_qmd_query` — Query QMD collections (workspace/daily-logs/projects)
- `memory_qmd_status` — QMD index status
- `memory_qmd_search2` — QMD hybrid search with scope filtering

#### Git Integration ⭐ NEW
- `memory_git_init` — Initialize git repo for versioned memory
- `memory_git_sync/history/note/pull/push` — Full git workflow

#### Cloud Backup ⭐ NEW
- `memory_cloud_sync/push/pull` — SuperMemory API + Custom REST dual mode

#### Weibull Decay ⭐ NEW
- `memory_decay_stats/strength` — Weibull-distributed forgetting curve
- Shape=1.5, scale=30 days, access reward +5% up to 50% cap

### Documentation
- README.md / README_CN.md fully rewritten (v2.5.0)
- SKILL.md / SKILL_CN.md fully rewritten (76 tools documented)
- All docs synchronized: version numbers, tool counts, feature lists

### Files Changed
- `src/vector_lancedb.js` — scope filtering at query level + B-tree index
- `src/fusion.js` — hybridSearch scope parameter
- `src/index.js` — memory_search/memory_vector scope parameter

---

## v2.4.0 (2026-03-27)

### Phase 2 — 86 Tools Complete
- 86 MCP tools registered (33 → 86)
- Episode / Procedural / Rule memory system
- Knowledge graph / proactive recall / prediction
- Observability (WAL tracing, metrics, templates)
- HTTP REST API
- Dual-language docs (Chinese + English)

---

## v2.1.0 (2026-03-27)

### Added
- 33 MCP tools fully registered
- Preference Slots system
- HOT/WARM/COLD tier management
- Write-Ahead Log for crash recovery
- Intent routing + noise filter
- BM25 + Vector + RRF pipeline

### Fixed
- noise.js `(?i)` regex bug
- tier.js ISO timestamp parsing

---

## v2.0.0 (2026-03-26)

- Full Node.js ESM rewrite (147 JS modules)
- Weibull time decay
- Scope isolation (AGENT/USER/TEAM/GLOBAL)

---

## v1.x (2026-03-25)

- Python prototype

## v2.8.0 (2026-03-28)
### 🚀 Features
- **Unified Web UI + API Server** - 整合所有 Web UI 和 API 到单一服务端口 (3850)
  - Dashboard v2.8 (嵌入式)
  - Memory API (/api/memories, /api/search, /api/stats)
  - Health check (/health)
  - 移除分散的 6 个 HTTP 服务

### 🔧 Refactor
- 新建 `src/webui/unified_server.js` 替代分散的服务
- 更新 index.js 启动脚本指向统一服务器

## v2.9.0 (2026-03-28)
### 🚀 重大重构
- **完整重写 Web UI** - 从 webui.js 整合所有功能到 unified_server.js
- **响应式移动端设计** - CSS media queries 支持手机/平板/桌面
- **中文界面** - 所有文字显示中文
- **深色/亮色主题切换** - 🌓 按钮，localStorage 持久化
- **修复 /memories 路由** - 现在正常显示记忆列表页
- **丰富 API 数据** - /api/stats 返回完整统计（分类、重要度分布、时间统计）

### 📱 页面功能
| 页面 | 路由 | 功能 |
|------|------|------|
| 概览 | `/` | 统计卡片、分类分布、最近记忆 |
| 记忆列表 | `/memories` | 分页、筛选、排序 |
| 搜索 | `/search` | 关键词搜索 |

### 🔌 API 端点
| 端点 | 功能 |
|------|------|
| `/api/stats` | 完整统计 |
| `/api/memories` | 记忆列表（分页） |
| `/api/categories` | 分类列表 |
| `/api/search?q=` | 搜索 |
| `/api/recent` | 最近记忆 |
| `/api/top` | 高重要度记忆 |
| `/health` | 健康检查 |
