/**
 * Export Plugin - 数据导出插件
 * 支持多种格式导出记忆数据
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 导出格式
const ExportFormat = {
  JSON: 'json',
  CSV: 'csv',
  MARKDOWN: 'markdown',
  TEXT: 'text'
};

// 插件配置
let pluginConfig = {
  defaultFormat: ExportFormat.JSON,
  exportDir: path.join(__dirname, '..', 'exports'),
  includeMetadata: true
};

// JSON 导出
function exportAsJSON(memories) {
  return JSON.stringify(memories, null, 2);
}

// CSV 导出
function exportAsCSV(memories) {
  if (!memories || memories.length === 0) {
    return 'id,content,timestamp,tags\n';
  }
  
  const headers = ['id', 'content', 'timestamp', 'tags'];
  const rows = memories.map(m => {
    return headers.map(h => {
      let value = m[h] || '';
      if (h === 'content' || h === 'text') {
        value = String(value).replace(/"/g, '""');
        if (value.includes(',') || value.includes('\n')) {
          value = `"${value}"`;
        }
      }
      return value;
    }).join(',');
  });
  
  return [headers.join(','), ...rows].join('\n');
}

// Markdown 导出
function exportAsMarkdown(memories) {
  if (!memories || memories.length === 0) {
    return '# Memory Export\n\nNo memories found.\n';
  }
  
  const lines = ['# Memory Export', '', `Generated: ${new Date().toISOString()}`, '', `Total: ${memories.length} memories`, ''];
  
  memories.forEach((m, i) => {
    lines.push(`## ${i + 1}. ${m.id || 'Untitled'}`, '');
    if (m.content || m.text) {
      lines.push(m.content || m.text);
    }
    lines.push('');
    if (m.timestamp) {
      lines.push(`- Created: ${m.timestamp}`);
    }
    if (m.tags && m.tags.length > 0) {
      lines.push(`- Tags: ${m.tags.join(', ')}`);
    }
    if (m.metadata) {
      lines.push(`- Metadata: ${JSON.stringify(m.metadata)}`);
    }
    lines.push('');
    lines.push('---');
    lines.push('');
  });
  
  return lines.join('\n');
}

// Text 导出
function exportAsText(memories) {
  if (!memories || memories.length === 0) {
    return 'No memories found.\n';
  }
  
  const lines = ['=== Memory Export ===', `Generated: ${new Date().toISOString()}`, `Total: ${memories.length} memories`, ''];
  
  memories.forEach((m, i) => {
    lines.push(`[${i + 1}] ${m.id || 'Untitled'}`);
    if (m.content || m.text) {
      lines.push(m.content || m.text);
    }
    if (m.timestamp) {
      lines.push(`Created: ${m.timestamp}`);
    }
    lines.push('');
    lines.push('----------------------------------------');
    lines.push('');
  });
  
  return lines.join('\n');
}

// 导出器映射
const exporters = {
  json: exportAsJSON,
  csv: exportAsCSV,
  markdown: exportAsMarkdown,
  text: exportAsText
};

export default {
  name: 'export',
  version: '1.0.0',
  description: '支持多种格式导出记忆数据 (JSON, CSV, Markdown, Text)',
  author: 'unified-memory',
  dependencies: [],
  
  defaultConfig: {
    defaultFormat: ExportFormat.JSON,
    exportDir: path.join(__dirname, '..', 'exports'),
    includeMetadata: true
  },
  
  async initialize(context) {
    pluginConfig = { ...pluginConfig, ...context.config };
    
    if (!fs.existsSync(pluginConfig.exportDir)) {
      fs.mkdirSync(pluginConfig.exportDir, { recursive: true });
    }
    
    console.log(`📤 Export plugin initialized: ${pluginConfig.exportDir}`);
  },
  
  async destroy(context) {
    console.log(`📤 Export plugin shutting down`);
  },
  
  hooks: {
    afterLoad: async (memories, context) => {
      context.setState('lastLoadedMemories', memories);
      return memories;
    }
  }
};

export async function exportMemories(memories, format, options = {}) {
  const exporter = exporters[format];
  if (!exporter) {
    throw new Error(`Unknown export format: ${format}`);
  }
  
  const data = exporter(memories);
  
  if (options.filePath) {
    const dir = path.dirname(options.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(options.filePath, data, 'utf8');
    return { success: true, filePath: options.filePath, size: data.length };
  }
  
  return { success: true, data, size: data.length };
}

export async function exportToFile(memories, format, filename, options = {}) {
  const exportDir = options.exportDir || pluginConfig.exportDir;
  if (!fs.existsSync(exportDir)) {
    fs.mkdirSync(exportDir, { recursive: true });
  }
  
  const filePath = path.join(exportDir, filename);
  return exportMemories(memories, format, { ...options, filePath });
}

export function getSupportedFormats() {
  return Object.keys(ExportFormat).map(k => ({
    format: k,
    name: ExportFormat[k],
    extension: '.' + ExportFormat[k]
  }));
}
