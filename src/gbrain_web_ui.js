/**
 * GBrain Web UI - GBrain 前端界面
 * 
 * 提供 Web UI 用于管理 GBrain 功能
 * 
 * 功能：
 * - 记忆管理（创建、编辑、删除）
 * - 实体查看（人物、公司、项目等）
 * - 关系可视化（关系图）
 * - 两层页面编辑
 * - 搜索功能
 * - 性能监控
 * 
 * @module gbrain-web-ui
 */

// HTML 模板
export const HTML_TEMPLATE = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GBrain - Unified Memory v5</title>
  <style>
    :root {
      --primary-color: #3b82f6;
      --success-color: #10b981;
      --warning-color: #f59e0b;
      --danger-color: #ef4444;
      --bg-color: #f9fafb;
      --card-bg: #ffffff;
      --text-color: #1f2937;
      --border-color: #e5e7eb;
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      line-height: 1.6;
    }
    
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 20px;
    }
    
    header {
      background: var(--card-bg);
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    h1 {
      font-size: 24px;
      font-weight: 600;
      color: var(--primary-color);
    }
    
    .stats {
      display: flex;
      gap: 20px;
      margin-top: 10px;
      flex-wrap: wrap;
    }
    
    .stat-card {
      background: var(--bg-color);
      padding: 10px 15px;
      border-radius: 6px;
      font-size: 14px;
    }
    
    .stat-card strong {
      color: var(--primary-color);
    }
    
    .main-content {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    
    @media (max-width: 768px) {
      .main-content {
        grid-template-columns: 1fr;
      }
    }
    
    .card {
      background: var(--card-bg);
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .card h2 {
      font-size: 18px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border-color);
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      font-size: 14px;
    }
    
    .form-group input,
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-size: 14px;
    }
    
    .form-group textarea {
      min-height: 100px;
      resize: vertical;
    }
    
    .btn {
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .btn-primary {
      background: var(--primary-color);
      color: white;
    }
    
    .btn-primary:hover {
      background: #2563eb;
    }
    
    .btn-success {
      background: var(--success-color);
      color: white;
    }
    
    .btn-success:hover {
      background: #059669;
    }
    
    .btn-danger {
      background: var(--danger-color);
      color: white;
    }
    
    .btn-danger:hover {
      background: #dc2626;
    }
    
    .btn-sm {
      padding: 6px 12px;
      font-size: 12px;
    }
    
    .entity-list {
      list-style: none;
    }
    
    .entity-item {
      padding: 10px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .entity-item:last-child {
      border-bottom: none;
    }
    
    .entity-type {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .entity-type.person {
      background: #dbeafe;
      color: #1e40af;
    }
    
    .entity-type.company {
      background: #d1fae5;
      color: #065f46;
    }
    
    .entity-type.project {
      background: #fef3c7;
      color: #92400e;
    }
    
    .entity-type.concept {
      background: #e0e7ff;
      color: #3730a3;
    }
    
    .search-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
    }
    
    .search-bar input {
      flex: 1;
    }
    
    .result-item {
      padding: 10px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      margin-bottom: 10px;
    }
    
    .result-item h3 {
      font-size: 16px;
      margin-bottom: 5px;
    }
    
    .result-item p {
      font-size: 14px;
      color: #6b7280;
    }
    
    .two-layer-page {
      font-family: 'Georgia', serif;
    }
    
    .two-layer-page h1 {
      font-size: 28px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border-color);
    }
    
    .two-layer-page h2 {
      font-size: 20px;
      margin-top: 20px;
      margin-bottom: 10px;
      color: var(--primary-color);
    }
    
    .two-layer-page .timeline {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 2px solid var(--border-color);
    }
    
    .timeline-item {
      padding: 10px 0;
      border-bottom: 1px solid var(--border-color);
    }
    
    .timeline-date {
      font-weight: 600;
      color: var(--primary-color);
    }
    
    .timeline-source {
      font-size: 12px;
      color: #6b7280;
      font-style: italic;
    }
    
    .performance-metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-top: 15px;
    }
    
    .metric-card {
      background: var(--bg-color);
      padding: 15px;
      border-radius: 6px;
    }
    
    .metric-card h4 {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 5px;
    }
    
    .metric-card .value {
      font-size: 24px;
      font-weight: 600;
      color: var(--primary-color);
    }
    
    .loading {
      text-align: center;
      padding: 40px;
      color: #6b7280;
    }
    
    .error {
      background: #fef2f2;
      color: var(--danger-color);
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 15px;
    }
    
    .success {
      background: #f0fdf4;
      color: var(--success-color);
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 15px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🧠 GBrain - Unified Memory v5</h1>
      <div class="stats" id="stats">
        <div class="stat-card">总记忆：<strong id="totalMemories">0</strong></div>
        <div class="stat-card">实体数量：<strong id="totalEntities">0</strong></div>
        <div class="stat-card">关系数量：<strong id="totalRelations">0</strong></div>
        <div class="stat-card">缓存命中率：<strong id="cacheHitRate">0%</strong></div>
      </div>
    </header>
    
    <div class="main-content">
      <!-- 左侧：记忆管理 -->
      <div class="card">
        <h2>📝 创建记忆</h2>
        <div id="message"></div>
        
        <form id="memoryForm">
          <div class="form-group">
            <label for="memoryText">记忆文本</label>
            <textarea id="memoryText" required placeholder="输入记忆内容..."></textarea>
          </div>
          
          <div class="form-group">
            <label for="memoryType">类型</label>
            <select id="memoryType">
              <option value="fact">事实</option>
              <option value="event">事件</option>
              <option value="person">人物</option>
              <option value="company">公司</option>
              <option value="project">项目</option>
              <option value="concept">概念</option>
              <option value="original">原创</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="memoryTags">标签（逗号分隔）</label>
            <input type="text" id="memoryTags" placeholder="tag1, tag2, tag3">
          </div>
          
          <div class="form-group">
            <label for="sourceType">来源类型</label>
            <select id="sourceType">
              <option value="feishu">飞书</option>
              <option value="email">邮件</option>
              <option value="meeting">会议</option>
              <option value="user">用户</option>
            </select>
          </div>
          
          <button type="submit" class="btn btn-primary">保存记忆</button>
        </form>
      </div>
      
      <!-- 右侧：实体列表 -->
      <div class="card">
        <h2>👥 实体列表</h2>
        <div class="search-bar">
          <input type="text" id="searchInput" placeholder="搜索实体...">
          <button class="btn btn-primary" onclick="searchEntities()">搜索</button>
        </div>
        
        <ul class="entity-list" id="entityList">
          <li class="loading">加载中...</li>
        </ul>
      </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
      <h2>📊 性能指标</h2>
      <div class="performance-metrics" id="performanceMetrics">
        <div class="metric-card">
          <h4>查询缓存</h4>
          <div class="value" id="queryCacheSize">0</div>
        </div>
        <div class="metric-card">
          <h4>实体索引</h4>
          <div class="value" id="entityIndexSize">0</div>
        </div>
        <div class="metric-card">
          <h4>关系索引</h4>
          <div class="value" id="relationshipIndexSize">0</div>
        </div>
        <div class="metric-card">
          <h4>异步任务</h4>
          <div class="value" id="asyncTasks">0</div>
        </div>
      </div>
    </div>
  </div>
  
  <script src="/js/app.js"></script>
</body>
</html>
`;

/**
 * 前端应用逻辑
 */
export class GBrainWebUI {
  constructor(options = {}) {
    this.apiBase = options.apiBase || 'http://localhost:8080';
    this.element = options.element || document.body;
  }

  /**
   * 初始化
   */
  async init() {
    this.render();
    await this.loadStats();
    await this.loadEntities();
    this.setupEventListeners();
    this.startAutoRefresh();
  }

  /**
   * 渲染界面
   */
  render() {
    this.element.innerHTML = HTML_TEMPLATE;
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    // 记忆表单提交
    const form = this.element.querySelector('#memoryForm');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.saveMemory();
    });

    // 搜索输入
    const searchInput = this.element.querySelector('#searchInput');
    searchInput.addEventListener('keypress', async (e) => {
      if (e.key === 'Enter') {
        await this.searchEntities();
      }
    });
  }

  /**
   * 加载统计信息
   */
  async loadStats() {
    try {
      const response = await fetch(`${this.apiBase}/api/gbrain/stats`);
      const data = await response.json();
      
      if (data.success) {
        this.updateStats(data.data);
      }
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  }

  /**
   * 更新统计信息
   */
  updateStats(stats) {
    document.getElementById('totalMemories').textContent = stats.totalMemories || 0;
    document.getElementById('totalEntities').textContent = stats.totalEntities || 0;
    document.getElementById('totalRelations').textContent = stats.totalRelations || 0;
    document.getElementById('cacheHitRate').textContent = stats.cacheHitRate || '0%';
  }

  /**
   * 加载实体列表
   */
  async loadEntities() {
    try {
      const response = await fetch(`${this.apiBase}/api/gbrain/entities`);
      const data = await response.json();
      
      if (data.success) {
        this.renderEntities(data.data);
      }
    } catch (error) {
      console.error('加载实体列表失败:', error);
    }
  }

  /**
   * 渲染实体列表
   */
  renderEntities(entities) {
    const list = this.element.querySelector('#entityList');
    
    if (entities.length === 0) {
      list.innerHTML = '<li class="loading">暂无实体</li>';
      return;
    }
    
    list.innerHTML = entities.map(entity => `
      <li class="entity-item">
        <div>
          <span class="entity-type ${entity.type}">${entity.type}</span>
          <strong>${entity.name}</strong>
        </div>
        <div>
          <button class="btn btn-sm btn-primary" onclick="viewEntity('${entity.id}')">查看</button>
          <button class="btn btn-sm btn-danger" onclick="deleteEntity('${entity.id}')">删除</button>
        </div>
      </li>
    `).join('');
  }

  /**
   * 保存记忆
   */
  async saveMemory() {
    const form = this.element.querySelector('#memoryForm');
    const messageDiv = this.element.querySelector('#message');
    
    try {
      const memory = {
        text: document.getElementById('memoryText').value,
        type: document.getElementById('memoryType').value,
        tags: document.getElementById('memoryTags').value.split(',').map(t => t.trim()).filter(Boolean),
      };
      
      const context = {
        sourceType: document.getElementById('sourceType').value,
      };
      
      const response = await fetch(`${this.apiBase}/api/gbrain/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory, context }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        messageDiv.innerHTML = '<div class="success">✅ 记忆保存成功！</div>';
        form.reset();
        
        // 重新加载
        await this.loadStats();
        await this.loadEntities();
        
        // 清除消息
        setTimeout(() => {
          messageDiv.innerHTML = '';
        }, 3000);
      } else {
        messageDiv.innerHTML = `<div class="error">❌ 保存失败：${data.error}</div>`;
      }
    } catch (error) {
      messageDiv.innerHTML = `<div class="error">❌ 保存失败：${error.message}</div>`;
    }
  }

  /**
   * 搜索实体
   */
  async searchEntities() {
    const query = document.getElementById('searchInput').value;
    
    if (!query) {
      await this.loadEntities();
      return;
    }
    
    try {
      const response = await fetch(`${this.apiBase}/api/gbrain/search?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data.success) {
        this.renderSearchResults(data.data.results);
      }
    } catch (error) {
      console.error('搜索失败:', error);
    }
  }

  /**
   * 渲染搜索结果
   */
  renderSearchResults(results) {
    const list = this.element.querySelector('#entityList');
    
    if (results.length === 0) {
      list.innerHTML = '<li class="loading">未找到结果</li>';
      return;
    }
    
    list.innerHTML = results.map(result => `
      <li class="result-item">
        <h3>${result.text.substring(0, 100)}...</h3>
        <p>类型：${result.type} | 目录：${result.gbrain?.directory || '未知'}</p>
      </li>
    `).join('');
  }

  /**
   * 启动自动刷新
   */
  startAutoRefresh() {
    // 每 30 秒刷新一次
    setInterval(() => {
      this.loadStats();
      this.loadEntities();
    }, 30000);
  }
}

/**
 * 创建 Web UI 实例
 */
export function createGBrainWebUI(options = {}) {
  return new GBrainWebUI(options);
}
