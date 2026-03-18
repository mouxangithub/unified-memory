#!/bin/bash
# check-versions.sh - 检查所有文档版本号一致性

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔍 检查版本号一致性..."
echo ""

# 从 skill.json 获取版本
MAIN_VERSION=$(grep '"version"' "$SKILL_DIR/skill.json" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/')
echo "📌 skill.json 版本: $MAIN_VERSION"

# 检查其他文件
ERRORS=0

# README.md
README_VER=$(grep -o "Version [0-9]\.[0-9]\.[0-9]" "$SKILL_DIR/README.md" | head -1 | awk '{print $2}')
if [ "$README_VER" != "$MAIN_VERSION" ]; then
  echo "❌ README.md 版本不匹配: $README_VER"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ README.md: $README_VER"
fi

# README_CN.md
README_CN_VER=$(grep -o "版本 [0-9]\.[0-9]\.[0-9]" "$SKILL_DIR/README_CN.md" | head -1 | awk '{print $2}')
if [ "$README_CN_VER" != "$MAIN_VERSION" ]; then
  echo "❌ README_CN.md 版本不匹配: $README_CN_VER"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ README_CN.md: $README_CN_VER"
fi

# SKILL.md
SKILL_VER=$(grep -o "v[0-9]\.[0-9]\.[0-9]" "$SKILL_DIR/SKILL.md" | head -1 | sed 's/v//')
if [ "$SKILL_VER" != "$MAIN_VERSION" ]; then
  echo "❌ SKILL.md 版本不匹配: $SKILL_VER"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ SKILL.md: $SKILL_VER"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ 所有版本号一致: $MAIN_VERSION"
  exit 0
else
  echo "❌ 发现 $ERRORS 个版本不一致"
  exit 1
fi
