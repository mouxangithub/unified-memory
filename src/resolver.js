/**
 * Resolver - 决策树
 * 
 * 确定内容应该放在哪个目录
 * 
 * 功能：
 * - 根据内容类型决定存储位置
 * - 冲突解决
 * - 分类建议
 * 
 * @module resolver
 */

/**
 * 目录类型
 */
export const DirectoryType = {
  PEOPLE: 'people',
  COMPANIES: 'companies',
  DEALS: 'deals',
  CONCEPTS: 'concepts',
  MEETINGS: 'meetings',
  PROJECTS: 'projects',
  IDEAS: 'ideas',
  ORIGINALS: 'originals',
  INBOX: 'inbox',
};

/**
 * 目录说明
 */
export const DirectoryInfo = {
  [DirectoryType.PEOPLE]: {
    name: '人物',
    description: '人物的主页面（姓名、职位、关系）',
    keywords: ['姓名', '职位', '公司', '同事', '朋友', '关系'],
  },
  [DirectoryType.COMPANIES]: {
    name: '公司',
    description: '公司的主页面（组织、业务、投资）',
    keywords: ['公司', '企业', '组织', '业务', '产品', '融资'],
  },
  [DirectoryType.DEALS]: {
    name: '交易',
    description: '交易相关的页面（合作、投资、采购）',
    keywords: ['交易', '合作', '投资', '融资', '合同', '协议'],
  },
  [DirectoryType.CONCEPTS]: {
    name: '概念',
    description: '概念、理论、框架、方法论',
    keywords: ['概念', '理论', '框架', '方法论', '原则', '模型'],
  },
  [DirectoryType.MEETINGS]: {
    name: '会议',
    description: '会议相关的页面（纪要、决策、行动项）',
    keywords: ['会议', '纪要', '决策', '行动项', '讨论', '同步'],
  },
  [DirectoryType.PROJECTS]: {
    name: '项目',
    description: '项目的主页面（计划、进度、里程碑）',
    keywords: ['项目', '计划', '进度', '里程碑', '团队', '开发'],
  },
  [DirectoryType.IDEAS]: {
    name: '点子',
    description: '点子、创意、想法',
    keywords: ['点子', '创意', '想法', '方案', '功能', '创新'],
  },
  [DirectoryType.ORIGINALS]: {
    name: '原创',
    description: '用户的原始想法、观点、洞察',
    keywords: ['原话', '观点', '洞察', '想法', '原话', '原始'],
  },
  [DirectoryType.INBOX]: {
    name: '待分类',
    description: '暂时无法确定分类的内容',
    keywords: ['待分类', '不确定', '暂存', '后续整理'],
  },
};

/**
 * 关键词匹配
 */
const KeywordMatches = {
  [DirectoryType.ORIGINALS]: [
    '我觉得', '我认为', '我感觉', '我观察到', '我洞察到', '我的观点',
    'ambition', 'lifespan', 'ratio', 'insight', 'original',
  ],
  [DirectoryType.MEETINGS]: [
    '会议', '纪要', '同步', '讨论', '决策', '行动项',
    'meeting', 'minutes', 'sync', 'decision', 'action item',
  ],
  [DirectoryType.PEOPLE]: [
    '加入', '离职', '职位', '同事', '朋友', '介绍',
    'works at', 'reports to', 'colleague', 'friend',
  ],
  [DirectoryType.COMPANIES]: [
    '公司', '企业', '组织', '融资', '投资', '产品',
    'corporation', 'company', 'organization', 'funding', 'product',
  ],
  [DirectoryType.DEALS]: [
    '交易', '合作', '协议', '合同', '融资', '投资',
    'deal', 'agreement', 'contract', 'funding', 'investment',
  ],
  [DirectoryType.PROJECTS]: [
    '项目', '计划', '进度', '里程碑', '延期', '开发',
    'project', 'plan', 'progress', 'milestone', 'delay', 'development',
  ],
  [DirectoryType.CONCEPTS]: [
    '概念', '理论', '框架', '方法论', '原则', '模型',
    'concept', 'theory', 'framework', 'methodology', 'principle', 'model',
  ],
  [DirectoryType.IDEAS]: [
    '点子', '创意', '想法', '方案', '功能', '创新',
    'idea', 'concept', 'thought', 'proposal', 'feature', 'innovation',
  ],
};

