#!/usr/bin/env node

/**
 * 记忆系统优化项目测试脚本
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class TestRunner {
  constructor() {
    this.projectRoot = path.join(__dirname, '..');
    this.testDir = path.join(this.projectRoot, 'tests');
    this.results = [];
  }

  /**
   * 运行所有测试
   */
  async runAllTests() {
    console.log('🧪 开始运行记忆系统优化测试...\n');
    
    const startTime = Date.now();
    
    try {
      // 1. 基础测试
      await this.runBasicTests();
      
      // 2. 模块测试
      await this.runModuleTests();
      
      // 3. 集成测试
      await this.runIntegrationTests();
      
      // 4. 性能测试
      await this.runPerformanceTests();
      
      // 5. 边界测试
      await this.runEdgeCaseTests();
      
      const duration = Date.now() - startTime;
      
      // 生成测试报告
      const report = await this.generateTestReport(duration);
      
      console.log('\n📊 测试完成！');
      console.log(`⏱️  总耗时: ${duration}ms`);
      console.log(`✅ 通过: ${report.summary.passed}`);
      console.log(`❌ 失败: ${report.summary.failed}`);
      console.log(`⚠️  跳过: ${report.summary.skipped}`);
      console.log(`📈 成功率: ${report.summary.successRate}%`);
      
      if (report.summary.failed > 0) {
        console.log('\n🔍 失败详情:');
        this.results
          .filter(r => r.status === 'failed')
          .forEach((test, idx) => {
            console.log(`  ${idx+1}. ${test.name}: ${test.error}`);
          });
      }
      
      return report;
      
    } catch (error) {
      console.error('❌ 测试运行失败:', error);
      return {
        success: false,
        error: error.message,
        duration: Date.now() - startTime
      };
    }
  }

  /**
   * 运行基础测试
   */
  async runBasicTests() {
    console.log('🔧 运行基础测试...');
    
    // 测试1: 项目结构
    await this.runTest('项目结构检查', async () => {
      const requiredDirs = ['sync', 'dedup', 'monitor', 'api', 'scripts', 'logs', 'tests'];
      
      for (const dir of requiredDirs) {
        const dirPath = path.join(this.projectRoot, dir);
        try {
          await fs.access(dirPath);
        } catch {
          throw new Error(`缺少目录: ${dir}`);
        }
      }
      
      return { directories: requiredDirs.length };
    });
    
    // 测试2: 配置文件
    await this.runTest('配置文件检查', async () => {
      const configPath = path.join(this.projectRoot, 'config.json');
      const content = await fs.readFile(configPath, 'utf8');
      const config = JSON.parse(content);
      
      const requiredFields = ['workspacePath', 'unifiedMemoryPath', 'sync'];
      for (const field of requiredFields) {
        if (!config[field]) {
          throw new Error(`配置缺少字段: ${field}`);
        }
      }
      
      return { fields: requiredFields.length };
    });
    
    // 测试3: 主入口文件
    await this.runTest('主入口文件检查', async () => {
      const indexPath = path.join(this.projectRoot, 'index.js');
      await fs.access(indexPath);
      
      const content = await fs.readFile(indexPath, 'utf8');
      if (!content.includes('SyncBridge') || !content.includes('UnifiedQueryAPI')) {
        throw new Error('主入口文件缺少关键导出');
      }
      
      return { fileSize: content.length };
    });
  }

  /**
   * 运行模块测试
   */
  async runModuleTests() {
    console.log('\n📦 运行模块测试...');
    
    // 测试4: 同步桥梁模块
    await this.runTest('同步桥梁模块', async () => {
      const SyncBridge = await import('../sync/sync_bridge.js');
      const bridge = new SyncBridge.default({ dryRun: true });
      
      // 测试状态加载
      const state = await bridge.loadSyncState();
      if (!state || typeof state !== 'object') {
        throw new Error('状态加载失败');
      }
      
      // 测试文件扫描
      const files = await bridge.scanWorkspaceFiles();
      if (!Array.isArray(files)) {
        throw new Error('文件扫描失败');
      }
      
      return { filesScanned: files.length };
    });
    
    // 测试5: 查询API模块
    await this.runTest('查询API模块', async () => {
      const UnifiedQueryAPI = await import('../api/unified_query_api.js');
      const api = new UnifiedQueryAPI.default();
      
      // 测试统计功能
      const stats = api.getStats();
      if (!stats || !stats.queries) {
        throw new Error('统计功能失败');
      }
      
      // 测试缓存管理
      const cacheResult = api.clearCache();
      if (!cacheResult.success) {
        throw new Error('缓存管理失败');
      }
      
      return { cacheCleared: true };
    });
    
    // 测试6: 去重模块
    await this.runTest('去重模块', async () => {
      const CrossSystemDeduplicator = await import('../dedup/cross_system_dedup.js');
      const dedup = new CrossSystemDeduplicator.default();
      
      // 测试统计功能
      const stats = dedup.getStats();
      if (!stats || !stats.checks) {
        throw new Error('统计功能失败');
      }
      
      // 测试记忆指纹生成
      const testMemory = {
        content: '测试记忆内容',
        source: 'test',
        type: 'facts'
      };
      
      const fingerprint = dedup.generateFingerprint(testMemory);
      if (!fingerprint || typeof fingerprint !== 'string') {
        throw new Error('指纹生成失败');
      }
      
      return { fingerprintGenerated: true };
    });
    
    // 测试7: 健康监控模块
    await this.runTest('健康监控模块', async () => {
      const MemoryHealthMonitor = await import('../monitor/health_check.js');
      const monitor = new MemoryHealthMonitor.default();
      
      // 测试统计收集
      const stats = await monitor.collectStats();
      if (!stats || !stats.timestamp) {
        throw new Error('统计收集失败');
      }
      
      return { statsCollected: true };
    });
  }

  /**
   * 运行集成测试
   */
  async runIntegrationTests() {
    console.log('\n🔗 运行集成测试...');
    
    // 测试8: 同步流程集成
    await this.runTest('同步流程集成', async () => {
      const SyncBridge = await import('../sync/sync_bridge.js');
      const bridge = new SyncBridge.default({ 
        dryRun: true,
        batchSize: 1
      });
      
      // 执行一次同步（干运行模式）
      const result = await bridge.sync();
      
      if (!result || typeof result !== 'object') {
        throw new Error('同步执行失败');
      }
      
      return { syncExecuted: true };
    });
    
    // 测试9: 查询流程集成
    await this.runTest('查询流程集成', async () => {
      const UnifiedQueryAPI = await import('../api/unified_query_api.js');
      const api = new UnifiedQueryAPI.default();
      
      // 执行一次查询
      const result = await api.query('测试', { limit: 1 });
      
      if (!result || typeof result !== 'object') {
        throw new Error('查询执行失败');
      }
      
      return { queryExecuted: true, success: result.success };
    });
    
    // 测试10: 去重检查集成
    await this.runTest('去重检查集成', async () => {
      const CrossSystemDeduplicator = await import('../dedup/cross_system_dedup.js');
      const dedup = new CrossSystemDeduplicator.default();
      
      const testMemory = {
        content: '这是一个测试记忆，用于验证去重功能。',
        source: 'test',
        type: 'facts'
      };
      
      const result = await dedup.checkDuplicate(testMemory, {
        crossSystemDedup: false
      });
      
      if (!result || typeof result !== 'object') {
        throw new Error('去重检查失败');
      }
      
      return { duplicateChecked: true, isDuplicate: result.isDuplicate };
    });
  }

  /**
   * 运行性能测试
   */
  async runPerformanceTests() {
    console.log('\n⚡ 运行性能测试...');
    
    // 测试11: 同步性能
    await this.runTest('同步性能基准', async () => {
      const SyncBridge = await import('../sync/sync_bridge.js');
      const bridge = new SyncBridge.default({ dryRun: true });
      
      const start = Date.now();
      const files = await bridge.scanWorkspaceFiles();
      const duration = Date.now() - start;
      
      if (duration > 5000) {
        throw new Error(`文件扫描过慢: ${duration}ms`);
      }
      
      return { scanTime: duration, filesFound: files.length };
    });
    
    // 测试12: 查询性能
    await this.runTest('查询性能基准', async () => {
      const UnifiedQueryAPI = await import('../api/unified_query_api.js');
      const api = new UnifiedQueryAPI.default();
      
      const queries = ['记忆', '系统', '测试', '优化'];
      const times = [];
      
      for (const query of queries) {
        const start = Date.now();
        await api.query(query, { limit: 1 });
        times.push(Date.now() - start);
      }
      
      const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
      
      if (avgTime > 1000) {
        throw new Error(`查询平均响应时间过长: ${avgTime.toFixed(0)}ms`);
      }
      
      return { avgQueryTime: avgTime.toFixed(2), queriesTested: queries.length };
    });
    
    // 测试13: 去重性能
    await this.runTest('去重性能基准', async () => {
      const CrossSystemDeduplicator = await import('../dedup/cross_system_dedup.js');
      const dedup = new CrossSystemDeduplicator.default();
      
      const testMemories = Array(10).fill(0).map((_, i) => ({
        content: `测试记忆 ${i}: 这是第${i}个测试记忆内容`,
        source: 'test',
        type: 'facts'
      }));
      
      const start = Date.now();
      const results = await dedup.batchCheckDuplicates(testMemories, {
        batchSize: 5,
        crossSystemDedup: false
      });
      const duration = Date.now() - start;
      
      const avgTimePerMemory = duration / testMemories.length;
      
      if (avgTimePerMemory > 500) {
        throw new Error(`去重检查过慢: ${avgTimePerMemory.toFixed(0)}ms/记忆`);
      }
      
      return { 
        totalTime: duration, 
        memoriesChecked: testMemories.length,
        avgTimePerMemory: avgTimePerMemory.toFixed(2)
      };
    });
  }

  /**
   * 运行边界测试
   */
  async runEdgeCaseTests() {
    console.log('\n⚠️  运行边界测试...');
    
    // 测试14: 空输入处理
    await this.runTest('空输入处理', async () => {
      const UnifiedQueryAPI = await import('../api/unified_query_api.js');
      const api = new UnifiedQueryAPI.default();
      
      const result = await api.query('', { limit: 1 });
      
      if (!result || !result.success) {
        throw new Error('空查询处理失败');
      }
      
      return { emptyQueryHandled: true };
    });
    
    // 测试15: 大文件处理
    await this.runTest('大文件处理', async () => {
      const SyncBridge = await import('../sync/sync_bridge.js');
      const bridge = new SyncBridge.default({ dryRun: true });
      
      // 测试大内容解析
      const largeContent = '大内容测试\n' + '测试行\n'.repeat(1000);
      const memories = await bridge.parseMarkdownFile('/dev/null', largeContent);
      
      if (!Array.isArray(memories)) {
        throw new Error('大内容解析失败');
      }
      
      return { largeContentParsed: true, memoriesFound: memories.length };
    });
    
    // 测试16: 错误恢复
    await this.runTest('错误恢复能力', async () => {
      const MemoryHealthMonitor = await import('../monitor/health_check.js');
      const monitor = new MemoryHealthMonitor.default();
      
      // 测试无效路径
      const invalidMonitor = new MemoryHealthMonitor.default({
        workspacePath: '/invalid/path/that/does/not/exist'
      });
      
      const result = await invalidMonitor.checkHealth();
      
      if (!result || result.overallStatus === 'healthy') {
        throw new Error('错误路径未正确处理');
      }
      
      return { errorHandled: true, status: result.overallStatus };
    });
  }

  /**
   * 运行单个测试
   */
  async runTest(name, testFn) {
    const startTime = Date.now();
    
    try {
      console.log(`  ${name}...`);
      const result = await testFn();
      const duration = Date.now() - startTime;
      
      this.results.push({
        name,
        status: 'passed',
        duration,
        result
      });
      
      console.log(`    ✅ 通过 (${duration}ms)`);
      
    } catch (error) {
      const duration = Date.now() - startTime;
      
      this.results.push({
        name,
        status: 'failed',
        duration,
        error: error.message
      });
      
      console.log(`    ❌ 失败 (${duration}ms): ${error.message}`);
    }
  }

  /**
   * 生成测试报告
   */
  async generateTestReport(duration) {
    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    const skipped = this.results.filter(r => r.status === 'skipped').length;
    const total = this.results.length;
    const successRate = total > 0 ? (passed / total * 100).toFixed(2) : 0;
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total,
        passed,
        failed,
        skipped,
        successRate: `${successRate}%`,
        duration
      },
      details: this.results,
      modules: {
        basic: this.results.filter(r => r.name.includes('基础') || r.name.includes('项目') || r.name.includes('配置')).length,
        module: this.results.filter(r => r.name.includes('模块')).length,
        integration: this.results.filter(r => r.name.includes('集成')).length,
        performance: this.results.filter(r => r.name.includes('性能')).length,
        edge: this.results.filter(r => r.name.includes('边界')).length
      },
      recommendations: this.generateRecommendations()
    };
    
    // 保存报告
    const reportDir = path.join(this.projectRoot, 'logs', 'test_reports');
    await fs.mkdir(reportDir, { recursive: true });
    
    const reportFile = path.join(reportDir, `test_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
    await fs.writeFile(reportFile, JSON.stringify(report, null, 2), 'utf8');
    
    return {
      ...report,
      savedPath: reportFile
    };
  }

  /**
   * 生成建议
   */
  generateRecommendations() {
    const recommendations = [];
    
    // 基于测试结果生成建议
    const failedTests = this.results.filter(r => r.status === 'failed');
    
    if (failedTests.length > 0) {
      recommendations.push('修复失败的测试用例');
    }
    
    // 性能建议
    const performanceTests = this.results.filter(r => r.name.includes('性能'));
    const slowTests = performanceTests.filter(p => p.result && p.result.avgQueryTime > 500);
    
    if (slowTests.length > 0) {
      recommendations.push('优化查询性能，考虑增加缓存或索引');
    }
    
    // 覆盖率建议
    if (this.results.length < 15) {
      recommendations.push('增加测试覆盖率，特别是边界条件测试');
    }
    
    return recommendations;
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const testRunner = new TestRunner();
  
  if (args[0] === '--all') {
    testRunner.runAllTests().then(report => {
      console.log('\n📄 测试报告已保存:', report.savedPath);
      process.exit(report.summary.failed > 0 ? 1 : 0);
    }).catch(error => {
      console.error('测试运行失败:', error);
      process.exit(1);
    });
  } else if (args[0] === '--basic') {
    testRunner.runBasicTests().then(() => {
      console.log('\n✅ 基础测试完成');
    }).catch(console.error);
  } else if (args[0] === '--modules') {
    testRunner.runModuleTests().then(() => {
      console.log('\n✅ 模块测试完成');
    }).catch(console.error);
  } else if (args[0] === '--integration') {
    testRunner.runIntegrationTests().then(() => {
      console.log('\n✅ 集成测试完成');
    }).catch(console.error);
  } else if (args[0] === '--performance') {
    testRunner.runPerformanceTests().then(() => {
      console.log('\n✅ 性能测试完成');
    }).catch(console.error);
  } else if (args[0] === '--edge') {
    testRunner.runEdgeCaseTests().then(() => {
      console.log('\n✅ 边界测试完成');
    }).catch(console.error);
  } else {
    console.log('使用方法:');
    console.log('  node test.js --all          # 运行所有测试');
    console.log('  node test.js --basic        # 运行基础测试');
    console.log('  node test.js --modules      # 运行模块测试');
    console.log('  node test.js --integration  # 运行集成测试');
    console.log('  node test.js --performance  # 运行性能测试');
    console.log('  node test.js --edge         # 运行边界测试');
  }
}

export default TestRunner;