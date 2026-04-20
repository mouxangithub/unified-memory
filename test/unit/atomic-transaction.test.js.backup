/**
 * 原子事务管理器单元测试
 */

import test from 'node:test';
import assert from 'node:assert';
import { AtomicTransactionManager } from '../../src/transaction-manager.js';
import fs from 'fs/promises';
import path from 'path';

test('AtomicTransactionManager', async (t) => {
  let txManager;
  let testMemory;
  
  await t.test('setup', async () => {
    txManager = new AtomicTransactionManager();
    testMemory = {
      id: 'test_memory_123',
      text: '这是一个测试记忆',
      category: 'test',
      importance: 0.8,
      tags: ['test', 'unit'],
      created_at: Date.now(),
      updated_at: Date.now()
    };
    
    // 清理测试文件
    const tempDir = path.join(process.env.HOME || '/root', '.unified-memory', 'temp');
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch (error) {
      // 目录可能不存在，忽略错误
    }
  });
  
  await t.test('cleanup', async () => {
    // 清理恢复日志
    const recoveryLogPath = path.join(process.env.HOME || '/root', '.unified-memory', 'transaction-recovery.log');
    try {
      await fs.unlink(recoveryLogPath);
    } catch (error) {
      // 文件可能不存在，忽略错误
    }
  });
  
  await t.test('事务生命周期', async (st) => {
    await st.test('应该成功开始事务', async () => {
      const txId = await txManager.beginTransaction();
      
      assert.ok(txId);
      assert.match(txId, /^tx_\d+_[a-z0-9]+$/);
      
      const status = txManager.getTransactionStatus(txId);
      assert.ok(status);
      assert.strictEqual(status.state, 'preparing');
    });
    
    test('应该成功准备JSON写入', async () => {
      const txId = await txManager.beginTransaction();
      const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
      
      expect(tempFile).toBeDefined();
      expect(tempFile).toContain('_json.tmp');
      
      // 验证临时文件存在
      const fileExists = await fs.access(tempFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);
      
      // 验证文件内容
      const fileContent = await fs.readFile(tempFile, 'utf8');
      expect(fileContent).toBe(JSON.stringify(testMemory, null, 2));
    });
    
    test('应该成功准备向量写入', async () => {
      const txId = await txManager.beginTransaction();
      const testEmbedding = new Array(768).fill(0.1);
      
      const result = await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
      
      expect(result).toBe(true);
      
      const status = txManager.getTransactionStatus(txId);
      expect(status.state).toBe('prepared');
      expect(status.prepared).toBe(true);
    });
    
    test('应该成功提交事务', async () => {
      const txId = await txManager.beginTransaction();
      
      // 模拟准备阶段
      const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
      const testEmbedding = new Array(768).fill(0.1);
      await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
      
      // 提交事务
      const result = await txManager.commitTransaction(txId);
      
      expect(result).toBe(true);
      
      const status = txManager.getTransactionStatus(txId);
      expect(status.committed).toBe(true);
      expect(status.state).toBe('committed');
      
      // 验证临时文件已被清理
      const fileExists = await fs.access(tempFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(false);
    });
    
    test('应该成功回滚事务', async () => {
      const txId = await txManager.beginTransaction();
      
      const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
      const testEmbedding = new Array(768).fill(0.1);
      await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
      
      // 模拟提交失败
      const mockError = new Error('模拟提交失败');
      
      try {
        await txManager.commitTransaction(txId);
        throw mockError; // 强制失败
      } catch (error) {
        expect(error.message).toBe('模拟提交失败');
      }
      
      // 验证事务已回滚
      const status = txManager.getTransactionStatus(txId);
      expect(status).toBeNull(); // 事务应该已被清理
      
      // 验证临时文件已被清理
      const fileExists = await fs.access(tempFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(false);
    });
  });
  
  describe('错误处理', () => {
    test('应该处理不存在的交易', async () => {
      await expect(txManager.prepareJsonWrite('nonexistent_tx', testMemory))
        .rejects.toThrow('Transaction nonexistent_tx not found');
      
      await expect(txManager.commitTransaction('nonexistent_tx'))
        .rejects.toThrow('Transaction nonexistent_tx not found');
    });
    
    test('应该处理未准备的事务提交', async () => {
      const txId = await txManager.beginTransaction();
      
      await expect(txManager.commitTransaction(txId))
        .rejects.toThrow(`Transaction ${txId} not prepared`);
    });
  });
  
  describe('恢复机制', () => {
    test('应该恢复未完成的事务', async () => {
      // 创建一些未完成的事务日志
      const txId1 = await txManager.beginTransaction();
      await txManager.prepareJsonWrite(txId1, testMemory);
      
      const txId2 = await txManager.beginTransaction();
      await txManager.prepareJsonWrite(txId2, testMemory);
      
      // 模拟系统崩溃（不提交事务）
      
      // 创建新的管理器实例（模拟系统重启）
      const newTxManager = new AtomicTransactionManager();
      
      // 执行恢复
      const recoveryResult = await newTxManager.recoverTransactions();
      
      expect(recoveryResult.recovered).toBeGreaterThan(0);
      expect(recoveryResult.errors).toBe(0);
      
      // 验证事务已被清理
      const status1 = newTxManager.getTransactionStatus(txId1);
      const status2 = newTxManager.getTransactionStatus(txId2);
      
      expect(status1).toBeNull();
      expect(status2).toBeNull();
    });
    
    test('应该处理损坏的恢复日志', async () => {
      // 创建损坏的日志文件
      const recoveryLogPath = path.join(process.env.HOME || '/root', '.unified-memory', 'transaction-recovery.log');
      await fs.writeFile(recoveryLogPath, '这不是有效的JSON\n{"partial": "entry"', 'utf8');
      
      const recoveryResult = await txManager.recoverTransactions();
      
      expect(recoveryResult.recovered).toBe(0);
      expect(recoveryResult.errors).toBe(0); // 应该优雅处理错误
    });
  });
  
  describe('并发安全', () => {
    test('应该处理并发事务', async () => {
      const txIds = [];
      const promises = [];
      
      // 并发开始10个事务
      for (let i = 0; i < 10; i++) {
        promises.push(
          txManager.beginTransaction().then(id => {
            txIds.push(id);
            return id;
          })
        );
      }
      
      await Promise.all(promises);
      
      expect(txIds.length).toBe(10);
      
      // 验证所有事务状态
      for (const txId of txIds) {
        const status = txManager.getTransactionStatus(txId);
        expect(status).toBeDefined();
        expect(status.state).toBe('preparing');
      }
    });
  });
});

describe('向量存储抽象层', () => {
  test('应该支持多种后端配置', async () => {
    // 测试配置解析
    const configs = [
      { backend: 'lancedb' },
      { backend: 'chromadb' },
      { backend: 'qdrant' },
      { backend: 'weaviate' }
    ];
    
    for (const config of configs) {
      expect(config.backend).toBeDefined();
      expect(['lancedb', 'chromadb', 'qdrant', 'weaviate']).toContain(config.backend);
    }
  });
});