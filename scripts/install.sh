#!/bin/bash
# Unified Memory v2.0 - Install Script (Node.js version)
# Project: /root/.openclaw/workspace/skills/unified-memory-ts/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="${HOME}/.openclaw/workspace/memory"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "========================================"
echo "🧠 Unified Memory v2.0 - Installer"
echo "========================================"
echo ""

# ============================================================
# 1. Check Node.js version
# ============================================================
log_info "Checking Node.js version..."

NODE_VERSION=$(node --version 2>/dev/null | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)

if [ -z "$NODE_VERSION" ]; then
    log_error "Node.js not found! Please install Node.js >= 18.0.0"
    exit 1
fi

if [ "$NODE_MAJOR" -lt 18 ]; then
    log_error "Node.js $NODE_VERSION found, but >= 18.0.0 is required"
    exit 1
fi

log_info "Node.js v${NODE_VERSION} ✓"

# ============================================================
# 2. Install npm dependencies
# ============================================================
log_info "Installing npm dependencies..."

cd "$SKILL_DIR"

if [ -f "package.json" ]; then
    if npm install --silent 2>/dev/null; then
        log_info "npm dependencies installed ✓"
    else
        log_warn "npm install had warnings, continuing anyway..."
    fi
else
    log_warn "No package.json found, skipping npm install"
fi

# ============================================================
# 3. Initialize memory directory
# ============================================================
log_info "Initializing memory directory..."

mkdir -p "$MEMORY_DIR"/{memories,backups,sessions,temp}
log_info "Memory directory: $MEMORY_DIR ✓"

# Create default config if not exists
if [ ! -f "$MEMORY_DIR/config.json" ]; then
    cat > "$MEMORY_DIR/config.json" << 'EOF'
{
  "version": "2.0.0",
  "installed_at": "2026-03-27",
  "storage": "auto",
  "features": {
    "bm25": true,
    "vector_search": true,
    "auto_store": true
  }
}
EOF
    log_info "Default config created ✓"
fi

# Create empty memories index if not exists
if [ ! -f "$MEMORY_DIR/memories.json" ]; then
    echo '[]' > "$MEMORY_DIR/memories.json"
    log_info "Memories index created ✓"
fi

# ============================================================
# 4. Check optional dependencies
# ============================================================
log_info "Checking optional dependencies..."

# Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_info "Ollama is running ✓"
    OLLAMA_AVAILABLE=true
else
    log_warn "Ollama not running (optional, vector search will use fallback)"
    OLLAMA_AVAILABLE=false
fi

# ============================================================
# 5. Configure mcporter (MCP server)
# ============================================================
log_info "Configuring MCP server (mcporter)..."

if command -v mcporter &> /dev/null; then
    log_info "mcporter found ✓"
    # Note: mcporter configuration is handled by OpenClaw plugin system
else
    log_warn "mcporter not in PATH, MCP tools configured via skill.json"
fi

# ============================================================
# 6. Run health check
# ============================================================
log_info "Running health check..."

cd "$SKILL_DIR"

HEALTH_OUTPUT=$(node src/cli/index.js health 2>&1 || true)
if echo "$HEALTH_OUTPUT" | grep -qi "error\|fail\|unhealthy"; then
    log_warn "Health check had warnings (this may be normal on first run)"
    echo "$HEALTH_OUTPUT" | head -5 | sed 's/^/   /'
else
    log_info "Health check passed ✓"
fi

# ============================================================
# 7. Summary
# ============================================================
echo ""
echo "========================================"
echo "✅ Unified Memory v2.0 Installed!"
echo "========================================"
echo ""
echo "📁 Memory dir: $MEMORY_DIR"
echo "📦 Node.js:    v$NODE_VERSION"
echo "🔧 Ollama:     $([ "$OLLAMA_AVAILABLE" = true ] && echo "running ✓" || echo "not running (optional)")"
echo ""
echo "🚀 Quick start:"
echo "   node src/cli/index.js health           # Health check"
echo "   node src/cli/index.js store 'Hello'    # Store first memory"
echo "   node src/cli/index.js search 'Hello'   # Search memories"
echo ""
echo "📚 Full docs:"
echo "   cat README.md              # English docs"
echo "   cat README_CN.md           # 中文文档"
echo "   cat README_QUICK_START.md   # Quick start guide"
echo ""
