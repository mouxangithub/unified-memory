/**
 * Two-Layer Memory Format - 两层页面格式处理
 * 
 * Compiled Truth (above) + Timeline (below)
 * 
 * 功能：
 * - 编译两层格式
 * - 解析两层格式
 * - 更新 Compiled Truth
 * - 添加 Timeline Entry
 * 
 * @module memory_two_layer
 */

import { Resolver, DirectoryType } from './resolver.js';

/**
 * 两层页面格式
 */
export const TwoLayerFormat = {
  /**
   * 创建新的两层页面
   */
  create({
    type = 'default',
    slug = 'unknown',
    tags = [],
    executiveSummary = '',
    state = {},
    assessment = '',
    openThreads = [],
    timeline = [],
    metadata = {},
  } = {}) {
    const parts = [];
    
    // 1. Frontmatter
    parts.push('---');
    parts.push(`type: ${type}`);
    parts.push(`slug: ${slug}`);
    if (tags.length > 0) {
      parts.push(`tags: [${tags.map(t => `"${t}"`).join(', ')}]`);
    }
    parts.push(`created: ${new Date().toISOString().split('T')[0]}`);
    parts.push('---');
    parts.push('');
    
    // 2. Compiled Truth (above the line)
    parts.push('## Executive Summary');
    parts.push(executiveSummary || '暂无摘要');
    parts.push('');
    
    if (Object.keys(state).length > 0) {
      parts.push('## State');
      for (const [key, value] of Object.entries(state)) {
        parts.push(`- **${key}**: ${value}`);
      }
      parts.push('');
    }
    
    if (assessment) {
      parts.push('## Assessment');
      parts.push(assessment);
      parts.push('');
    }
    
    if (openThreads.length > 0) {
      parts.push('## Open Threads');
      for (const thread of openThreads) {
        parts.push(`- [ ] ${thread.text} (priority: ${thread.priority || 'medium'}, due: ${thread.due || 'pending'})`);
      }
      parts.push('');
    }
    
    // 3. Separator
    parts.push('---');
    parts.push('');
    
    // 4. Timeline (below the line)
    parts.push('## Timeline');
    parts.push('');
    
    if (timeline.length > 0) {
      for (const entry of timeline) {
        parts.push(`- **${entry.date}** | ${entry.summary}`);
        if (entry.detail) {
          parts.push(`  ${entry.detail}`);
        }
        if (entry.source) {
          parts.push(`  [Source: ${entry.source}]`);
        }
        parts.push('');
      }
    } else {
      parts.push('暂无历史记录');
      parts.push('');
    }
    
    return parts.join('\n');
  },

  /**
   * 解析两层页面
   */
  parse(content) {
    const result = {
      type: 'default',
      slug: 'unknown',
      tags: [],
      executiveSummary: '',
      state: {},
      assessment: '',
      openThreads: [],
      timeline: [],
      metadata: {},
    };
    
    // Split by ---
    const parts = content.split('---');
    
    if (parts.length < 3) {
      return result; // 无法解析
    }
    
    // Parse frontmatter (between first two ---)
    const frontmatter = this.parseFrontmatter(parts[1]);
    result.type = frontmatter.type || 'default';
    result.slug = frontmatter.slug || 'unknown';
    result.tags = frontmatter.tags || [];
    
    // Parse body (after second ---)
    const body = parts[2];
    const lines = body.split('\n');
    
    let currentSection = null;
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // Section headers
      if (trimmed.startsWith('## ')) {
        currentSection = trimmed.substring(3).trim();
        continue;
      }
      
      // Timeline separator
      if (trimmed === '---') {
        currentSection = 'timeline';
        continue;
      }
      
      // Content based on section
      if (currentSection === 'Executive Summary') {
        result.executiveSummary += trimmed + ' ';
      } else if (currentSection === 'State') {
        const match = trimmed.match(/- \*\*(.+?)\*\*: (.+)/);
        if (match) {
          result.state[match[1]] = match[2];
        }
      } else if (currentSection === 'Assessment') {
        result.assessment += trimmed + '\n';
      } else if (currentSection === 'Open Threads') {
        const match = trimmed.match(/- \[ \] (.+) \(priority: (.+), due: (.+)\)/);
        if (match) {
          result.openThreads.push({
            text: match[1],
            priority: match[2],
            due: match[3],
          });
        }
      } else if (currentSection === 'Timeline') {
        const match = trimmed.match(/- \*\*(.+?)\*\* \| (.+)/);
        if (match) {
          result.timeline.push({
            date: match[1],
            summary: match[2],
            detail: '',
            source: '',
          });
        } else if (result.timeline.length > 0 && trimmed.startsWith('  ')) {
          // Detail or source line
          const lastEntry = result.timeline[result.timeline.length - 1];
          if (trimmed.includes('[Source:')) {
            lastEntry.source = trimmed.replace('[Source: ', '').replace(']', '');
          } else {
            lastEntry.detail = trimmed.trim();
          }
        }
      }
    }
    
    return result;
  },

  /**
   * 解析 frontmatter
   */
  parseFrontmatter(content) {
    const result = {};
    
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (trimmed.startsWith('type:')) {
        result.type = trimmed.substring(5).trim();
      } else if (trimmed.startsWith('slug:')) {
        result.slug = trimmed.substring(5).trim();
      } else if (trimmed.startsWith('tags:')) {
        const tagsMatch = trimmed.match(/\[(.*)\]/);
        if (tagsMatch) {
          result.tags = tagsMatch[1].split(',').map(t => t.trim().replace(/"/g, ''));
        }
      }
    }
    
    return result;
  },

  /**
   * 添加 Timeline Entry
   */
  addTimelineEntry(content, entry) {
    const parsed = this.parse(content);
    
    parsed.timeline.push({
      date: entry.date || new Date().toISOString().split('T')[0],
      summary: entry.summary || '',
      detail: entry.detail || '',
      source: entry.source || '',
    });
    
    return this.create(parsed);
  },

  /**
   * 更新 Compiled Truth
   */
  updateCompiledTruth(content, updates) {
    const parsed = this.parse(content);
    
    if (updates.executiveSummary) {
      parsed.executiveSummary = updates.executiveSummary;
    }
    
    if (updates.state) {
      parsed.state = { ...parsed.state, ...updates.state };
    }
    
    if (updates.assessment) {
      parsed.assessment = updates.assessment;
    }
    
    if (updates.openThreads) {
      parsed.openThreads = updates.openThreads;
    }
    
    return this.create(parsed);
  },
};

