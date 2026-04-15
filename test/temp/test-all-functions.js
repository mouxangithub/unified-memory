/**
 * 全面测试 Unified Memory 所有功能
 * 验证修复后的系统完整性
 */

import fs from 'fs/promises';
import path from 'path';

// 测试结果
const testResults = {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    details: []
};

function recordTest(name, passed, message = '') {
    testResults.total++;
    if (passed) {
        testResults.passed++;
        testResults.details.push({ name, status: '✅', message });
    } else {
        testResults.failed++;
        testResults.details.push({ name, status: '❌', message });
    }
}

function recordSkip(name, reason = '') {
    testResults.total++;
    testResults.skipped++;
    testResults.details.push({ name, status: '⏭', message: reason });
}

async function testFileExists(filePath) {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

async function testCoreFiles() {
    console.log('📁 测试核心文件存在...');
    
    const coreFiles = [
        'src/index.js',
        'src/storage.js',
        'src/config.js',
        'src/logger.js',
        'src/metrics.js',
        'src/transaction-manager.js',
        'src/vector_lancedb.js',
        'src/vector-chromadb-backend.js',
        'src/vector-store-abstract.js'
    ];
    
    for (const file of coreFiles) {
        const exists = await testFileExists(file);
        recordTest(`文件: ${file}`, exists, exists ? '存在' : '不存在');
    }
}

async function testImportModules() {
    console.log('\n🔧 测试模块导入...');
    
    try {
        // 测试事务管理器
        const { AtomicTransactionManager } = await import('./src/transaction-manager.js');
        recordTest('导入 AtomicTransactionManager', true, '成功导入');
        
        // 测试存储模块
        const storageModule = await import('./src/storage.js');
        const requiredExports = ['getAllMemories', 'addMemory', 'deleteMemory', 'saveMemories'];
        for (const exportName of requiredExports) {
            const hasExport = exportName in storageModule;
            recordTest(`存储模块导出: ${exportName}`, hasExport, hasExport ? '存在' : '不存在');
        }
        
        // 测试配置模块
        const configModule = await import('./src/config.js');
        recordTest('导入 config.js', !!configModule.config, '成功导入');
        
    } catch (error) {
        recordTest('模块导入测试', false, `导入失败: ${error.message}`);
    }
}

async function testTransactionManager() {
    console.log('\n⚡ 测试原子事务管理器...');
    
    try {
        const { AtomicTransactionManager } = await import('./src/transaction-manager.js');
        const txManager = new AtomicTransactionManager();
        
        // 测试开始事务
        const txId = await txManager.beginTransaction();
        recordTest('开始事务', !!txId, `事务ID: ${txId}`);
        
        // 测试准备 JSON 写入
        const testMemory = {
            id: 'test_' + Date.now(),
            text: '测试记忆',
            category: 'test',
            created_at: Date.now()
        };
        
        const tempFile = await txManager.prepareJsonWrite(txId, testMemory);
        const fileExists = await testFileExists(tempFile);
        recordTest('准备 JSON 写入', fileExists, `临时文件: ${tempFile}`);
        
        // 测试准备向量写入
        const testEmbedding = new Array(10).fill(0.1);
        const vectorResult = await txManager.prepareVectorWrite(txId, testMemory, testEmbedding);
        recordTest('准备向量写入', vectorResult === true, '向量准备成功');
        
        // 测试提交事务
        const commitResult = await txManager.commitTransaction(txId);
        recordTest('提交事务', commitResult === true, '事务提交成功');
        
        // 清理临时文件
        try {
            await fs.unlink(tempFile);
        } catch { /* 忽略 */ }
        
    } catch (error) {
        recordTest('事务管理器测试', false, `测试失败: ${error.message}`);
    }
}

async function testStorageFunctions() {
    console.log('\n💾 测试存储功能...');
    
    try {
        const storage = await import('./src/storage.js');
        
        // 测试获取所有记忆
        const memories = await storage.getAllMemories();
        recordTest('获取所有记忆', Array.isArray(memories), `找到 ${memories.length} 条记忆`);
        
        // 测试添加记忆
        const testMemory = {
            text: '功能测试记忆 ' + Date.now(),
            category: 'test',
            importance: 0.7,
            tags: ['test', 'functional']
        };
        
        const addedMemory = await storage.addMemory(testMemory);
        recordTest('添加记忆', !!addedMemory && !!addedMemory.id, `添加成功，ID: ${addedMemory?.id}`);
        
        // 测试获取单个记忆
        if (addedMemory) {
            const retrievedMemory = await storage.getMemory(addedMemory.id);
            recordTest('获取单个记忆', !!retrievedMemory, retrievedMemory ? '获取成功' : '获取失败');
            
            // 测试删除记忆
            const deleteResult = await storage.deleteMemory(addedMemory.id);
            recordTest('删除记忆', deleteResult === true, '删除成功');
        }
        
    } catch (error) {
        recordTest('存储功能测试', false, `测试失败: ${error.message}`);
    }
}

async function testVectorStore() {
    console.log('\n🔍 测试向量存储...');
    
    try {
        // 检查向量存储文件
        const vectorFile = 'src/vector_lancedb.js';
        const exists = await testFileExists(vectorFile);
        
        if (!exists) {
            recordSkip('向量存储测试', '向量存储文件不存在');
            return;
        }
        
        const { VectorMemory } = await import('./src/vector_lancedb.js');
        const vm = new VectorMemory();
        
        // 测试初始化
        try {
            await vm.initialize();
            recordTest('向量存储初始化', true, '初始化成功');
        } catch (error) {
            recordTest('向量存储初始化', false, `初始化失败: ${error.message}`);
            return;
        }
        
        // 测试 upsert
        const testId = 'vector_test_' + Date.now();
        try {
            await vm.upsert({
                id: testId,
                text: '向量测试文本',
                category: 'test',
                scope: 'USER'
            });
            recordTest('向量存储 upsert', true, 'upsert 成功');
        } catch (error) {
            recordTest('向量存储 upsert', false, `upsert 失败: ${error.message}`);
        }
        
        // 测试搜索（可能没有足够数据）
        try {
            const results = await vm.search('测试', 5);
            recordTest('向量搜索', Array.isArray(results), `搜索返回 ${results.length} 个结果`);
        } catch (error) {
            recordTest('向量搜索', false, `搜索失败: ${error.message}`);
        }
        
        // 测试删除
        try {
            await vm.delete(testId);
            recordTest('向量删除', true, '删除成功');
        } catch (error) {
            recordTest('向量删除', false, `删除失败: ${error.message}`);
        }
        
    } catch (error) {
        recordTest('向量存储测试', false, `测试失败: ${error.message}`);
    }
}

async function testConfigAndLogging() {
    console.log('\n⚙️ 测试配置和日志...');
    
    try {
        const configModule = await import('./src/config.js');
        const loggerModule = await import('./src/logger.js');
        
        // 测试配置
        recordTest('配置对象', !!configModule.config, '配置对象存在');
        
        // 测试日志函数
        recordTest('日志函数', typeof loggerModule.log === 'function', '日志函数存在');
        
        // 测试结构化日志
        if (loggerModule.structuredLog) {
            recordTest('结构化日志', typeof loggerModule.structuredLog === 'function', '结构化日志函数存在');
        }
        
    } catch (error) {
        recordTest('配置和日志测试', false, `测试失败: ${error.message}`);
    }
}

async function testDeploymentScripts() {
    console.log('\n🚀 测试部署脚本...');
    
    const scripts = [
        'deploy-atomic-fixes.sh',
        'scripts/deploy-fixes.sh'
    ];
    
    for (const script of scripts) {
        const exists = await testFileExists(script);
        if (exists) {
            // 检查脚本是否可执行
            try {
                const stats = await fs.stat(script);
                const isExecutable = !!(stats.mode & 0o111);
                recordTest(`部署脚本: ${script}`, true, isExecutable ? '可执行' : '不可执行');
            } catch {
                recordTest(`部署脚本: ${script}`, true, '存在');
            }
        } else {
            recordSkip(`部署脚本: ${script}`, '文件不存在');
        }
    }
}

async function testDocumentation() {
    console.log('\n📚 测试文档...');
    
    const docs = [
        'README.md',
        'docs/FIXES-AND-OPTIMIZATIONS.md',
        'CHANGELOG.md',
        'SKILL.md'
    ];
    
    for (const doc of docs) {
        const exists = await testFileExists(doc);
        recordTest(`文档: ${doc}`, exists, exists ? '存在' : '不存在');
    }
}

async function runAllTests() {
    console.log('🧪 开始全面测试 Unified Memory 系统\n');
    console.log('='.repeat(60));
    
    await testCoreFiles();
    await testImportModules();
    await testTransactionManager();
    await testStorageFunctions();
    await testVectorStore();
    await testConfigAndLogging();
    await testDeploymentScripts();
    await testDocumentation();
    
    // 输出结果
    console.log('\n' + '='.repeat(60));
    console.log('📊 测试结果总结');
    console.log('='.repeat(60));
    
    // 显示详细结果
    for (const detail of testResults.details) {
        console.log(`${detail.status} ${detail.name}`);
        if (detail.message) {
            console.log(`   ${detail.message}`);
        }
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('📈 统计信息:');
    console.log(`   总计测试: ${testResults.total}`);
    console.log(`   通过: ${testResults.passed}`);
    console.log(`   失败: ${testResults.failed}`);
    console.log(`   跳过: ${testResults.skipped}`);
    console.log(`   通过率: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
    console.log('='.repeat(60));
    
    if (testResults.failed > 0) {
        console.log('\n⚠️  有测试失败，请检查修复');
        return false;
    } else {
        console.log('\n🎉 所有测试通过！系统功能完整。');
        return true;
    }
}

// 运行所有测试
if (import.meta.url === `file://${process.argv[1]}`) {
    runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('测试运行失败:', error);
            process.exit(1);
        });
}

export default runAllTests;