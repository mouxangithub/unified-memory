#!/bin/bash
# release.sh - 发布自动化脚本
# Usage: ./release.sh [patch|minor|major]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Unified Memory 发布脚本${NC}"
echo ""

# 检查 git 状态
cd "$SKILL_DIR"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  有未提交的更改${NC}"
    git status --short
    echo ""
    read -p "是否先提交这些更改？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "提交信息: " commit_msg
        git commit -m "$commit_msg"
    else
        echo -e "${RED}❌ 请先提交更改${NC}"
        exit 1
    fi
fi

# 获取当前版本
CURRENT_VERSION=$(grep '"version"' "$SKILL_DIR/skill.json" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/')
echo -e "📌 当前版本: ${GREEN}$CURRENT_VERSION${NC}"

# 计算新版本
RELEASE_TYPE="${1:-patch}"
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case "$RELEASE_TYPE" in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        echo -e "${RED}❌ 无效的版本类型: $RELEASE_TYPE${NC}"
        echo "用法: $0 [patch|minor|major]"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo -e "🎯 新版本: ${GREEN}$NEW_VERSION${NC}"
echo ""

# 确认发布
read -p "确认发布 $NEW_VERSION？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 更新版本号
echo ""
echo -e "${YELLOW}📝 更新版本号...${NC}"

# skill.json
sed -i "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" "$SKILL_DIR/skill.json"

# README.md
sed -i "s/Version $CURRENT_VERSION/Version $NEW_VERSION/g" "$SKILL_DIR/README.md"
sed -i "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$SKILL_DIR/README.md"

# README_CN.md
sed -i "s/版本 $CURRENT_VERSION/版本 $NEW_VERSION/g" "$SKILL_DIR/README_CN.md"
sed -i "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$SKILL_DIR/README_CN.md"

# SKILL.md
sed -i "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$SKILL_DIR/SKILL.md"

# VERSION.md - 添加版本历史
if ! grep -q "$NEW_VERSION" "$SKILL_DIR/VERSION.md"; then
    # 在版本历史表的第一行数据后插入新版本
    sed -i "/^| \*\*[0-9]/a | **$NEW_VERSION** | $(date +%Y-%m-%d) | 本次更新 |" "$SKILL_DIR/VERSION.md"
fi

# WebUI 版本
sed -i "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$SKILL_DIR/scripts/memory_webui.py"

echo -e "${GREEN}✅ 版本号已更新${NC}"

# 检查版本一致性
echo ""
echo -e "${YELLOW}🔍 检查版本一致性...${NC}"
"$SCRIPT_DIR/check-versions.sh"

# 运行测试
echo ""
echo -e "${YELLOW}🧪 运行测试...${NC}"
if [ -f "$SCRIPT_DIR/test-all.sh" ]; then
    "$SCRIPT_DIR/test-all.sh" || echo -e "${YELLOW}⚠️  测试未通过，继续发布${NC}"
else
    echo "跳过测试（test-all.sh 不存在）"
fi

# Git 提交
echo ""
echo -e "${YELLOW}📦 Git 提交...${NC}"
git add -A
git commit -m "release: v$NEW_VERSION"
git tag "v$NEW_VERSION"

echo -e "${GREEN}✅ Git 提交完成${NC}"

# 推送
echo ""
read -p "推送到远程仓库？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    git push origin "v$NEW_VERSION"
    echo -e "${GREEN}✅ 已推送到远程${NC}"
fi

# 发布到 ClawHub
echo ""
read -p "发布到 ClawHub？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📤 发布到 ClawHub...${NC}"
    cd "$SKILL_DIR"
    clawhub publish . --version "$NEW_VERSION" || echo -e "${YELLOW}⚠️  ClawHub 发布失败，请手动发布${NC}"
fi

echo ""
echo -e "${GREEN}🎉 发布完成！${NC}"
echo -e "   版本: ${GREEN}v$NEW_VERSION${NC}"
echo -e "   ClawHub: https://clawhub.com/skill/unified-memory@$NEW_VERSION"
echo -e "   GitHub: https://github.com/mouxangithub/unified-memory/releases/tag/v$NEW_VERSION"
