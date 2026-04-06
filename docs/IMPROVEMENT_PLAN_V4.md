# Unified Memory v4.0 改进计划

> 基于 memory-tencentdb 优势分析，完善 unified-memory

## 对比分析

| 功能 | memory-tencentdb | unified-memory 现状 | 改进方向 |
|------|------------------|---------------------|----------|
| L0 对话录制 | ✅ SQLite + JSONL | ✅ transcript_first.js | 保持 |
| L1 记忆提取 | ✅ LLM 自动提取 | ✅ extract.js | 保持 |
| L2 场景归纳 | ✅ Scene Blocks | ❌ 无 | **新增** |
| L3 用户画像 | ✅ Persona | ✅ profile.js | 增强 |
| 中文分词 | ✅ Jieba | ❌ 无 | **新增** |
| 自动调度 | ✅ Pipeline Scheduler | ❌ 无 | **新增** |
| 零配置 | ✅ 开箱即用 | ⚠️ 需配置 | **改进** |
| 团队空间 | ❌ 无 | ✅ v4 tools | 保持优势 |
| WAL | ❌ 无 | ✅ wal.js | 保持优势 |
| Evidence Chain | ❌ 无 | ✅ evidence.js | 保持优势 |

## Phase 1: 场景归纳器 (L2 Scene Blocks)

### 1.1 新增文件: `src/scene_block.js`

```javascript
/**
 * Scene Block Inductor - L2 场景归纳
 * 
 * 从 L1 记忆中自动归纳场景块：
 * - 按时间窗口聚类相关记忆
 * - 提取场景主题、关键实体、行动项
 * - 生成 Markdown 格式的场景块
 */

import { search } from './search.js';
import { getAllMemories } from './storage.js';
import { llmCall } from './config.js';
import { log } from './logger.js';

const SCENE_WINDOW_HOURS = 24;  // 场景时间窗口
const MIN_MEMORIES_PER_SCENE = 3;  // 最少记忆数
const MAX_SCENES = 20;  // 最大场景数

/**
 * 场景块结构
 */
const SceneBlock = {
  id: '',           // scene_xxx
  title: '',        // 场景标题
  summary: '',      // 摘要
  entities: [],     // 关键实体
  actions: [],      // 行动项
  memories: [],     // 关联记忆 ID
  timeRange: {},    // { start, end }
  tags: [],         // 标签
  created: 0,
  updated: 0,
};

/**
 * 从记忆中归纳场景块
 */
export async function inductScenes(options = {}) {
  const {
    scope = 'USER',
    timeRange,
    minMemories = MIN_MEMORIES_PER_SCENE,
    maxScenes = MAX_SCENES,
  } = options;
  
  // 1. 获取相关记忆
  const memories = await getMemoriesForSceneInduction(scope, timeRange);
  
  // 2. 按时间窗口聚类
  const clusters = clusterByTimeWindow(memories, SCENE_WINDOW_HOURS);
  
  // 3. 对每个聚类生成场景块
  const scenes = [];
  for (const cluster of clusters) {
    if (cluster.length < minMemories) continue;
    
    const scene = await generateSceneBlock(cluster);
    if (scene) scenes.push(scene);
    
    if (scenes.length >= maxScenes) break;
  }
  
  return scenes;
}

/**
 * 使用 LLM 生成场景块
 */
async function generateSceneBlock(memories) {
  const memoryTexts = memories.map(m => 
    `[${m.category}] ${m.text}`
  ).join('\n');
  
  const prompt = `从以下记忆中归纳一个场景块：

${memoryTexts}

请输出 JSON 格式：
{
  "title": "场景标题（简短）",
  "summary": "场景摘要（1-2句话）",
  "entities": ["关键实体1", "关键实体2"],
  "actions": ["行动项1", "行动项2"],
  "tags": ["标签1", "标签2"]
}`;

  const response = await llmCall(prompt);
  
  try {
    const parsed = JSON.parse(response);
    return {
      id: `scene_${Date.now()}`,
      ...parsed,
      memories: memories.map(m => m.id),
      timeRange: {
        start: Math.min(...memories.map(m => m.created)),
        end: Math.max(...memories.map(m => m.created)),
      },
      created: Date.now(),
      updated: Date.now(),
    };
  } catch (err) {
    log.error('Failed to parse scene block:', err);
    return null;
  }
}

/**
 * 按时间窗口聚类记忆
 */
function clusterByTimeWindow(memories, windowHours) {
  if (memories.length === 0) return [];
  
  // 按时间排序
  const sorted = [...memories].sort((a, b) => a.created - b.created);
  
  const clusters = [];
  let currentCluster = [sorted[0]];
  let windowStart = sorted[0].created;
  
  for (let i = 1; i < sorted.length; i++) {
    const mem = sorted[i];
    const windowEnd = windowStart + windowHours * 60 * 60 * 1000;
    
    if (mem.created <= windowEnd) {
      currentCluster.push(mem);
    } else {
      if (currentCluster.length >= MIN_MEMORIES_PER_SCENE) {
        clusters.push(currentCluster);
      }
      currentCluster = [mem];
      windowStart = mem.created;
    }
  }
  
  if (currentCluster.length >= MIN_MEMORIES_PER_SCENE) {
    clusters.push(currentCluster);
  }
  
  return clusters;
}
```

