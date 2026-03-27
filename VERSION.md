# Unified Memory - Version History

## 当前版本

**v2.0.0** (2026-03-27)

---

## 版本历史

| 版本 | 日期 | 主要功能 |
|------|------|----------|
| **v2.0.0** | 2026-03-27 | 完全 Node.js ESM 重构，129 模块，MCP Server + REST API + WebUI + Workflow Engine + Sandbox + Code Generator |
| **v0.9.0** | 2026-03-22 | Agent 协作系统，Workflow Engine + LLM Provider + Sandbox + Code Generator |
| **v0.8.0** | 2026-03-21 | 敏感信息加密 + 记忆预测 + 多模态记忆 |
| **v0.7.0** | 2026-03-21 | 文档更新+发布修复 |
| **v0.6.0** | 2026-03-21 | 决策追溯+热力图+协作可视化+压缩评估+跨Agent共享 |
| **v0.5.1** | 2026-03-21 | QMD风格搜索+MCP Server |
| **v0.3.5** | 2026-03-21 | QMD风格搜索+MCP Server |
| **v0.3.1** | 2026-03-18 | 完整架构 + 多代理同步 + 审计日志 |
| 0.3.0 | 2026-03-18 | 自适应置信度 + 主动注入 |
| 0.2.3 | 2026-03-18 | 云同步完整使用指南 |
| 0.2.2 | 2026-03-18 | 云同步全平台支持 |
| 0.2.1 | 2026-03-18 | 性能+洞察+隐私+云同步 |
| 0.2.0 | 2026-03-18 | 智能问答+图谱+多模态+全自动 |
| 0.1.9 | 2026-03-18 | 完整 Agent 集成 |
| **0.1.3** | 2026-03-18 | 记忆摘要 + 知识卡片导出 |
| 0.1.2 | 2026-03-18 | 对话去重 + 批量预热 + 并发查询 |
| 0.1.1 | 2026-03-18 | 文档版本号清理 |
| 0.1.0 | 2026-03-18 | 关联推荐 + 自动标签 |
| 0.0.9 | 2026-03-18 | 权限声明修复 |
| 0.0.8 | 2026-03-18 | 重命名脚本 + 隐私修复 |
| 0.0.7 | 2026-03-18 | 分层缓存 + 知识合并 |
| 0.0.6 | - | 多通道记忆合并 |
| 0.0.5 | - | Ontology 知识图谱 |
| 0.0.4 | - | 混合检索 |
| 0.0.3 | - | 用户画像维护 |
| 0.0.2 | - | 向量数据库集成 |
| 0.0.1 | - | 基础记忆存储 |

---

## v2.0.0 迁移说明

### Python 版本已 DEPRECATED

Python 版本的 unified-memory 已标记为废弃，请迁移到 Node.js 版本。

### 迁移路径

| 旧版 (Python) | 新版 (Node.js) |
|--------------|----------------|
| `python3 scripts/memory.py` | `node src/cli/index.js` |
| `python3 scripts/memory_all_in_one.py` | `node src/system/all_in_one.js` |
| MCP Server | `node src/index.js` |
| REST API | `node src/api/rest_server.js` |
| WebUI | `node src/webui/webui.js` |

### 版本命名规则

- **MAJOR.MINOR.PATCH** (v2.0.0 起)
- **MAJOR**: 重大架构变更
- **MINOR**: 新功能
- **PATCH**: Bug 修复

---

## 发布检查清单

每次发布前确认：
- [ ] 更新 `skill.json` 版本号
- [ ] 更新 `VERSION.md` 变更日志
- [ ] 更新 `CHANGELOG.md`
- [ ] `git commit && git push`
- [ ] `clawhub publish . --version x.x.x`
