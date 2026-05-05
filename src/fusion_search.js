/**
 * Fusion Search - 搜找融合引擎
 * 
 * 搜通道: 向量搜索 (BM25 + 向量)
 * 找通道: viking:// 文件系统
 * RRF 融合输出
 */

import { getVikingFS } from './viking_fs.js';
import { SkillsStore } from './skills_store.js';
import { PreferencesStore } from './preferences_store.js';

export class FusionSearch {
  constructor(options = {}) {
    this.fs = getVikingFS();
    this.skillsStore = options.skillsStore || new SkillsStore();
    this.preferencesStore = options.preferencesStore || new PreferencesStore();
    this.vectorSearchFn = options.vectorSearch || null;
    this.bm25SearchFn = options.bm25Search || null;
    this.rrfK = options.rrfK || 60;
  }

  /**
   * Reciprocal Rank Fusion
   * @param {Array} resultLists - Multiple result lists
   * @param {number} k - RRF parameter
   * @returns {Array}
   */
  reciprocalRankFusion(resultLists, k = 60) {
    const scores = new Map();

    for (const results of resultLists) {
      if (!results || results.length === 0) continue;
      
      for (let i = 0; i < results.length; i++) {
        const item = results[i];
        const id = item.id || item.path || JSON.stringify(item);
        const rank = i + 1;
        const rrfScore = 1 / (k + rank);

        if (scores.has(id)) {
          scores.get(id).fusionScore += rrfScore;
        } else {
          scores.set(id, {
            ...item,
            fusionScore: rrfScore,
          });
        }
      }
    }

    return Array.from(scores.values())
      .sort((a, b) => b.fusionScore - a.fusionScore);
  }

  /**
   * 搜通道: 向量搜索 (BM25 + 向量)
   * @param {string} query - Search query
   * @param {number} topK - Number of results
   * @returns {Promise<Array>}
   */
  async vectorSearch(query, topK = 10) {
    const results = [];
    
    // 如果有外部向量搜索，使用它
    if (this.vectorSearchFn && typeof this.vectorSearchFn === 'function') {
      try {
        const vectorResults = await this.vectorSearchFn(query, topK);
        for (const r of vectorResults) {
          results.push({
            id: r.memory?.id || r.id,
            source: 'vector',
            score: r.score || r.vectorScore,
            content: r.memory?.text || r.text || '',
            memory: r.memory,
          });
        }
      } catch (e) {
        console.warn('Vector search failed:', e.message);
      }
    }
    
    // 如果有 BM25 搜索，使用它
    if (this.bm25SearchFn && typeof this.bm25SearchFn === 'function') {
      try {
        const bm25Results = this.bm25SearchFn(query, topK);
        for (const r of bm25Results) {
          results.push({
            id: r.memory?.id || r.id,
            source: 'bm25',
            score: r.score || r.bm25Score,
            content: r.memory?.text || r.text || '',
            memory: r.memory,
          });
        }
      } catch (e) {
        console.warn('BM25 search failed:', e.message);
      }
    }
    
    return results;
  }

  /**
   * 找通道: viking:// 文件系统搜索
   * @param {string} query - Search query
   * @returns {Array}
   */
  fsSearch(query) {
    const results = [];
    const queryLower = query.toLowerCase();
    
    // 搜索所有文件
    const allFiles = this.fs.find('viking://**');
    
    for (const file of allFiles) {
      if (file.type === 'file') {
        const content = this.fs.read(file.path);
        if (content && content.toLowerCase().includes(queryLower)) {
          results.push({
            id: file.path,
            source: 'filesystem',
            path: file.path,
            score: 1,
            content: content.slice(0, 200),
          });
        }
      }
    }
    
    // 搜索 skills
    try {
      const skills = this.skillsStore.searchSkills(query);
      for (const skill of skills) {
        const instructions = this.skillsStore.getInstructions(skill.category);
        results.push({
          id: `skill:${skill.category}`,
          source: 'skills',
          path: `viking://agent/skills/${skill.category}/instructions`,
          score: skill.score,
          content: instructions.slice(0, 200),
        });
      }
    } catch (e) {
      // Skills store 可能未初始化
    }
    
    // 搜索 preferences
    try {
      const prefs = this.preferencesStore.search(query);
      for (const pref of prefs) {
        results.push({
          id: `pref:${pref.category}:${pref.key}`,
          source: 'preferences',
          path: `viking://user/preferences/${pref.category}/${pref.key}`,
          score: 1,
          content: typeof pref.value === 'string' ? pref.value : JSON.stringify(pref.value),
        });
      }
    } catch (e) {
      // Preferences store 可能未初始化
    }
    
    return results;
  }

  /**
   * 搜找融合搜索
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @param {number} options.topK - Number of results
   * @param {boolean} options.enableVector - Enable vector search
   * @param {boolean} options.enableFS - Enable filesystem search
   * @param {number} options.vectorWeight - Vector search weight
   * @param {number} options.fsWeight - Filesystem search weight
   * @returns {Promise<Array>}
   */
  async search(query, options = {}) {
    const {
      topK = 10,
      enableVector = true,
      enableFS = true,
      vectorWeight = 1,
      fsWeight = 1,
    } = options;

    const resultLists = [];

    // 搜通道
    if (enableVector) {
      const vectorResults = await this.vectorSearch(query, topK * 2);
      if (vectorResults.length > 0) {
        resultLists.push(vectorResults);
      }
    }

    // 找通道
    if (enableFS) {
      const fsResults = this.fsSearch(query);
      if (fsResults.length > 0) {
        resultLists.push(fsResults);
      }
    }

    // RRF 融合
    if (resultLists.length === 0) {
      return [];
    }

    const fused = this.reciprocalRankFusion(resultLists, this.rrfK);
    
    // 应用权重
    for (const result of fused) {
      if (result.source === 'vector' || result.source === 'bm25') {
        result.fusionScore *= vectorWeight;
      } else {
        result.fusionScore *= fsWeight;
      }
    }

    // 重新排序
    fused.sort((a, b) => b.fusionScore - a.fusionScore);

    return fused.slice(0, topK);
  }

  /**
   * 快速搜索 - 仅文件系统
   * @param {string} query - Search query
   * @returns {Array}
   */
  quickSearch(query) {
    return this.fsSearch(query);
  }

  /**
   * 深度搜索 - 向量 + 文件系统
   * @param {string} query - Search query
   * @param {number} topK - Number of results
   * @returns {Promise<Array>}
   */
  async deepSearch(query, topK = 10) {
    return this.search(query, { topK, enableVector: true, enableFS: true });
  }
}

// 单例
let instance = null;
export function getFusionSearch(options) {
  if (!instance) {
    instance = new FusionSearch(options);
  }
  return instance;
}

export default FusionSearch;
