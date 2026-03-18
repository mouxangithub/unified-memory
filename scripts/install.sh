#!/bin/bash
# Unified Memory - Install Script
# Version: 0.0.7

set -e

echo "📦 Installing Unified Memory 0.0.7..."

# ============================================================
# 1. Install Required Skills
# ============================================================
echo "🔍 Checking required skills..."

SKILLS_DIR="$HOME/.openclaw/workspace/skills"
MEMORY_LANCEDB_PRO="$SKILLS_DIR/memory-lancedb-pro"

if [ ! -d "$MEMORY_LANCEDB_PRO" ]; then
    echo "⚠️ memory-lancedb-pro not found!"
    echo ""
    echo "Installing memory-lancedb-pro..."
    
    # Try clawhub first
    if command -v clawhub &> /dev/null; then
        echo "  Using clawhub to install..."
        clawhub install memory-lancedb-pro && echo "  ✅ Installed via clawhub"
    # Fallback to git clone
    elif command -v git &> /dev/null; then
        echo "  Using git clone..."
        git clone https://github.com/CortexReach/memory-lancedb-pro.git "$MEMORY_LANCEDB_PRO" && \
            echo "  ✅ Cloned from GitHub"
    else
        echo "❌ Neither clawhub nor git found!"
        echo "   Please install manually:"
        echo "   clawhub install memory-lancedb-pro"
        echo "   or"
        echo "   git clone https://github.com/CortexReach/memory-lancedb-pro.git"
        exit 1
    fi
else
    echo "  ✅ memory-lancedb-pro already installed"
fi

# ============================================================
# 2. Setup Virtual Environment
# ============================================================
echo "📚 Setting up Python environment..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

# Create venv if not exists
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" && echo "  ✅ Virtual environment created at $VENV_DIR"
fi

# Activate venv
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "  ⚠️ Virtual environment not found, using system Python"
fi

# Check Python packages
if python3 -c "import requests" 2>/dev/null; then
    echo "  ✅ requests available"
else
    # Try installing in venv
    if [ -f "$VENV_DIR/bin/pip" ]; then
        "$VENV_DIR/bin/pip" install -q requests && echo "  ✅ requests installed in venv"
    else
        echo "  ⚠️ requests not available (some features may be limited)"
    fi
fi

# Check LanceDB (should be provided by memory-lancedb-pro)
if python3 -c "import lancedb" 2>/dev/null; then
    echo "  ✅ LanceDB available"
else
    echo "  ⚠️ LanceDB not in Python path"
    echo "     LanceDB should be installed by memory-lancedb-pro"
    echo "     JSON fallback will be used for storage"
fi

# ============================================================
# 2. Initialize Directory Structure
# ============================================================
echo "📁 Initializing directory structure..."

MEMORY_DIR="$HOME/.openclaw/workspace/memory"
mkdir -p "$MEMORY_DIR"/{vector,hierarchy,knowledge_blocks,predictions,validation,feedback,archive,backups,sessions}

echo "  ✅ Directories created at $MEMORY_DIR"

# ============================================================
# 3. Check External Services
# ============================================================
echo "🔍 Checking external services..."

# Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  ✅ Ollama is running"
    OLLAMA_AVAILABLE=true
else
    echo "  ⚠️ Ollama not running (optional, LLM features disabled)"
    OLLAMA_AVAILABLE=false
fi

# ============================================================
# 4. Initialize Vector Database (if LanceDB available)
# ============================================================
if [ "$LANCEDB_AVAILABLE" = true ]; then
    echo "🗄️ Initializing LanceDB..."
    python3 -c "
import lancedb
db = lancedb.connect('$MEMORY_DIR/vector')
# Create memories table if not exists
try:
    table = db.open_table('memories')
except:
    table = db.create_table('memories', schema=[
        ('id', 'string'),
        ('text', 'string'),
        ('category', 'string'),
        ('importance', 'float'),
        ('created_at', 'string'),
        ('embedding', 'list<float>')
    ])
    print('  ✅ Vector table created')
"
else
    # Create fallback JSON storage
    echo "📝 Setting up JSON fallback storage..."
    if [ ! -f "$MEMORY_DIR/memories.json" ]; then
        echo '[]' > "$MEMORY_DIR/memories.json"
        echo "  ✅ JSON storage created"
    fi
fi

# ============================================================
# 5. Create Default Config
# ============================================================
echo "⚙️ Creating default configuration..."
cat > "$MEMORY_DIR/config.json" << 'EOF'
{
  "version": "0.0.7",
  "installed_at": "2026-03-18",
  "features": {
    "vector_search": false,
    "llm_extraction": false,
    "ontology": false
  },
  "parameters": {
    "L1_HOT_HOURS": 24,
    "L2_WARM_DAYS": 7,
    "L1_MAX_SIZE": 20,
    "L2_MAX_SIZE": 100,
    "SIMILARITY_THRESHOLD": 0.85,
    "STALE_DAYS": 30,
    "FORGET_IMPORTANCE": 0.1
  }
}
EOF
echo "  ✅ Config created"

# ============================================================
# 6. Verify Installation
# ============================================================
echo "🔬 Verifying installation..."
cd "$(dirname "$0")"
python3 scripts/memory.py status 2>/dev/null || echo "  ⚠️ Status check skipped"

echo ""
echo "========================================"
echo "✅ Unified Memory 0.0.7 Installed!"
echo "========================================"
echo ""
echo "📝 Next steps:"
echo "   1. Start Ollama for full features: ollama serve"
echo "   2. Run: python3 scripts/memory.py init"
echo "   3. Check status: python3 scripts/memory.py status"
echo ""
echo "📚 Documentation: cat ../README.md"
echo ""
