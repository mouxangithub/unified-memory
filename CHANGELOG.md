# Changelog

## v2.1.0 (2026-03-27)

### Added
- 33 MCP tools fully registered (previously 22)
- 11 new tools: `memory_noise`, `memory_intent`, `memory_extract`, `memory_reflection`, `memory_wal`, `memory_tier`, `memory_adaptive`, `memory_bm25`, `memory_vector`, `memory_mmr`, `memory_scope`, `memory_rerank_llm`
- Complete search pipeline: BM25 → Vector → LLM Rerank → MMR → Weibull Decay → Scope Filter → RRF Fusion
- SKILL.md completely rewritten to reflect actual 33 tools and 147 modules
- Preference Slots system (`memory_preference_slots`)
- Lesson system (`memory_lessons`)
- HOT/WARM/COLD tier management (`memory_tier`)
- Write-Ahead Log for crash recovery (`memory_wal`)
- Intent routing for query classification (`memory_intent`)
- Noise pattern learning (`memory_noise`)

### Fixed
- noise.js `(?i)` regex bug (subagent-generated, incompatible with Node.js)
- tier.js ISO timestamp parsing (ISO string + Unix ms dual format support)
- SKILL.md outdated claims (memory-lancedb-pro dependency, wrong tool count)

### Changed
- SKILL.md: accurate 33 tools / 147 modules description
- Removed outdated docs: AGENT_MEMORY_GUID.md, PROMPT.md, OPTIMIZATION.md, TODO.md, README_MCP.md, README_QMD.md, index.html
- Version bumped to v2.1.0

## v2.0.0 (2026-03-27)

### Added
- Full Node.js ESM rewrite (147 JS modules)
- MCP Server with 22 tools
- Hybrid search (BM25 + Vector + RRF)
- Weibull time decay
- Scope isolation (AGENT/USER/TEAM/GLOBAL)
- Self-improving: reflection, dedup, lesson system
- Ollama integration for embeddings and LLM

### Removed
- Python version (deprecated)

---

## v2.0 (2026-03-27) — Phase 2 Complete

### 新增 | Added
- 86个MCP工具（从33个大幅扩展）
- 完整的BM25 + Vector + RRF混合搜索管道
- Episode / Procedural / Rule 记忆系统
- 知识图谱 / 主动召回 / 预测推荐
- 可观测性（WAL追踪、指标、模板）
- HTTP REST API（health/search/memory端点）
- 零门槛安装脚本（install.sh）
- 双语文档（中英文索引）

### 修复 | Fixed
- node_modules不再上传Git
- package.json peerDependencies修正

### 文档 | Documentation
- README完全重写（零门槛接入方案）
- SKILL.md/SKILL_EN.md双语索引
