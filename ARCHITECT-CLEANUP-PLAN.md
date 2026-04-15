# Unified Memory 项目架构整理计划

## 🎯 整理目标
1. 清理冗余文件和脚本
2. 标准化项目结构
3. 准备文档专家工作
4. 准备 ClawHub 发布

## 📊 当前问题分析

### 1. 脚本问题
- **6个 .sh 脚本**，需要评估必要性
- 部分脚本可能功能重叠
- 缺乏统一的脚本管理

### 2. 文档问题
- **201个 .md 文件**，大量重复
- 79个 README.md 文件需要清理
- 中英文文档不统一

### 3. 结构问题
- memory-optimization 文件夹已删除 ✓
- 目录结构需要进一步标准化
- 测试文件需要整理

## 🧹 清理策略

### 阶段1: 脚本整理 ✅
```
保留的脚本:
├── install.sh                    # 用户安装 (根目录)
├── scripts/deploy.sh            # 通用部署
├── scripts/deploy/deploy-atomic-fixes.sh # 原子修复部署
├── scripts/dev.sh               # 开发环境
├── scripts/docs/update-docs.sh  # 文档更新
└── scripts/verify/verify-repairs.sh # 修复验证

删除的脚本: 无 (所有脚本都有用)
```

### 阶段2: 文档初步清理
```
删除策略:
1. 删除 test/ 目录外的重复 README.md
2. 统一 docs/ 目录结构
3. 清理 archive/ 中的临时文档
```

### 阶段3: 项目结构标准化
```
目标结构:
unified-memory/
├── src/                    # 核心系统
├── plugins/               # 插件系统
├── scripts/               # 脚本目录
├── test/                  # 测试目录
├── docs/                  # 文档目录 (待专家重写)
├── config/                # 配置文件
├── bin/                   # 可执行文件
└── install.sh            # 安装脚本
```

## 📋 执行步骤

### 步骤1: 清理重复文档
```bash
# 删除 docs/ 外的重复 README.md
find . -name "README.md" -type f ! -path "./docs/*" ! -path "./test/*" -delete

# 保留必要的 README.md
# - docs/README.md (主文档)
# - test/README.md (测试文档)
```

### 步骤2: 创建标准目录结构
```bash
# 创建缺失的目录
mkdir -p config bin examples

# 移动配置文件
mv *.json config/ 2>/dev/null || true
mv *.config.js config/ 2>/dev/null || true

# 移动示例文件
find . -name "*example*" -type f -exec mv {} examples/ 2>/dev/null \;
```

### 步骤3: 更新 package.json
```json
{
  "scripts": {
    "start": "node src/index.js",
    "dev": "./scripts/dev.sh",
    "deploy": "./scripts/deploy.sh",
    "deploy:atomic": "./scripts/deploy/deploy-atomic-fixes.sh",
    "verify": "./scripts/verify/verify-repairs.sh",
    "docs": "./scripts/docs/update-docs.sh",
    "install": "./install.sh"
  },
  "bin": {
    "unified-memory": "./bin/cli.js"
  }
}
```

### 步骤4: 创建 ClawHub 准备目录
```bash
mkdir -p .clawhub
# 准备 ClawHub 发布文件
```

## 🚀 交付物

### 1. 清理后的项目结构
```
unified-memory/
├── src/                    # 核心代码
├── plugins/               # 插件系统
├── scripts/               # 统一脚本
├── test/                  # 测试文件
├── docs/                  # 文档目录 (待重写)
├── config/                # 配置文件
├── bin/                   # CLI工具
├── examples/              # 示例代码
├── .clawhub/              # ClawHub 配置
├── install.sh            # 安装脚本
├── README.md             # 主文档
├── package.json          # 项目配置
└── PROJECT-STRUCTURE.md  # 项目结构文档
```

### 2. 清理报告
- 删除的文件列表
- 保留的文件说明
- 结构变更记录

### 3. 下一步工作建议
- 文档专家: 重写所有文档
- ClawHub 专家: 准备发布配置
- 测试专家: 完善测试套件

## ⏱️ 时间估计
- 脚本整理: 已完成 ✓
- 文档初步清理: 1小时
- 结构标准化: 1小时
- 配置更新: 30分钟
- 测试验证: 1小时

**总计**: 3.5小时

## 📝 成功标准
1. 文件数量减少 20%+
2. 脚本数量合理 (6个)
3. 目录结构清晰标准
4. 文档专家可以开始工作
5. ClawHub 专家可以开始工作

## 🔧 风险控制
- 备份重要文件 before 删除
- 逐步执行，验证每一步
- 保持 Git 提交记录
- 测试核心功能 after 清理

---

**计划制定时间**: 2026-04-15 19:30 GMT+8  
**执行者**: 架构师 (手动执行)  
**项目版本**: v5.2.0  
**GitHub**: https://github.com/mouxangithub/unified-memory