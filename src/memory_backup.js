/**
 * 记忆备份与恢复模块 - AgentBrain 企业级功能
 * 
 * 灾难恢复：自动备份、增量备份、一键恢复
 * 
 * @module memory_backup
 */

import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import { EventEmitter } from 'events';

/**
 * 备份类型
 */
export const BackupType = {
  FULL: 'full',
  INCREMENTAL: 'incremental',
  DIFFERENTIAL: 'differential'
};

/**
 * 备份状态
 */
export const BackupStatus = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
  RESTORED: 'restored'
};

/**
 * 备份元数据
 */
class BackupMetadata {
  constructor({ id, type, memoryIds = [], parentBackupId = null, metadata = {} }) {
    this.id = id || `backup_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    this.type = type;
    this.memoryIds = memoryIds;
    this.parentBackupId = parentBackupId;
    this.metadata = {
      ...metadata,
      createdAt: Date.now(),
      size: 0,
      memoryCount: memoryIds.length
    };
    this.status = BackupStatus.PENDING;
    this.completedAt = null;
    this.error = null;
    this.checksum = null;
    this.filePath = null;
  }
  
  complete(filePath, size, checksum) {
    this.status = BackupStatus.COMPLETED;
    this.completedAt = Date.now();
    this.filePath = filePath;
    this.metadata.size = size;
    this.checksum = checksum;
  }
  
  fail(error) {
    this.status = BackupStatus.FAILED;
    this.error = error;
    this.completedAt = Date.now();
  }
}

/**
 * 备份恢复点
 */
class RestorePoint {
  constructor({ id, backupId, memoryId, versionId, timestamp }) {
    this.id = id || `rp_${Date.now()}`;
    this.backupId = backupId;
    this.memoryId = memoryId;
    this.versionId = versionId;
    this.timestamp = timestamp || Date.now();
  }
}

/**
 * 记忆备份管理器
 */
export class MemoryBackup extends EventEmitter {
  constructor(options = {}) {
    super();
    
    // 备份存储
    this.backups = new Map();
    this.restorePoints = new Map();
    
    // 配置
    this.config = {
      backupDir: options.backupDir || './backups',
      maxBackups: options.maxBackups || 10,
      maxBackupAge: options.maxBackupAge || 30 * 24 * 60 * 60 * 1000, // 30天
      autoBackup: options.autoBackup !== false,
      backupInterval: options.backupInterval || 60 * 60 * 1000, // 1小时
      compression: options.compression !== false,
      encryption: options.encryption || false,
      encryptionKey: options.encryptionKey || null,
      ...options
    };
    
    // 备份索引
    this.backupIndex = new Map();
    
    // 统计
    this.stats = {
      totalBackups: 0,
      totalRestores: 0,
      lastBackupAt: null,
      lastRestoreAt: null,
      totalBackupSize: 0
    };
    
    // 初始化
    this._init();
  }

  async _init() {
    try {
      await fs.mkdir(this.config.backupDir, { recursive: true });
    } catch (e) {
      // 目录可能已存在
    }
    
    // 加载现有备份索引
    await this._loadBackupIndex();
  }

  // ─────────────────────────────────────────────────────────────
  // 备份操作
  // ─────────────────────────────────────────────────────────────

  /**
   * 创建备份
   * 
   * @param {Object} options - 备份选项
   * @returns {Object} 备份结果
   * 
   * @example
   * const backup = await memoryBackup.createBackup({
   *   type: 'full',
   *   destination: 's3://backup'
   * });
   */
  async createBackup(options = {}) {
    const { type = BackupType.FULL, memoryIds = [], destination = this.config.backupDir } = options;
    
    const backup = new BackupMetadata({
      id: options.id,
      type,
      memoryIds,
      parentBackupId: type === BackupType.INCREMENTAL ? this._getLatestBackupId() : null
    });
    
    this.emit('backup:start', { backupId: backup.id, type });
    
    try {
      backup.status = BackupStatus.IN_PROGRESS;
      
      // 收集数据
      const data = await this._collectBackupData(memoryIds, backup);
      
      // 序列化
      const serialized = JSON.stringify(data);
      
      // 压缩（如果启用）
      const content = this.config.compression ? await this._compress(serialized) : serialized;
      
      // 加密（如果启用）
      const finalContent = this.config.encryption ? this._encrypt(content) : content;
      
      // 计算校验和
      const checksum = crypto.createHash('sha256').update(finalContent).digest('hex');
      
      // 保存文件
      const filePath = path.join(destination, `${backup.id}.backup`);
      await fs.writeFile(filePath, finalContent);
      
      // 完成备份
      backup.complete(filePath, finalContent.length, checksum);
      this.backups.set(backup.id, backup);
      this.backupIndex.set(backup.id, backup);
      
      // 更新统计
      this.stats.totalBackups++;
      this.stats.lastBackupAt = Date.now();
      this.stats.totalBackupSize += backup.metadata.size;
      
      // 保存索引
      await this._saveBackupIndex();
      
      // 清理旧备份
      await this._cleanupOldBackups();
      
      this.emit('backup:complete', backup);
      
      return {
        success: true,
        backupId: backup.id,
        type: backup.type,
        memoryCount: backup.metadata.memoryCount,
        size: backup.metadata.size,
        checksum: backup.checksum,
        createdAt: backup.metadata.createdAt
      };
      
    } catch (error) {
      backup.fail(error.message);
      this.emit('backup:failed', { backupId: backup.id, error: error.message });
      return { success: false, error: error.message };
    }
  }

  /**
   * 创建增量备份
   * 
   * @param {Array} memoryIds - 要备份的记忆 ID 列表
   * @returns {Object} 备份结果
   */
  async createIncrementalBackup(memoryIds = []) {
    return this.createBackup({ type: BackupType.INCREMENTAL, memoryIds });
  }

  /**
   * 创建差异备份
   * 
   * @param {Array} memoryIds - 要备份的记忆 ID 列表
   * @returns {Object} 备份结果
   */
  async createDifferentialBackup(memoryIds = []) {
    const lastFullBackup = this._getLatestBackup(BackupType.FULL);
    return this.createBackup({
      type: BackupType.DIFFERENTIAL,
      memoryIds,
      parentBackupId: lastFullBackup?.id
    });
  }

  /**
   * 列出所有备份
   * 
   * @param {Object} filter - 过滤条件
   * @returns {Array} 备份列表
   */
  async listBackups(filter = {}) {
    let backups = Array.from(this.backups.values());
    
    if (filter.type) {
      backups = backups.filter(b => b.type === filter.type);
    }
    
    if (filter.status) {
      backups = backups.filter(b => b.status === filter.status);
    }
    
    if (filter.since) {
      backups = backups.filter(b => b.metadata.createdAt >= filter.since);
    }
    
    backups.sort((a, b) => b.metadata.createdAt - a.metadata.createdAt);
    
    return backups.map(b => ({
      id: b.id,
      type: b.type,
      status: b.status,
      memoryCount: b.metadata.memoryCount,
      size: b.metadata.size,
      createdAt: b.metadata.createdAt,
      completedAt: b.completedAt,
      checksum: b.checksum
    }));
  }

  /**
   * 获取备份详情
   * 
   * @param {string} backupId - 备份 ID
   * @returns {Object} 备份详情
   */
  async getBackup(backupId) {
    const backup = this.backups.get(backupId);
    if (!backup) return null;
    
    return {
      id: backup.id,
      type: backup.type,
      status: backup.status,
      memoryIds: backup.memoryIds,
      parentBackupId: backup.parentBackupId,
      metadata: backup.metadata,
      completedAt: backup.completedAt,
      error: backup.error,
      checksum: backup.checksum,
      filePath: backup.filePath
    };
  }

  /**
   * 恢复备份
   * 
   * @param {string} backupId - 备份 ID
   * @param {Object} options - 恢复选项
   * @returns {Object} 恢复结果
   * 
   * @example
   * const restored = await memoryBackup.restore('backup_20240423', {
   *   targetMemoryIds: ['memory_1', 'memory_2']
   * });
   */
  async restore(backupId, options = {}) {
    const backup = this.backups.get(backupId);
    if (!backup) return { success: false, error: '备份不存在' };
    if (backup.status !== BackupStatus.COMPLETED) {
      return { success: false, error: '备份未完成' };
    }
    
    this.emit('restore:start', { backupId, options });
    
    try {
      // 读取备份文件
      let content = await fs.readFile(backup.filePath);
      
      // 解密（如果加密）
      if (this.config.encryption) {
        content = this._decrypt(content);
      }
      
      // 解压（如果压缩）
      if (this.config.compression) {
        content = await this._decompress(content);
      }
      
      // 验证校验和
      const checksum = crypto.createHash('sha256').update(content).digest('hex');
      if (checksum !== backup.checksum) {
        throw new Error('备份校验失败');
      }
      
      // 解析数据
      const data = JSON.parse(content);
      
      // 创建恢复点
      const restorePoint = new RestorePoint({
        backupId,
        memoryId: 'bulk_restore',
        timestamp: Date.now()
      });
      this.restorePoints.set(restorePoint.id, restorePoint);
      
      // 执行恢复
      const result = await this._executeRestore(data, options);
      
      // 更新统计
      this.stats.totalRestores++;
      this.stats.lastRestoreAt = Date.now();
      backup.status = BackupStatus.RESTORED;
      
      this.emit('restore:complete', { backupId, result });
      
      return {
        success: true,
        backupId,
        restoredMemories: result.restoredCount,
        restorePointId: restorePoint.id,
        timestamp: Date.now()
      };
      
    } catch (error) {
      this.emit('restore:failed', { backupId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  /**
   * 恢复到特定时间点
   * 
   * @param {Date} timestamp - 目标时间戳
   * @param {Object} options - 恢复选项
   * @returns {Object} 恢复结果
   */
  async restoreToTimestamp(timestamp, options = {}) {
    // 找到时间点之前的最新备份
    const backups = await this.listBackups({ status: BackupStatus.COMPLETED });
    const suitableBackups = backups.filter(b => b.createdAt <= timestamp);
    
    if (suitableBackups.length === 0) {
      return { success: false, error: '没有找到合适的备份' };
    }
    
    // 从最新到最旧尝试恢复
    for (const backup of suitableBackups) {
      try {
        return await this.restore(backup.id, options);
      } catch (e) {
        continue;
      }
    }
    
    return { success: false, error: '所有恢复尝试都失败' };
  }

  /**
   * 删除备份
   * 
   * @param {string} backupId - 备份 ID
   * @returns {Object} 删除结果
   */
  async deleteBackup(backupId) {
    const backup = this.backups.get(backupId);
    if (!backup) return { success: false, error: '备份不存在' };
    
    // 删除文件
    if (backup.filePath) {
      try {
        await fs.unlink(backup.filePath);
      } catch (e) {
        // 文件可能已不存在
      }
    }
    
    this.backups.delete(backupId);
    this.backupIndex.delete(backupId);
    await this._saveBackupIndex();
    
    this.emit('backup:deleted', { backupId });
    
    return { success: true, backupId };
  }

  /**
   * 验证备份完整性
   * 
   * @param {string} backupId - 备份 ID
   * @returns {Object} 验证结果
   */
  async verifyBackup(backupId) {
    const backup = this.backups.get(backupId);
    if (!backup) return { valid: false, error: '备份不存在' };
    
    if (backup.status !== BackupStatus.COMPLETED) {
      return { valid: false, error: '备份未完成' };
    }
    
    try {
      const content = await fs.readFile(backup.filePath);
      const checksum = crypto.createHash('sha256').update(content).digest('hex');
      
      if (checksum !== backup.checksum) {
        return { valid: false, error: '校验和不匹配，备份可能已损坏' };
      }
      
      // 尝试解析
      const decrypted = this.config.encryption ? this._decrypt(content) : content;
      const decompressed = this.config.compression ? await this._decompress(decrypted) : decrypted;
      JSON.parse(decompressed);
      
      return { valid: true, backupId, size: backup.metadata.size };
      
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 自动备份
  // ─────────────────────────────────────────────────────────────

  /**
   * 启动自动备份
   */
  startAutoBackup() {
    if (this.autoBackupTimer) return;
    
    this.autoBackupTimer = setInterval(async () => {
      try {
        await this.createBackup({ type: BackupType.INCREMENTAL });
      } catch (error) {
        this.emit('auto_backup:failed', { error: error.message });
      }
    }, this.config.backupInterval);
    
    this.emit('auto_backup:started', { interval: this.config.backupInterval });
  }

  /**
   * 停止自动备份
   */
  stopAutoBackup() {
    if (this.autoBackupTimer) {
      clearInterval(this.autoBackupTimer);
      this.autoBackupTimer = null;
      this.emit('auto_backup:stopped');
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 私有方法
  // ─────────────────────────────────────────────────────────────

  async _collectBackupData(memoryIds, backup) {
    // 这是一个抽象方法，需要由外部提供数据源
    // 返回格式: { memories: [...], version: '1.0' }
    const data = {
      version: '1.0',
      backupId: backup.id,
      backupType: backup.type,
      createdAt: Date.now(),
      memories: []
    };
    
    this.emit('backup:collecting', { backupId: backup.id });
    return data;
  }

  async _executeRestore(data, options) {
    let restoredCount = 0;
    
    if (data.memories && Array.isArray(data.memories)) {
      for (const memory of data.memories) {
        if (!options.targetMemoryIds || options.targetMemoryIds.includes(memory.id)) {
          // 这里应该调用实际的恢复逻辑
          restoredCount++;
        }
      }
    }
    
    return { restoredCount };
  }

  async _compress(data) {
    // 简单的 base64 编码作为压缩示例
    // 实际应该使用 zlib 或其他压缩库
    return Buffer.from(data).toString('base64');
  }

  async _decompress(data) {
    return Buffer.from(data, 'base64').toString('utf8');
  }

  _encrypt(content) {
    if (!this.config.encryptionKey) return content;
    const key = Buffer.from(this.config.encryptionKey, 'hex');
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    const encrypted = Buffer.concat([cipher.update(content), cipher.final()]);
    return Buffer.concat([iv, encrypted]).toString('base64');
  }

  _decrypt(content) {
    if (!this.config.encryptionKey) return content;
    const key = Buffer.from(this.config.encryptionKey, 'hex');
    const buffer = Buffer.from(content, 'base64');
    const iv = buffer.slice(0, 16);
    const encrypted = buffer.slice(16);
    const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
    return Buffer.concat([decipher.update(encrypted), decipher.final()]).toString('utf8');
  }

  _getLatestBackupId() {
    let latest = null;
    let latestTime = 0;
    for (const backup of this.backups.values()) {
      if (backup.status === BackupStatus.COMPLETED && backup.metadata.createdAt > latestTime) {
        latest = backup;
        latestTime = backup.metadata.createdAt;
      }
    }
    return latest?.id || null;
  }

  _getLatestBackup(type) {
    let latest = null;
    let latestTime = 0;
    for (const backup of this.backups.values()) {
      if (backup.status === BackupStatus.COMPLETED && 
          (!type || backup.type === type) && 
          backup.metadata.createdAt > latestTime) {
        latest = backup;
        latestTime = backup.metadata.createdAt;
      }
    }
    return latest;
  }

  async _cleanupOldBackups() {
    if (this.backups.size <= this.config.maxBackups) return;
    
    const backups = Array.from(this.backups.values())
      .filter(b => b.status === BackupStatus.COMPLETED)
      .sort((a, b) => b.metadata.createdAt - a.metadata.createdAt);
    
    const toDelete = backups.slice(this.config.maxBackups);
    for (const backup of toDelete) {
      await this.deleteBackup(backup.id);
    }
  }

  async _saveBackupIndex() {
    const indexPath = path.join(this.config.backupDir, 'backup_index.json');
    const index = {};
    for (const [id, backup] of this.backups) {
      index[id] = {
        id: backup.id,
        type: backup.type,
        status: backup.status,
        createdAt: backup.metadata.createdAt,
        size: backup.metadata.size
      };
    }
    await fs.writeFile(indexPath, JSON.stringify(index, null, 2));
  }

  async _loadBackupIndex() {
    const indexPath = path.join(this.config.backupDir, 'backup_index.json');
    try {
      const content = await fs.readFile(indexPath);
      const index = JSON.parse(content);
      for (const [id, data] of Object.entries(index)) {
        const backup = new BackupMetadata({ id, type: data.type, memoryIds: [] });
        backup.status = data.status;
        backup.metadata.createdAt = data.createdAt;
        backup.metadata.size = data.size;
        this.backups.set(id, backup);
        this.backupIndex.set(id, backup);
      }
    } catch (e) {
      // 索引文件不存在，从头开始
    }
  }

  /**
   * 获取备份统计
   */
  getStats() {
    return {
      ...this.stats,
      totalBackups: this.backups.size,
      completedBackups: Array.from(this.backups.values()).filter(b => b.status === BackupStatus.COMPLETED).length,
      autoBackupEnabled: !!this.autoBackupTimer
    };
  }
}

let _instance = null;
export function getMemoryBackup(options = {}) {
  if (!_instance) _instance = new MemoryBackup(options);
  return _instance;
}

export default MemoryBackup;
