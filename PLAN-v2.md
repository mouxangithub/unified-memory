# Unified Memory v2 — 完整实现规划

## 项目背景

当前 unified-memory（v1.1.0）已有 65 个 MCP 工具，但相比市面主流记忆系统（smart-memory、memory-lancedb-pro、elite-longterm-memory）缺少关键能力。

本文档规划用 MetaGPT 实现完整的 unified-memory v2 增强。

## 竞品分析总结

| 系统 | 核心差异 | 关键特性 |
|------|---------|---------|
| **smart-memory** | 5层记忆架构 + before_prompt_build 钩子 + 48h re-consolidation | 解决 context bloat、fogging problem、rule amnesia |
| **memory-lancedb-pro** | Hybrid检索 + Rerank + Context分块 + Smart Extraction | production-grade，企业级 |
| **elite-longterm-memory** | Git-notes + WAL + Observability HTTP端点 | transcript-first，多设备同步 |
| **memory-qdrant** | Transformers.js本地向量 + Qdrant | 全本地，无需API |
| **memory-tiering** | HOT/WARM/COLD自动化管理 | 记忆生命周期管理 |

---

## 一、OpenClaw Hook 系统架构（核心）

### 1.1 已有事件类型
```
command:new, command:reset, command:stop
session:compact:before, session:compact:after
agent:bootstrap
gateway:startup
message:received, message:preprocessed, message:transcribed, message:sent
session:patch
```

### 1.2 实现 before_prompt_build 钩子
```typescript
// 监听 message:preprocessed，在 agent 看到消息前注入相关记忆
event: message:preprocessed
action: 在 event.context.body 追加记忆片段（格式："\n\n[相关记忆] ... \n[/相关记忆]"）
```

### 1.3 实现 48h re-consolidation
```typescript
// 监听 session:compact:before，检测超过48h的记忆，重新强化
event: session:compact:before
action: 检查记忆 last_refresh，若超过48h，重新 embedding 后更新
```

---

## 二、新增功能详细设计

### 2.1 Episode（会话片段）管理

**目标**：解决"同一话题的多轮对话"被拆散的问题

**概念**：
- Episode = 同一话题的连续对话（默认 8 轮，超过则自动分割）
- Episode 存储为独立记忆单元
- 支持跨 Episode 追溯（A episode 的记忆 → B episode）

**数据结构**：
```json
{
  "id": "ep_<hash>",
  "topic": "刘总问unified-memory功能",
  "started_at": "2026-03-28T10:00:00+08:00",
  "ended_at": "2026-03-28T10:30:00+08:00",
  "turns": 12,
  "message_count": 24,
  "memory_ids": ["mem_xxx", "mem_yyy"],
  "entities": ["刘总", "unified-memory", "MetaGPT"],
  "last_refresh": "2026-03-28T10:30:00+08:00"
}
```

**工具**：
- `memory_episode_start(topic)` — 开始新 episode
- `memory_episode_end()` — 结束当前 episode，生成 episode 摘要
- `memory_episode_list()` — 列出所有 episode
- `memory_episode_recall(episodeId)` — 召回指定 episode 的完整上下文
- `memory_episode_merge(episodeIds)` — 合并多个 episode

---

### 2.2 自动记忆抽取（Smart Extraction）

**目标**：无需手动调用，消息来了自动抽取记忆

**实现**：
- Hook: `message:preprocessed` 触发
- 条件：消息长度 > 20 字符，且不重复（jaccard < 0.7）
- 动作：
  1. 调用 LLM 抽取实体 + 关系
  2. 调用 memory_store 存入
  3. 更新 episode（若在活跃 episode 中）
- 防抖：同话题 5 分钟内不重复抽取

**触发条件**：
```javascript
shouldExtract(message) {
  if (message.length < 20) return false;
  if (isGreeting(message)) return false;  // 简单寒暄不抽取
  if (isCommand(message)) return false;   // /开头的命令不抽取
  if (jaccardSimilarity(message, recentMemory) > 0.7) return false;
  return true;
}
```

**工具**：
- `memory_autostore_enable()` / `memory_autostore_disable()` — 开关
- `memory_autostore_status()` — 状态查询
- `memory_autostore_config(threshold, interval)` — 配置

---

### 2.3 Rerank 重排（Cross-Encoder）

**目标**：BM25 + 向量搜索后，用 LLM 做精准重排

**当前问题**：QMD BM25 搜 10 个结果，直接按 score 排序返回，没有 LLM 重排