### 1.2 新增工具: `memory_scene_induct`

```javascript
server.registerTool('memory_scene_induct', {
  description: '从记忆中归纳场景块 (L2 Scene Induction)',
  inputSchema: z.object({
    scope: z.string().optional().default('USER'),
    timeRange: z.object({
      start: z.number().optional(),
      end: z.number().optional(),
    }).optional(),
    minMemories: z.number().optional().default(3),
    maxScenes: z.number().optional().default(20),
  }),
}, async ({ scope, timeRange, minMemories, maxScenes }) => {
  const scenes = await inductScenes({ scope, timeRange, minMemories, maxScenes });
  return { content: [{ type: 'text', text: JSON.stringify(scenes, null, 2) }] };
});
```

### 1.3 新增工具: `memory_scene_list`

```javascript
server.registerTool('memory_scene_list', {
  description: '列出所有场景块',
  inputSchema: z.object({
    scope: z.string().optional().default('USER'),
    limit: z.number().optional().default(20),
  }),
}, async ({ scope, limit }) => {
  const scenes = await listSceneBlocks(scope, limit);
  return { content: [{ type: 'text', text: JSON.stringify(scenes, null, 2) }] };
});
```

## Phase 2: 中文分词支持

### 2.1 新增依赖: `@node-rs/jieba`

```json
{
  "dependencies": {
    "@node-rs/jieba": "^2.0.1"
  }
}
```

### 2.2 修改: `src/bm25.js`

```javascript
import { cut } from '@node-rs/jieba';

/**
 * 中文分词 + 英文 tokenize
 */
export function tokenize(text) {
  // 中文分词
  const chineseTokens = cut(text, false);
  
  // 英文 tokenization
  const englishTokens = text
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1);
  
  // 合并去重
  return [...new Set([...chineseTokens, ...englishTokens])];
}
```

### 2.3 修改: `src/fusion.js`

```javascript
import { cut } from '@node-rs/jieba';

/**
 * 混合搜索 - 支持中文
 */
export async function hybridSearch(query, options = {}) {
  // 中文分词
  const tokens = cut(query, false);
  
  // BM25 搜索
  const bm25Results = await bm25Search(tokens.join(' '), options);
  
  // 向量搜索
  const vectorResults = await vectorSearch(query, options);
  
  // RRF 融合
  return rrfFusion(bm25Results, vectorResults);
}
```

## Phase 3: 自动调度管线

### 3.1 新增文件: `src/pipeline_scheduler.js`

