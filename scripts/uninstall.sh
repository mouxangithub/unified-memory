#!/bin/bash
# Unified Memory - Uninstall Script
# Version: 0.0.7

set -e

echo "🗑️ Uninstalling Unified Memory 0.0.7..."

# ============================================================
# 1. Confirm Uninstall
# ============================================================
if [ "$1" != "--yes" ]; then
    echo "⚠️ This will remove:"
    echo "   - Vector database"
    echo "   - All memory data"
    echo "   - Configuration files"
    echo ""
    read -p "Continue? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "❌ Uninstall cancelled"
        exit 0
    fi
fi

# ============================================================
# 2. Backup Data
# ============================================================
MEMORY_DIR="$HOME/.openclaw/workspace/memory"
BACKUP_DIR="$HOME/.openclaw/workspace/memory/backups/uninstall_$(date +%Y%m%d_%H%M%S)"

if [ -d "$MEMORY_DIR/vector" ] || [ -f "$MEMORY_DIR/memories.json" ]; then
    echo "📦 Creating backup..."
    mkdir -p "$BACKUP_DIR"
    
    [ -d "$MEMORY_DIR/vector" ] && cp -r "$MEMORY_DIR/vector" "$BACKUP_DIR/"
    [ -f "$MEMORY_DIR/memories.json" ] && cp "$MEMORY_DIR/memories.json" "$BACKUP_DIR/"
    [ -d "$MEMORY_DIR/knowledge_blocks" ] && cp -r "$MEMORY_DIR/knowledge_blocks" "$BACKUP_DIR/"
    
    echo "  ✅ Backup saved to $BACKUP_DIR"
fi

# ============================================================
# 3. Remove Data
# ============================================================
echo "🗑️ Removing data..."

# Keep directory structure, only remove data
rm -rf "$MEMORY_DIR/vector" 2>/dev/null || true
rm -rf "$MEMORY_DIR/hierarchy" 2>/dev/null || true
rm -rf "$MEMORY_DIR/knowledge_blocks" 2>/dev/null || true
rm -rf "$MEMORY_DIR/predictions" 2>/dev/null || true
rm -rf "$MEMORY_DIR/validation" 2>/dev/null || true
rm -rf "$MEMORY_DIR/feedback" 2>/dev/null || true
rm -rf "$MEMORY_DIR/archive" 2>/dev/null || true
rm -rf "$MEMORY_DIR/sessions" 2>/dev/null || true
rm -f "$MEMORY_DIR/memories.json" 2>/dev/null || true
rm -f "$MEMORY_DIR/config.json" 2>/dev/null || true

echo "  ✅ Data removed"

# ============================================================
# 4. Optional: Remove Python Dependencies
# ============================================================
if [ "$1" == "--full" ]; then
    echo "📚 Removing Python dependencies..."
    pip uninstall -y lancedb 2>/dev/null || echo "  ⚠️ LanceDB not installed"
    echo "  ✅ Dependencies removed"
fi

# ============================================================
# 5. Summary
# ============================================================
echo ""
echo "========================================"
echo "✅ Unified Memory Uninstalled!"
echo "========================================"
echo ""
echo "📦 Backup location: $BACKUP_DIR"
echo ""
echo "To reinstall:"
echo "   clawhub install unified-memory"
echo "   # or"
echo "   ./scripts/install.sh"
echo ""
