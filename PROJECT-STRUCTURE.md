# Unified Memory v5.2.0 - 项目结构

## 🏗️ 整体架构

```
unified-memory/
├── src/                          # 核心系统
│   ├── storage.js               # 存储引擎 (原子事务)
│   ├── transaction-manager.js   # 事务管理器
│   ├── vector_lancedb.js        # LanceDB 向量存储
│   ├── vector-chromadb-backend.js # ChromaDB 后端
│   ├── vector-store-abstract.js # 向量存储抽象层
│   ├── working_memory.js        # 工作内存
│   ├── working_memory_manager.js # 工作内存管理
│   ├── working_memory_injector.js # 工作内存注入器
│   ├── version_store.js         # 版本存储
│   ├── wal.js                   # 预写日志
│   ├── visualize/               # 可视化
│   │   ├── graph_visualizer.js
│   │   ├── heatmap.js
│   │   └── visualize.js
│   └── webui/                   # Web UI
│       ├── dashboard.js
│       ├── unified_server.js
│       └── webui.js
│
├── plugins/                     # 插件系统 (新增)
│   ├── sync/                    # 同步插件 (来自 memory-optimization)
│   │   ├── sync_bridge.js       # 同步桥梁
│   │   └── sync_cron.js         # 定时调度
│   ├── dedup/                   # 去重插件
│   │   └── cross_system_dedup.js # 跨系统去重
│   ├── api/                     # API 插件
│   │   └── unified_query_api.js # 统一查询 API
│   └── monitor/                 # 监控插件
│       └── health_check.js      # 健康检查
│
├── test/                        # 测试目录
│   ├── unit/                    # 单元测试
│   │   └── atomic-transaction.test.js
│   ├── integration/             # 集成测试
│   │   └── atomic-write.test.js
│   ├── benchmark/               # 性能测试
│   │   └── write-performance.js
│   ├── temp/                    # 临时测试脚本
│   │   ├── test-all-functions.js
│   │   ├── test-atomic-fix.js
│   │   ├── test-atomic-write.js
│   │   ├── test-core-modules.js
│   │   └── test-service.js
│   ├── test_enhanced_system.js
│   ├── test_integration_v270.js
│   ├── test_openviking_system.js
│   ├── verify_system.js
│   └── simple-atomic-test.js
│
├── docs/                        # 文档
│   ├── API.md                   # API 参考
│   ├── API_REFERENCE.md         # API 详细参考
│   ├── ARCHITECTURE.md          # 架构设计
│   ├── CHANGELOG.md             # 变更日志
│   ├── DEPLOYMENT.md            # 部署指南
│   ├── FEATURES.md              # 功能特性
│   ├── FIXES-AND-OPTIMIZATIONS.md # 修复与优化
│   ├── OPENVIKING_COMPARISON.md # OpenViking 对比
│   ├── QUICKSTART.md            # 快速开始
│   └── README-backup.md         # README 备份
│
├── archive/                     # 归档目录
│   ├── deployment-reports/      # 部署报告归档
│   │   ├── deployment-report-20260415-130816.md
│   │   └── deployment-report-20260415-133646.md
│   └── docs-backup/             # 文档备份
│       ├── COMPLETION-REPORT.md
│       ├── FINAL-COMPLETION-REPORT.md
│       ├── PROJECT-COMPLETION-SUMMARY.md
│       ├── PUSH-TO-GITHUB.md
│       ├── README-UPDATED.md
│       └── README-backup.md
│
├── scripts/                     # 脚本
│   ├── deploy-atomic-fixes.sh   # 原子修复部署脚本
│   ├── update-docs.sh           # 文档更新脚本
│   └── verify-repairs.sh        # 修复验证脚本
│
├── .clawhub/                    # ClawHub 配置
│   ├── lock.json
│   └── origin.json
│
├── .learnings/                  # 学习记录
│   └── learnings.md
│
├── CHANGELOG.md                 # 主变更日志
├── CONTRIBUTING.md              # 贡献指南
├── INSTALL.md                   # 安装指南
├── LICENSE                      # 许可证
├── README.md                    # 主 README
├── SKILL.md                     # 技能文档
├── _meta.json                   # 元数据
├── clawhub.json                 # ClawHub 配置
├── package.json                 # Node.js 配置
└── PROJECT-STRUCTURE.md         # 本项目结构文档
```

## 🔄 合并说明

### memory-optimization 合并
将 `memory-optimization` 分支的核心功能合并为插件系统：

1. **同步桥梁** (`plugins/sync/`)
   - `sync_bridge.js`: Workspace Memory ↔ Unified Memory 同步
   - `sync_cron.js`: 定时同步调度

2. **去重检查** (`plugins/dedup/`)
   - `cross_system_dedup.js`: 跨系统去重检查

3. **统一查询** (`plugins/api/`)
   - `unified_query_api.js`: 统一检索接口

4. **健康监控** (`plugins/monitor/`)
   - `health_check.js`: 系统健康监控

### 文件整理原则
1. **核心系统** (`src/`): 保持原有结构
2. **插件系统** (`plugins/`): 新增，来自 memory-optimization
3. **测试目录** (`test/`): 整理所有测试文件
4. **文档目录** (`docs/`): 统一文档
5. **归档目录** (`archive/`): 临时文件归档
6. **脚本目录** (`scripts/`): 部署和验证脚本

## 🚀 使用方式

### 核心系统
```bash
# 启动 Unified Memory 服务
node src/index.js

# 使用原子事务功能
import { addMemory, getAllMemories } from './src/storage.js';
```

### 插件系统
```bash
# 同步 Workspace Memory 到 Unified Memory
node plugins/sync/sync_bridge.js

# 定时同步 (cron)
node plugins/sync/sync_cron.js --scheduled

# 统一查询
node plugins/api/unified_query_api.js "搜索关键词"

# 健康检查
node plugins/monitor/health_check.js
```

### 部署与验证
```bash
# 部署原子修复
./scripts/deploy-atomic-fixes.sh

# 验证修复
./scripts/verify-repairs.sh

# 更新文档
./scripts/update-docs.sh
```

## 📊 版本信息

### v5.2.0 (当前版本)
- **原子事务管理器**: 两阶段提交协议，100% 数据一致性
- **数据持久化保证**: fsync + 原子重命名，零数据丢失
- **向量搜索优化**: 修复 WHERE 子句 bug，5-10倍性能提升
- **插件系统**: 集成 memory-optimization 功能
- **文档统一**: 完整的文档体系

### 分支状态
- **main**: 主分支，包含完整系统 + 插件
- **memory-optimization**: 已合并，可删除

## 🔧 维护指南

### 添加新插件
1. 在 `plugins/` 下创建新目录
2. 实现插件功能
3. 更新 `PROJECT-STRUCTURE.md`
4. 添加到 `package.json` scripts

### 更新文档
1. 修改 `docs/` 下的对应文件
2. 运行 `./scripts/update-docs.sh`
3. 更新 `CHANGELOG.md`

### 测试流程
```bash
# 单元测试
npm test -- test/unit/

# 集成测试
npm test -- test/integration/

# 性能测试
npm test -- test/benchmark/

# 临时测试
npm test -- test/temp/
```

## 📝 下一步计划

1. **删除 memory-optimization 分支** (已合并)
2. **更新 package.json** 包含插件 scripts
3. **创建插件配置系统**
4. **添加插件文档**
5. **优化插件集成**

---

**最后更新**: 2026-04-15  
**版本**: v5.2.0  
**状态**: 🟢 生产就绪  
**GitHub**: https://github.com/mouxangithub/unified-memory