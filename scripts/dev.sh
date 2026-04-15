#!/bin/bash
# Unified Memory Development Script
# 开发环境启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[DEV]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[DEV]${NC} $1"
}

# 显示帮助
show_help() {
    echo "Unified Memory Development Script"
    echo ""
    echo "用法: ./scripts/dev.sh [命令]"
    echo ""
    echo "命令:"
    echo "  start         启动开发服务器"
    echo "  test          运行开发测试"
    echo "  lint          代码检查"
    echo "  format        代码格式化"
    echo "  watch         监听文件变化并自动重启"
    echo "  debug         启动调试模式"
    echo ""
    echo "选项:"
    echo "  --port <port> 指定端口 (默认: 3000)"
    echo "  --help        显示此帮助信息"
}

# 启动开发服务器
start_dev_server() {
    log_info "启动开发服务器..."
    
    PORT=${PORT:-3000}
    log_info "端口: $PORT"
    
    # 检查端口是否被占用
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 $PORT 已被占用"
        read -p "是否尝试其他端口? (y/n): " choice
        if [[ $choice == "y" ]]; then
            PORT=$((PORT + 1))
            log_info "尝试端口: $PORT"
        else
            exit 1
        fi
    fi
    
    # 设置环境变量并启动
    export NODE_ENV=development
    export PORT=$PORT
    
    log_info "启动命令: npm run dev"
    npm run dev
}

# 运行开发测试
run_dev_tests() {
    log_info "运行开发测试..."
    
    # 设置测试环境
    export NODE_ENV=test
    
    # 运行测试
    npm test -- --watch --coverage
    
    log_success "开发测试完成"
}

# 代码检查
run_lint() {
    log_info "运行代码检查..."
    
    # 检查是否有 ESLint
    if [ -f "node_modules/.bin/eslint" ]; then
        npx eslint src/ test/ --ext .js,.jsx,.ts,.tsx
    else
        log_warning "ESLint 未安装，跳过代码检查"
        log_info "安装 ESLint: npm install --save-dev eslint"
    fi
    
    log_success "代码检查完成"
}

# 代码格式化
run_format() {
    log_info "运行代码格式化..."
    
    # 检查是否有 Prettier
    if [ -f "node_modules/.bin/prettier" ]; then
        npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,md}"
        npx prettier --write "test/**/*.{js,jsx,ts,tsx,json,md}"
    else
        log_warning "Prettier 未安装，跳过代码格式化"
        log_info "安装 Prettier: npm install --save-dev prettier"
    fi
    
    log_success "代码格式化完成"
}

# 监听文件变化
watch_files() {
    log_info "启动文件监听..."
    
    # 检查是否有 nodemon
    if [ -f "node_modules/.bin/nodemon" ]; then
        npx nodemon --watch src --watch test --exec "npm test"
    else
        log_warning "nodemon 未安装，使用简单监听"
        log_info "安装 nodemon: npm install --save-dev nodemon"
        
        # 简单文件监听
        while true; do
            inotifywait -r -e modify src/ test/ 2>/dev/null || \
            fswatch -r src/ test/ 2>/dev/null || \
            sleep 5
            echo "文件变化检测到，重新运行测试..."
            npm test
        done
    fi
}

# 启动调试模式
start_debug() {
    log_info "启动调试模式..."
    
    PORT=${PORT:-9229}
    log_info "调试端口: $PORT"
    
    # 设置调试环境
    export NODE_ENV=development
    export DEBUG=unified-memory:*
    
    # 启动 Node.js 调试
    node --inspect=0.0.0.0:$PORT src/index.js
    
    log_info "调试服务器已启动"
    log_info "在 Chrome 中打开: chrome://inspect"
    log_info "点击 'Open dedicated DevTools for Node'"
}

# 主函数
main() {
    # 默认值
    COMMAND=""
    PORT="3000"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            start|test|lint|format|watch|debug)
                COMMAND="$1"
                shift
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_warning "未知参数: $1"
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
        "start")
            start_dev_server
            ;;
        "test")
            run_dev_tests
            ;;
        "lint")
            run_lint
            ;;
        "format")
            run_format
            ;;
        "watch")
            watch_files
            ;;
        "debug")
            start_debug
            ;;
    esac
}

# 运行主函数
main "$@"