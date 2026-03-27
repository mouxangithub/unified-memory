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
