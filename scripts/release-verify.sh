#!/bin/bash
# release-verify.sh - Unified Memory ClawHub 发布前验证脚本
# 用法: ./scripts/release-verify.sh

set -e

echo "=== Unified Memory 发布前验证 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED=1
}

check_warn() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

FAILED=0

# 1. 检查文件完整性
echo "[1/6] 检查文件完整性..."
required_files=(
    "SKILL.md"
    "README.md"
    "package.json"
    "config/skill.json"
    "CHANGELOG.md"
    "LICENSE"
    "INSTALL.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "找到文件: $file"
    else
        check_fail "缺少必需文件: $file"
    fi
done
echo ""

# 2. 验证 skill.json 格式
echo "[2/6] 验证 skill.json 格式..."
if [ -f "config/skill.json" ]; then
    if command -v jq &> /dev/null; then
        if jq empty config/skill.json 2>/dev/null; then
            check_pass "skill.json 格式正确"
        else
            check_fail "skill.json 格式错误"
        fi
    else
        check_warn "jq 未安装，跳过 JSON 格式验证"
    fi
else
    check_fail "config/skill.json 不存在"
fi
echo ""

# 3. 检查版本号一致性
echo "[3/6] 检查版本号一致性..."
if [ -f "package.json" ] && [ -f "config/skill.json" ]; then
    if command -v jq &> /dev/null; then
        VERSION=$(jq -r '.version' package.json)
        CONFIG_VERSION=$(jq -r '.version' config/skill.json)
        if [ "$VERSION" = "$CONFIG_VERSION" ]; then
            check_pass "版本号一致: $VERSION"
        else
            check_fail "版本号不一致: package.json=$VERSION, skill.json=$CONFIG_VERSION"
        fi
    else
        check_warn "jq 未安装，跳过版本号验证"
    fi
else
    check_fail "package.json 或 skill.json 不存在"
fi
echo ""

# 4. 检查必需字段
echo "[4/6] 检查 skill.json 必需字段..."
if [ -f "config/skill.json" ] && command -v jq &> /dev/null; then
    required_fields=(
        "name"
        "version"
        "description"
        "author"
        "license"
        "mcp"
        "features"
        "installation"
        "categories"
        "tags"
    )
    
    for field in "${required_fields[@]}"; do
        if jq -e ".$field" config/skill.json > /dev/null 2>&1; then
            check_pass "字段存在: $field"
        else
            check_fail "缺少字段: $field"
        fi
    done
else
    check_warn "跳过字段检查（jq 未安装或文件不存在）"
fi
echo ""

# 5. 检查文档链接
echo "[5/6] 检查文档内容..."
doc_files=(
    "README.md:使用说明"
    "SKILL.md:技术文档"
    "CHANGELOG.md:更新日志"
)

for item in "${doc_files[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        if [ "$size" -gt 100 ]; then
            check_pass "文档完整 ($desc): ${size}B"
        else
            check_fail "文档过小 ($desc): ${size}B"
        fi
    else
        check_fail "缺少文档: $file"
    fi
done
echo ""

# 6. 检查源代码
echo "[6/6] 检查源代码..."
if [ -d "src" ]; then
    src_files=$(find src -name "*.js" -o -name "*.ts" 2>/dev/null | wc -l)
    check_pass "源代码文件: $src_files 个"
else
    check_fail "src 目录不存在"
fi

if [ -f "src/index.js" ]; then
    check_pass "入口文件存在: src/index.js"
else
    check_fail "缺少入口文件: src/index.js"
fi
echo ""

# 总结
echo "=================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}=== ✅ 所有检查通过，ready to publish! ===${NC}"
    exit 0
else
    echo -e "${RED}=== ❌ 检查未通过，请修复上述问题 ===${NC}"
    exit 1
fi
