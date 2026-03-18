#!/bin/bash
# test-all.sh - 运行所有测试

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧪 运行测试..."
echo ""

ERRORS=0

# 测试 1: Python 语法检查
echo "1️⃣  Python 语法检查..."
for py in "$SKILL_DIR"/scripts/*.py; do
    if python3 -m py_compile "$py" 2>/dev/null; then
        echo "   ✅ $(basename $py)"
    else
        echo "   ❌ $(basename $py)"
        ERRORS=$((ERRORS + 1))
    fi
done

# 测试 2: 导入检查
echo ""
echo "2️⃣  模块导入检查..."
cd "$SKILL_DIR/scripts"
if python3 -c "import memory; print('   ✅ memory.py')" 2>/dev/null; then
    :
else
    echo "   ❌ memory.py 导入失败"
    ERRORS=$((ERRORS + 1))
fi

# 测试 3: 命令测试
echo ""
echo "3️⃣  命令测试..."
if python3 memory.py --help > /dev/null 2>&1; then
    echo "   ✅ memory.py --help"
else
    echo "   ❌ memory.py --help"
    ERRORS=$((ERRORS + 1))
fi

if python3 memory.py stats > /dev/null 2>&1; then
    echo "   ✅ memory.py stats"
else
    echo "   ❌ memory.py stats"
    ERRORS=$((ERRORS + 1))
fi

# 测试 4: LanceDB 连接
echo ""
echo "4️⃣  LanceDB 连接测试..."
if python3 -c "
import lancedb
from pathlib import Path
db_path = Path.home() / '.openclaw' / 'workspace' / 'memory' / 'vector'
db = lancedb.connect(str(db_path))
print('   ✅ LanceDB 连接成功')
" 2>/dev/null; then
    :
else
    echo "   ⚠️  LanceDB 连接失败（可选依赖）"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ 所有测试通过"
    exit 0
else
    echo "❌ $ERRORS 个测试失败"
    exit 1
fi