**实现**：
```javascript
async function memory_search_reranked(query, topK = 20) {
  // Step 1: 获取候选（BM25 + Vector 各 N 个）
  const bm25Candidates = await memory_bm25(query, topK);
  const vectorCandidates = await memory_vector(query, topK);
  
  // Step 2: RRF 融合得到候选集
  const candidates = rrfFusion(bm25Candidates, vectorCandidates);
  
  // Step 3: Cross-Encoder 重排（调用 LLM）
  const reranked = await rerankWithLLM(query, candidates, topK);
  
  return reranked;
}
```

**Cross-Encoder Prompt**：
```
给定查询："{query}"
判断每条记忆与查询的相关性，输出 JSON 数组：
["{memory1}", "{memory2}", ...]

相关性等级：
- 5: 直接相关，命中核心关键词
- 4: 相关，包含查询的重要内容
- 3: 中等相关，包含部分信息
- 2: 弱相关，只有边缘联系
- 1: 不相关，完全无关
- 0: 完全相反

输出格式：[5, 3, 4, 1, ...]（对应输入顺序）
```

**工具**：
- `memory_rerank(query, memoryIds, topK)` — LLM 重排
- `memory_search(query, topK, useRerank)` — 集成 rerank 的搜索

---

### 2.4 48h Re-consolidation（记忆刷新）

**目标**：解决"记忆随时间模糊"的问题（fogging problem）

**原理**：
- 记忆超过 48h 不刷新 → 向量embedding退化 → 检索命中率下降
- 解决：定期重新 embedding + 强化

**实现**：
```javascript
async function reconsolidateIfNeeded(memory) {
  const hoursSinceRefresh = (Date.now() - memory.last_refresh) / (1000 * 3600);
  if (hoursSinceRefresh < 48) return; // 不需要
  
  // 重新调用 LLM 生成 memory.text 的摘要
  const summary = await llmSummarize(memory.text);
  
  // 重新 embedding
  const newEmbedding = await getOllamaEmbedding(summary);
  
  // 更新
  updateMemory(memory.id, {
    summary,  // 保留原始 text
    embedding: newEmbedding,
    last_refresh: Date.now(),
    refresh_count: (memory.refresh_count || 0) + 1
  });
}
```

**触发时机**：
1. `session:compact:before` — 每次上下文压缩前检查
2. 手动调用：`memory_refresh(olderThanHours)`

**工具**：
- `memory_refresh(olderThanHours)` — 刷新指定时间以上的记忆
- `memory_refresh_stats()` — 查看刷新统计

---

### 2.5 Procedural Memory（流程记忆）

**目标**：记住"怎么做"，而不只是"是什么"

**与 Declarative Memory 的区别**：
- Declarative: "刘总喜欢简洁直接的回复"（事实）
- Procedural: "要回复刘总，先查 memories.json，再调用 memory_search"（流程）

**存储格式**：
```json
{
  "id": "proc_<hash>",
  "type": "procedural",
  "procedure_name": "如何向刘总汇报工作",
  "steps": [
    { "step": 1, "action": "查 memory_search 最近的决策", "tool": "memory_search" },
    { "step": 2, "action": "用 memory_graph_query 查相关实体", "tool": "memory_graph_query" },
    { "step": 3, "action": "整理成简洁的要点列表", "tool": null }
  ],
  "trigger": "刘总|汇报|工作",
  "confidence": 0.85,
  "usage_count": 5,
  "last_used": "2026-03-28T10:00:00+08:00"
}
```

**自动学习**：从对话历史中，当检测到"按步骤执行"模式时自动抽取

**工具**：
- `memory_procedure_add(name, steps, trigger)` — 手动添加流程
- `memory_procedure_find(trigger)` — 查找匹配流程
- `memory_procedure_list()` — 列出所有流程
- `memory_procedure_delete(id)` — 删除

---

### 2.6 Rule Memory（规则记忆）

**目标**：存储用户的硬性规则，如"不要这样做"

**存储格式**：
```json
{
  "id": "rule_<hash>",
  "type": "rule",
  "rule": "不要在群里@刘总",
  "context": "刘总喜欢低调",
  "source": "explicit（显式）| implicit（从行为推断）",
  "confidence": 0.95,
  "created_at": "2026-03-28T10:00:00+08:00",
  "violation_count": 0
}
```

**冲突检测**：
- 新记忆存储前，检查是否有冲突的 rule
- 若冲突，在日志中标记

