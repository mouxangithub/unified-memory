#!/bin/bash

# Unified Memory 修复部署脚本
# 自动部署所有修复和优化

set -e

echo "🚀 开始部署 Unified Memory 修复"
echo "📅 $(date)"
echo ""

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
    
    if [ $NODE_MAJOR -lt 18 ]; then
        log_error "需要 Node.js 18 或更高版本，当前版本: $NODE_VERSION"
        exit 1
    fi
    
    log_success "Node.js 版本: $NODE_VERSION"
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    log_success "npm 可用"
    
    # 检查 ChromaDB (可选)
    if command -v docker &> /dev/null; then
        log_info "Docker 可用，可以部署 ChromaDB"
    else
        log_warning "Docker 未安装，ChromaDB 部署需要 Docker"
    fi
}

# 备份现有数据
backup_data() {
    log_info "备份现有数据..."
    
    BACKUP_DIR="/tmp/unified-memory-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份记忆文件
    if [ -f "memory/memories.json" ]; then
        cp "memory/memories.json" "$BACKUP_DIR/"
        log_success "备份记忆文件"
    fi
    
    # 备份配置
    if [ -f "config.json" ]; then
        cp "config.json" "$BACKUP_DIR/"
        log_success "备份配置文件"
    fi
    
    # 备份向量数据
    LANCEDB_DIR="$HOME/.unified-memory/vector.lance"
    if [ -d "$LANCEDB_DIR" ]; then
        cp -r "$LANCEDB_DIR" "$BACKUP_DIR/vector.lance.bak"
        log_success "备份向量数据"
    fi
    
    log_success "数据备份完成: $BACKUP_DIR"
}

# 安装新依赖
install_dependencies() {
    log_info "安装新依赖..."
    
    # 检查 package.json 是否有更新
    if [ -f "package.json" ]; then
        log_info "更新 npm 依赖..."
        npm install
        
        # 安装测试依赖
        log_info "安装测试依赖..."
        npm install --save-dev c8
        
        log_success "依赖安装完成"
    else
        log_warning "未找到 package.json，跳过依赖安装"
    fi
}

# 部署原子事务修复
deploy_atomic_fixes() {
    log_info "部署原子事务修复..."
    
    # 检查新文件是否存在
    if [ ! -f "src/transaction-manager.js" ]; then
        log_error "transaction-manager.js 未找到"
        exit 1
    fi
    
    if [ ! -f "src/vector-store-abstract.js" ]; then
        log_error "vector-store-abstract.js 未找到"
        exit 1
    fi
    
    if [ ! -f "src/vector-chromadb-backend.js" ]; then
        log_error "vector-chromadb-backend.js 未找到"
        exit 1
    fi
    
    log_success "原子事务修复文件就绪"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    # 运行单元测试
    log_info "运行单元测试..."
    if npm run test:unit 2>&1 | tee test-unit.log; then
        log_success "单元测试通过"
    else
        log_error "单元测试失败"
        cat test-unit.log
        exit 1
    fi
    
    # 运行集成测试
    log_info "运行集成测试..."
    if npm run test:integration 2>&1 | tee test-integration.log; then
        log_success "集成测试通过"
    else
        log_error "集成测试失败"
        cat test-integration.log
        exit 1
    fi
    
    # 运行性能测试
    log_info "运行性能基准测试..."
    if node test/benchmark/write-performance.js 2>&1 | tee test-benchmark.log; then
        log_success "性能基准测试完成"
    else
        log_warning "性能基准测试失败，但继续部署"
    fi
}

# 部署 ChromaDB (可选)
deploy_chromadb() {
    log_info "部署 ChromaDB 向量数据库..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker 未安装，跳过 ChromaDB 部署"
        return
    fi
    
    # 检查 ChromaDB 是否已经在运行
    if docker ps | grep -q chromadb; then
        log_info "ChromaDB 已经在运行"
        return
    fi
    
    # 创建数据目录
    CHROMADB_DATA="$HOME/.unified-memory/chromadb-data"
    mkdir -p "$CHROMADB_DATA"
    
    # 启动 ChromaDB
    log_info "启动 ChromaDB 容器..."
    docker run -d \
        --name chromadb \
        -p 8000:8000 \
        -v "$CHROMADB_DATA:/chroma/chroma" \
        ghcr.io/chroma-core/chroma:latest
    
    # 等待 ChromaDB 启动
    log_info "等待 ChromaDB 启动..."
    sleep 10
    
    # 测试连接
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        log_success "ChromaDB 部署成功"
    else
        log_error "ChromaDB 启动失败"
        exit 1
    fi
}

# 更新配置
update_config() {
    log_info "更新配置..."
    
    # 创建新的配置示例
    cat > config.example.json << 'EOF'
{
  "storage": {
    "mode": "json",
    "atomicTransactions": true,
    "recoveryLog": true
  },
  "vectorStore": {
    "backend": "chromadb",
    "chromadb": {
      "host": "localhost",
      "port": 8000,
      "collectionName": "unified_memory"
    },
    "lancedb": {
      "path": "~/.unified-memory/vector.lance"
    }
  },
  "performance": {
    "batchSize": 100,
    "concurrentWrites": 5,
    "enableFsync": true
  },
  "monitoring": {
    "enableMetrics": true,
    "enableAuditLog": true,
    "enableErrorTracking": true
  }
}
EOF
    
    log_success "配置示例已更新"
}

