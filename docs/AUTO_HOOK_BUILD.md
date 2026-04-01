# 自动构建 Hook 机制

## 概述

Unified Memory v4.0+ 支持在 `clawhub install` 或 `npm install` 时自动构建并启用 OpenClaw Hook，无需手动配置。

## 工作原理

### 1. 自动触发

当执行以下任一命令时，会自动触发 Hook 构建：

```bash
# 通过 Clawhub 安装
clawhub install unified-memory

# 或通过 npm 安装
npm install
```

### 2. 构建流程

`postinstall` 脚本会自动执行 `scripts/build-hook.js`：

```
1. 检查 Node.js 版本（需要 22+）
2. 检测 OpenClaw 安装路径
3. 启用已存在的 Hook（移除 .disabled 后缀）
   或创建新的 Hook 目录
4. 复制 HOOK.md 和 handler.js
5. 显示下一步操作提示
```

### 3. OpenClaw 路径检测

脚本会按以下顺序检测 OpenClaw 安装路径：

1. `OPENCLAW_HOME` 环境变量
2. `~/.openclaw`（默认路径）
3. `/root/.openclaw`
4. 相对路径 `../../..`

## 使用方式

### 方式 1：Clawhub 安装（推荐）

```bash
clawhub install unified-memory
openclaw gateway restart
```

### 方式 2：手动安装

```bash
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory
npm install
openclaw gateway restart
```

### 方式 3：仅构建 Hook

如果 Hook 构建失败或需要重新构建：

```bash
cd unified-memory
node scripts/build-hook.js
```

## 验证安装

### 1. 检查 Hook 状态

```bash
openclaw hooks list
```

应该看到：

```
unified-memory (enabled)
  Events: agent_loop:before_prompt_build, agent_loop:agent_end
```

### 2. 检查 Hook 目录

```bash
ls -la ~/.openclaw/hooks/unified-memory/
```

应该包含：

```
HOOK.md     - Hook 配置文件
handler.js  - Hook 执行脚本
```

## 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENCLAW_HOME` | OpenClaw 安装路径 | `~/.openclaw` |

### 手动启用/禁用 Hook

```bash
# 禁用 Hook
mv ~/.openclaw/hooks/unified-memory ~/.openclaw/hooks/unified-memory.disabled

# 启用 Hook
mv ~/.openclaw/hooks/unified-memory.disabled ~/.openclaw/hooks/unified-memory

# 重启 gateway 使生效
openclaw gateway restart
```

## 故障排查

### Hook 未自动构建

**可能原因**：
1. OpenClaw 未安装
2. 环境变量未设置
3. 权限不足

**解决方案**：

```bash
# 设置环境变量
export OPENCLAW_HOME=~/.openclaw

# 手动构建
node scripts/build-hook.js

# 或手动复制
mkdir -p ~/.openclaw/hooks/unified-memory
cp HOOK.md ~/.openclaw/hooks/unified-memory/
cp hooks/handler.js ~/.openclaw/hooks/unified-memory/
```

### Hook 未生效

**检查步骤**：

1. 确认 Hook 目录存在：

```bash
ls -la ~/.openclaw/hooks/unified-memory/
```

2. 确认 gateway 已重启：

```bash
openclaw gateway restart
```

3. 查看 gateway 日志：

```bash
openclaw gateway logs | grep unified-memory
```

### 权限问题

如果遇到权限错误：

```bash
chmod +x ~/.openclaw/hooks/unified-memory/handler.js
```

## 架构说明

### Hook 配置（HOOK.md）

```yaml
---
name: unified-memory
description: "Unified Memory v4.0 — 自动记忆抽取、注入与重排"
openclaw:
  emoji: "🧠"
  events:
    - "agent_loop:before_prompt_build"
    - "agent_loop:agent_end"
  hooks:
    allowPromptInjection: true
---
```

### Hook 执行脚本（handler.js）

导出两个异步函数：

```javascript
export async function before_prompt_build(context) {
  // 注入相关记忆到 prompt
  const memories = await context.tools.memory_search({...});
  return { prependContext: "..." };
}

export async function agent_end(context) {
  // 自动抽取关键信息
  await context.tools.memory_store({...});
  return {};
}
```

## 相关文档

- [Hook 集成详解](./en/HOOK_INTEGRATION.md)
- [MCP 集成指南](./en/MCP_INTEGRATION.md)
- [集成方式对比](./en/INTEGRATION_COMPARISON.md)

## 更新日志

### v4.0.4 (2026-04-01)
- ✨ 新增自动构建 Hook 机制
- ✨ 支持 postinstall 自动启用 Hook
- ✨ 新增 `scripts/build-hook.js` 构建脚本
- 📝 新增本文档

---

**作者**: 程序员小刘 (@mouxangithub)  
**更新时间**: 2026-04-01
