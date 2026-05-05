/**
 * GBrain Web Server - GBrain Web 服务器
 * 
 * 提供 Web UI 和 API 服务
 * 
 * @module gbrain-web-server
 */

import http from 'http';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { createGBrainAPI } from './api/gbrain_api.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Web 服务器类
 */
export class GBrainWebServer {
  constructor(options = {}) {
    this.port = options.port || 3000;
    this.api = createGBrainAPI();
    this.server = null;
  }

  /**
   * 启动服务器
   */
  async start() {
    this.server = http.createServer(async (req, res) => {
      await this.handleRequest(req, res);
    });

    return new Promise((resolve) => {
      this.server.listen(this.port, () => {
        console.log(`GBrain Web Server running at http://localhost:${this.port}`);
        resolve(this);
      });
    });
  }

  /**
   * 处理请求
   */
  async handleRequest(req, res) {
    const url = new URL(req.url, `http://localhost:${this.port}`);
    const pathname = url.pathname;

    // 路由处理
    if (pathname === '/' || pathname === '/index.html') {
      await this.serveHTML(res);
    } else if (pathname === '/js/app.js') {
      await this.serveJS(res);
    } else if (pathname === '/css/style.css') {
      await this.serveCSS(res);
    } else if (pathname === '/api/gbrain/save') {
      await this.handleSaveMemory(req, res);
    } else if (pathname === '/api/gbrain/search') {
      await this.handleSearch(req, res);
    } else if (pathname === '/api/gbrain/entities') {
      await this.handleGetEntities(req, res);
    } else if (pathname === '/api/gbrain/stats') {
      await this.handleGetStats(req, res);
    } else if (pathname === '/api/gbrain/two-layer') {
      await this.handleCreateTwoLayer(req, res);
    } else if (pathname === '/api/gbrain/typed-links') {
      await this.handleAddTypedLink(req, res);
    } else if (pathname === '/api/gbrain/entities') {
      await this.handleDetectEntities(req, res);
    } else if (pathname === '/api/gbrain/directory') {
      await this.handleGetDirectory(req, res);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
    }
  }

  /**
   * 提供 HTML
   */
  async serveHTML(res) {
    try {
      const html = await fs.readFile(path.join(__dirname, 'gbrain_web_ui.html'), 'utf-8');
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(html);
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error loading HTML');
    }
  }

  /**
   * 提供 JavaScript
   */
  async serveJS(res) {
    try {
      const js = await fs.readFile(path.join(__dirname, 'gbrain_web_ui.js'), 'utf-8');
      res.writeHead(200, { 'Content-Type': 'application/javascript' });
      res.end(js);
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error loading JavaScript');
    }
  }

  /**
   * 提供 CSS
   */
  async serveCSS(res) {
    try {
      const css = await fs.readFile(path.join(__dirname, 'css', 'style.css'), 'utf-8');
      res.writeHead(200, { 'Content-Type': 'text/css' });
      res.end(css);
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error loading CSS');
    }
  }

  /**
   * 处理保存记忆
   */
  async handleSaveMemory(req, res) {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const { memory, context } = JSON.parse(body);
        this.api.saveMemory(
          { body: { memory, context } },
          {
            json: (data) => {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(data, null, 2));
            },
          }
        );
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }

  /**
   * 处理搜索
   */
  async handleSearch(req, res) {
    const query = new URL(req.url, `http://localhost:${this.port}`).searchParams.get('query');
    
    if (!query) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Missing query parameter' }));
      return;
    }

    this.api.searchMemory(
      { query, getQuery: () => `?query=${query}` },
      {
        json: (data) => {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(data, null, 2));
        },
      }
    );
  }

  /**
   * 处理获取实体
   */
  async handleGetEntities(req, res) {
    // 这里需要实现实际的实体获取逻辑
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: [],
    }));
  }

  /**
   * 处理获取统计
   */
  async handleGetStats(req, res) {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: {
        totalMemories: 0,
        totalEntities: 0,
        totalRelations: 0,
        cacheHitRate: '0%',
      },
    }));
  }

  /**
   * 处理创建两层页面
   */
  async handleCreateTwoLayer(req, res) {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        this.api.createTwoLayerPage(
          { body: data },
          {
            json: (response) => {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(response, null, 2));
            },
          }
        );
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }

  /**
   * 处理添加关系
   */
  async handleAddTypedLink(req, res) {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        this.api.addTypedLink(
          { body: data },
          {
            json: (response) => {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(response, null, 2));
            },
          }
        );
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }

  /**
   * 处理检测实体
   */
  async handleDetectEntities(req, res) {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        this.api.detectEntities(
          { body: data },
          {
            json: (response) => {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(response, null, 2));
            },
          }
        );
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }

  /**
   * 处理获取目录
   */
  async handleGetDirectory(req, res) {
    const url = new URL(req.url, `http://localhost:${this.port}`);
    const text = url.searchParams.get('text');
    
    if (!text) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Missing text parameter' }));
      return;
    }

    this.api.getDirectoryRecommendation(
      { query: { text }, getQuery: () => `?text=${text}` },
      {
        json: (response) => {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(response, null, 2));
        },
      }
    );
  }

  /**
   * 停止服务器
   */
  stop() {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          console.log(`GBrain Web Server stopped`);
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

/**
 * 创建 Web 服务器实例
 */
export function createGBrainWebServer(options = {}) {
  return new GBrainWebServer(options);
}
