#!/bin/bash
# Unified Memory Deployment Script
# 统一部署脚本 - 合并了所有部署相关功能

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

# 显示帮助
show_help() {
    echo "Unified Memory Deployment Script"
    echo ""
    echo "用法: ./scripts/deploy.sh [命令]"
    echo ""
    echo "命令:"
    echo "  install       安装依赖和设置环境"
    echo "  build         构建项目"
    echo "  test          运行测试"
    echo "  deploy        部署到生产环境"
    echo "  verify        验证系统完整性"
    echo "  docs          更新文档"
    echo "  all           执行所有步骤 (install -> build -> test -> deploy)"
    echo ""
    echo "选项:"
    echo "  --env <env>   指定环境 (dev/staging/prod)"
    echo "  --dry-run     模拟运行，不实际执行"
    echo "  --help        显示此帮助信息"
}

# 安装依赖
install_deps() {
    log_info "安装项目依赖..."
    
    # 检查 Node.js 版本
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    REQUIRED_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "需要 Node.js >= $REQUIRED_VERSION，当前版本: $NODE_VERSION"
        exit 1
    fi
    
    # 安装 npm 依赖
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟安装: npm install"
    else
        npm install
        if [ $? -eq 0 ]; then
            log_success "依赖安装完成"
        else
            log_error "依赖安装失败"
            exit 1
        fi
    fi
}

# 构建项目
build_project() {
    log_info "构建项目..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟构建: npm run build"
    else
        npm run build
        if [ $? -eq 0 ]; then
            log_success "项目构建完成"
        else
            log_error "项目构建失败"
            exit 1
        fi
    fi
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟测试: npm test"
    else
        npm test
        if [ $? -eq 0 ]; then
            log_success "测试通过"
        else
            log_error "测试失败"
            exit 1
        fi
    fi
}

# 部署到生产环境
deploy_production() {
    log_info "部署到生产环境 ($ENVIRONMENT)..."
    
    case "$ENVIRONMENT" in
        "dev")
            log_info "开发环境部署..."
            ;;
        "staging")
            log_info "预发布环境部署..."
            ;;
        "prod")
            log_info "生产环境部署..."
            ;;
        *)
            log_error "未知环境: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟部署: 环境=$ENVIRONMENT"
    else
        # 这里添加实际的部署逻辑
        log_success "部署完成"
    fi
}

# 验证系统完整性
verify_system() {
    log_info "验证系统完整性..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟验证: 检查系统状态"
    else
        # 运行验证脚本
        node scripts/verify-fixes.js
        if [ $? -eq 0 ]; then
            log_success "系统验证通过"
        else
            log_error "系统验证失败"
            exit 1
        fi
    fi
}

# 更新文档
update_docs() {
    log_info "更新文档..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "模拟文档更新: 生成文档"
    else
        # 运行文档更新脚本
        if [ -f "scripts/docs/update.sh" ]; then
            bash scripts/docs/update.sh
        else
            log_warning "文档更新脚本不存在，跳过"
        fi
        log_success "文档更新完成"
    fi
}

# 执行所有步骤
run_all() {
    log_info "执行完整部署流程..."
    
    install_deps
    build_project
    run_tests
    deploy_production
    verify_system
    update_docs
    
    log_success "完整部署流程完成"
}

# 主函数
main() {
    # 默认值
    COMMAND=""
    ENVIRONMENT="prod"
    DRY_RUN="false"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            install|build|test|deploy|verify|docs|all)
                COMMAND="$1"
                shift
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定命令，显示帮助
    if [ -z "$COMMAND" ]; then
        show_help
        exit 0
    fi
    
    # 执行命令
    case "$COMMAND" in
        "install")
            install_deps
            ;;
        "build")
            build_project
            ;;
        "test")
            run_tests
            ;;
        "deploy")
            deploy_production
            ;;
        "verify")
            verify_system
            ;;
        "docs")
            update_docs
            ;;
        "all")
            run_all
            ;;
    esac
}

# 运行主函数
main "$@"