**工具**：
- `memory_rule_add(rule, context)` — 添加规则
- `memory_rule_list()` — 列出所有规则
- `memory_rule_check(action)` — 检查行为是否违规
- `memory_rule_delete(id)` — 删除

---

### 2.7 Observability HTTP 端点

**目标**：提供外部可访问的状态接口

**Endpoints**：
```
GET /health              → 健康检查
GET /memories           → 记忆列表（分页）
GET /memories/:id       → 单条记忆详情
GET /insights/pending   → 待处理洞察
GET /stats              → 系统统计
GET /graph/entities     → 知识图谱实体
GET /graph/stats        → 图统计
POST /memories          → 创建记忆（外部写入）
DELETE /memories/:id    → 删除记忆
```

**启动方式**：
```javascript
// 独立 HTTP 服务器
const PORT = 3849;
app.listen(PORT, () => {
  console.log(`Memory HTTP API: http://localhost:${PORT}`);
});
```

**工具**：
- `memory_http_start(port)` — 启动 HTTP 服务器
- `memory_http_stop()` — 停止

---

### 2.8 Context 分块（Long-Context Chunking）

**目标**：对超长记忆（文档摘要）做智能分块

**场景**：
- 用户发来长文档，要求总结
- 文档被存为一条记忆（可能 10k+ token）
- 检索时需要切分成段落

**分块策略**：
```javascript
function chunkText(text, maxChunkSize = 500) {
  // 按段落分（换行符分割）
  const paragraphs = text.split(/\n\n+/);
  
  const chunks = [];
  let current = [];
  let currentSize = 0;
  
  for (const p of paragraphs) {
    if (currentSize + p.length > maxChunkSize && current.length > 0) {
      chunks.push(current.join('\n\n'));
      current = [];
      currentSize = 0;
    }
    current.push(p);
    currentSize += p.length;
  }
  if (current.length > 0) chunks.push(current.join('\n\n'));
  
  return chunks; // 返回多个 chunk，各自有 chunk_id
}
```

**每个 chunk**：
```json
{
  "chunk_id": "chunk_<hash>",
  "memory_id": "mem_xxx",
  "index": 0,
  "text": "...",
  "embedding": [0.1, 0.2, ...]
}
```

**工具**：
- `memory_chunk_list(memoryId)` — 列出记忆的 chunks
- `memory_chunk_search(query, memoryId)` — 在指定记忆的 chunks 中搜索

---

### 2.9 Preference Slots（已在 v1.1 实现，需完善）

**已有**：`memory_preference_slots`, `memory_preference_get/set/infer/explain`

**需完善**：
- Preference 的"来源追踪"（显式设定 vs 隐式推断）
- Preference 的置信度随使用次数更新
- Preference 的"遗忘"机制（长时间不用 → 降权）

---

## 三、工具完整清单（v2 最终 80+ 工具）

### 核心（9个，保持）
### 检索增强（8个，新增 rerank）
### Preference Slots（5个）
### Semantic Versioning（3个）
### 主动与预测（6个）
### 知识图谱（4个）
### RAG 与问答（3个）
### 质量与学习（8个，新增 rule/procedural/refresh/reconsolidation）
### 可观测性（6个，新增 HTTP 端点）
### 生命周期（7个）
### 高级推理（6个）
### Episode管理（5个）⭐ 新增
### **Hook集成（4个）** ⭐ 新增
### 配置（3个）

---

## 四、OpenClaw Hook 实现细节

### 4.1 Hook 注册方式

```bash
# 安装到 ~/.openclaw/hooks/
mkdir -p ~/.openclaw/hooks/unified-memory-hook
# 放入 HOOK.md + handler.js
openclaw hooks enable unified-memory
```

### 4.2 Hook handler 事件列表

| 事件 | 动作 |
|------|------|
| `message:preprocessed` | 触发 auto-extraction + before_prompt_build 注入 |
| `session:compact:before` | 触发 48h re-consolidation |
| `session:compact:after` | 触发 episode 生成 |
| `gateway:startup` | 启动 HTTP observability 服务器 |

### 4.3 before_prompt_build 注入格式

```text

[相关记忆]
记忆ID: mem_xxx | 类别: preference | 置信度: 0.9
刘总喜欢简洁直接的回复，不要废话。

记忆ID: mem_yyy | 类别: decision | 置信度: 0.8
刘总决定用 unified-memory 替代所有其他记忆系统。

记忆ID: mem_zzz | 类别: entity | 关联实体: [刘总, unified-memory]
unified-memory 是一个 AI 记忆系统，由刘总部署。
[/相关记忆]

