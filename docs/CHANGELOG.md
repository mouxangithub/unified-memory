# Changelog (v3.8.6)
<!-- zh -->
> 统一记忆系统完整版本历史 | Consolidated Version History

All notable changes to unified-memory are documented here.

---

## v3.8.0 (2026-03-30) — WAL · Evidence · Auto-Organize
<!-- zh -->

### 🚀 New Features

#### WAL Protocol (Write-Ahead Log)
- `memory_wal_write` — Write entry to WAL with checksum
- `memory_wal_replay` — Replay WAL entries for crash recovery
- `memory_wal_status` — Get WAL status and statistics
- `memory_wal_truncate` — Truncate WAL after successful commit
- `memory_wal_export` — Export WAL for backup
- `memory_wal_import` — Import WAL from backup
- Checksum verification for data integrity
- Automatic crash recovery on startup
- Backward compatible with existing storage.js

#### Evidence Chain Mechanism
- `memory_evidence_add` — Add evidence to memory's chain
- `memory_evidence_get` — Get evidence chain for a memory
- `memory_evidence_find_by_type` — Find memories by evidence type
- `memory_evidence_find_by_source` — Find memories by source ID
- `memory_evidence_stats` — Get evidence statistics
- Source tracking: transcript, message, manual, inference, git_note, revision
- Confidence scoring (0-1)

#### Auto Organization
- `memory_organize` — Organize memories across tiers
- `memory_compress_tier` — Compress memories in a specific tier
- `memory_archive_old` — Archive memories older than threshold
- `memory_tier_stats` — Get tier statistics
- `memory_full_organize` — Run full organization (organize + compress + archive)
- Automatic tier migration: HOT (7d, 50%), WARM (30d, 30%), COLD (365d, 10%)

### 📊 Statistics
| Metric | Value |
|--------|-------|
| Total Tools | 112 (+15) |
| Lines of Code | ~29K (+4K) |
| New Files | 3 |

---

## v3.7.0 (2026-03-29)
<!-- zh -->

### Features
- 97 MCP tools fully registered
- Complete memory system with all core features
- HOT/WARM/COLD tier management
- BM25 + Vector + RRF hybrid search
- Scope isolation (AGENT/USER/TEAM/GLOBAL)
- Weibull time decay
- Git-Notes integration
- Cloud backup API
- Cognitive scheduler
- Memory lanes
- Token budget
- Revision manager

---

## v3.6.0 (2026-03-29)
<!-- zh -->

### 🐛 Bug Fixes

- **WAL cleanup on startup**: `initWalStorage()` now deletes old WAL files on each restart, preventing WAL directory bloat (previously 104 stale .wal.jsonl files accumulated)
- **Vector cache health check false 0%**: Health check was using `Array.isArray(embedding)` but LanceDB stores embeddings as base64 strings in JSON — fixed to accept both string and array formats
- **vector_cache_complete_rate**: Correctly reports 100% when all 117 memories have vectors in LanceDB

### 📊 System Health (after fixes)
```
memoryCount: 117
vector_cache_complete_rate: 100%
ollama: connected
WAL record count: 0 (clean on restart)
```

---

## v3.5.0 (2026-03-28)
<!-- zh -->

### 🚀 Features

- **Unified Web UI + API Server** — Single port (3850) for all dashboards, memory API, and health endpoints
- **Responsive mobile design** — CSS media queries for phone/tablet/desktop
- **Chinese interface** — Full Chinese localization
- **Dark/Light theme toggle** — Persisted in localStorage
- **Enriched API data** — `/api/stats` returns category, importance, time distributions

### 📱 Pages
| Page | Route | Features |
|------|-------|----------|
| Overview | `/` | Stats cards, category distribution, recent memories |
| Memory List | `/memories` | Pagination, filter, sort |
| Search | `/search` | Keyword search |

### 🔌 API Endpoints
| Endpoint | Feature |
|----------|---------|
| `/api/stats` | Complete statistics |
| `/api/memories` | Memory list (paginated) |
| `/api/categories` | Category list |
| `/api/search?q=` | Search |
| `/api/recent` | Recent memories |
| `/api/top` | High-importance memories |
| `/health` | Health check |

---

## v2.7.0 (2026-03-28)
<!-- zh -->

### Web UI Dashboard ⭐ NEW
- `npm run dashboard` — Launch monitoring dashboard on port 3849
- Real-time stats: total memories, 7d growth, access counts
- Memory distribution: by category, scope, tier, importance, tags
- System health: Ollama, LanceDB, memory file, storage usage
- 14-day growth trend chart (Chart.js bar chart)
- Scope donut chart
- Management actions: cleanup old memories, export JSON
- Auto-refresh every 5 seconds via AJAX

### Identity Memory Type ⭐ NEW
- New `identity` category family: `identity`, `preference`, `habit`, `requirement`, `skill`, `goal`
- Identity memories always use `importance >= 0.9`
- Identity extraction tools: `memory_identity_extract`, `memory_identity_update`, `memory_identity_get`
- Auto-store integration with IDENTITY_PATTERNS

---

## v2.6.0 (2026-03-28)
<!-- zh -->

### Phase 3 — Complete

- **LanceDB query-level scope filtering** — B-tree index on `scope` column
- **Plugin Interface** — `phase3_memory_search`, `phase3_memory_get`, `phase3_memory_write`
- **QMD Search Backend** — `memory_qmd_query`, `memory_qmd_status`, `memory_qmd_search2`
- **Git Integration** — `memory_git_init`, `memory_git_sync/history/note/pull/push`
- **Cloud Backup** — `memory_cloud_sync/push/pull`
- **Weibull Decay** — Shape=1.5, scale=30 days, access reward +5% up to 50% cap

---

## v2.4.0 (2026-03-27)
<!-- zh -->

- 86 MCP tools complete (33 → 86)
- Episode / Procedural / Rule memory system
- Knowledge graph / proactive recall / prediction
- Observability (WAL tracing, metrics, templates)
- HTTP REST API
- Dual-language docs (Chinese + English)

---

## v2.1.0 (2026-03-27)
<!-- zh -->

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
<!-- zh -->

- Full Node.js ESM rewrite (147 JS modules)
- Weibull time decay
- Scope isolation (AGENT/USER/TEAM/GLOBAL)

---

## v1.x (2026-03-25)
<!-- zh -->

- Python prototype

---

## Summary / 版本概要
<!-- zh -->

| Version | Date | Key Additions |
|---------|------|--------------|
| v3.8.0 | 2026-03-30 | WAL Protocol, Evidence Chain, Auto-Organize |
| v3.7.0 | 2026-03-29 | 97 tools, complete feature set |
| v3.6.0 | 2026-03-29 | Bug fixes (WAL cleanup, vector cache) |
| v3.5.0 | 2026-03-28 | Web UI, API Server, Chinese UI |
| v2.7.0 | 2026-03-28 | Dashboard, Identity memory |
| v2.6.0 | 2026-03-28 | Phase 3 plugins, Git, Cloud backup |
| v2.4.0 | 2026-03-27 | 86 tools, KG, REST API |
| v2.1.0 | 2026-03-27 | 33 tools, tier management, WAL |
| v2.0.0 | 2026-03-26 | Node.js ESM rewrite |
| v1.x | 2026-03-25 | Python prototype |

---

*Last updated: 2026-03-31*
