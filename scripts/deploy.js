#!/usr/bin/env node

/**
 * 记忆系统优化项目部署脚本
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

class DeploymentManager {
  constructor() {
    this.projectRoot = path.join(__dirname, '..');
    this.logDir = path.join(this.projectRoot, 'logs');
    this.configPath = path.join(this.projectRoot, 'config.json');
  }

  /**
   * 初始化项目
   */
  async initProject() {
    console.log('🚀 初始化记忆系统优化项目...');
    
    try {
      // 1. 创建目录结构
      const dirs = [
        'sync',
        'dedup', 
        'monitor',
        'api',
        'scripts',
        'logs',
        'logs/reports',
        'tests'
      ];
      
      for (const dir of dirs) {
        const dirPath = path.join(this.projectRoot, dir);
        await fs.mkdir(dirPath, { recursive: true });
        console.log(`  📁 创建目录: ${dir}`);
      }
      
      // 2. 创建默认配置
      const defaultConfig = {
        workspacePath: '/root/.openclaw/workspace/memory',
        unifiedMemoryPath: '/root/.openclaw/skills/unified-memory',
        sync: {
          enabled: true,
          schedule: '0 2 * * *', // 每天凌晨2点
          batchSize: 50,
          dryRun: false
        },
        dedup: {
          similarityThreshold: 0.85,
          exactMatchThreshold: 0.95,
          cacheSize: 1000
        },
        monitor: {
          healthCheckInterval: 3600, // 每小时检查一次
          alertThreshold: 3 // 连续3次检查失败才报警
        },
        api: {
          port: 3851,
          cacheSize: 100,
          enableStats: true
        }
      };
      
      await fs.writeFile(
        this.configPath,
        JSON.stringify(defaultConfig, null, 2),
        'utf8'
      );
      console.log('  📄 创建配置文件: config.json');
      
      // 3. 创建package.json
      const packageJson = {
        name: "memory-system-optimization",
        version: "1.0.0",
        description: "记忆系统优化项目 - Workspace Memory与Unified Memory的集成优化",
        type: "module",
        main: "index.js",
        scripts: {
          "sync": "node sync/sync_cron.js",
          "sync:dry-run": "node sync/sync_cron.js --dry-run",
          "sync:manual": "node sync/sync_bridge.js",
          "query": "node api/unified_query_api.js",
          "dedup": "node dedup/cross_system_dedup.js",
          "monitor": "node monitor/health_check.js",
          "monitor:dashboard": "node monitor/health_check.js --dashboard",
          "deploy": "node scripts/deploy.js",
          "test": "node scripts/test.js",
          "crontab": "node sync/sync_cron.js --crontab"
        },
        dependencies: {},
        devDependencies: {},
        keywords: ["memory", "optimization", "unified-memory", "workspace"],
        author: "OpenClaw Assistant",
        license: "MIT"
      };
      
      await fs.writeFile(
        path.join(this.projectRoot, 'package.json'),
        JSON.stringify(packageJson, null, 2),
        'utf8'
      );
      console.log('  📄 创建package.json');
      
      // 4. 创建主索引文件
      const indexContent = `#!/usr/bin/env node

/**
 * 记忆系统优化项目 - 主入口
 */

import SyncBridge from './sync/sync_bridge.js';
import UnifiedQueryAPI from './api/unified_query_api.js';
import CrossSystemDeduplicator from './dedup/cross_system_dedup.js';
import MemoryHealthMonitor from './monitor/health_check.js';

export {
  SyncBridge,
  UnifiedQueryAPI,
  CrossSystemDeduplicator,
  MemoryHealthMonitor
};

// CLI支持
if (import.meta.url === \`file://\${process.argv[1]}\`) {
  console.log('🧠 记忆系统优化项目');
  console.log('='.repeat(40));
  console.log('可用模块:');
  console.log('  • SyncBridge - 同步桥梁');
  console.log('  • UnifiedQueryAPI - 统一检索API');
  console.log('  • CrossSystemDeduplicator - 跨系统去重');
  console.log('  • MemoryHealthMonitor - 健康监控');
  console.log('');
  console.log('使用方法:');
  console.log('  npm run sync     - 执行同步');
  console.log('  npm run query    - 执行查询');
  console.log('  npm run dedup    - 执行去重检查');
  console.log('  npm run monitor  - 健康检查');
  console.log('  npm run crontab  - 生成crontab配置');
}
`;
      
      await fs.writeFile(
        path.join(this.projectRoot, 'index.js'),
        indexContent,
        'utf8'
      );
      console.log('  📄 创建主索引文件: index.js');
      
      // 5. 创建README
      const readmeContent = `# 记忆系统优化项目

## 项目概述

优化OpenClaw的记忆系统架构，实现Workspace Memory与Unified Memory的协同工作。

## 架构目标

1. **短期**: 建立同步机制，优化检索流程，添加去重逻辑
2. **中期**: 统一存储层，智能压缩，实时索引  
3. **长期**: 完全集成，智能归档，跨会话记忆

## 项目结构

\`\`\`
memory-optimization/
├── sync/                    # 同步模块
│   ├── sync_bridge.js      # 同步桥梁
│   └── sync_cron.js        # 同步调度
├── dedup/                  # 去重模块
│   └── cross_system_dedup.js # 跨系统去重
├── api/                    # API模块
│   └── unified_query_api.js # 统一检索API
├── monitor/                # 监控模块
│   └── health_check.js     # 健康检查
├── scripts/                # 脚本
│   ├── deploy.js          # 部署脚本
│   └── test.js            # 测试脚本
├── logs/                   # 日志目录
├── tests/                  # 测试目录
├── config.json            # 配置文件
├── package.json           # 项目配置
└── index.js              # 主入口
\`\`\`

## 快速开始

### 1. 初始化项目
\`\`\`bash
cd /root/.openclaw/workspace/memory-optimization
node scripts/deploy.js --init
\`\`\`

### 2. 执行首次同步
\`\`\`bash
npm run sync:manual
\`\`\`

### 3. 测试查询
\`\`\`bash
npm run query -- "搜索关键词"
\`\`\`

### 4. 设置定时任务
\`\`\`bash
npm run crontab
# 将输出添加到crontab
\`\`\`

## 模块说明

### SyncBridge (同步桥梁)
- 单向同步: Workspace Memory → Unified Memory
- 智能解析Markdown文件
- 去重检查避免重复存储
- 支持批量处理和重试

### UnifiedQueryAPI (统一检索API)
- 优先搜索Unified Memory (向量+BM25)
- 文件系统作为后备检索
- 结果合并和去重
- 缓存优化

### CrossSystemDeduplicator (跨系统去重)
- 扩展Unified Memory的去重功能
- 支持跨系统去重检查
- 语义相似度计算
- 批量处理支持

### MemoryHealthMonitor (健康监控)
- 检查Workspace Memory状态
- 检查Unified Memory状态  
- 监控同步延迟
- 性能基准测试
- 生成健康报告

## 配置说明

编辑 \`config.json\` 文件:

\`\`\`json
{
  "workspacePath": "/root/.openclaw/workspace/memory",
  "unifiedMemoryPath": "/root/.openclaw/skills/unified-memory",
  "sync": {
    "enabled": true,
    "schedule": "0 2 * * *",
    "batchSize": 50
  }
}
\`\`\`

## 监控指标

- **同步延迟**: 文件系统与Unified Memory的同步时间差
- **检索命中率**: Unified Memory的查询命中率
- **去重率**: 重复记忆的检测率
- **响应时间**: 查询平均响应时间
- **存储使用**: 记忆系统的存储空间使用情况

## 故障排除

### 同步失败
1. 检查Workspace Memory目录权限
2. 检查Unified Memory服务状态
3. 查看同步日志: \`logs/sync_*.jsonl\`

### 查询性能慢
1. 检查Unified Memory的向量索引
2. 优化查询缓存设置
3. 减少文件系统扫描范围

### 去重效果不佳
1. 调整相似度阈值
2. 检查记忆类型分类
3. 验证指纹生成算法

## 后续开发计划

1. **双向同步**: 支持Unified Memory → Workspace Memory的回写
2. **智能压缩**: 自动归档旧记忆到文件系统
3. **实时索引**: 对话时实时索引到Unified Memory
4. **记忆网格**: 跨会话记忆共享和关联

## 许可证

MIT License
`;
      
      await fs.writeFile(
        path.join(this.projectRoot, 'README.md'),
        readmeContent,
        'utf8'
      );
      console.log('  📄 创建README.md');
      
      console.log('\n✅ 项目初始化完成！');
      console.log('\n📋 下一步:');
      console.log('  1. 检查配置: cat config.json');
      console.log('  2. 测试同步: npm run sync:manual');
      console.log('  3. 设置定时任务: npm run crontab');
      
      return { success: true, message: '项目初始化成功' };
      
    } catch (error) {
      console.error('❌ 初始化失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 验证环境
   */
  async validateEnvironment() {
    console.log('🔍 验证环境配置...');
    
    const checks = [];
    
    // 检查Workspace Memory
    try {
      await fs.access('/root/.openclaw/workspace/memory');
      checks.push({ component: 'Workspace Memory', status: '✅', message: '目录存在' });
    } catch {
      checks.push({ component: 'Workspace Memory', status: '❌', message: '目录不存在' });
    }
    
    // 检查Unified Memory
    try {
      await fs.access('/root/.openclaw/skills/unified-memory');
      checks.push({ component: 'Unified Memory', status: '✅', message: '目录存在' });
    } catch {
      checks.push({ component: 'Unified Memory', status: '❌', message: '目录不存在' });
    }
    
    // 检查Node.js版本
    try {
      const { stdout } = await execAsync('node --version');
      checks.push({ component: 'Node.js', status: '✅', message: `版本: ${stdout.trim()}` });
    } catch {
      checks.push({ component: 'Node.js', status: '❌', message: '未安装或不可用' });
    }
    
    // 检查依赖
    try {
      const { stdout } = await execAsync('cd /root/.openclaw/skills/unified-memory && npm list --depth=0 2>/dev/null | head -5');
      checks.push({ component: 'Unified Memory依赖', status: '✅', message: '依赖已安装' });
    } catch {
      checks.push({ component: 'Unified Memory依赖', status: '⚠️', message: '依赖检查失败' });
    }
    
    // 输出检查结果
    console.log('\n📊 环境检查结果:');
    checks.forEach(check => {
      console.log(`  ${check.status} ${check.component}: ${check.message}`);
    });
    
    const allPassed = checks.every(c => c.status === '✅');
    return {
      success: allPassed,
      checks,
      message: allPassed ? '环境验证通过' : '环境验证失败，请检查配置'
    };
  }

  /**
   * 运行测试
   */
  async runTests() {
    console.log('🧪 运行系统测试...');
    
    const tests = [];
    
    // 测试1: 同步桥梁
    try {
      const SyncBridge = await import('../sync/sync_bridge.js');
      const bridge = new SyncBridge.default({ dryRun: true });
      const state = await bridge.loadSyncState();
      tests.push({ test: '同步桥梁初始化', status: '✅', message: '成功加载同步状态' });
    } catch (error) {
      tests.push({ test: '同步桥梁初始化', status: '❌', message: error.message });
    }
    
    // 测试2: 查询API
    try {
      const UnifiedQueryAPI = await import('../api/unified_query_api.js');
      const api = new UnifiedQueryAPI.default();
      const stats = api.getStats();
      tests.push({ test: '查询API初始化', status: '✅', message: 'API状态正常' });
    } catch (error) {
      tests.push({ test: '查询API初始化', status: '❌', message: error.message });
    }
    
    // 测试3: 去重模块
    try {
      const CrossSystemDeduplicator = await import('../dedup/cross_system_dedup.js');
      const dedup = new CrossSystemDeduplicator.default();
      const stats = dedup.getStats();
      tests.push({ test: '去重模块初始化', status: '✅', message: '去重模块正常' });
    } catch (error) {
      tests.push({ test: '去重模块初始化', status: '❌', message: error.message });
    }
    
    // 输出测试结果
    console.log('\n📊 测试结果:');
    tests.forEach(test => {
      console.log(`  ${test.status} ${test.test}: ${test.message}`);
    });
    
    const allPassed = tests.every(t => t.status === '✅');
    return {
      success: allPassed,
      tests,
      message: allPassed ? '所有测试通过' : '部分测试失败'
    };
  }

  /**
   * 部署crontab任务
   */
  async deployCrontab() {
    console.log('⏰ 部署定时任务...');
    
    try {
      const { stdout } = await execAsync('crontab -l 2>/dev/null || echo ""');
      const currentCrontab = stdout;
      
      // 生成新的crontab配置
      const SyncScheduler = await import('../sync/sync_cron.js');
      const scheduler = new SyncScheduler.default();
      const newEntry = scheduler.generateCrontab();
      
      // 检查是否已存在
      if (currentCrontab.includes('记忆系统同步任务')) {
        console.log('⚠️  定时任务已存在，跳过部署');
        return { success: true, message: '定时任务已存在' };
      }
      
      // 添加新任务
      const updatedCrontab = currentCrontab + '\n' + newEntry + '\n';
      await fs.writeFile('/tmp/new_crontab', updatedCrontab, 'utf8');
      await execAsync('crontab /tmp/new_crontab');
      
      console.log('✅ 定时任务部署完成');
      return { success: true, message: '定时任务已部署' };
      
    } catch (error) {
      console.error('❌ 部署定时任务失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 生成部署报告
   */
  async generateDeploymentReport() {
    const timestamp = new Date().toISOString();
    const report = {
      timestamp,
      deployment: {
        project: '记忆系统优化',
        version: '1.0.0',
        location: this.projectRoot
      },
      environment: await this.validateEnvironment(),
      tests: await this.runTests(),
      modules: [
        { name: 'SyncBridge', path: 'sync/sync_bridge.js', status: 'ready' },
        { name: 'UnifiedQueryAPI', path: 'api/unified_query_api.js', status: 'ready' },
        { name: 'CrossSystemDeduplicator', path: 'dedup/cross_system_dedup.js', status: 'ready' },
        { name: 'MemoryHealthMonitor', path: 'monitor/health_check.js', status: 'ready' }
      ],
      nextSteps: [
        '1. 执行首次同步: npm run sync:manual',
        '2. 测试查询功能: npm run query -- "测试"',
        '3. 检查健康状态: npm run monitor:dashboard',
        '4. 设置定时任务: npm run crontab'
      ]
    };
    
    const reportFile = path.join(this.logDir, `deployment_${timestamp.replace(/[:.]/g, '-')}.json`);
    await fs.writeFile(reportFile, JSON.stringify(report, null, 2), 'utf8');
    
    return {
      ...report,
      savedPath: reportFile
    };
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const deployer = new DeploymentManager();
  
  if (args[0] === '--init') {
    deployer.initProject().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--validate') {
    deployer.validateEnvironment().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--test') {
    deployer.runTests().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--crontab') {
    deployer.deployCrontab().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--report') {
    deployer.generateDeploymentReport().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--full') {
    console.log('🚀 执行完整部署流程...\n');
    
    deployer.validateEnvironment().then(envResult => {
      console.log('1. 环境验证:', envResult.success ? '✅' : '❌');
      if (!envResult.success) {
        console.log('   环境验证失败，停止部署');
        return;
      }
      
      return deployer.runTests().then(testResult => {
        console.log('2. 系统测试:', testResult.success ? '✅' : '❌');
        if (!testResult.success) {
          console.log('   系统测试失败，停止部署');
          return;
        }
        
        return deployer.deployCrontab().then(cronResult => {
          console.log('3. 定时任务:', cronResult.success ? '✅' : '❌');
          
          return deployer.generateDeploymentReport().then(report => {
            console.log('4. 部署报告:', '✅ 已生成');
            console.log('\n📋 部署完成！');
            console.log(`📄 报告位置: ${report.savedPath}`);
            console.log('\n🎯 下一步:');
            report.nextSteps.forEach(step => console.log(`  ${step}`));
          });
        });
      });
    }).catch(error => {
      console.error('❌ 部署失败:', error);
    });
  } else {
    console.log('使用方法:');
    console.log('  node deploy.js --init        # 初始化项目');
    console.log('  node deploy.js --validate    # 验证环境');
    console.log('  node deploy.js --test        # 运行测试');
    console.log('  node deploy.js --crontab     # 部署定时任务');
    console.log('  node deploy.js --report      # 生成部署报告');
    console.log('  node deploy.js --full        # 执行完整部署');
  }
}

export default DeploymentManager;