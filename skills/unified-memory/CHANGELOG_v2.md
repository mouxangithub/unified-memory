# Changelog - v2.0.0

**发布日期**: 2026-03-23  
**代号**: 全面对标 QMD/MetaGPT

---

## 新增功能

### 1. Context Tree（项目级上下文管理）

对标 QMD 的核心创新，提供层级上下文管理。

**功能**:
- 自动维护 `current.md`（当前状态）
- 自动记录决策
- 快速恢复上下文
- 导出项目状态

**使用**:
```bash
mem ctx init "项目名"
mem ctx update "任务" --progress 50
mem ctx decision "标题" "内容"
mem ctx status
mem ctx export
```

---

### 2. Smart Summarizer（智能摘要）

压缩历史，提取精华。

**功能**:
- 压缩 7 天内的日志
- 提取关键决策
- 生成项目摘要
- 提取关键实体

**使用**:
```bash
mem summary compress --days 7
mem summary decisions --days 30
mem summary summary
```

---

### 3. Project Templates（项目模板）

快速启动常用项目。

**模板**:
- `software-project` - 软件开发项目
- `content-creation` - 内容创作项目
- `research` - 研究项目

**使用**:
```bash
mem template list
mem template create software-project ./my-app
```

---

### 4. Workflow Validator（工作流验证）

确保工作流能用。

**功能**:
- 验证 SOP 配置
- 验证 CLI 命令
- 验证核心模块
- 生成测试报告

**使用**:
```bash
mem validate
```

---

### 5. 统一 CLI v3.0

整合所有功能到一个入口。

**命令**:
```bash
# 记忆管理
mem store "内容" --tags "标签"
mem search "查询"

# 项目管理
mem ctx init/update/decision/status/export

# 智能摘要
mem summary compress/decisions/summary

# 项目模板
mem template list/create

# 系统管理
mem health
mem validate
```

---

### 6. 真实案例文档

5 个真实使用案例：
1. 软件开发项目
2. 问题排查
3. 知识管理
4. 团队协作
5. 持续改进

**路径**: `docs/REAL_CASES.md`

---

## 核心改进

| 改进项 | 状态 | 说明 |
|--------|------|------|
| Context Tree | ✅ | 对标 QMD |
| 智能摘要 | ✅ | 压缩历史 |
| 项目模板 | ✅ | 快速启动 |
| 工作流验证 | ✅ | 确保能用 |
| 真实案例 | ✅ | 快速上手 |
| CLI v3.0 | ✅ | 统一入口 |
| 降级逻辑 | ✅ | 确保任何情况都能工作 |

---

## 对比 QMD/MetaGPT

| 维度 | 我们 | QMD | MetaGPT |
|------|------|-----|---------|
| 依赖数量 | 0 个 ✅ | ~5 个 | 70+ 个 |
| 记忆系统 | ✅ | ✅ | ❌ |
| Context Tree | ✅ | ✅ | ⚠️ |
| 智能摘要 | ✅ | ✅ | ❌ |
| 项目模板 | ✅ | ❌ | ✅ |
| 多模态 | ✅ | ❌ | ⚠️ |
| 智能分类 | ✅ | ❌ | ❌ |
| 工作流验证 | ✅ | ❌ | ⚠️ |
| 零依赖 | ✅ | ❌ | ❌ |

---

## 差异化定位

**定位**: AI Agent 的"大脑 + 记忆 + 工作流"一体化

**优势**:
1. 多模态 - OCR/STT/QA
2. 智能分类 - 自动打标签
3. 零依赖 - 开箱即用
4. 功能全面 - 记忆 + 协作 + 工作流

**差异化**:
- QMD 擅长个人项目记忆 → 我们做**团队 + 项目 + 多模态**
- MetaGPT 擅长多 Agent → 我们做**智能调度 + 记忆驱动**

---

## 实战验证

**验证项目**: 官网更新

**发现的问题**:
1. CLI 导入失败 → ✅ 已修复
2. 缺少降级逻辑 → ✅ 已添加
3. 错误提示不清晰 → ✅ 已改进
4. 文档不够实用 → ✅ 已添加真实案例

**修复**:
- 重写 CLI，添加降级逻辑
- 确保任何情况下都能工作
- 添加友好错误提示

**效率**:
- 项目启动: 2 分钟
- 首页开发: 8 分钟
- 问题修复: 15 分钟
- 总计: 25 分钟

---

## 下一步

### 第一周
- [ ] 收集用户反馈
- [ ] 修复发现的问题
- [ ] 优化性能

### 第二周
- [ ] 添加更多项目模板
- [ ] 完善文档
- [ ] 添加更多案例

### 第三周
- [ ] 开放 API
- [ ] 建设社区
- [ ] 收集反馈

### 第四周
- [ ] 生态系统建设
- [ ] 插件系统
- [ ] 持续改进

---

*更新时间: 2026-03-23 09:35 Asia/Shanghai*
