# 记忆系统真实案例

本文档包含真实使用场景和案例。

---

## 案例 1：软件开发项目

### 场景

使用记忆系统管理一个软件开发项目的完整生命周期。

### 步骤

```bash
# 1. 初始化项目
cd ~/projects
mem template create software-project my-app --name "My App" --desc "一个 Web 应用"

# 2. 进入项目目录
cd my-app

# 3. 初始化上下文
mem ctx init "My App" --desc "一个 Web 应用"

# 4. 记录架构决策
mem ctx decision "选择技术栈" "前端使用 React，后端使用 Node.js，数据库使用 PostgreSQL"

# 5. 更新进度
mem ctx update "实现用户登录" --progress 20 --notes "使用 JWT 认证"

# 6. 存储重要决策
mem store "用户认证使用 JWT，有效期 7 天" --tags "架构,认证,JWT"

# 7. 搜索历史决策
mem search "认证"

# 8. 压缩历史日志
mem summary compress --days 7
```

### 结果

```
my-app/
├── .context/
│   ├── current.md         # 当前状态
│   ├── architecture.md    # 架构设计
│   └── decisions/
│       └── 20260323-*.md  # 决策记录
├── memory/
│   └── 2026-03-23.md      # 日志
├── docs/
│   └── README.md
└── src/
    ├── frontend/
    ├── backend/
    └── shared/
```

---

## 案例 2：问题排查

### 场景

使用记忆系统记录问题排查过程。

### 步骤

```bash
# 1. 记录问题
mem store "发现 CLI 导入失败: cannot import name 'AgentMemory'" --tags "bug,CLI"

# 2. 记录排查过程
mem store "检查 agent_memory.py，发现没有 AgentMemory 类" --tags "排查"

# 3. 记录解决方案
mem store "解决方案：添加降级逻辑，直接写文件" --tags "fix,降级"

# 4. 记录验证结果
mem store "验证：CLI 现在可以工作，使用文件模式" --tags "验证"

# 5. 查看所有相关问题
mem search "CLI"
```

### 结果

- 完整的问题排查记录
- 可搜索的历史
- 可追溯的解决方案

---

## 案例 3：知识管理

### 场景

使用记忆系统管理项目知识。

### 步骤

```bash
# 1. 记录技术决策
mem ctx decision "API 设计" "使用 RESTful API，遵循 OpenAPI 3.0 规范"

# 2. 记录最佳实践
mem store "日志记录最佳实践：使用结构化日志，包含时间戳和上下文" --tags "最佳实践,日志"

# 3. 记录经验教训
mem store "教训：降级逻辑至关重要，任何可能失败的地方都要有后备方案" --tags "经验,降级"

# 4. 定期压缩
mem summary compress --days 30

# 5. 提取关键决策
mem summary decisions --days 90
```

### 结果

- 知识可搜索
- 决策可追溯
- 经验可复用

---

## 案例 4：团队协作

### 场景

使用记忆系统支持团队协作。

### 步骤

```bash
# 1. 项目经理：初始化项目
mem ctx init "团队项目" --desc "多 Agent 协作系统"

# 2. 架构师：记录架构决策
mem ctx decision "微服务架构" "采用微服务架构，每个服务独立部署"

# 3. 开发者：更新进度
mem ctx update "实现服务 A" --progress 30 --notes "完成了核心接口"

# 4. 测试：记录问题
mem store "发现服务 A 接口返回 500 错误" --tags "bug,服务A"

# 5. 查看当前状态
mem ctx status

# 6. 导出上下文给新成员
mem ctx export
```

### 结果

- 团队成员快速了解项目状态
- 决策有记录
- 进度可追踪

---

## 案例 5：持续改进

### 场景

使用记忆系统支持持续改进。

### 步骤

```bash
# 1. 记录改进点
mem store "改进：CLI 应该更简单，第一次用就要成功" --tags "改进,CLI"

# 2. 记录实施
mem store "实施：重写 CLI，添加降级逻辑" --tags "实施,CLI"

# 3. 验证结果
mem store "验证：CLI 现在可以工作，成功率 100%" --tags "验证,CLI"

# 4. 定期总结
mem summary summary

# 5. 提取经验
mem summary decisions --days 90
```

### 结果

- 改进可追踪
- 效果可验证
- 经验可积累

---

## 最佳实践

### 1. 定期压缩

```bash
# 每周压缩一次
mem summary compress --days 7
```

### 2. 标签规范

```bash
# 使用一致的标签
mem store "内容" --tags "分类,子分类,优先级"
```

### 3. 决策记录

```bash
# 重要决策都要记录
mem ctx decision "标题" "内容" --tags "标签"
```

### 4. 状态更新

```bash
# 定期更新进度
mem ctx update "当前任务" --progress 50 --notes "备注"
```

### 5. 定期验证

```bash
# 定期验证工作流
mem validate
```

---

## 常见问题

### Q: 如何恢复项目上下文？

```bash
mem ctx status
```

### Q: 如何查找历史决策？

```bash
mem summary decisions --days 90
```

### Q: 如何压缩历史日志？

```bash
mem summary compress --days 7
```

### Q: 如何创建新项目？

```bash
mem template create software-project /path/to/project --name "项目名"
```

### Q: 如何验证系统健康？

```bash
mem health
```

---

*更新时间: 2026-03-23*