```javascript
/**
 * Pipeline Scheduler - 自动调度管线
 * 
 * 实现 memory-tencentdb 风格的自动调度：
 * - L0 → L1: 每 N 轮对话后触发
 * - L1 → L2: L1 完成后延迟触发
 * - L2 → L3: 每 M 条新记忆触发
 */

import { log } from './logger.js';

const DEFAULT_CONFIG = {
  everyNConversations: 5,      // 每 N 轮对话触发 L1
  enableWarmup: true,          // Warm-up 模式
  l1IdleTimeoutSeconds: 60,    // 用户停止对话后多久触发 L1
  l2DelayAfterL1Seconds: 90,   // L1 完成后延迟多久触发 L2
  l2MinIntervalSeconds: 300,   // 同一 session 两次 L2 的最小间隔
  l2MaxIntervalSeconds: 1800,  // 活跃 session 的 L2 最大轮询间隔
  sessionActiveWindowHours: 24, // 超过此时间不活跃的 session 停止 L2 轮询
  l3TriggerEveryN: 50,         // 每 N 条新记忆触发 L3
};

class PipelineScheduler {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.sessionCounters = new Map();  // sessionId -> counter
    this.sessionLastActive = new Map(); // sessionId -> timestamp
    this.l1Queue = [];  // L1 待处理队列
    this.l2Queue = [];  // L2 待处理队列
    this.l3Counter = 0; // L3 计数器
  }
  
  /**
   * 记录对话结束，触发管线检查
   */
  async onConversationEnd(sessionId) {
    // 更新计数器
    const counter = (this.sessionCounters.get(sessionId) || 0) + 1;
    this.sessionCounters.set(sessionId, counter);
    this.sessionLastActive.set(sessionId, Date.now());
    
    // 检查是否触发 L1
    const effectiveN = this.getEffectiveN(sessionId);
    if (counter % effectiveN === 0) {
      await this.scheduleL1(sessionId);
    }
  }
  
  /**
   * 获取有效的 N 值（Warm-up 模式）
   */
  getEffectiveN(sessionId) {
    if (!this.config.enableWarmup) {
      return this.config.everyNConversations;
    }
    
    // Warm-up: 1 → 2 → 4 → 8 → ... → N
    const counter = this.sessionCounters.get(sessionId) || 0;
    const maxN = this.config.everyNConversations;
    
    // 找到最大的 2^k <= counter 且 2^k <= maxN
    let effectiveN = 1;
    while (effectiveN * 2 <= counter && effectiveN * 2 <= maxN) {
      effectiveN *= 2;
    }
    
    return Math.max(1, effectiveN);
  }
  
  /**
   * 调度 L1 提取
   */
  async scheduleL1(sessionId) {
    log.info(`[Pipeline] Scheduling L1 for session ${sessionId}`);
    
    // 延迟执行（等待用户停止对话）
    setTimeout(async () => {
      // 检查是否仍在活跃
      const lastActive = this.sessionLastActive.get(sessionId) || 0;
      const idleTime = Date.now() - lastActive;
      
      if (idleTime < this.config.l1IdleTimeoutSeconds * 1000) {
        // 仍在活跃，重新调度
        this.scheduleL1(sessionId);
        return;
      }
      
      // 执行 L1
      await this.executeL1(sessionId);
      
      // 调度 L2
      setTimeout(() => this.scheduleL2(sessionId), 
        this.config.l2DelayAfterL1Seconds * 1000);
    }, this.config.l1IdleTimeoutSeconds * 1000);
  }
  
  /**
   * 执行 L1 提取
   */
  async executeL1(sessionId) {
    log.info(`[Pipeline] Executing L1 for session ${sessionId}`);
    
    // 调用 extract.js 提取记忆
    const { extractMemories } = await import('./extract.js');
    const memories = await extractMemories({ sessionId });
    
    // 更新 L3 计数器
    this.l3Counter += memories.length;
    
    // 检查是否触发 L3
    if (this.l3Counter >= this.config.l3TriggerEveryN) {
      await this.scheduleL3();
      this.l3Counter = 0;
    }
    
    return memories;
  }
  
  /**
   * 调度 L2 场景归纳
   */
  async scheduleL2(sessionId) {
    log.info(`[Pipeline] Scheduling L2 for session ${sessionId}`);
    
    // 检查最小间隔
    const lastL2 = this.lastL2Time || 0;
    const elapsed = Date.now() - lastL2;
    
    if (elapsed < this.config.l2MinIntervalSeconds * 1000) {
      log.info(`[Pipeline] L2 skipped: too soon (${elapsed}s < ${this.config.l2MinIntervalSeconds}s)`);
      return;
    }
    
    await this.executeL2(sessionId);
  }
  
  /**
   * 执行 L2 场景归纳
   */
  async executeL2(sessionId) {
    log.info(`[Pipeline] Executing L2 for session ${sessionId}`);
    
    const { inductScenes } = await import('./scene_block.js');
    const scenes = await inductScenes({ scope: 'USER' });
    
    this.lastL2Time = Date.now();
    
    return scenes;
  }
  
  /**
   * 调度 L3 用户画像更新
   */
  async scheduleL3() {
    log.info(`[Pipeline] Scheduling L3`);
    await this.executeL3();
  }
  
  /**
   * 执行 L3 用户画像更新
   */
  async executeL3() {
    log.info(`[Pipeline] Executing L3`);
    
    const { getProfile } = await import('./profile.js');
    const profile = await getProfile({ scope: 'USER' });
    
    return profile;
  }
}

export const scheduler = new PipelineScheduler();
```

### 3.2 集成到 Hook

