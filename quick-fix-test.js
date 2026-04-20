// 快速修复验证 - 事务系统API测试

console.log('🔧 快速修复验证 - 事务系统API');
console.log('='.repeat(50));

async function testTransactionSystem() {
  try {
    // 导入事务系统
    const { TransactionManager } = await import('./src/transaction-system.js');
    
    console.log('✅ 1. 成功导入 TransactionManager');
    console.log(`   类名: ${TransactionManager.name}`);
    
    // 创建实例
    const tm = new TransactionManager({
      walDir: '/tmp/test-wal-quick',
      enableDeadlockDetection: false
    });
    
    console.log('✅ 2. 成功创建 TransactionManager 实例');
    
    // 测试正确的方法名
    const txId = await tm.begin();
    console.log(`✅ 3. 成功调用 tm.begin()，事务ID: ${txId}`);
    
    // 执行操作
    await tm.execute(txId, {
      type: 'insert',
      memoryId: 'test-memory-1',
      data: { content: '快速修复测试记忆' }
    });
    
    console.log('✅ 4. 成功调用 tm.execute()');
    
    // 提交事务
    const result = await tm.commit(txId);
    console.log(`✅ 5. 成功调用 tm.commit()，结果: ${result.success ? '成功' : '失败'}`);
    
    // 获取统计
    const stats = tm.getStats();
    console.log('✅ 6. 成功调用 tm.getStats()');
    console.log(`   事务统计: ${JSON.stringify(stats, null, 2)}`);
    
    // 关闭
    tm.close();
    console.log('✅ 7. 成功调用 tm.close()');
    
    console.log('\n🎯 事务系统API验证完成！');
    console.log('   正确的方法名: begin(), execute(), commit(), getStats(), close()');
    
    return true;
  } catch (error) {
    console.error('❌ 事务系统测试失败:', error.message);
    console.error('   堆栈:', error.stack);
    return false;
  }
}

// 运行测试
(async () => {
  console.log('🚀 开始事务系统API验证...\n');
  const success = await testTransactionSystem();
  
  console.log('\n' + '='.repeat(50));
  if (success) {
    console.log('✅ 事务系统修复成功！API调用正常！');
    console.log('🔧 只需要更新测试代码中的方法名即可');
  } else {
    console.log('❌ 事务系统需要进一步调试');
  }
  
  console.log('\n📋 正确的API调用方式:');
  console.log('   const tm = new TransactionManager(options);');
  console.log('   const txId = await tm.begin();');
  console.log('   await tm.execute(txId, operation);');
  console.log('   await tm.commit(txId);');
  console.log('   const stats = tm.getStats();');
  console.log('   tm.close();');
})();