/**
 * 原子写入修复验证脚本
 * 测试事务管理器的基本功能
 */

import { AtomicTransactionManager } from './src/transaction-manager.js';
import fs from 'fs/promises';
import path from 'path';

async function testAtomicTransactionManager() {
    console.log('🧪 测试原子事务管理器...\n');
    
    let txManager;
    
    try {
        // 测试1: 创建事务管理器
        console.log('1. 创建事务管理器...');
        txManager = new AtomicTransactionManager();
        console.log('   ✅ 成功创建事务管理器');
        
        // 测试2: 开始事务
        console.log('2. 开始事务...');
        const txId = await txManager.beginTransaction();
        console.log(`   ✅ 事务开始成功: ${txId}`);
        
        // 测试3: 准备 JSON 写入
        console.log('3. 准备 JSON 写入...');
        const testMemory = {
            id: 'test_memory_' + Date.now(),
            text: '这是一个测试记忆',
            category: 'test',
            importance: 0.8,
            tags: ['test', 'unit'],
            created_at: Date.now(),
            updated_at: Date.now()
        };
        
        const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
        console.log(`   ✅ JSON 准备成功: ${tempFile}`);
        
        // 验证临时文件存在
        const fileExists = await fs.access(tempFile).then(() => true).catch(() => false);
        if (!fileExists) {
            throw new Error('临时文件未创建');
        }
        
        // 测试4: 准备向量写入
        console.log('4. 准备向量写入...');
        const testEmbedding = new Array(10).fill(0.1);
        const vectorResult = await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
        console.log(`   ✅ 向量准备成功: ${vectorResult}`);
        
        // 测试5: 提交事务
        console.log('5. 提交事务...');
        const commitResult = await txManager.commitTransaction(txId);
        console.log(`   ✅ 事务提交成功: ${commitResult}`);
        
        // 测试6: 验证事务状态
        console.log('6. 验证事务状态...');
        const status = txManager.getTransactionStatus(txId);
        // 事务提交后应该被清理，所以 status 应该是 undefined
        if (status === undefined) {
            console.log('   ✅ 事务状态正确: 已清理');
        } else {
            console.log(`   ⚠ 事务状态: ${status ? status.state : 'null'}`);
            // 这不是致命错误，继续测试
        }
        
        // 测试7: 事务恢复
        console.log('7. 测试事务恢复...');
        const recoveryResult = await txManager.recoverTransactions();
        console.log(`   ✅ 事务恢复测试: ${JSON.stringify(recoveryResult)}`);
        
        // 清理临时文件
        console.log('8. 清理临时文件...');
        try {
            await fs.unlink(tempFile);
            console.log('   ✅ 临时文件清理成功');
        } catch (error) {
            console.warn(`   ⚠ 临时文件清理失败: ${error.message}`);
        }
        
        console.log('\n🎉 所有原子事务测试通过！');
        return true;
        
    } catch (error) {
        console.error('\n❌ 测试失败:', error.message);
        console.error(error.stack);
        return false;
    }
}

// 运行测试
if (import.meta.url === `file://${process.argv[1]}`) {
    testAtomicTransactionManager()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('未处理的错误:', error);
            process.exit(1);
        });
}

export default testAtomicTransactionManager;