/**
 * 决策树
 */
export class Resolver {
  constructor() {
    this.config = {
      confidenceThreshold: 0.6,
      maxSuggestions: 3,
    };
  }

  /**
   * 决策内容应该放在哪个目录
   * 
   * @param {string} text - 内容文本
   * @returns {Object} 决策结果 { directory, confidence, reasoning }
   */
  decide(text, context = {}) {
    const scores = this.scoreDirectories(text);
    const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    
    const best = sorted[0];
    const top3 = sorted.slice(0, this.config.maxSuggestions);
    
    return {
      directory: best[0],
      confidence: best[1],
      reasoning: this.generateReasoning(best, top3, text, context),
      suggestions: top3.map(([dir, score]) => ({
        directory: dir,
        confidence: score,
        info: DirectoryInfo[dir],
      })),
    };
  }

  /**
   * 为每个目录打分
   */
  scoreDirectories(text) {
    const scores = {};
    
    for (const dir of Object.values(DirectoryType)) {
      scores[dir] = this.scoreDirectory(dir, text);
    }
    
    return scores;
  }

  /**
   * 为单个目录打分
   */
  scoreDirectory(directory, text) {
    const keywords = KeywordMatches[directory] || [];
    const textLower = text.toLowerCase();
    
    let score = 0;
    let matchCount = 0;
    
    for (const keyword of keywords) {
      const keywordLower = keyword.toLowerCase();
      if (textLower.includes(keywordLower)) {
        score += 1;
        matchCount++;
      }
    }
    
    // 归一化分数
    const normalized = matchCount / keywords.length;
    
    return Math.min(1, normalized + (score * 0.1));
  }

  /**
   * 生成决策理由
   */
  generateReasoning(best, top3, text, context) {
    const [bestDir, bestScore] = best;
    const bestInfo = DirectoryInfo[bestDir];
    
    let reasoning = `根据内容分析，建议放在 **${bestInfo.name}** 目录。\n\n`;
    
    reasoning += `**理由**：\n`;
    reasoning += `- 匹配关键词：${this.findMatchingKeywords(bestDir, text).join(', ') || '无明显匹配'}\n`;
    reasoning += `- 置信度：${(bestScore * 100).toFixed(0)}%\n\n`;
    
    if (top3.length > 1) {
      const second = top3[1];
      const secondInfo = DirectoryInfo[second[0]];
      
      if (bestScore - second[1] < 0.2) {
        reasoning += `⚠️ **注意**：与 **${secondInfo.name}** 目录的置信度接近（${(second[1] * 100).toFixed(0)}%），建议参考决策树确认。\n`;
      }
    }
    
    return reasoning;
  }

  /**
   * 找到匹配的关键词
   */
  findMatchingKeywords(directory, text) {
    const keywords = KeywordMatches[directory] || [];
    const textLower = text.toLowerCase();
    
    return keywords.filter(k => textLower.includes(k.toLowerCase()));
  }

  /**
   * 获取目录信息
   */
  getDirectoryInfo(directory) {
    return DirectoryInfo[directory];
  }

  /**
   * 获取所有目录
   */
  getAllDirectories() {
    return Object.values(DirectoryType);
  }
}

/**
 * 工具函数：从文本中提取实体
 */
export function extractEntities(text) {
  // 简单实现，后续可以扩展
  const entities = {
    people: [],
    companies: [],
    dates: [],
  };
  
  // 简单的关键词匹配
  const peopleKeywords = ['张三', '李四', '王五', '赵六'];
  const companyKeywords = ['Acme', 'TechCorp', 'StartUp'];
  
  for (const person of peopleKeywords) {
    if (text.includes(person)) {
      entities.people.push(person);
    }
  }
  
  for (const company of companyKeywords) {
    if (text.includes(company)) {
      entities.companies.push(company);
    }
  }
  
  // 日期匹配
  const dateRegex = /\d{4}-\d{2}-\d{2}/g;
  const dates = text.match(dateRegex);
  if (dates) {
    entities.dates.push(...dates);
  }
  
  return entities;
}
