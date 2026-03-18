#!/bin/bash
# Memory v7.0 定期维护脚本
# 建议：每周运行一次

echo "🧠 Memory v7.0 定期维护"
echo "========================"

cd ~/.openclaw/workspace/skills/unified-memory/scripts

# 1. 验证记忆
echo ""
echo "1️⃣ 验证记忆..."
python3 memory.py validate

# 2. 应用反馈调整
echo ""
echo "2️⃣ 应用反馈调整..."
python3 memory.py feedback

# 3. 智能遗忘（预览）
echo ""
echo "3️⃣ 智能遗忘预览..."
python3 memory.py forget --dry-run

# 4. 重建分层
echo ""
echo "4️⃣ 重建分层缓存..."
python3 memory.py rebuild

# 5. 显示状态
echo ""
echo "5️⃣ 系统状态..."
python3 memory.py status

echo ""
echo "✅ 维护完成"
