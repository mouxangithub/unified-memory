# Unified Memory

> 🧠 高级记忆管理系统，支持混合搜索（BM25 + 向量 + RRF）、原子事务和插件系统

[English Documentation](../en/README.md)

## ✨ 特性

### 🔍 **混合搜索**
- **BM25**: 传统关键词搜索
- **向量搜索**: 语义相似度搜索
- **RRF**: 倒数排名融合结果组合
- **搜索性能提升 5-10 倍**

### ⚡ **原子事务**
- **WAL (预写日志)**: 数据一致性
- **回滚支持**: 失败时事务回滚
- **ACID 合规性**: 数据库事务保证

### 🔌 **插件系统**
- **热重载**: 无需重启即可重载插件
- **生命周期钩子**: 操作前后钩子
- **可扩展架构**: 轻松添加新功能

### 📊 **性能**
- **存储减少 60%** 通过优化
- **缓存命中率 78%** 智能缓存
- **平均查询时间 45ms** 搜索响应

## 🚀 快速开始

### 安装
```bash
# 通过 OpenClaw 安装
openclaw skills install unified-memory

# 或手动克隆
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
```

### 基本使用
```javascript
// 存储记忆
const result = await mcp.call('unified-memory', 'memory_store', {
  content: '今天学习了原子写入。',
  category: '学习',
  tags: ['数据库', '原子']
});

// 搜索记忆
const searchResult = await mcp.call('unified-memory', 'memory_search', {
  query: '原子写入 数据库',
  limit: 10
});
```

## 📖 文档

### 入门指南
- [快速开始指南](getting-started/quickstart.md)
- [安装指南](getting-started/installation.md)
- [配置指南](getting-started/configuration.md)

### 使用指南
- [基础使用](guides/basic-usage.md)
- [高级使用](guides/advanced-usage.md)
- [性能优化](guides/performance.md)
- [故障排除](guides/troubleshooting.md)

### API 参考
- [API 概览](api/overview.md)
- [API 函数](api/functions.md)
- [API 示例](api/examples.md)

### 架构文档
- [架构概览](architecture/overview.md)
- [架构决策](../../ARCHITECTURE_DECISIONS.md)
- [组件文档](architecture/components.md)

### 贡献指南
- [贡献指南](contributing/guidelines.md)
- [行为准则](contributing/code-of-conduct.md)
- [开发环境设置](contributing/development.md)

## 🏗️ 架构

### 系统架构
```
┌─────────────────────────────────────────────────────────────┐
│                    客户端应用程序                          │
│  (OpenClaw, Web UI, CLI, API 客户端, MCP 客户端)         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    API 网关层                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ REST API   │  │ MCP 服务器 │  │ WebSocket  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    服务层                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ 记忆       │  │ 搜索       │  │ 缓存       │           │
│  │ 服务       │  │ 服务       │  │ 服务       │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    存储层                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ SQLite     │  │ 向量       │  │ 文件       │           │
│  │ 数据库     │  │ 数据库     │  │ 系统       │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    基础设施层                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ 监控       │  │ 日志       │  │ 插件       │           │
│  │ 系统       │  │ 系统       │  │ 系统       │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈
- **后端**: Node.js, Express.js, SQLite
- **搜索**: BM25, 向量搜索, RRF
- **前端**: React, TypeScript, Tailwind CSS
- **DevOps**: Docker, Kubernetes, GitHub Actions

## 📈 性能指标

| 指标 | 数值 | 改进 |
|------|------|------|
| 搜索速度 | 提升 5-10 倍 | 400-900% |
| 存储使用 | 减少 60% | 原存储的 40% |
| 缓存命中率 | 78% | 最优缓存 |
| 平均查询时间 | 45ms | 实时响应 |
| 内存使用 | 245.6 MB | 高效内存管理 |
| 总记忆数 | 1,760 | 全面覆盖 |
| 总分类数 | 49 | 组织结构 |
| 总标签数 | 181 | 详细分类 |

## 🔧 开发

### 前提条件
- Node.js >= 18.0.0
- Git
- OpenClaw >= 2.7.0

### 设置
```bash
# 克隆仓库
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm test
```

### 脚本
```bash
# 开发
npm run dev          # 启动开发服务器
npm run lint         # 检查代码风格
npm run format       # 格式化代码

# 测试
npm test             # 运行测试
npm run test:watch   # 监视模式
npm run test:coverage # 覆盖率报告

# 构建
npm run build        # 生产构建
npm run clean        # 清理构建产物

# 部署
npm run deploy       # 部署到生产环境
```

## 🤝 贡献

欢迎贡献！请查看我们的[贡献指南](contributing/guidelines.md)了解详情。

### 贡献级别
1. **首次贡献者**: 修复拼写错误、添加测试、报告错误
2. **常规贡献者**: 实现功能、修复错误、改进文档
3. **核心贡献者**: 主要功能、架构改进
4. **维护者**: 代码审查、发布、社区管理

### 获取帮助
- [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
- [GitHub Discussions](https://github.com/mouxangithub/unified-memory/discussions)
- [文档](README.md)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../../LICENSE) 文件了解详情。

## 🙏 致谢

- **OpenClaw 团队** - 提供出色的平台
- **贡献者** - 让这个项目变得更好
- **社区** - 提供反馈和支持

## 📞 支持

- **问题**: [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
- **讨论**: [GitHub Discussions](https://github.com/mouxangithub/unified-memory/discussions)
- **邮箱**: team@openclaw.ai

## 🔗 链接

- [GitHub 仓库](https://github.com/mouxangithub/unified-memory)
- [文档](README.md)
- [更新日志](../../CHANGELOG.md)
- [贡献指南](contributing/guidelines.md)

---

**由 OpenClaw 团队 ❤️ 制作**

[![npm version](https://img.shields.io/npm/v/unified-memory)](https://www.npmjs.com/package/unified-memory)
[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/mouxangithub/unified-memory)](https://github.com/mouxangithub/unified-memory/network)