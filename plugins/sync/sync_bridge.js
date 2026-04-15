#!/usr/bin/env node

/**
 * SyncBridge - 记忆系统同步桥梁
 * 单向同步：Workspace Memory (.md文件) → Unified Memory (向量存储)
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

class SyncBridge {
  constructor(options = {}) {
    this.workspacePath = options.workspacePath || '/root/.openclaw/workspace/memory';
    this.unifiedMemoryPath = options.unifiedMemoryPath || '/root/.openclaw/skills/unified-memory';
    this.syncStatePath = options.syncStatePath || '/root/.openclaw/workspace/memory-optimization/sync/sync_state.json';
    this.batchSize = options.batchSize || 50;
    this.dryRun = options.dryRun || false;
    
    // 支持的记忆类型
    this.memoryTypes = {
      'facts': 1,      // 事实型记忆
      'patterns': 2,   // 模式型记忆
      'skills': 3,     // 技能型记忆
      'cases': 4,      // 案例型记忆
      'events': 5,     // 事件型记忆
      'preferences': 6 // 偏好型记忆
    };
  }

  /**
   * 加载同步状态
   */
  async loadSyncState() {
    try {
      const data = await fs.readFile(this.syncStatePath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      // 文件不存在，返回默认状态
      return {
        lastSyncTime: null,
        lastSyncMtime: {},
        totalFilesProcessed: 0,
        totalMemoriesSynced: 0,
        errors: []
      };
    }
  }

  /**
   * 保存同步状态
   */
  async saveSyncState(state) {
    await fs.writeFile(
      this.syncStatePath,
      JSON.stringify(state, null, 2),
      'utf8'
    );
  }

  /**
   * 扫描Workspace Memory中的.md文件
   */
  async scanWorkspaceFiles() {
    const files = [];
    
    try {
      const entries = await fs.readdir(this.workspacePath, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.isFile() && entry.name.endsWith('.md')) {
          const filePath = path.join(this.workspacePath, entry.name);
          try {
            const stats = await fs.stat(filePath);
            files.push({
              name: entry.name,
              path: filePath,
              mtime: stats.mtime.getTime(),
              size: stats.size
            });
          } catch (err) {
            console.warn(`无法获取文件状态 ${filePath}:`, err.message);
          }
        }
      }
      
      // 按修改时间排序（最新的优先）
      files.sort((a, b) => b.mtime - a.mtime);
      
      return files;
    } catch (error) {
      console.error('扫描文件时出错:', error);
      return [];
    }
  }

  /**
   * 解析Markdown文件内容
   */
  async parseMarkdownFile(filePath) {
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const fileName = path.basename(filePath);
      
      // 提取文件中的记忆段落
      const memories = [];
      const lines = content.split('\n');
      let currentMemory = null;
      let currentContent = [];
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // 检测记忆段落开始（日期标题或重要标记）
        if (this.isMemoryStart(line, fileName)) {
          // 保存上一个记忆
          if (currentMemory && currentContent.length > 0) {
            memories.push(this.createMemoryObject(currentMemory, currentContent.join('\n'), fileName));
          }
          
          // 开始新记忆
          currentMemory = {
            title: line,
            startLine: i + 1,
            type: this.detectMemoryType(line, content)
          };
          currentContent = [line];
        } else if (currentMemory) {
          // 继续当前记忆内容
          currentContent.push(line);
          
          // 检测记忆段落结束
          if (this.isMemoryEnd(line) || i === lines.length - 1) {
            memories.push(this.createMemoryObject(currentMemory, currentContent.join('\n'), fileName));
            currentMemory = null;
            currentContent = [];
          }
        }
      }
      
      // 如果没有检测到结构化记忆，将整个文件作为一个记忆
      if (memories.length === 0 && content.trim().length > 0) {
        memories.push({
          content: content,
          source: `workspace:${fileName}`,
          type: 'events',
          metadata: {
            file: fileName,
            lines: '1-' + lines.length,
            extracted_at: new Date().toISOString()
          }
        });
      }
      
      return memories;
    } catch (error) {
      console.error(`解析文件 ${filePath} 时出错:`, error);
      return [];
    }
  }

  /**
   * 检测记忆段落开始
   */
  isMemoryStart(line, fileName) {
    // 日期标题模式：2026-03-30, 2026/03/30, 3月30日等
    if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(line)) return true;
    
    // 标题模式：## 标题，### 标题
    if (/^#{2,4}\s+.+/.test(line)) return true;
    
    // 重要事件标记：**事件**, ⚡, 🚀, ✅, ❌
    if (/(\*\*.+\*\*|⚡|🚀|✅|❌|🎯|⚠️|📝)/.test(line)) return true;
    
    // 文件名为特定格式（如考试记录）
    if (fileName.includes('clawvard') || fileName.includes('exam')) {
      if (/^(成绩|考试|练习|错误|教训):/.test(line)) return true;
    }
    
    return false;
  }

  /**
   * 检测记忆段落结束
   */
  isMemoryEnd(line) {
    // 空行或下一个记忆开始
    return line === '' || line === '---' || line === '***';
  }

  /**
   * 检测记忆类型
   */
  detectMemoryType(line, context) {
    const text = line.toLowerCase();
    const contextLower = context.toLowerCase();
    
    // 事实型：包含具体数据、数字、日期
    if (/\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(text) || 
        /(成绩|分数|得分|百分比)/.test(text) ||
        /(成本|价格|金额|预算)/.test(text)) {
      return 'facts';
    }
    
    // 模式型：包含模式、规律、趋势
    if (/(模式|规律|趋势|周期|重复)/.test(text) ||
        /(always|never|every|each)/.test(contextLower)) {
      return 'patterns';
    }
    
    // 技能型：包含技能、方法、技巧
    if (/(技能|方法|技巧|步骤|流程)/.test(text) ||
        /(how to|step by step|tutorial)/.test(contextLower)) {
      return 'skills';
    }
    
    // 案例型：包含案例、示例、故事
    if (/(案例|示例|例子|故事|经历)/.test(text) ||
        /(example|case study|story)/.test(contextLower)) {
      return 'cases';
    }
    
    // 偏好型：包含喜欢、不喜欢、偏好、习惯
    if (/(喜欢|不喜欢|偏好|习惯|常用)/.test(text) ||
        /(prefer|like|dislike|habit)/.test(contextLower)) {
      return 'preferences';
    }
    
    // 默认：事件型
    return 'events';
  }

  /**
   * 创建记忆对象
   */
  createMemoryObject(memoryInfo, content, fileName) {
    return {
      content: content,
      source: `workspace:${fileName}`,
      type: memoryInfo.type,
      metadata: {
        file: fileName,
        lines: `${memoryInfo.startLine}-${memoryInfo.startLine + content.split('\n').length - 1}`,
        title: memoryInfo.title,
        extracted_at: new Date().toISOString()
      }
    };
  }

  /**
   * 调用Unified Memory API存储记忆
   */
  async storeToUnifiedMemory(memory) {
    if (this.dryRun) {
      console.log(`[DRY RUN] 将存储记忆: ${memory.content.substring(0, 100)}...`);
      return { success: true, id: 'dry-run-id' };
    }
    
    try {
      // 构建存储命令
      const cmd = `cd ${this.unifiedMemoryPath} && node -e "
        import('./src/core/enhanced_memory_system.js').then(async (module) => {
          const memorySystem = module.default || module;
          const result = await memorySystem.storeMemory({
            content: ${JSON.stringify(memory.content)},
            source: ${JSON.stringify(memory.source)},
            type: ${JSON.stringify(memory.type)},
            metadata: ${JSON.stringify(memory.metadata)}
          });
          console.log(JSON.stringify(result));
        }).catch(err => {
          console.error(JSON.stringify({ error: err.message }));
        });
      "`;
      
      const { stdout, stderr } = await execAsync(cmd);
      
      if (stderr && !stderr.includes('ExperimentalWarning')) {
        console.error(`存储记忆时出错: ${stderr}`);
        return { success: false, error: stderr };
      }
      
      try {
        const result = JSON.parse(stdout.trim());
        return result;
      } catch (parseError) {
        // 如果不是JSON，可能是其他输出
        return { success: true, rawOutput: stdout };
      }
    } catch (error) {
      console.error(`执行存储命令时出错:`, error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 执行去重检查
   */
  async checkDuplicate(memory) {
    if (this.dryRun) {
      console.log(`[DRY RUN] 检查重复: ${memory.content.substring(0, 50)}...`);
      return { isDuplicate: false };
    }
    
    try {
      // 调用Unified Memory的去重功能
      const cmd = `cd ${this.unifiedMemoryPath} && node -e "
        import('./src/core/smart_deduplicator.js').then(async (module) => {
          const deduplicator = module.default || module;
          const result = await deduplicator.checkDuplicate({
            content: ${JSON.stringify(memory.content)},
            source: ${JSON.stringify(memory.source)},
            type: ${JSON.stringify(memory.type)}
          }, {
            sources: ['unified_memory'],
            crossSystemDedup: false
          });
          console.log(JSON.stringify(result));
        }).catch(err => {
          console.error(JSON.stringify({ error: err.message }));
        });
      "`;
      
      const { stdout, stderr } = await execAsync(cmd);
      
      if (stderr && !stderr.includes('ExperimentalWarning')) {
        console.error(`去重检查时出错: ${stderr}`);
        return { isDuplicate: false, error: stderr };
      }
      
      try {
        const result = JSON.parse(stdout.trim());
        return result;
      } catch (parseError) {
        return { isDuplicate: false, error: '解析响应失败' };
      }
    } catch (error) {
      console.error(`执行去重检查时出错:`, error);
      return { isDuplicate: false, error: error.message };
    }
  }

  /**
   * 执行同步
   */
  async sync(options = {}) {
    console.log('🚀 开始同步 Workspace Memory → Unified Memory');
    console.log(`工作目录: ${this.workspacePath}`);
    console.log(`批量大小: ${this.batchSize}`);
    console.log(`干运行模式: ${this.dryRun ? '是' : '否'}`);
    
    // 加载状态
    const state = await this.loadSyncState();
    const startTime = Date.now();
    
    // 扫描文件
    console.log('\n📁 扫描Workspace Memory文件...');
    const files = await this.scanWorkspaceFiles();
    console.log(`找到 ${files.length} 个.md文件`);
    
    if (files.length === 0) {
      console.log('❌ 没有找到可同步的文件');
      return state;
    }
    
    // 过滤需要同步的文件
    const filesToSync = files.filter(file => {
      const lastMtime = state.lastSyncMtime[file.name] || 0;
      return file.mtime > lastMtime;
    });
    
    console.log(`需要同步 ${filesToSync.length} 个文件（${files.length - filesToSync.length} 个已同步）`);
    
    if (filesToSync.length === 0) {
      console.log('✅ 所有文件都已同步，无需操作');
      return state;
    }
    
    // 处理文件
    let totalMemories = 0;
    let successfulMemories = 0;
    const errors = [];
    
    for (let i = 0; i < filesToSync.length; i++) {
      const file = filesToSync[i];
      console.log(`\n📄 处理文件 ${i+1}/${filesToSync.length}: ${file.name}`);
      
      try {
        // 解析文件
        const memories = await this.parseMarkdownFile(file.path);
        console.log(`  提取到 ${memories.length} 个记忆段落`);
        
        // 分批处理记忆
        for (let j = 0; j < memories.length; j += this.batchSize) {
          const batch = memories.slice(j, j + this.batchSize);
          
          for (const memory of batch) {
            totalMemories++;
            
            try {
              // 去重检查
              const dupResult = await this.checkDuplicate(memory);
              
              if (dupResult.isDuplicate) {
                console.log(`   ⏭️  跳过重复记忆: ${memory.content.substring(0, 50)}...`);
                continue;
              }
              
              // 存储到Unified Memory
              const storeResult = await this.storeToUnifiedMemory(memory);
              
              if (storeResult.success) {
                successfulMemories++;
                console.log(`   ✅  存储成功: ${memory.content.substring(0, 50)}...`);
              } else {
                errors.push({
                  file: file.name,
                  memory: memory.content.substring(0, 100),
                  error: storeResult.error
                });
                console.log(`   ❌  存储失败: ${storeResult.error}`);
              }
            } catch (memoryError) {
              errors.push({
                file: file.name,
                error: memoryError.message
              });
              console.log(`   ❌  处理记忆时出错: ${memoryError.message}`);
            }
          }
        }
        
        // 更新文件同步状态
        state.lastSyncMtime[file.name] = file.mtime;
        state.totalFilesProcessed++;
        
      } catch (fileError) {
        errors.push({
          file: file.name,
          error: fileError.message
        });
        console.log(`❌ 处理文件时出错: ${fileError.message}`);
      }
    }
    
    // 更新状态
    state.lastSyncTime = new Date().toISOString();
    state.totalMemoriesSynced += successfulMemories;
    state.errors = [...state.errors, ...errors];
    
    // 保存状态
    await this.saveSyncState(state);
    
    // 输出统计
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log('\n📊 同步完成！');
    console.log(`⏱️  耗时: ${duration}秒`);
    console.log(`📄 处理文件: ${filesToSync.length}/${files.length}`);
    console.log(`🧠 提取记忆: ${totalMemories}个`);
    console.log(`✅ 成功存储: ${successfulMemories}个`);
    console.log(`❌ 失败: ${errors.length}个`);
    console.log(`📈 累计同步记忆: ${state.totalMemoriesSynced}个`);
    
    if (errors.length > 0) {
      console.log('\n⚠️  错误详情:');
      errors.forEach((err, idx) => {
        console.log(`  ${idx+1}. ${err.file}: ${err.error}`);
      });
    }
    
    return state;
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const options = {
    dryRun: args.includes('--dry-run'),
    batchSize: parseInt(args.find(arg => arg.startsWith('--batch-size='))?.split('=')[1] || '50')
  };
  
  const syncBridge = new SyncBridge(options);
  syncBridge.sync().catch(error => {
    console.error('同步失败:', error);
    process.exit(1);
  });
}

export default SyncBridge;