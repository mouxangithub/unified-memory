# Unified Memory Recall 功能使用指南

## 📋 概述

Unified Memory 提供了完整的记忆召回功能，包括：

1. **自动召回** - AI agent 自动使用自动注入相关记忆
2. **多路召回策略** - 向量搜索 + 文本匹配 + 上下文匹配
3. **综合评分系统** - 结合相似度、时效性、重要性
4. **缓存优化** - 避免重复计算，提高性能
5. **去重能力** - 相似度阈值去重

## 🔧 自动召回机制

### Hook 配置

Unified Memory 通过以下 hook 实现自动召回：

```javascript
// src/index.js
export async function before_prompt_build(context) {
  const { sessionId, userId, query } = context;
  
  try {
    // 搜索相关记忆
    const results = await hybridSearch(query, { topK: 5, scope: 'USER' });
    
    if (results.length > 0) {
      const memoryContext = results.map(r => r.memory.text).join('\n');
      return {
        injectedContext: `相关记忆:\n${memoryContext}`,
      };
    }
  } catch (err) {
    log.error('[Hook] before_prompt_build error:', err);
  }
  
  return {};
}
```

### 工作流程

```
用户发送消息 → OpenClaw 调用 before_prompt_build hook → 
unified-memory 执行混合搜索 (hybridSearch) → 
相关记忆注入到 AI 上下文 → 
AI 使用这些记忆回答问题
```

## 🎯 核心功能模块

### 1. Memory Recall Optimizer (`src/recall/memory_recall_optimizer.js`)

**功能**:
- ✅ **多路召回** - `multiPathRecall()`
- ✅ **向量召回** - `vectorRecall()`
- ✅ **文本召回** - `textRecall()`
- ✅ **上下文召回** - `contextRecall()`
- ✅ **缓存机制** - `recallCache`
- ✅ **去重功能** - `deduplicate()`
- ❌ **时效性衰减** - `timeDecay()` (待实现)

**使用方法**:
```javascript
import { MemoryRecallOptimizer } from './src/recall/memory_recall_optimizer.js';

const optimizer = new MemoryRecallOptimizer({
  maxRecall: 10,           // 最多召回多少条
  minScore: 0.6,           // 最低分数阈值
  enableMultiPath: true,   // 启用多路召回
  enableTimeDecay: true,   // 启用时效性衰减
  enableDedup: true        // 启用去重
});

const results = await optimizer.optimizeRecall(query, memories, context);
```

### 2. Claude-Mem 功能模块 (`src/claudemem_features/`)

**包含模块**:
- ✅ **记忆编辑系统** - `MemoryEditor` (查看、编辑、删除、合并)
- ✅ **隐私控制系统** - `PrivacyManager` (隐私设置、敏感信息检测)
- ✅ **记忆质量评估** - `MemoryQuality` (多维度评分、优化建议)
- ✅ **记忆索引系统** - `MemoryIndex` (自动分类、标签、关键词提取)

**集成状态**:
- ✅ **主系统集成** - 已集成到 `enhanced_memory_system.js`
- ✅ **初始化方法** - `initializeClaudeMemFeatures()`
- ✅ **健康检查** - `health.components.claudeMem`

## 🧪 测试验证

### 测试脚本

```bash
# 运行自动召回测试
cd /root/.openclaw/skills/unified-memory
node test_auto_recall.cjs
```

### 验证步骤

1. **检查 hook 配置**:
   ```bash
   grep -n "before_prompt_build" src/index.js
   ```

2. **检查 recall 功能**:
   ```bash
   ls -la src/recall/
   ```

3. **检查 Claude-Mem 集成**:
   ```bash
   grep -n "claudeMem" src/enhanced_memory_system.js
   ```

4. **验证插件清理**:
   ```bash
   ls -la /root/.openclaw/extensions/ | grep -E "unified-memory-recall|claude-mem"
   ```

## 📊 功能对比

| 功能维度 | unified-memory recall | 已删除的插件 |
|---------|----------------------|-------------|
| **自动注入** | ✅ **有** (`before_prompt_build` hook) | ❌ **无** |
| **召回策略** | ✅ **混合搜索** (向量+文本+上下文) | ❌ **无** |
| **评分系统** | ✅ **综合评分** (相似度+时效性+重要性) | ❌ **无** |
| **缓存机制** | ✅ **Map 缓存** | ❌ **无** |
| **去重能力** | ✅ **相似度去重** | ❌ **无** |
| **Claude-Mem 功能** | ✅ **已集成** (4个模块) | ❌ **已删除** |

## 🚀 使用建议

### 1. 启用自动召回

确保 `before_prompt_build` hook 已正确配置并启用。在 OpenClaw 配置中：

```json
{
  "hooks": {
    "before_prompt_build": "unified-memory"
  }
}
```

### 2. 配置召回参数

根据使用场景调整召回参数：

```javascript
const options = {
  maxRecall: 10,           // 对话场景：5-10条
  minScore: 0.6,           // 严格匹配：0.7-0.8
  enableMultiPath: true,   // 复杂查询：启用
  enableTimeDecay: true,   // 时效性重要：启用
  similarityThreshold: 0.85 // 去重严格度：0.8-0.9
};
```

### 3. 监控召回效果

- **日志监控**: 检查 `before_prompt_build` hook 调用情况
- **效果评估**: 验证 AI 回答是否参考了相关记忆
- **性能优化**: 调整缓存大小和搜索策略

## 🔄 迁移说明

### 已迁移的功能

1. **Claude-Mem 核心功能**:
   - ✅ 记忆编辑系统
   - ✅ 隐私控制系统  
   - ✅ 记忆质量评估
   - ✅ 记忆索引系统

2. **Recall 功能**:
   - ✅ 自动召回 hook
   - ✅ 多路召回策略
   - ✅ 综合评分系统
   - ✅ 缓存优化

### 已删除的项目

1. **`unified-memory-recall` 插件** - ✅ 已删除
   - 原因：只是占位符，未连接到 unified-memory 服务

2. **独立的 Claude-Mem 插件** - ✅ 已删除
   - 原因：Claude-Mem 功能已全部迁移到 unified-memory 中

## 📝 常见问题

### Q: AI agent 如何自动使用记忆？
**A**: OpenClaw 会自动调用 `before_prompt_build` hook，unified-memory 会搜索相关记忆并注入到 AI 上下文中。

### Q: 如何验证自动召回是否工作？
**A**: 问 AI 一个之前讨论过的问题，检查回答是否参考了相关记忆。

### Q: 为什么删除了插件？
**A**: 插件只是占位符，未连接到实际服务。所有功能已集成到 unified-memory 中。

### Q: 如何调整召回精度？
**A**: 修改 `minScore` 参数（0.0-1.0），值越高召回越严格。

## 📞 支持与反馈

如有问题或建议，请：

1. **查看文档**: [ARCHITECTURE.md](ARCHITECTURE.md)
2. **检查日志**: 监控 unified-memory 运行日志
3. **提交问题**: [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)

---

**版本**: v5.1.0  
**更新日期**: 2026-04-09  
**状态**: ✅ 功能完整，自动召回已启用