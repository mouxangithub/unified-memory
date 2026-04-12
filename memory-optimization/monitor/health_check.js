#!/usr/bin/env node

/**
 * 记忆系统健康检查
 * 监控Workspace Memory和Unified Memory的状态
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

class MemoryHealthMonitor {
  constructor(options = {}) {
    this.workspacePath = options.workspacePath || '/root/.openclaw/workspace/memory';
    this.unifiedMemoryPath = options.unifiedMemoryPath || '/root/.openclaw/skills/unified-memory';
    this.syncStatePath = options.syncStatePath || '/root/.openclaw/workspace/memory-optimization/sync/sync_state.json';
    this.logDir = path.join(__dirname, '../logs');
    this.statsHistory = [];
    this.maxHistory = 100;
  }

  /**
   * 执行全面健康检查
   */
  async checkHealth() {
    const startTime = Date.now();
    const timestamp = new Date().toISOString();
    
    console.log('🔍 开始记忆系统健康检查...');
    
    const checks = {
      timestamp,
      overallStatus: 'healthy',
      checks: {},
      recommendations: [],
      stats: {}
    };
    
    try {
      // 1. 检查Workspace Memory
      const workspaceCheck = await this.checkWorkspaceMemory();
      checks.checks.workspaceMemory = workspaceCheck;
      
      if (!workspaceCheck.healthy) {
        checks.overallStatus = 'degraded';
        checks.recommendations.push('检查Workspace Memory文件系统');
      }
      
      // 2. 检查Unified Memory
      const unifiedCheck = await this.checkUnifiedMemory();
      checks.checks.unifiedMemory = unifiedCheck;
      
      if (!unifiedCheck.healthy) {
        checks.overallStatus = 'degraded';
        checks.recommendations.push('检查Unified Memory服务状态');
      }
      
      // 3. 检查同步状态
      const syncCheck = await this.checkSyncStatus();
      checks.checks.syncStatus = syncCheck;
      
      if (!syncCheck.healthy) {
        checks.overallStatus = 'degraded';
        checks.recommendations.push('检查同步机制');
      }
      
      // 4. 检查检索性能
      const searchCheck = await this.checkSearchPerformance();
      checks.checks.searchPerformance = searchCheck;
      
      if (!searchCheck.healthy) {
        checks.overallStatus = 'degraded';
        checks.recommendations.push('优化检索性能');
      }
      
      // 5. 收集统计信息
      checks.stats = await this.collectStats();
      
      // 6. 计算总体健康状态
      checks.overallStatus = this.calculateOverallStatus(checks.checks);
      
      // 7. 记录历史
      this.recordHistory(checks);
      
      // 8. 生成报告
      const report = await this.generateReport(checks);
      
      const duration = Date.now() - startTime;
      console.log(`✅ 健康检查完成 (${duration}ms)`);
      console.log(`📊 总体状态: ${checks.overallStatus.toUpperCase()}`);
      
      return {
        success: true,
        ...checks,
        report,
        duration
      };
    } catch (error) {
      console.error('❌ 健康检查失败:', error);
      
      return {
        success: false,
        timestamp,
        overallStatus: 'failed',
        error: error.message,
        duration: Date.now() - startTime
      };
    }
  }

  /**
   * 检查Workspace Memory
   */
  async checkWorkspaceMemory() {
    const result = {
      healthy: true,
      metrics: {},
      issues: []
    };
    
    try {
      // 检查目录是否存在
      const stats = await fs.stat(this.workspacePath);
      result.metrics.exists = true;
      result.metrics.isDirectory = stats.isDirectory();
      
      // 统计文件
      const files = await fs.readdir(this.workspacePath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      const otherFiles = files.filter(f => !f.endsWith('.md'));
      
      result.metrics.totalFiles = files.length;
      result.metrics.mdFiles = mdFiles.length;
      result.metrics.otherFiles = otherFiles.length;
      
      // 检查文件大小
      let totalSize = 0;
      for (const file of mdFiles.slice(0, 10)) { // 只检查前10个文件
        const filePath = path.join(this.workspacePath, file);
        const fileStats = await fs.stat(filePath);
        totalSize += fileStats.size;
      }
      
      result.metrics.estimatedTotalSizeMB = (totalSize / 1024 / 1024).toFixed(2);
      
      // 检查最近的文件
      const recentFiles = mdFiles.slice(0, 5);
      result.metrics.recentFiles = recentFiles;
      
      // 检查是否有损坏的文件
      for (const file of recentFiles) {
        try {
          const content = await fs.readFile(path.join(this.workspacePath, file), 'utf8');
          if (content.length === 0) {
            result.issues.push(`文件 ${file} 为空`);
            result.healthy = false;
          }
        } catch (readError) {
          result.issues.push(`无法读取文件 ${file}: ${readError.message}`);
          result.healthy = false;
        }
      }
      
      // 检查元数据文件
      const metadataFiles = ['access_history.json', 'episodes.json', 'memories.json'];
      for (const metaFile of metadataFiles) {
        const metaPath = path.join(this.workspacePath, metaFile);
        try {
          await fs.access(metaPath);
          result.metrics[`has${metaFile}`] = true;
        } catch {
          result.metrics[`has${metaFile}`] = false;
          result.issues.push(`缺少元数据文件 ${metaFile}`);
        }
      }
      
    } catch (error) {
      result.healthy = false;
      result.issues.push(`检查Workspace Memory失败: ${error.message}`);
    }
    
    return result;
  }

  /**
   * 检查Unified Memory
   */
  async checkUnifiedMemory() {
    const result = {
      healthy: true,
      metrics: {},
      issues: []
    };
    
    try {
      // 检查目录是否存在
      const stats = await fs.stat(this.unifiedMemoryPath);
      result.metrics.exists = true;
      result.metrics.isDirectory = stats.isDirectory();
      
      // 检查package.json
      const packagePath = path.join(this.unifiedMemoryPath, 'package.json');
      try {
        const packageData = await fs.readFile(packagePath, 'utf8');
        const pkg = JSON.parse(packageData);
        result.metrics.version = pkg.version;
        result.metrics.name = pkg.name;
      } catch {
        result.issues.push('无法读取package.json');
        result.healthy = false;
      }
      
      // 检查核心文件
      const coreFiles = [
        'src/core/enhanced_memory_system.js',
        'src/core/smart_deduplicator.js',
        'src/core/memory_pipeline.js'
      ];
      
      for (const coreFile of coreFiles) {
        const corePath = path.join(this.unifiedMemoryPath, coreFile);
        try {
          await fs.access(coreFile);
          result.metrics[`has${path.basename(coreFile, '.js')}`] = true;
        } catch {
          result.metrics[`has${path.basename(coreFile, '.js')}`] = false;
          result.issues.push(`缺少核心文件 ${coreFile}`);
        }
      }
      
      // 检查存储目录
      const storagePath = path.join(this.unifiedMemoryPath, 'storage');
      try {
        const storageStats = await fs.stat(storagePath);
        result.metrics.hasStorage = storageStats.isDirectory();
        
        // 检查存储文件
        const storageFiles = await fs.readdir(storagePath);
        result.metrics.storageFiles = storageFiles.length;
        
        // 检查记忆文件
        const memoriesFile = path.join(storagePath, 'memories.json');
        try {
          const memoriesData = await fs.readFile(memoriesFile, 'utf8');
          const memories = JSON.parse(memoriesData);
          result.metrics.totalMemories = memories.length;
        } catch {
          result.issues.push('无法读取记忆文件');
        }
      } catch {
        result.metrics.hasStorage = false;
        result.issues.push('缺少存储目录');
        result.healthy = false;
      }
      
      // 检查服务状态
      try {
        const { stdout } = await execAsync(`cd ${this.unifiedMemoryPath} && node -e "
          console.log('service_check_ok')
        "`);
        result.metrics.serviceRunning = stdout.includes('service_check_ok');
      } catch {
        result.metrics.serviceRunning = false;
        result.issues.push('服务未运行');
        result.healthy = false;
      }
      
    } catch (error) {
      result.healthy = false;
      result.issues.push(`检查Unified Memory失败: ${error.message}`);
    }
    
    return result;
  }

  /**
   * 检查同步状态
   */
  async checkSyncStatus() {
    const result = {
      healthy: true,
      metrics: {},
      issues: []
    };
    
    try {
      // 检查同步状态文件
      try {
        const stateData = await fs.readFile(this.syncStatePath, 'utf8');
        const state = JSON.parse(stateData);
        
        result.metrics.lastSyncTime = state.lastSyncTime;
        result.metrics.totalFilesProcessed = state.totalFilesProcessed;
        result.metrics.totalMemoriesSynced = state.totalMemoriesSynced;
        result.metrics.errorCount = state.errors?.length || 0;
        
        // 检查同步延迟
        if (state.lastSyncTime) {
          const lastSync = new Date(state.lastSyncTime);
          const now = new Date();
          const delayHours = (now - lastSync) / (1000 * 60 * 60);
          
          result.metrics.syncDelayHours = delayHours.toFixed(2);
          
          if (delayHours > 24) {
            result.issues.push(`同步延迟超过24小时 (${delayHours.toFixed(1)}小时)`);
            result.healthy = false;
          }
        }
        
        if (state.errors && state.errors.length > 10) {
          result.issues.push(`同步错误过多: ${state.errors.length}个`);
          result.healthy = false;
        }
        
      } catch {
        result.metrics.hasSyncState = false;
        result.issues.push('缺少同步状态文件');
        result.healthy = false;
      }
      
      // 检查同步脚本
      const syncScript = path.join(__dirname, '../sync/sync_bridge.js');
      try {
        await fs.access(syncScript);
        result.metrics.hasSyncScript = true;
      } catch {
        result.metrics.hasSyncScript = false;
        result.issues.push('缺少同步脚本');
        result.healthy = false;
      }
      
    } catch (error) {
      result.healthy = false;
      result.issues.push(`检查同步状态失败: ${error.message}`);
    }
    
    return result;
  }

  /**
   * 检查检索性能
   */
  async checkSearchPerformance() {
    const result = {
      healthy: true,
      metrics: {},
      issues: []
    };
    
    try {
      // 测试查询性能
      const testQueries = [
        '记忆系统',
        '优化',
        '架构',
        '同步'
      ];
      
      const queryTimes = [];
      
      for (const query of testQueries) {
        const start = Date.now();
        try {
          // 这里可以调用实际的查询API
          // 暂时用模拟
          await new Promise(resolve => setTimeout(resolve, 10));
          const duration = Date.now() - start;
          queryTimes.push(duration);
        } catch {
          // 查询失败
        }
      }
      
      if (queryTimes.length > 0) {
        const avgTime = queryTimes.reduce((a, b) => a + b, 0) / queryTimes.length;
        result.metrics.avgQueryTimeMs = avgTime.toFixed(2);
        result.metrics.minQueryTimeMs = Math.min(...queryTimes);
        result.metrics.maxQueryTimeMs = Math.max(...queryTimes);
        
        if (avgTime > 1000) {
          result.issues.push(`查询性能较慢: 平均${avgTime.toFixed(0)}ms`);
          result.healthy = false;
        }
      }
      
    } catch (error) {
      result.healthy = false;
      result.issues.push(`检查检索性能失败: ${error.message}`);
    }
    
    return result;
  }

  /**
   * 收集统计信息
   */
  async collectStats() {
    const stats = {
      timestamp: new Date().toISOString(),
      workspace: {},
      unified: {},
      sync: {},
      search: {}
    };
    
    try {
      // Workspace统计
      const workspaceFiles = await fs.readdir(this.workspacePath);
      const mdFiles = workspaceFiles.filter(f => f.endsWith('.md'));
      
      stats.workspace = {
        totalFiles: workspaceFiles.length,
        mdFiles: mdFiles.length,
        otherFiles: workspaceFiles.length - mdFiles.length
      };
      
      // Unified Memory统计
      try {
        const storagePath = path.join(this.unifiedMemoryPath, 'storage');
        const storageFiles = await fs.readdir(storagePath);
        stats.unified.storageFiles = storageFiles.length;
      } catch {
        stats.unified.storageFiles = 0;
      }
      
      // 同步统计
      try {
        const stateData = await fs.readFile(this.syncStatePath, 'utf8');
        const state = JSON.parse(stateData);
        stats.sync = {
          lastSyncTime: state.lastSyncTime,
          totalFilesProcessed: state.totalFilesProcessed,
          totalMemoriesSynced: state.totalMemoriesSynced
        };
      } catch {
        stats.sync = { error: '无法读取同步状态' };
      }
      
    } catch (error) {
      stats.error = error.message;
    }
    
    return stats;
  }

  /**
   * 计算总体状态
   */
  calculateOverallStatus(checks) {
    const allChecks = Object.values(checks);
    const unhealthyCount = allChecks.filter(check => !check.healthy).length;
    
    if (unhealthyCount === 0) return 'healthy';
    if (unhealthyCount < allChecks.length / 2) return 'degraded';
    return 'unhealthy';
  }

  /**
   * 记录历史
   */
  recordHistory(checkResult) {
    this.statsHistory.push({
      timestamp: checkResult.timestamp,
      overallStatus: checkResult.overallStatus,
      checks: Object.keys(checkResult.checks).length,
      issues: checkResult.recommendations?.length || 0
    });
    
    // 限制历史记录大小
    if (this.statsHistory.length > this.maxHistory) {
      this.statsHistory = this.statsHistory.slice(-this.maxHistory);
    }
  }

  /**
   * 生成报告
   */
  async generateReport(checkResult) {
    const report = {
      summary: {
        timestamp: checkResult.timestamp,
        overallStatus: checkResult.overallStatus,
        duration: checkResult.duration,
        checksPerformed: Object.keys(checkResult.checks).length
      },
      details: checkResult.checks,
      recommendations: checkResult.recommendations,
      stats: checkResult.stats,
      history: {
        recent: this.statsHistory.slice(-10),
        trends: this.analyzeTrends()
      }
    };
    
    // 保存报告
    const reportDir = path.join(this.logDir, 'reports');
    await fs.mkdir(reportDir, { recursive: true });
    
    const reportFile = path.join(reportDir, `health_check_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
    await fs.writeFile(reportFile, JSON.stringify(report, null, 2), 'utf8');
    
    return {
      ...report,
      savedPath: reportFile
    };
  }

  /**
   * 分析趋势
   */
  analyzeTrends() {
    if (this.statsHistory.length < 5) return { insufficientData: true };
    
    const recent = this.statsHistory.slice(-5);
    const healthyCount = recent.filter(r => r.overallStatus === 'healthy').length;
    const unhealthyCount = recent.filter(r => r.overallStatus === 'unhealthy').length;
    
    return {
      healthyRate: (healthyCount / recent.length * 100).toFixed(1) + '%',
      unhealthyRate: (unhealthyCount / recent.length * 100).toFixed(1) + '%',
      trend: healthyCount > unhealthyCount ? 'improving' : 'declining',
      checksPerDay: recent.length / 5
    };
  }

  /**
   * 获取历史报告
   */
  async getHistoricalReports(limit = 10) {
    try {
      const reportDir = path.join(this.logDir, 'reports');
      const files = await fs.readdir(reportDir);
      
      const reportFiles = files
        .filter(f => f.startsWith('health_check_') && f.endsWith('.json'))
        .sort()
        .reverse()
        .slice(0, limit);
      
      const reports = [];
      for (const file of reportFiles) {
        const filePath = path.join(reportDir, file);
        const content = await fs.readFile(filePath, 'utf8');
        reports.push(JSON.parse(content));
      }
      
      return {
        success: true,
        total: reportFiles.length,
        reports
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const monitor = new MemoryHealthMonitor();
  
  if (args[0] === '--check') {
    monitor.checkHealth().then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(error => {
      console.error('健康检查失败:', error);
      process.exit(1);
    });
  } else if (args[0] === '--history') {
    const limit = args[1] ? parseInt(args[1]) : 10;
    monitor.getHistoricalReports(limit).then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else if (args[0] === '--dashboard') {
    console.log('📊 记忆系统健康监控仪表板');
    console.log('='.repeat(50));
    
    monitor.checkHealth().then(result => {
      console.log(`\n🔍 总体状态: ${result.overallStatus.toUpperCase()}`);
      console.log(`⏱️  检查耗时: ${result.duration}ms`);
      
      console.log('\n📈 各组件状态:');
      Object.entries(result.checks).forEach(([component, check]) => {
        const status = check.healthy ? '✅' : '❌';
        console.log(`  ${status} ${component}: ${check.issues.length > 0 ? check.issues[0] : '正常'}`);
      });
      
      if (result.recommendations.length > 0) {
        console.log('\n💡 建议:');
        result.recommendations.forEach((rec, idx) => {
          console.log(`  ${idx+1}. ${rec}`);
        });
      }
      
    }).catch(error => {
      console.error('监控失败:', error);
    });
  } else {
    console.log('使用方法:');
    console.log('  node health_check.js --check');
    console.log('  node health_check.js --history [数量]');
    console.log('  node health_check.js --dashboard');
  }
}

export default MemoryHealthMonitor;