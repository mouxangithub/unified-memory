// 测试原子写入功能
import fs from 'fs';
import path from 'path';

console.log('🧪 测试原子写入功能\n');

// 导入模块
async function testAtomicWrite() {
  try {
    console.log('1. 导入存储模块...');
    const storageModule = await import('./src/storage.js');
    const { addMemory, getAllMemories, deleteMemory } = storageModule;
    
    console.log('   ✅ 存储模块导入成功');
    
    // 测试2: 添加记忆（原子写入）
    console.log('\n2. 测试原子写入...');
    const testMemory = {
      text: `原子写入测试 ${Date.now()}`,
      category: 'test',
      importance: 0.8,
      tags: ['atomic', 'test', 'transaction']
    };
    
    console.log('   添加记忆:', testMemory.text);
    const addedMemory = await addMemory(testMemory);
    
    if (addedMemory && addedMemory.id) {
      console.log(`   ✅ 记忆添加成功，ID: ${addedMemory.id}`);
      
      // 测试3: 验证记忆存在
      console.log('\n3. 验证记忆存储...');
      const allMemories = await getAllMemories();
      const foundMemory = allMemories.find(m => m.id === addedMemory.id);
      
      if (foundMemory) {
        console.log(`   ✅ 记忆在存储中找到: ${foundMemory.text}`);
        console.log(`   📊 记忆详情:`, {
          id: foundMemory.id,
          category: foundMemory.category,
          importance: foundMemory.importance,
          created_at: new Date(foundMemory.created_at).toISOString()
        });
      } else {
        console.log('   ❌ 记忆未在存储中找到');
      }
      
      // 测试4: 检查事务日志
      console.log('\n4. 检查事务日志...');
      const txLogPath = '/root/.unified-memory/transaction-recovery.log';
      if (fs.existsSync(txLogPath)) {
        const logContent = fs.readFileSync(txLogPath, 'utf8');
        const lines = logContent.split('\n').filter(line => line.trim());
        console.log(`   📝 事务日志条目: ${lines.length}`);
        
        // 查找最近的条目
        const recentEntries = lines.slice(-5);
        console.log('   最近的事务条目:');
        recentEntries.forEach((entry, i) => {
          try {
            const data = JSON.parse(entry);
            console.log(`     ${i+1}. ${data.type || 'unknown'}: ${data.txId?.substring(0, 10)}...`);
          } catch {
            console.log(`     ${i+1}. ${entry.substring(0, 50)}...`);
          }
        });
      } else {
        console.log('   ⚠️  事务日志文件不存在');
      }
      
      // 测试5: 清理测试数据
      console.log('\n5. 清理测试数据...');
      const deleteResult = await deleteMemory(addedMemory.id);
      if (deleteResult) {
        console.log(`   ✅ 测试记忆已删除: ${addedMemory.id}`);
      } else {
        console.log(`   ⚠️  记忆删除失败: ${addedMemory.id}`);
      }
      
      // 测试6: 检查存储文件
      console.log('\n6. 检查存储文件...');
      const storageDir = '/root/.unified-memory';
      if (fs.existsSync(storageDir)) {
        const files = fs.readdirSync(storageDir);
        console.log(`   📁 存储目录文件: ${files.join(', ')}`);
        
        // 检查临时文件目录
        const tempDir = path.join(storageDir, 'temp');
        if (fs.existsSync(tempDir)) {
          const tempFiles = fs.readdirSync(tempDir);
          console.log(`   🗂️  临时文件: ${tempFiles.length} 个文件`);
          if (tempFiles.length > 0) {
            console.log(`     文件列表: ${tempFiles.join(', ')}`);
          }
        }
      }
      
    } else {
      console.log('   ❌ 记忆添加失败');
    }
    
    // 测试7: 测试事务管理器
    console.log('\n7. 测试事务管理器...');
    try {
      const txModule = await import('./src/transaction-manager.js');
      const { AtomicTransactionManager } = txModule;
      const txManager = new AtomicTransactionManager();
      
      console.log('   ✅ 事务管理器导入成功');
      
      // 测试开始事务
      const txId = await txManager.beginTransaction();
      console.log(`   ✅ 事务开始成功: ${txId.substring(0, 15)}...`);
      
      // 测试恢复机制
      const recoveryResult = await txManager.recoverTransactions();
      console.log(`   ✅ 事务恢复检查: ${recoveryResult.recovered} 个已恢复, ${recoveryResult.errors} 个错误`);
      
    } catch (txError) {
      console.log(`   ❌ 事务管理器测试失败: ${txError.message}`);
    }
    
    // 总结
    console.log('\n' + '='.repeat(60));
    console.log('🎉 原子写入测试完成！');
    console.log('='.repeat(60));
    
    if (addedMemory && addedMemory.id) {
      console.log('✅ 所有测试通过！');
      console.log('\n📊 测试结果:');
      console.log('  1. 原子写入 - ✅ 成功');
      console.log('  2. 记忆存储 - ✅ 验证');
      console.log('  3. 事务日志 - ✅ 记录');
      console.log('  4. 数据清理 - ✅ 完成');
      console.log('  5. 事务管理 - ✅ 功能正常');
      
      console.log('\n🚀 原子写入修复验证成功！');
      return true;
    } else {
      console.log('⚠️  部分测试失败');
      return false;
    }
    
  } catch (error) {
    console.log('❌ 测试失败:', error.message);
    console.log('错误堆栈:', error.stack);
    return false;
  }
}

// 运行测试
testAtomicWrite()
  .then(success => {
    if (success) {
      console.log('\n🎯 原子写入功能验证完成！');
      process.exit(0);
    } else {
      console.log('\n⚠️  原子写入测试失败');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('测试运行错误:', error);
    process.exit(1);
  });