# Release Checklist - unified-memory

每次发布前必须完成以下检查：

## ✅ 版本号同步

```bash
# 检查所有文件版本号
./scripts/check-versions.sh
```

- [ ] `skill.json` - version 字段
- [ ] `SKILL.md` - 标题和正文版本号
- [ ] `README.md` - 头部版本标识
- [ ] `README_CN.md` - 头部版本标识
- [ ] `VERSION.md` - 版本历史表

## ✅ 文档更新

- [ ] 新功能已添加到 SKILL.md
- [ ] 新功能已添加到 README.md (英文)
- [ ] 新功能已添加到 README_CN.md (中文)
- [ ] 快速开始示例已更新
- [ ] 版本历史已更新
- [ ] 变更日志已更新

## ✅ 代码检查

- [ ] 所有测试通过
- [ ] 代码格式检查通过
- [ ] 依赖声明完整
- [ ] 权限声明准确

## ✅ 发布前测试

```bash
# 安装测试
./scripts/install.sh --test

# 功能测试
./scripts/test-all.sh

# 版本检查
./scripts/check-versions.sh
```

## ✅ 发布命令

```bash
# 1. 提交代码
git add -A
git commit -m "release: vX.X.X"
git push

# 2. 打标签
git tag vX.X.X
git push origin vX.X.X

# 3. 发布到 ClawHub
clawhub publish . --version X.X.X

# 4. 验证发布
curl https://clawhub.com/skill/unified-memory@X.X.X
```

## ✅ 发布后验证

- [ ] ClawHub 页面显示正确版本
- [ ] 安装命令可用
- [ ] 功能正常运行

---

## 自动化脚本

创建 `scripts/release.sh` 自动执行以上检查。
