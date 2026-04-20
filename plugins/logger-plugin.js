/**
 * Logger Plugin - 操作日志记录插件
 * 记录所有 memory 操作到日志文件
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

// 日志配置（模块级别）
let logConfig = {
  logFile: path.join(__dirname, '..', 'logs', 'operations.log'),
  maxLogSize: 10 * 1024 * 1024,
  rotation: true
};

// 日志级别
const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
};

// 当前日志级别
let currentLogLevel = LogLevel.INFO;

function setLogLevel(level) {
  if (typeof level === 'string') {
    currentLogLevel = LogLevel[level.toUpperCase()] || LogLevel.INFO;
  } else {
    currentLogLevel = level;
  }
}

function shouldLog(level) {
  return level >= currentLogLevel;
}

// 日志记录函数
function log(level, operation, data) {
  if (!shouldLog(level)) return;
  
  const entry = {
    timestamp: new Date().toISOString(),
    level: Object.keys(LogLevel).find(k => LogLevel[k] === level) || 'INFO',
    operation,
    data,
    pid: process.pid
  };
  
  const logLine = JSON.stringify(entry) + '\n';
  
  try {
    const logDir = path.dirname(logConfig.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    // 检查日志轮换
    if (logConfig.rotation && fs.existsSync(logConfig.logFile)) {
      const stats = fs.statSync(logConfig.logFile);
      if (stats.size >= logConfig.maxLogSize) {
        rotateLog();
      }
    }
    
    fs.appendFileSync(logConfig.logFile, logLine, 'utf8');
  } catch (error) {
    console.error('[Logger] Failed to write log:', error.message);
  }
}

function rotateLog() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const oldLog = logConfig.logFile;
  const newLog = `${logConfig.logFile}.${timestamp}`;
  
  try {
    fs.renameSync(oldLog, newLog);
    console.log(`[Logger] Rotated log to: ${newLog}`);
  } catch (error) {
    console.error('[Logger] Failed to rotate log:', error.message);
  }
}

// 插件定义
export default {
  name: 'logger',
  version: '1.0.0',
  description: '记录所有 memory 操作日志',
  author: 'unified-memory',
  dependencies: [],
  
  defaultConfig: {
    logFile: path.join(__dirname, '..', 'logs', 'operations.log'),
    maxLogSize: 10 * 1024 * 1024,
    rotation: true,
    logLevel: 'INFO'
  },
  
  // 生命周期
  async initialize(context) {
    logConfig = { ...logConfig, ...context.config };
    setLogLevel(context.config.logLevel || 'INFO');
    
    const logDir = path.dirname(logConfig.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    context.setState('logCount', 0);
    context.setState('startTime', Date.now());
    
    log(LogLevel.INFO, 'PLUGIN_INIT', { config: logConfig });
    console.log(`📝 Logger plugin initialized: ${logConfig.logFile}`);
  },
  
  async destroy(context) {
    const logCount = context.getState('logCount') || 0;
    const duration = Date.now() - (context.getState('startTime') || Date.now());
    log(LogLevel.INFO, 'PLUGIN_DESTROY', { logCount, duration });
    console.log(`📝 Logger plugin shutting down after ${logCount} operations over ${duration}ms`);
  },
  
  // 钩子
  hooks: {
    beforeSave: async (memory, context) => {
      log(LogLevel.DEBUG, 'BEFORE_SAVE', {
        id: memory?.id || 'unknown',
        contentPreview: memory?.content?.substring(0, 30) || ''
      });
      context.setState('logCount', (context.getState('logCount') || 0) + 1);
      return memory;
    },
    
    afterSave: async (result, context) => {
      log(LogLevel.INFO, 'AFTER_SAVE', {
        id: result?.id || 'unknown',
        success: !!result
      });
      return result;
    },
    
    beforeSearch: async (query, context) => {
      log(LogLevel.DEBUG, 'BEFORE_SEARCH', { query: query?.substring(0, 50) });
      return query;
    },
    
    afterSearch: async (results, context) => {
      log(LogLevel.INFO, 'AFTER_SEARCH', {
        resultCount: results?.length || 0
      });
      return results;
    },
    
    beforeLoad: async (context) => {
      log(LogLevel.DEBUG, 'BEFORE_LOAD', {});
      return true;
    },
    
    afterLoad: async (memories, context) => {
      log(LogLevel.INFO, 'AFTER_LOAD', {
        count: memories?.length || 0
      });
      return memories;
    },
    
    beforeDelete: async (memoryId, context) => {
      log(LogLevel.WARN, 'BEFORE_DELETE', { id: memoryId });
      return memoryId;
    },
    
    afterDelete: async (memoryId, context) => {
      log(LogLevel.INFO, 'AFTER_DELETE', { id: memoryId });
      return memoryId;
    }
  }
};

// 导出工具函数供外部使用
export { log, LogLevel };
