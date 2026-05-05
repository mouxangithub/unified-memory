# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] - 2026-05-05

### Added

- 🧠 **自动记忆功能** - 重要性评分 > 0.7 时自动存储
  - 7维度重要性评分算法：
    - 内容长度 (+0.1)
    - 决策/偏好信号 (+0.2)
    - 情感/情绪信号 (+0.15)
    - 事实/信息性内容 (+0.15)
    - 项目/任务关联 (+0.15)
    - 实体检测 (+0.1)
    - 问句 (-0.1)
  - `auto_analyze` 工具 - 仅分析不存储
  - `auto` 参数 - 控制自动评估开关

- 📊 统计跟踪 - `autoRememberCount` 跟踪自动记忆次数

- 🔬 重要性分析 - 预分析功能，返回评分、理由、存储建议

### Changed

- `gbrain_mcp_server.js` 升级到 v1.1.0
- 更新 SKILL.md 和 README.md 添加自动记忆说明
- 优化一句话安装配置说明

### Fixed

- 修复统计保存功能（saveStats）

## [1.0.0] - 2026-04-20

### Added

- 初始版本
- 基础记忆存储 (`remember`)
- 语义搜索 (`search`)
- 记忆关联网络 (MemoryGraph)
- 实体检测 (EntityDetector)
- 类型化链接 (Typed Links)
- 来源追溯 (Source Attribution)
- MCP 服务器接口
- OpenClaw Skill 定义
- 高级功能模块：
  - API Gateway
  - Version Control
  - Cache Manager
  - Monitoring
  - Backup/Restore
  - Archival
  - Benchmark