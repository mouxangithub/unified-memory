/**
 * 简单的原子事务测试
 */

import { AtomicTransactionManager } from '../src/transaction-manager.js';
import fs from 'fs/promises';
import path from 'path';

async function runTests() {
  console.log('🧪 开始原子事务测试\n');
  
  let passed = 0;
  let failed = 0;
  
  // 测试 1: 创建事务管理器
  try {
    const txManager = new AtomicTransactionManager();
    console.log('✅ 测试 1: 成功创建事务管理器');
    passed++;
  } catch (error) {
    console.log('❌ 测试 1: 创建事务管理器失败', error.message);
    failed++;
  }
  
  // 测试 2: 开始事务
  try {
    const txManager = new AtomicTransactionManager();
    const txId = await txManager.beginTransaction();
    
    if (txId && txId.startsWith('tx_')) {
      console.log('✅ 测试 2: 成功开始事务', txId);
      passed++;
    } else {
      throw new Error('事务ID格式不正确');
    }
  } catch (error) {
    console.log('❌ 测试 2: 开始事务失败', error.message);
    failed++;
  }
  
  // 测试 3: 准备 JSON 写入
  try {
    const txManager = new AtomicTransactionManager();
    const txId = await txManager.beginTransaction();
    
    const testMemory = {
      id: 'test_memory_123',
      text: '测试记忆',
      category: 'test',
      created_at: Date.now()
    };
    
    const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
    
    // 验证临时文件存在
    const fileExists = await fs.access(tempFile).then(() => true).catch(() => false);
    
    if (fileExists && tempFile.includes('_json.tmp')) {
      console.log('✅ 测试 3: 成功准备 JSON 写入', tempFile);
      passed++;
      
      // 清理临时文件
      await fs.unlink(tempFile).catch(() => {});
    } else {
      throw new Error('临时文件创建失败');
    }
  } catch (error) {
    console.log('❌ 测试 3: 准备 JSON 写入失败', error.message);
    failed++;
  }
  
  // 测试 4: 准备向量写入
  try {
    const txManager = new AtomicTransactionManager();
    const txId = await txManager.beginTransaction();
    
    const testMemory = {
      id: 'test_memory_456',
      text: '测试向量记忆'
    };
    
    const testEmbedding = new Array(10).fill(0.1); // 简化的 embedding
    
    const result = await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
    
    if (result === true) {
      console.log('✅ 测试 4: 成功准备向量写入');
      passed++;
    } else {
      throw new Error('向量准备返回非 true 值');
    }
  } catch (error) {
    console.log('❌ 测试 4: 准备向量写入失败', error.message);
    failed++;
  }
  
  // 测试 5: 提交事务
  try {
    const txManager = new AtomicTransactionManager();
    const txId = await txManager.beginTransaction();
    
    const testMemory = {
      id: 'test_memory_789',
      text: '提交测试记忆'
    };
    
    // 准备写入
    await txManager.prepareJsonWrite(txId, testMemory);
    await txManager.prepareVectorWrite(txId, testMemory, new Array(10).fill(0.1));
    
    // 提交事务
    const result = await txManager.commitTransaction(txId);
    
    if (result === true) {
      console.log('✅ 测试 5: 成功提交事务');
      passed++;
    } else {
      throw new Error('事务提交返回非 true 值');
    }
  } catch (error) {
    console.log('❌ 测试 5: 提交事务失败', error.message);
    failed++;
  }
  
  // 测试 6: 事务恢复
  try {
    const txManager = new AtomicTransactionManager();
    
    // 创建一些未完成的事务日志
    const recoveryLogPath = path.join(process.env.HOME || '/root', '.unified-memory', 'transaction-recovery.log');
    
    // 写入测试日志
    const testLogs = [
      { timestamp: new Date().toISOString(), transactionId: 'test_recovery_1', action: 'BEGIN', details: {} },
      { timestamp: new Date().toISOString(), transactionId: 'test_recovery_1', action: 'PREPARE_JSON', details: {} }
    ];
    
    for (const log of testLogs) {
      await fs.appendFile(recoveryLogPath, JSON.stringify(log) + '\n', 'utf8');
    }
    
    // 执行恢复
    const recoveryResult = await txManager.recoverTransactions();
    
    if (typeof recoveryResult.recovered === 'number' && typeof recoveryResult.errors === 'number') {
      console.log('✅ 测试 6: 成功执行事务恢复', recoveryResult);
      passed++;
    } else {
      throw new Error('恢复结果格式不正确');
    }
    
    // 清理日志文件
    await fs.unlink(recoveryLogPath).catch(() => {});
    
  } catch (error) {
    console.log('❌ 测试 6: 事务恢复失败', error.message);
    failed++;
  }
  
  // 测试 7: 向量存储抽象层
  try {
    // 检查文件是否存在
    const vectorStorePath = path.join(process.cwd(), 'src/vector-store-abstract.js');
    const fileExists = await fs.access(vectorStorePath).then(() => true).catch(() => false);
    
    if (fileExists) {
      console.log('✅ 测试 7: 向量存储抽象层文件存在');
      passed++;
    } else {
      throw new Error('向量存储抽象层文件不存在');
    }
  } catch (error) {
    console.log('❌ 测试 7: 向量存储抽象层检查失败', error.message);
    failed++;
  }
  
  // 测试 8: ChromaDB 后端
  try {
    const chromaDBPath = path.join(process.cwd(), 'src/vector-chromadb-backend.js');
    const fileExists = await fs.access(chromaDBPath).then(() => true).catch(() => false);
    
    if (fileExists) {
      console.log('✅ 测试 8: ChromaDB 后端文件存在');
      passed++;
    } else {
      throw new Error('ChromaDB 后端文件不存在');
    }
  } catch (error) {
    console.log('❌ 测试 8: ChromaDB 后端检查失败', error.message);
    failed++;
  }
  
  // 总结
  console.log('\n' + '='.repeat(50));
  console.log('📊 测试结果总结:');
  console.log(`   通过: ${passed}`);
  console.log(`   失败: ${failed}`);
  console.log(`   总计: ${passed + failed}`);
  console.log(`   通过率: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);
  console.log('='.repeat(50));
  
  if (failed > 0) {
    console.log('\n⚠️  有测试失败，请检查修复');
    process.exit(1);
  } else {
    console.log('\n🎉 所有测试通过！');
    process.exit(0);
  }
}

// 运行测试
runTests().catch(error => {
  console.error('测试运行失败:', error);
  process.exit(1);
});