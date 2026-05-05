/**
 * Source Attribution - 来源标注
 * 
 * 为每条记忆添加来源信息
 * 
 * 功能：
 * - 格式化来源
 * - 验证来源
 * - 来源引用
 * 
 * @module source_attribution
 */

/**
 * 来源类型
 */
export const SourceType = {
  USER: 'user',              // 用户直接提供
  FEISHU: 'feishu',          // 飞书
  EMAIL: 'email',            // 邮件
  MEETING: 'meeting',        // 会议
  WECHAT: 'wechat',          // 微信
  WHATSAPP: 'whatsapp',      // WhatsApp
  SLACK: 'slack',            // Slack
  WEBSITE: 'website',        // 网站
  DOCUMENT: 'document',      // 文档
  API: 'api',                // API
  MANUAL: 'manual',          // 手动输入
};

/**
 * 来源格式
 */
export const SourceFormat = {
  [SourceType.USER]: 'User',
  [SourceType.FEISHU]: 'Feishu',
  [SourceType.EMAIL]: 'Email',
  [SourceType.MEETING]: 'Meeting',
  [SourceType.WECHAT]: 'WeChat',
  [SourceType.WHATSAPP]: 'WhatsApp',
  [SourceType.SLACK]: 'Slack',
  [SourceType.WEBSITE]: 'Website',
  [SourceType.DOCUMENT]: 'Document',
  [SourceType.API]: 'API',
  [SourceType.MANUAL]: 'Manual',
};

/**
 * 来源对象
 */
export class Source {
  constructor(options = {}) {
    this.type = options.type || SourceType.USER;
    this.channel = options.channel || '';
    this.timestamp = options.timestamp || new Date();
    this.author = options.author || '';
    this.url = options.url || '';
    this.metadata = options.metadata || {};
  }

  /**
   * 格式化来源字符串
   */
  format() {
    const parts = [];
    
    // 类型
    parts.push(SourceFormat[this.type] || this.type);
    
    // 渠道
    if (this.channel) {
      parts.push(this.channel);
    }
    
    // 作者
    if (this.author) {
      parts.push(this.author);
    }
    
    // 时间
    const dateStr = this.timestamp.toISOString().split('T')[0];
    const timeStr = this.timestamp.toTimeString().split(' ')[0];
    parts.push(`${dateStr} ${timeStr}`);
    
    return `[Source: ${parts.join(', ')}]`;
  }

  /**
   * 格式化来源（用于 Timeline）
   */
  formatTimeline() {
    const parts = [];
    
    // 类型
    parts.push(SourceFormat[this.type] || this.type);
    
    // 渠道
    if (this.channel) {
      parts.push(this.channel);
    }
    
    // 时间
    const dateStr = this.timestamp.toISOString().split('T')[0];
    const timeStr = this.timestamp.toTimeString().split(' ')[0];
    parts.push(`${dateStr} ${timeStr}`);
    
    return `[Source: ${parts.join(', ')}]`;
  }

  /**
   * 从字符串解析来源
   */
  static parse(str) {
    const match = str.match(/\[Source:\s*(.+?)\]/);
    if (!match) {
      return null;
    }
    
    const content = match[1];
    const parts = content.split(',').map(p => p.trim());
    
    if (parts.length < 1) {
      return null;
    }
    
    // 解析类型
    const type = parts[0] || SourceType.USER;
    
    // 解析其他字段
    const channel = parts[1] || '';
    const author = parts[2] || '';
    const timestampStr = parts[3] || '';
    
    let timestamp = new Date();
    if (timestampStr) {
      const [date, time] = timestampStr.split(' ');
      timestamp = new Date(`${date}T${time}`);
    }
    
    return new Source({
      type,
      channel,
      author,
      timestamp,
    });
  }

  /**
   * 创建标准来源
   */
  static createStandard(options = {}) {
    return new Source({
      type: options.type || SourceType.USER,
      channel: options.channel || '',
      timestamp: options.timestamp || new Date(),
      author: options.author || '',
    });
  }
}

/**
 * 来源管理器
 */
export class SourceManager {
  constructor() {
    this.sources = new Map();
  }

  /**
   * 添加来源
   */
  add(memoryId, source) {
    if (!this.sources.has(memoryId)) {
      this.sources.set(memoryId, []);
    }
    
    this.sources.get(memoryId).push({
      source,
      createdAt: Date.now(),
    });
  }

  /**
   * 获取来源
   */
  get(memoryId) {
    return this.sources.get(memoryId) || [];
  }

  /**
   * 格式化来源字符串
   */
  format(memoryId) {
    const sources = this.get(memoryId);
    if (sources.length === 0) {
      return '';
    }
    
    const parts = sources.map(s => s.source.format());
    return parts.join(' | ');
  }

  /**
   * 验证来源
   */
  validate(memoryId) {
    const sources = this.get(memoryId);
    
    if (sources.length === 0) {
      return {
        valid: false,
        reason: '缺少来源',
      };
    }
    
    // 检查时间戳
    for (const source of sources) {
      if (!source.source.timestamp) {
        return {
          valid: false,
          reason: '时间戳缺失',
        };
      }
    }
    
    return {
      valid: true,
      reason: '来源完整',
    };
  }
}

/**
 * 工具函数：创建来源
 */
export function createSource(options = {}) {
  return Source.createStandard(options);
}

/**
 * 工具函数：格式化来源字符串
 */
export function formatSourceString(options = {}) {
  const source = createSource(options);
  return source.format();
}

/**
 * 工具函数：从文本中提取来源
 */
export function extractSourceFromText(text) {
  const match = text.match(/\[Source:\s*(.+?)\]/);
  if (!match) {
    return null;
  }
  
  return Source.parse(match[0]);
}
