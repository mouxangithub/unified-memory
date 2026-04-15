#!/bin/bash

# Unified Memory ClawHub 发布验证脚本
# 验证技能包是否符合 ClawHub 发布标准

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查必需文件
check_required_files() {
    log_info "检查必需文件..."
    
    local files=(
        ".clawhub/config.json"
        "package.json"
        "README.md"
        "docs/README.md"
        "docs/README_CN.md"
        "install.sh"
        "LICENSE"
    )
    
    local missing=0
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺失文件: $file"
            missing=$((missing + 1))
        else
            log_success "文件存在: $file"
        fi
    done
    
    if [ $missing -eq 0 ]; then
        log_success "所有必需文件存在"
        return 0
    else
        log_error "缺失 $missing 个必需文件"
        return 1
    fi
}

# 验证配置
validate_config() {
    log_info "验证 ClawHub 配置..."
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，跳过 JSON 验证"
        return 0
    fi
    
    # 检查 config.json 格式
    if ! jq empty .clawhub/config.json 2>/dev/null; then
        log_error "config.json JSON 格式错误"
        return 1
    fi
    
    # 检查必需字段
    local required_fields=("name" "version" "description" "author" "license")
    for field in "${required_fields[@]}"; do
        if ! jq -e ".${field}" .clawhub/config.json >/dev/null 2>&1; then
            log_error "config.json 缺失必需字段: $field"
            return 1
        fi
    done
    
    # 检查版本格式
    local version=$(jq -r '.version' .clawhub/config.json)
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "版本格式错误: $version (应为 X.Y.Z)"
        return 1
    fi
    
    log_success "ClawHub 配置验证通过 (版本: $version)"
    return 0
}

# 验证 package.json
validate_package_json() {
    log_info "验证 package.json..."
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，跳过 package.json 验证"
        return 0
    fi
    
    # 检查 package.json 格式
    if ! jq empty package.json 2>/dev/null; then
        log_error "package.json JSON 格式错误"
        return 1
    fi
    
    # 检查版本匹配
    local clawhub_version=$(jq -r '.version' .clawhub/config.json)
    local package_version=$(jq -r '.version' package.json)
    
    if [ "$clawhub_version" != "$package_version" ]; then
        log_error "版本不匹配: ClawHub($clawhub_version) != package.json($package_version)"
        return 1
    fi
    
    log_success "package.json 验证通过 (版本: $package_version)"
    return 0
}

# 验证文档结构
validate_docs() {
    log_info "验证文档结构..."
    
    local required_docs=(
        "docs/en/getting-started/quickstart.md"
        "docs/zh/getting-started/quickstart.md"
        "docs/en/architecture/atomic-transactions.md"
    )
    
    local missing=0
    for doc in "${required_docs[@]}"; do
        if [ ! -f "$doc" ]; then
            log_error "缺失文档: $doc"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        log_success "核心文档结构完整"
        return 0
    else
        log_error "缺失 $missing 个核心文档"
        return 1
    fi
}

# 验证截图
validate_screenshots() {
    log_info "验证截图文件..."
    
    local screenshot_dir=".clawhub/screenshots"
    if [ ! -d "$screenshot_dir" ]; then
        log_warning "截图目录不存在: $screenshot_dir"
        return 0
    fi
    
    # 检查截图说明
    if [ ! -f "$screenshot_dir/README.md" ]; then
        log_warning "缺失截图说明文档"
    else
        log_success "截图说明文档存在"
    fi
    
    # 检查占位符文件
    local placeholders=("dashboard.png.placeholder" "search.png.placeholder" "analytics.png.placeholder")
    for placeholder in "${placeholders[@]}"; do
        if [ -f "$screenshot_dir/$placeholder" ]; then
            log_success "截图占位符存在: $placeholder"
        else
            log_warning "缺失截图占位符: $placeholder"
        fi
    done
    
    return 0
}

# 运行安装测试
test_installation() {
    log_info "测试安装脚本..."
    
    if [ ! -x "install.sh" ]; then
        log_error "install.sh 不可执行"
        return 1
    fi
    
    # 测试安装脚本语法
    if ! bash -n install.sh; then
        log_error "install.sh 语法错误"
        return 1
    fi
    
    log_success "安装脚本语法检查通过"
    return 0
}

# 运行构建测试
test_build() {
    log_info "测试构建过程..."
    
    # 检查 package.json scripts
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，跳过构建脚本检查"
        return 0
    fi
    
    local build_script=$(jq -r '.scripts.deploy' package.json 2>/dev/null)
    if [ -z "$build_script" ] || [ "$build_script" = "null" ]; then
        log_warning "package.json 中未找到 deploy 脚本"
    else
        log_success "构建脚本配置: $build_script"
    fi
    
    return 0
}

# 主验证函数
main() {
    log_info "开始 Unified Memory ClawHub 发布验证"
    log_info "时间: $(date)"
    log_info "版本: $(jq -r '.version' .clawhub/config.json 2>/dev/null || echo '未知')"
    echo ""
    
    local errors=0
    local warnings=0
    
    # 运行所有检查
    check_required_files || errors=$((errors + 1))
    echo ""
    
    validate_config || errors=$((errors + 1))
    echo ""
    
    validate_package_json || errors=$((errors + 1))
    echo ""
    
    validate_docs || errors=$((errors + 1))
    echo ""
    
    validate_screenshots || warnings=$((warnings + 1))
    echo ""
    
    test_installation || errors=$((errors + 1))
    echo ""
    
    test_build || warnings=$((warnings + 1))
    echo ""
    
    # 输出总结
    log_info "验证完成"
    log_info "错误: $errors 个"
    log_info "警告: $warnings 个"
    echo ""
    
    if [ $errors -eq 0 ]; then
        log_success "✅ ClawHub 发布验证通过！"
        log_success "技能包符合 ClawHub 发布标准"
        return 0
    else
        log_error "❌ ClawHub 发布验证失败"
        log_error "请修复以上错误后重试"
        return 1
    fi
}

# 运行主函数
main "$@"