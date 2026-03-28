# Changelog

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
