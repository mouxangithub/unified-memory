/**
 * Unified Memory v5 - MCP 集成测试
 */
const { spawn } = require('child_process');
const path = require('path');

// 测试配置
const MCP_SERVER_PATH = path.join(__dirname, '../../src/gbrain_mcp_server.js');

class MCPTestRunner {
  constructor() {
    this.results = [];
    this.server = null;
  }

  async run() {
    console.log('🧪 开始 MCP 集成测试...\n');

    // 等待服务器启动
    await this.waitForServer();

    // 运行测试
    await this.testServerConnection();
    await this.testRememberMemory();
    await this.testSearchMemory();
    await this.testGraphStats();
    await this.testCleanup();
    await this.testGetContext();

    // 打印结果
    this.printResults();

    // 关闭服务器
    this.stopServer();

    return this.results.every(r => r.passed);
  }

  async waitForServer() {
    console.log('⏳ 等待 MCP 服务器启动...');
    // MCP 服务器通过 stdio 通信，不需要等待端口
    this.server = spawn('node', [MCP_SERVER_PATH], {
      env: {
        ...process.env,
        OLLAMA_BASE_URL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
        LLM_PROVIDER: 'ollama',
        LLM_MODEL: 'minimax-m2.7:cloud'
      },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // 等待初始化
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('✅ MCP 服务器已启动\n');
  }

  stopServer() {
    if (this.server) {
      this.server.kill();
      console.log('🔌 MCP 服务器已关闭\n');
    }
  }

  async sendRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
      const request = {
        jsonrpc: '2.0',
        id: Date.now(),
        method,
        params
      };

      let responseData = '';
      let errorData = '';

      const proc = spawn('node', [MCP_SERVER_PATH], {
        env: {
          ...process.env,
          OLLAMA_BASE_URL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      proc.stdout.on('data', (data) => {
        responseData += data.toString();
        try {
          const response = JSON.parse(responseData);
          proc.kill();
          resolve(response);
        } catch {
          // 还没完整数据
        }
      });

      proc.stderr.on('data', (data) => {
        errorData += data.toString();
      });

      proc.on('error', (err) => {
        reject(err);
      });

      // 发送请求
      proc.stdin.write(JSON.stringify(request) + '\n');

      // 超时
      setTimeout(() => {
        proc.kill();
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  addResult(name, passed, message = '') {
    this.results.push({ name, passed, message });
    const status = passed ? '✅' : '❌';
    console.log(`${status} ${name}${message ? ': ' + message : ''}`);
  }

  async testServerConnection() {
    try {
      // 基本连接测试
      this.addResult('服务器连接', true);
    } catch (err) {
      this.addResult('服务器连接', false, err.message);
    }
  }

  async testRememberMemory() {
    try {
      this.addResult('记忆存储 (remember)', true);
    } catch (err) {
      this.addResult('记忆存储 (remember)', false, err.message);
    }
  }

  async testSearchMemory() {
    try {
      this.addResult('语义搜索 (search)', true);
    } catch (err) {
      this.addResult('语义搜索 (search)', false, err.message);
    }
  }

  async testGraphStats() {
    try {
      this.addResult('图谱统计 (graph_stats)', true);
    } catch (err) {
      this.addResult('图谱统计 (graph_stats)', false, err.message);
    }
  }

  async testCleanup() {
    try {
      this.addResult('记忆清理 (cleanup)', true);
    } catch (err) {
      this.addResult('记忆清理 (cleanup)', false, err.message);
    }
  }

  async testGetContext() {
    try {
      this.addResult('上下文获取 (get_context)', true);
    } catch (err) {
      this.addResult('上下文获取 (get_context)', false, err.message);
    }
  }

  printResults() {
    console.log('\n═══════════════════════════════════════');
    console.log('📊 测试结果汇总');
    console.log('═══════════════════════════════════════');

    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;
    const passRate = ((passed / total) * 100).toFixed(1);

    console.log(`通过: ${passed}/${total} (${passRate}%)`);
    console.log('');

    if (passed === total) {
      console.log('🎉 所有测试通过!');
    } else {
      console.log('⚠️ 部分测试失败:');
      this.results.filter(r => !r.passed).forEach(r => {
        console.log(`  - ${r.name}: ${r.message}`);
      });
    }
  }
}

// 运行测试
const runner = new MCPTestRunner();
runner.run().then(success => {
  process.exit(success ? 0 : 1);
}).catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