```javascript
// 在 agent_end hook 中触发管线
import { scheduler } from './pipeline_scheduler.js';

// Hook: agent_end
export async function onAgentEnd(sessionId) {
  await scheduler.onConversationEnd(sessionId);
}
```

## Phase 4: 零配置默认值

### 4.1 修改: `src/config.js`

```javascript
// 零配置默认值
export const DEFAULT_CONFIG = {
  // 存储配置
  storage: {
    mode: 'json',  // 默认 JSON，无需数据库
    path: '~/.openclaw/workspace/memory/',
  },
  
  // 向量配置
  vector: {
    enabled: false,  // 默认禁用，零依赖
    provider: 'none',
    dimensions: 0,
  },
  
  // 管线配置
  pipeline: {
    enabled: true,
    everyNConversations: 5,
    enableWarmup: true,
    l1IdleTimeoutSeconds: 60,
    l2DelayAfterL1Seconds: 90,
    l2MinIntervalSeconds: 300,
    l2MaxIntervalSeconds: 1800,
    sessionActiveWindowHours: 24,
    l3TriggerEveryN: 50,
  },
  
  // 召回配置
  recall: {
    enabled: true,
    maxResults: 5,
    scoreThreshold: 0.3,
    strategy: 'keyword',  // 默认关键词，无需向量
  },
  
  // 中文配置
  chinese: {
    enabled: true,
    segmenter: 'jieba',
  },
};

// 自动检测并应用配置
export function autoConfig() {
  const config = { ...DEFAULT_CONFIG };
  
  // 检测 Ollama
  if (process.env.OLLAMA_HOST) {
    config.vector.enabled = true;
    config.vector.provider = 'ollama';
    config.recall.strategy = 'hybrid';
  }
  
  // 检测 OpenAI API Key
  if (process.env.OPENAI_API_KEY) {
    config.vector.enabled = true;
    config.vector.provider = 'openai';
    config.recall.strategy = 'hybrid';
  }
  
  return config;
}
```

## Phase 5: 四层管线整合

### 5.1 新增工具: `memory_pipeline_status`

```javascript
server.registerTool('memory_pipeline_status', {
  description: '获取四层管线状态',
  inputSchema: z.object({}),
}, async () => {
  const status = {
    L0: {
      name: 'Conversation Recording',
      status: 'active',
      stats: await getTranscriptStats(),
    },
    L1: {
      name: 'Memory Extraction',
      status: 'active',
      stats: await getMemoryStats(),
    },
    L2: {
      name: 'Scene Induction',
      status: 'active',
      stats: await getSceneStats(),
    },
    L3: {
      name: 'User Profile',
      status: 'active',
      stats: await getProfileStats(),
    },
    scheduler: scheduler.getStatus(),
  };
  
  return { content: [{ type: 'text', text: JSON.stringify(status, null, 2) }] };
});
```

### 5.2 新增工具: `memory_pipeline_trigger`

```javascript
server.registerTool('memory_pipeline_trigger', {
  description: '手动触发管线阶段',
  inputSchema: z.object({
    stage: z.enum(['L1', 'L2', 'L3']),
    sessionId: z.string().optional(),
  }),
}, async ({ stage, sessionId }) => {
  switch (stage) {
    case 'L1':
      return await scheduler.executeL1(sessionId);
    case 'L2':
      return await scheduler.executeL2(sessionId);
    case 'L3':
      return await scheduler.executeL3();
  }
});
```

## 实施优先级

| Phase | 功能 | 优先级 | 工作量 |
|-------|------|--------|--------|
| Phase 1 | 场景归纳器 (L2) | P0 | 2天 |
| Phase 2 | 中文分词 | P0 | 1天 |
| Phase 3 | 自动调度管线 | P1 | 2天 |
| Phase 4 | 零配置默认值 | P1 | 1天 |
| Phase 5 | 四层整合 | P2 | 1天 |

## 预期成果

完成后，unified-memory 将具备：

1. ✅ **四层渐进式管线** — L0→L1→L2→L3 全自动
2. ✅ **场景归纳** — 自动从记忆中归纳场景块
3. ✅ **中文优化** — Jieba 分词，中文搜索效果更好
4. ✅ **零配置** — 开箱即用，所有配置有合理默认值
5. ✅ **自动调度** — Pipeline Scheduler 自动管理
6. ✅ **企业级特性** — 团队空间、WAL、Evidence Chain（保留优势）

---

**创建时间**: 2026-04-06
**作者**: OpenClaw Assistant
