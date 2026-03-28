#!/bin/bash
# ============================================================
# unified-memory 零门槛安装脚本
# 支持：Linux / macOS / WSL
# 用法: curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 检测 Node.js
check_node() {
  if ! command -v node &>/dev/null; then
    error "Node.js 未安装。请先安装 Node.js 22+: https://nodejs.org/"
  fi
  V=$(node -v | cut -d. -f1 | tr -d v)
  if [ "$V" -lt 22 ]; then
    error "Node.js 版本过低。当前: $(node -v)，需要: v22+"
  fi
  info "Node.js $(node -v) ✓"
}

# 检测 Git
check_git() {
  command -v git &>/dev/null || error "Git 未安装。"
  info "Git $(git --version | cut -d' ' -f3) ✓"
}

# 克隆或更新
clone_or_pull() {
  TARGET="${HOME}/.openclaw/workspace/skills/unified-memory"
  if [ -d "$TARGET/.git" ]; then
    info "已有旧版本，跳过 git clone..."
    cd "$TARGET" && git pull origin main
  else
    info "克隆 unified-memory 到 ${TARGET}..."
    mkdir -p "$(dirname "$TARGET")"
    git clone https://github.com/mouxangithub/unified-memory.git "$TARGET"
  fi
}

# 安装依赖（只装 npm 包，不装 peer）
install_deps() {
  info "安装 npm 依赖..."
  cd "$TARGET"
  # 只安装 dependencies，不安装 peerDependencies（由 host 提供）
  npm install --ignore-scripts --no-peer-dependencies 2>&1 | tail -3
  info "依赖安装完成 ✓"
}

# 检测/安装 Ollama（可选）
check_ollama() {
  if command -v ollama &>/dev/null; then
    info "Ollama $(ollama --version | cut -d' ' -f2) ✓"
    if ! ollama list | grep -q nomic-embed-text; then
      warn "建议运行: ollama pull nomic-embed-text  安装嵌入模型"
    fi
  else
    warn "Ollama 未安装（可选，无 Ollama 时自动降级到 BM25 模式）"
    warn "安装: curl -fsSL https://ollama.com/install.sh | sh"
  fi
}

# 验证运行
verify() {
  info "验证 MCP Server..."
  cd "$TARGET"
  timeout 5 node src/index.js &>/dev/null &
  sleep 2
  if pgrep -f "node src/index.js" >/dev/null 2>&1; then
    info "MCP Server 启动成功 ✓"
    pkill -f "node src/index.js" 2>/dev/null || true
  else
    error "MCP Server 启动失败"
  fi
}

# 输出接入指南
show_next_steps() {
  echo ""
  echo "========================================="
  echo -e "${GREEN}✅ 安装完成！${NC}"
  echo "========================================="
  echo ""
  echo "下一步："
  echo ""
  echo "【OpenClaw 用户】"
  echo "  重启 OpenClaw 即可自动加载："
  echo "    openclaw gateway restart"
  echo ""
  echo "【其他 AI Agent（如 Cursor/Windsurf）】"
  echo "  在你的 MCP 配置文件中添加："
  echo ""
  echo "  Unix/macOS:"
  echo "    echo '{\"mcpServers\":{\"unified-memory\":{\"command\":\"node\",\"args\":[\"${TARGET}/src/index.js\"]}}}' \\"
  echo "      >> ~/.config/claude/mcp_servers.json"
  echo ""
  echo "  或查看完整文档："
  echo "    cat ${TARGET}/README.md"
  echo ""
  echo "【快速测试】"
  echo "  cd ${TARGET}"
  echo "  node src/cli/index.js search \"测试\""
  echo ""
}

# ============================================================
main() {
  echo "========================================="
  echo "  🧠 unified-memory 安装脚本"
  echo "========================================="
  echo ""
  check_node
  check_git
  clone_or_pull
  install_deps
  check_ollama
  verify
  show_next_steps
}

main "$@"
