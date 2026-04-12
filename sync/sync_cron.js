#!/usr/bin/env node

/**
 * 同步调度脚本
 * 每日凌晨2点自动执行同步
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import SyncBridge from './sync_bridge.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class SyncScheduler {
  constructor() {
    this.logDir = path.join(__dirname, '../logs');
    this.syncBridge = new SyncBridge();
    this.maxRetries = 3;
    this.retryDelay = 5000; // 5秒
  }

  /**
   * 初始化日志目录
   */
  async initLogDir() {
    try {
      await fs.mkdir(this.logDir, { recursive: true });
    } catch (error) {
      console.error('创建日志目录失败:', error);
    }
  }

  /**
   * 写入日志
   */
  async writeLog(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };
    
    const logFile = path.join(this.logDir, `sync_${new Date().toISOString().split('T')[0]}.jsonl`);
    
    try {
      await fs.appendFile(logFile, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入日志失败:', error);
    }
    
    // 同时输出到控制台
    console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
  }

  /**
   * 带重试的同步
   */
  async syncWithRetry() {
    let lastError = null;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        await this.writeLog('info', `开始同步尝试 ${attempt}/${this.maxRetries}`);
        
        const result = await this.syncBridge.sync();
        
        await this.writeLog('info', '同步完成', {
          filesProcessed: result.totalFilesProcessed,
          memoriesSynced: result.totalMemoriesSynced,
          errors: result.errors.length
        });
        
        return result;
      } catch (error) {
        lastError = error;
        await this.writeLog('error', `同步尝试 ${attempt} 失败`, {
          error: error.message,
          stack: error.stack
        });
        
        if (attempt < this.maxRetries) {
          await this.writeLog('info', `等待 ${this.retryDelay}ms 后重试...`);
          await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        }
      }
    }
    
    throw lastError;
  }

  /**
   * 执行一次同步
   */
  async runOnce() {
    await this.initLogDir();
    
    try {
      await this.writeLog('info', '开始手动同步');
      const result = await this.syncWithRetry();
      await this.writeLog('info', '手动同步完成');
      return result;
    } catch (error) {
      await this.writeLog('error', '手动同步失败', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  /**
   * 启动定时调度
   */
  async startScheduler() {
    await this.initLogDir();
    await this.writeLog('info', '启动同步调度器');
    
    // 计算到下一个凌晨2点的时间
    const now = new Date();
    const nextRun = new Date(now);
    
    if (now.getHours() >= 2) {
      // 如果已经过了2点，安排到明天2点
      nextRun.setDate(nextRun.getDate() + 1);
    }
    
    nextRun.setHours(2, 0, 0, 0);
    
    const delay = nextRun.getTime() - now.getTime();
    
    await this.writeLog('info', '下一次同步时间', {
      nextRun: nextRun.toISOString(),
      delayMs: delay,
      delayHours: (delay / (1000 * 60 * 60)).toFixed(2)
    });
    
    // 设置定时器
    setTimeout(() => {
      this.runScheduledSync();
      // 之后每天执行一次
      setInterval(() => this.runScheduledSync(), 24 * 60 * 60 * 1000);
    }, delay);
    
    console.log('🕒 同步调度器已启动');
    console.log(`⏰ 下一次同步: ${nextRun.toLocaleString('zh-CN')}`);
    console.log(`📁 日志目录: ${this.logDir}`);
  }

  /**
   * 执行定时同步
   */
  async runScheduledSync() {
    await this.initLogDir();
    
    try {
      await this.writeLog('info', '开始定时同步');
      const result = await this.syncWithRetry();
      await this.writeLog('info', '定时同步完成', {
        stats: {
          filesProcessed: result.totalFilesProcessed,
          memoriesSynced: result.totalMemoriesSynced,
          errors: result.errors.length
        }
      });
    } catch (error) {
      await this.writeLog('error', '定时同步失败', {
        error: error.message,
        stack: error.stack
      });
    }
  }

  /**
   * 生成crontab配置
   */
  generateCrontab() {
    const crontab = `# 记忆系统同步任务
# 每天凌晨2点执行同步
0 2 * * * cd /root/.openclaw/workspace/memory-optimization && node sync/sync_cron.js --scheduled >> /root/.openclaw/workspace/memory-optimization/logs/cron.log 2>&1

# 每小时检查一次同步状态（可选）
0 * * * * cd /root/.openclaw/workspace/memory-optimization && node scripts/health_check.js >> /root/.openclaw/workspace/memory-optimization/logs/health.log 2>&1`;
    
    return crontab;
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const scheduler = new SyncScheduler();
  
  if (args.includes('--scheduled')) {
    // 定时任务模式
    scheduler.runScheduledSync().catch(error => {
      console.error('定时同步失败:', error);
      process.exit(1);
    });
  } else if (args.includes('--start-scheduler')) {
    // 启动调度器
    scheduler.startScheduler().catch(error => {
      console.error('启动调度器失败:', error);
      process.exit(1);
    });
  } else if (args.includes('--crontab')) {
    // 生成crontab配置
    console.log(scheduler.generateCrontab());
  } else {
    // 手动执行一次
    scheduler.runOnce().catch(error => {
      console.error('手动同步失败:', error);
      process.exit(1);
    });
  }
}

export default SyncScheduler;