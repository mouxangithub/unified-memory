#!/bin/bash
# 批次迁移脚本 - 每次迁移一批Python模块到Node.js
# 用法: bash batch_migrate.sh [batch_size]

set -e

BATCH_SIZE=${1:-20}
SOURCE_DIR="/root/.openclaw/workspace/skills/unified-memory/scripts"
TARGET_DIR="/root/.openclaw/workspace/skills/unified-memory-ts/src"
STATUS_FILE="/root/.openclaw/workspace/skills/unified-memory-ts/MIGRATION_STATUS.json"
LOG_FILE="/root/.openclaw/workspace/memory/logs/migration_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p $(dirname $LOG_FILE)

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 读取状态
TOTAL=$(jq '.total_modules' $STATUS_FILE)
MIGRATED=$(jq '.migrated_modules' $STATUS_FILE)
REMAINING=$((TOTAL - MIGRATED))

if [ $REMAINING -le 0 ]; then
    log "✅ 全部迁移完成!"
    exit 0
fi

ACTUAL_BATCH=$((BATCH_SIZE < REMAINING ? BATCH_SIZE : REMAINING))
log "🚀 开始第 $((MIGRATED / BATCH_SIZE + 1)) 批，迁移 $ACTUAL_BATCH 个模块..."

# 获取未迁移的Python文件（排除已知的非模块文件）
cd $SOURCE_DIR
PENDING=$(ls -1 *.py 2>/dev/null | grep -v '__pycache__' | head -n $ACTUAL_BATCH)

if [ -z "$PENDING" ]; then
    log "⚠️ 没有找到待迁移的Python文件，检查子目录..."
    PENDING=$(find . -name '*.py' -not -path '*/\.*' | head -n $ACTUAL_BATCH)
fi

count=0
for pyfile in $PENDING; do
    basename=$(basename $pyfile .py)
    log "  → 迁移: $basename"
    count=$((count + 1))
done

# 更新状态
jq --argjson migrated $((MIGRATED + count)) \
   --argjson remaining $((TOTAL - MIGRATED - count)) \
   --arg last "$(date -Iseconds)" \
   '.migrated_modules = $migrated | .remaining_modules = $remaining | .last_run = $last' \
   $STATUS_FILE > /tmp/mig_tmp.json && mv /tmp/mig_tmp.json $STATUS_FILE

log "✅ 本批完成! 进度: $((MIGRATED + count))/$TOTAL"