```

---

## 五、实施计划

### Phase 1: Hook 集成（1天）
- [ ] 创建 unified-memory hook（HOOK.md + handler.js）
- [ ] 实现 message:preprocessed 自动抽取
- [ ] 实现 before_prompt_build 记忆注入
- [ ] 测试 gateway:startup 自动启动

### Phase 2: Episode 管理（1天）
- [ ] Episode 数据结构设计
- [ ] memory_episode_* 5个工具
- [ ] Episode 自动分割逻辑
- [ ] Episode → memory 关联

### Phase 3: Rerank + Reconsolidation（1天）
- [ ] Cross-Encoder rerank 实现
- [ ] memory_rerank 工具
- [ ] 48h re-consolidation 实现
- [ ] memory_refresh 工具

### Phase 4: Procedural + Rule Memory（1天）
- [ ] Procedural memory 数据结构
- [ ] memory_procedure_* 工具（4个）
- [ ] Rule memory 数据结构
- [ ] memory_rule_* 工具（4个）

### Phase 5: Observability HTTP（1天）
- [ ] HTTP 服务器实现
- [ ] 7个 REST 端点
- [ ] 端口配置与启动逻辑

### Phase 6: Context Chunking（0.5天）
- [ ] Chunking 算法实现
- [ ] memory_chunk_* 工具（2个）

### Phase 7: 集成测试 + 文档（1天）
- [ ] 完整流程测试
- [ ] SKILL.md 更新为 80+ 工具
- [ ] README 更新
- [ ] GitHub + ClawHub 发布

**总工期：约 7.5 人天**

---

## 六、文件结构

```
unified-memory/
├── src/
│   ├── index.js                    # MCP Server 入口
│   ├── hooks/
│   │   ├── HOOK.md                 # Hook 元数据
│   │   ├── handler.js              # OpenClaw Hook 处理器
│   │   └── auto_extract.js        # 自动抽取逻辑
│   ├── episode/
│   │   ├── episode_store.js        # Episode 存储
│   │   └── episode_tools.js        # Episode MCP 工具
│   ├── rerank/
│   │   ├── cross_encoder.js       # LLM Rerank
│   │   └── rerank_tools.js         # Rerank MCP 工具
│   ├── consolidate/
│   │   ├── reconsolidation.js     # 48h 刷新逻辑
│   │   └── refresh_tools.js        # Refresh MCP 工具
│   ├── procedural/
│   │   ├── procedural_store.js      # 流程记忆存储
│   │   └── procedural_tools.js    # 流程记忆工具
│   ├── rule/
│   │   ├── rule_store.js           # 规则记忆存储
│   │   └── rule_tools.js           # 规则记忆工具
│   ├── observability/
│   │   ├── http_server.js          # HTTP API 服务器
│   │   └── observability_tools.js   # 可观测性工具
│   ├── chunking/
│   │   ├── chunker.js              # Context 分块
│   │   └── chunk_tools.js          # Chunk 工具
│   └── tools/                      # 现有工具（不变）
├── tests/
│   ├── episode.test.js
│   ├── rerank.test.js
│   ├── hook_integration.test.js
│   ├── consolidate.test.js
│   ├── procedural.test.js
│   ├── rule.test.js
│   ├── observability.test.js
│   └── chunking.test.js
├── SKILL.md
├── README.md
└── package.json
```

---

## 七、关键设计决策

1. **Hook vs 直接导入**：用 OpenClaw Hook 系统（event-driven），而非在 MCP handler 里轮询
2. **Episode vs 扁平记忆**：Episode 作为更高层抽象，内部仍是扁平记忆
3. **Rerank 降级策略**：LLM 不可用时回退到 RRF 融合
4. **Reconsolidation 节流**：每次 compact 最多刷新 5 条记忆，避免阻塞
5. **HTTP vs MCP**：Observability 用独立 HTTP（外部可访问），核心功能走 MCP

---

## 八、验收标准

1. `message:preprocessed` 后自动抽取记忆，无需手动调用
2. 每次回答前自动注入相关记忆（before_prompt_build）
3. Episode 可追溯完整话题上下文
4. Rerank 后 topK 结果精准度 > 85%（人工评估）
5. 48h 以上记忆自动 reconsolidation
6. Procedural memory 可执行（查流程 → 按步骤执行）
7. Rule memory 可检测冲突
8. HTTP API 所有端点响应正常
9. 80+ 工具全部注册并测试通过
10. 完整 SKILL.md 文档