/**
 * 工具函数：从文本中提取两层格式内容
 */
export function extractTwoLayerContent(text) {
  const result = {
    executiveSummary: '',
    state: {},
    assessment: '',
    openThreads: [],
    timeline: [],
  };
  
  // 简单实现，后续可以扩展
  const lines = text.split('\n');
  
  let currentSection = null;
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    if (trimmed.startsWith('## ')) {
      currentSection = trimmed.substring(3).trim();
      continue;
    }
    
    if (currentSection === 'Executive Summary') {
      result.executiveSummary += trimmed + ' ';
    } else if (currentSection === 'State') {
      const match = trimmed.match(/- \*\*(.+?)\*\*: (.+)/);
      if (match) {
        result.state[match[1]] = match[2];
      }
    } else if (currentSection === 'Assessment') {
      result.assessment += trimmed + '\n';
    } else if (currentSection === 'Open Threads') {
      const match = trimmed.match(/- \[ \] (.+) \(priority: (.+), due: (.+)\)/);
      if (match) {
        result.openThreads.push({
          text: match[1],
          priority: match[2],
          due: match[3],
        });
      }
    } else if (currentSection === 'Timeline') {
      const match = trimmed.match(/- \*\*(.+?)\*\| (.+)/);
      if (match) {
        result.timeline.push({
          date: match[1],
          summary: match[2],
        });
      }
    }
  }
  
  return result;
}
