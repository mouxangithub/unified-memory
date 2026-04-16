#!/bin/bash

# Unified Memory ClawHub 发布脚本
# 版本: 1.0.0
# 作者: OpenClaw Team

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查 git
    if ! command -v git &> /dev/null; then
        log_error "git 未安装"
        exit 1
    fi
    
    # 检查 node
    if ! command -v node &> /dev/null; then
        log_error "node 未安装"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    # 检查 openclaw
    if ! command -v openclaw &> /dev/null; then
        log_warning "openclaw 未安装，跳过技能验证"
    fi
    
    log_success "所有依赖检查通过"
}

# 清理项目
clean_project() {
    log_info "清理项目..."
    
    # 删除 node_modules
    if [ -d "node_modules" ]; then
        log_info "删除 node_modules..."
        rm -rf node_modules
    fi
    
    # 删除临时文件
    log_info "清理临时文件..."
    find . -name "*.log" -type f -delete
    find . -name "*.tmp" -type f -delete
    find . -name "*.temp" -type f -delete
    
    # 清理备份目录（如果存在）
    if [ -d "docs-backup-old" ]; then
        log_info "清理旧文档备份..."
        rm -rf docs-backup-old
    fi
    
    log_success "项目清理完成"
}

# 验证项目结构
validate_structure() {
    log_info "验证项目结构..."
    
    local required_files=(
        "README.md"
        "package.json"
        "SKILL.md"
        "CHANGELOG.md"
        "CONTRIBUTING.md"
        "INSTALL.md"
        "LICENSE"
        "install.sh"
        "config/clawhub.json"
        ".clawhub/config.json"
        ".gitignore"
        ".env.example"
    )
    
    local required_dirs=(
        "src"
        "docs"
        "scripts"
        "test"
        "plugins"
        "examples"
    )
    
    # 检查必需文件
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺少必需文件: $file"
            exit 1
        fi
    done
    
    # 检查必需目录
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_warning "缺少目录: $dir"
        fi
    done
    
    # 检查 package.json 版本
    local version=$(node -p "require('./package.json').version")
    if [ -z "$version" ]; then
        log_error "无法读取 package.json 版本"
        exit 1
    fi
    
    log_success "项目结构验证通过 (版本: $version)"
}

# 创建发布包
create_package() {
    log_info "创建发布包..."
    
    local version=$(node -p "require('./package.json').version")
    local package_name="unified-memory-v${version}-clawhub.zip"
    
    # 创建临时目录
    local temp_dir=$(mktemp -d)
    local package_dir="$temp_dir/unified-memory"
    
    # 复制文件（排除不需要的）
    log_info "复制文件到临时目录..."
    mkdir -p "$package_dir"
    
    # 使用 find 和 cp 复制，排除特定文件和目录
    find . -type f -not -path "./node_modules/*" \
        -not -path "./.git/*" \
        -not -path "./docs-backup-old/*" \
        -not -path "./archive/*" \
        -not -name "*.log" \
        -not -name "*.tmp" \
        -not -name "*.temp" \
        -not -name ".env" \
        -not -name ".DS_Store" \
        -not -name "Thumbs.db" | while read file; do
        # 创建目标目录
        target_dir="$package_dir/$(dirname "$file")"
        mkdir -p "$target_dir"
        # 复制文件
        cp "$file" "$package_dir/$file"
    done
    
    # 创建 ZIP 包
    log_info "创建 ZIP 包: $package_name"
    cd "$temp_dir"
    zip -r "$package_name" "unified-memory" > /dev/null
    
    # 移动回原目录
    cd - > /dev/null
    mv "$temp_dir/$package_name" .
    
    # 清理临时目录
    rm -rf "$temp_dir"
    
    # 检查文件大小
    local size=$(du -h "$package_name" | cut -f1)
    log_success "发布包创建完成: $package_name (大小: $size)"
}

# 验证 ClawHub 配置
validate_clawhub() {
    log_info "验证 ClawHub 配置..."
    
    # 检查 .clawhub/config.json
    if [ ! -f ".clawhub/config.json" ]; then
        log_error "缺少 .clawhub/config.json"
        exit 1
    fi
    
    # 验证 JSON 格式
    if ! node -e "const config = require('./.clawhub/config.json'); console.log('ClawHub 配置版本:', config.version);" 2>/dev/null; then
        log_error ".clawhub/config.json JSON 格式错误"
        exit 1
    fi
    
    # 检查 config/clawhub.json
    if [ ! -f "config/clawhub.json" ]; then
        log_error "缺少 config/clawhub.json"
        exit 1
    fi
    
    # 验证 JSON 格式
    if ! node -e "const config = require('./config/clawhub.json'); console.log('技能配置版本:', config.version);" 2>/dev/null; then
        log_error "config/clawhub.json JSON 格式错误"
        exit 1
    fi
    
    log_success "ClawHub 配置验证通过"
}

# 生成发布报告
generate_report() {
    log_info "生成发布报告..."
    
    local version=$(node -p "require('./package.json').version")
    local package_name="unified-memory-v${version}-clawhub.zip"
    local size=$(du -h "$package_name" 2>/dev/null | cut -f1 || echo "N/A")
    local date=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "CLAWHUB-RELEASE-REPORT.md" << EOF
# Unified Memory ClawHub 发布报告

## 发布信息
- **版本**: v${version}
- **发布日期**: ${date}
- **发布包**: ${package_name}
- **包大小**: ${size}

## 验证结果
- ✅ 依赖检查通过
- ✅ 项目结构验证通过
- ✅ ClawHub 配置验证通过
- ✅ 发布包创建成功

## 文件清单
\`\`\`
$(find . -type f -name "*.md" -o -name "*.json" -o -name "*.js" -o -name "*.sh" | grep -v node_modules | grep -v ".git" | sort)
\`\`\`

## 目录结构
\`\`\`
$(tree -I 'node_modules|.git|docs-backup-old|archive|*.log|*.tmp|*.temp' -L 3)
\`\`\`

## 下一步
1. 上传 \`${package_name}\` 到 ClawHub
2. 在 ClawHub 网站填写发布信息
3. 等待审核通过
4. 通知用户更新

## 注意事项
- 确保 \`.env\` 文件不被包含在发布包中
- 确保所有敏感信息已从配置中移除
- 确保文档链接正确
- 确保安装脚本可正常执行

---
**生成时间**: ${date}
**脚本版本**: 1.0.0
EOF
    
    log_success "发布报告生成完成: CLAWHUB-RELEASE-REPORT.md"
}

# 主函数
main() {
    log_info "开始 Unified Memory ClawHub 发布流程..."
    log_info "=========================================="
    
    # 检查当前目录
    if [ ! -f "package.json" ]; then
        log_error "请在 unified-memory 项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行步骤
    check_dependencies
    clean_project
    validate_structure
    validate_clawhub
    create_package
    generate_report
    
    log_info "=========================================="
    log_success "Unified Memory ClawHub 发布准备完成！"
    log_info ""
    log_info "下一步操作:"
    log_info "1. 查看发布报告: cat CLAWHUB-RELEASE-REPORT.md"
    log_info "2. 上传发布包到 ClawHub"
    log_info "3. 填写发布信息"
    log_info "4. 等待审核"
    log_info ""
    log_info "发布包: $(ls -la unified-memory-v*-clawhub.zip 2>/dev/null | head -1 | awk '{print $9}')"
}

# 运行主函数
main "$@"