# 创建监控脚本
setup_monitoring() {
    log_info "设置监控..."
    
    # 创建监控目录
    mkdir -p monitoring
    
    # 创建健康检查脚本
    cat > monitoring/health-check.js << 'EOF'
/**
 * Unified Memory 健康检查脚本
 */

import { getTransactionManager } from '../src/transaction-manager.js';
import { getVectorStore } from '../src/vector-store-abstract.js';

async function healthCheck() {
  const results = {
    timestamp: new Date().toISOString(),
    checks: {},
    overall: 'healthy'
  };
  
  try {
    // 检查事务管理器
    const txManager = getTransactionManager();
    const txStatus = txManager.getAllTransactions();
    
    results.checks.transactionManager = {
      status: 'healthy',
      activeTransactions: txStatus.length,
      details: txStatus
    };
    
  } catch (error) {
    results.checks.transactionManager = {
      status: 'unhealthy',
      error: error.message
    };
    results.overall = 'unhealthy';
  }
  
  try {
    // 检查向量存储
    const vectorStore = getVectorStore();
    const vectorHealth = await vectorStore.healthCheck();
    
    results.checks.vectorStore = {
      status: vectorHealth.healthy ? 'healthy' : 'unhealthy',
      details: vectorHealth
    };
    
    if (!vectorHealth.healthy) {
      results.overall = 'unhealthy';
    }
    
  } catch (error) {
    results.checks.vectorStore = {
      status: 'unhealthy',
      error: error.message
    };
    results.overall = 'unhealthy';
  }
  
  // 检查记忆文件
  try {
    const fs = await import('fs');
    const memoriesExist = fs.existsSync('memory/memories.json');
    
    results.checks.memoryFile = {
      status: memoriesExist ? 'healthy' : 'warning',
      exists: memoriesExist
    };
    
    if (!memoriesExist) {
      results.overall = 'degraded';
    }
    
  } catch (error) {
    results.checks.memoryFile = {
      status: 'unhealthy',
      error: error.message
    };
    results.overall = 'unhealthy';
  }
  
  return results;
}

// 运行健康检查
if (import.meta.url === `file://${process.argv[1]}`) {
  healthCheck()
    .then(results => {
      console.log(JSON.stringify(results, null, 2));
      
      if (results.overall !== 'healthy') {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('健康检查失败:', error);
      process.exit(1);
    });
}

export default healthCheck;
EOF
    
    # 创建监控配置
    cat > monitoring/config.json << 'EOF'
{
  "healthCheck": {
    "interval": 300,
    "timeout": 30,
    "retries": 3
  },
  "metrics": {
    "enabled": true,
    "port": 9090,
    "path": "/metrics"
  },
  "alerts": {
    "enabled": true,
    "slackWebhook": "",
    "email": ""
  },
  "logging": {
    "level": "info",
    "file": "monitoring/unified-memory.log",
    "maxSize": "10MB",
    "maxFiles": 5
  }
}
EOF
    
    log_success "监控设置完成"
}

# 创建部署完成报告
create_deployment_report() {
    log_info "创建部署报告..."
    
    DEPLOYMENT_REPORT="deployment-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$DEPLOYMENT_REPORT" << EOF
# Unified Memory 修复部署报告

## 部署信息
- **部署时间**: $(date)
- **部署节点**: $(hostname)
- **Node.js 版本**: $(node -v)
- **npm 版本**: $(npm -v)

## 部署内容

### 1. 原子事务修复 ✅
- 事务管理器: \`src/transaction-manager.js\`
- 向量存储抽象层: \`src/vector-store-abstract.js\`
- ChromaDB 后端: \`src/vector-chromadb-backend.js\`

### 2. 测试框架 ✅
- 单元测试: \`test/unit/\`
- 集成测试: \`test/integration/\`
- 性能基准测试: \`test/benchmark/\`

### 3. 监控系统 ✅
- 健康检查脚本: \`monitoring/health-check.js\`
- 监控配置: \`monitoring/config.json\`

## 测试结果

### 单元测试
\`\`\`
$(tail -20 test-unit.log 2>/dev/null || echo "无日志")
\`\`\`

### 集成测试
\`\`\`
$(tail -20 test-integration.log 2>/dev/null || echo "无日志")
\`\`\`

## 性能基准

### 原子写入性能
- 平均写入时间: < 200ms (目标)
- P95 响应时间: < 500ms (目标)

### 并发写入性能
- 吞吐量: > 50 writes/sec (目标)

## 下一步行动

1. **验证部署**: 运行健康检查脚本
2. **监控系统**: 设置告警和仪表板
3. **性能调优**: 根据基准测试结果优化
4. **文档更新**: 更新用户和开发者文档

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据不一致 | 高 | 原子事务保证双写一致性 |
| 性能下降 | 中 | 分批写入，异步处理 |
| 迁移失败 | 高 | 备份数据，可回滚设计 |

---

**部署完成时间**: $(date)
**部署状态**: ✅ 成功

EOF
    
    log_success "部署报告已创建: $DEPLOYMENT_REPORT"
}

# 主部署流程
main() {
    log_info "开始 Unified Memory 修复部署"
    
    # 1. 检查依赖
    check_dependencies
    
    # 2. 备份数据
    backup_data
    
    # 3. 安装依赖
    install_dependencies
    
    # 4. 部署原子事务修复
    deploy_atomic_fixes
    
    # 5. 运行测试
    run_tests
    
    # 6. 部署 ChromaDB (可选)
    deploy_chromadb
    
    # 7. 更新配置
    update_config
    
    # 8. 设置监控
    setup_monitoring
    
    # 9. 创建部署报告
    create_deployment_report
    
    log_success "🎉 Unified Memory 修复部署完成！"
    log_info "请查看部署报告获取详细信息和下一步行动"
}

# 运行主函数
main "$@"

exit 0