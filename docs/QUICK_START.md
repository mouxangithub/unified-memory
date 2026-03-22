# 快速开始指南

## 🚀 5 分钟上手

### 1. 安装

```bash
# 安装技能
clawhub install unified-memory

# 或从 GitHub 安装
git clone https://github.com/mouxangithub/unified-memory
cd unified-memory
pip install -r requirements.txt
```

### 2. 初始化

```bash
# 初始化系统
mem init

# 检查健康状态
mem health
```

### 3. 基础使用

```bash
# 存储记忆
mem store "今天完成了用户登录功能，使用了 FastAPI 框架" --tags "技术,开发"

# 搜索记忆
mem search "登录功能"

# 查看统计
mem stats
```

---

## 📚 常用命令

| 命令 | 说明 |
|------|------|
| `mem init` | 初始化系统 |
| `mem store "内容"` | 存储记忆 |
| `mem search "关键词"` | 搜索记忆 |
| `mem health` | 健康检查 |
| `mem doctor` | 深度诊断 |
| `mem fix` | 自动修复 |
| `mem stats` | 统计信息 |
| `mem export` | 导出备份 |

---

## ❓ 常见问题

### Q: 向量搜索失败怎么办？

```bash
# 运行诊断
mem doctor

# 自动修复
mem fix
```

### Q: Ollama 连接失败？

```bash
# 检查 Ollama 是否启动
curl http://localhost:11434/api/tags

# 启动 Ollama
ollama serve
```

### Q: 如何备份数据？

```bash
# 导出备份
mem export --output backup.json

# 恢复（手动导入）
# 编辑 backup.json 后重新存储
```

---

## 🎯 实战示例

### 示例 1: 项目记忆管理

```bash
# 存储项目关键信息
mem store "项目使用 React 18 + TypeScript + Vite" --tags "项目,技术栈"
mem store "API 基地址: https://api.example.com" --tags "项目,配置"
mem store "数据库: PostgreSQL 15, 地址: localhost:5432" --tags "项目,数据库"

# 搜索项目配置
mem search "项目 配置"
```

### 示例 2: 学习笔记

```bash
# 存储学习笔记
mem store "React Hooks 最佳实践:
1. useEffect 依赖数组要完整
2. useCallback 用于函数缓存
3. useMemo 用于值缓存
" --tags "学习,React,Hooks"

# 搜索学习内容
mem search "React Hooks"
```

### 示例 3: Bug 记录

```bash
# 记录 Bug 和解决方案
mem store "Bug: 页面刷新后状态丢失
原因: useState 初始值没有从 localStorage 读取
解决: 使用 useEffect 初始化状态
" --tags "bug,React,状态管理"

# 搜索 Bug 解决方案
mem search "bug 状态丢失"
```

---

## 🔧 高级功能

### 智能分类

```bash
mem classify "今天完成了用户登录功能的开发"
# 输出: 分类: 技术 (60%), 标签: 登录, 功能, 开发
```

### 代码质量评估

```bash
mem quality ./my_code.py
# 输出: 质量分数、问题列表、改进建议
```

### Agent 调度

```bash
mem schedule
# 输出: 任务分配、负载情况
```

### Web UI

```bash
mem serve --port 38080
# 访问 http://localhost:38080
```

---

## 📊 监控和诊断

```bash
# 健康检查
mem health

# 深度诊断
mem doctor

# 查看统计
mem stats

# 查看学习记录
python3 scripts/learning/self_learner.py list
```

---

## 🐛 故障排查

### 问题 1: 命令找不到

```bash
# 确保 mem 命令在 PATH 中
export PATH="$HOME/.openclaw/skills/unified-memory/scripts:$PATH"

# 或使用完整路径
python3 ~/.openclaw/skills/unified-memory/scripts/mem health
```

### 问题 2: 向量库错误

```bash
# 检查向量表
mem doctor

# 修复向量表
mem fix

# 重新初始化
rm -rf ~/.openclaw/workspace/memory/vector
mem init
```

### 问题 3: 内存占用高

```bash
# 清理缓存
rm -rf ~/.openclaw/workspace/memory/cache/*

# 导出备份后重建
mem export
rm -rf ~/.openclaw/workspace/memory
mem init
# 手动导入备份
```

---

## 📖 更多文档

- [README.md](README.md) - 完整文档
- [README_CN.md](README_CN.md) - 中文文档
- [API 文档](docs/API_DOCS.md) - API 参考
- [架构设计](docs/ARCHITECTURE.md) - 系统架构

---

## 💬 获取帮助

- GitHub Issues: https://github.com/mouxangithub/unified-memory/issues
- ClawHub: https://clawhub.com/skill/unified-memory

---

**祝你使用愉快！** 🎉
