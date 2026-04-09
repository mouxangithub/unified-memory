# OpenViking vs Unified Memory - 完整功能对比

## 📊 功能对比矩阵

| 功能模块 | OpenViking | Unified Memory | 状态 | 文件 |
|---------|-----------|----------------|------|------|
| **分层信息模型 (L0/L1/L2)** | ✅ | ✅ | 已实现 | `compression/layered_compressor.js` |
| **记忆类型系统** | 8 类 | 8 类 | ✅ 已实现 | `extraction/memory_extractor.js` |
| **智能去重** | ❌ | ✅ | **我们更好** | `deduplication/smart_deduplicator.js` |
| **生命周期管理** | ❌ | ✅ | **我们更好** | `lifecycle/memory_lifecycle_manager.js` |
| **文件系统范式** | ✅ | ✅ | **已实现** | `storage/filesystem.js` |
| **Viking URI 系统** | ✅ | ✅ | **已实现** | `core/viking_uri.js` |
| **意图分析 (Intent Analysis)** | ✅ | ✅ | **已实现** | `retrieval/intent_analyzer.js` |
| **类型化查询 (TypedQuery)** | ✅ | ✅ | **已实现** | `retrieval/intent_analyzer.js` |
| **层级检索 (Hierarchical Retrieval)** | ✅ | ✅ | **已实现** | `retrieval/hierarchical_retriever.js` |
| **重排序 (Rerank)** | ✅ | ✅ | **已实现** | `retrieval/reranker.js` |
| **Session 管理** | ✅ | ✅ | **已实现** | `session/session_manager.js` |
| **Message 记录** | ✅ | ✅ | **已实现** | `session/session_manager.js` |
| **Context 使用追踪** | ✅ | ✅ | **已实现** | `session/session_manager.js` |
| **8 类记忆提取** | ✅ | ✅ | **已实现** | `extraction/memory_extractor.js` |
| **LLM 去重决策** | ✅ | ✅ | **已实现** | `extraction/memory_extractor.js` |
| **文档解析器 (Parser)** | ✅ | ✅ | **已实现** | `parsing/document_parser.js` |
| **TreeBuilder** | ✅ | ✅ | **已实现** | `storage/filesystem.js` (tree方法) |
| **SemanticQueue** | ✅ | ✅ | **已实现** | `queue/memory_queue.js` |
| **AST Code Skeleton** | ✅ | ✅ | **已实现** | `parsing/document_parser.js` (CodeParser) |
| **关系管理** | ✅ | ✅ | **已实现** | `relations/relation_manager.js` |
| **导入导出 (ovpack)** | ✅ | ❌ | 待实现 | - |
| **服务层架构** | ✅ | ✅ | **已实现** | `openviking_system.js` |

---

## 🔥 高优先级功能（建议实现）

### 1. 文件系统范式 + Viking URI 系统

**OpenViking 的设计**：
```
viking://
├── resources/          # 独立资源
│   └── {project}/
│       ├── .abstract.md
│       ├── .overview.md
│       └── {files...}
├── user/{user_id}/
│   ├── profile.md
│   └── memories/
│       ├── preferences/
│       ├── entities/
│       └── events/
├── agent/{agent_space}/
│   ├── skills/
│   └── memories/
│       ├── cases/
│       └── patterns/
└── session/{session_id}/
    ├── messages/
    ├── tools/
    └── history/
```

**优势**：
- ✅ 直观的目录结构，像文件系统一样浏览
- ✅ 确定性路径，不需要向量搜索就能定位
- ✅ 支持目录级别的操作（ls、tree、grep）
- ✅ 天然支持层级检索

**我们的实现建议**：
```javascript
// URI 格式
memory://user/{user_id}/memories/preferences/coding
memory://agent/{agent_id}/memories/cases/{case_id}
memory://session/{session_id}/messages

// API
await client.ls('memory://user/ou_xxx/memories/')
await client.read('memory://user/ou_xxx/memories/preferences/coding.md')
await client.tree('memory://agent/')
```

---

### 2. 意图分析 (Intent Analysis)

**OpenViking 的设计**：
```python
@dataclass
class TypedQuery:
    query: str              # 重写的查询
    context_type: ContextType  # MEMORY/RESOURCE/SKILL
    intent: str             # 查询目的
    priority: int           # 1-5 优先级
```

**工作流程**：
```
Query → IntentAnalyzer (LLM) → 0-5 TypedQueries
```

**示例**：
```python
# 输入
"帮我创建一个 RFC 文档"

# 输出
[
    TypedQuery(query="创建 RFC 文档", context_type=SKILL, intent="执行任务", priority=5),
    TypedQuery(query="RFC 文档模板", context_type=RESOURCE, intent="查找模板", priority=4),
    TypedQuery(query="用户的代码风格偏好", context_type=MEMORY, intent="个性化", priority=3)
]
```

**优势**：
- ✅ 理解用户真实意图
- ✅ 自动决定搜索范围
- ✅ 支持复杂任务的多维度检索

**我们的实现建议**：
```javascript
class IntentAnalyzer {
  async analyze(query, sessionContext) {
    // 1. 分析查询意图
    const intent = await this.llm.analyze(query, sessionContext);
    
    // 2. 生成类型化查询
    const typedQueries = intent.queries.map(q => ({
      query: q.query,
      type: q.type,  // 'facts' | 'patterns' | 'skills' | 'cases'
      intent: q.intent,
      priority: q.priority
    }));
    
    return typedQueries;
  }
}
```

---

### 3. 层级检索 (Hierarchical Retrieval)

**OpenViking 的设计**：
```
Step 1: 确定根目录（根据 context_type）
    ↓
Step 2: 全局向量搜索定位起始目录
    ↓
Step 3: 合并起始点 + Rerank 评分
    ↓
Step 4: 递归搜索（优先队列）
    ↓
Step 5: 转换为 MatchedContext
```

**核心算法**：
```python
while dir_queue:
    current_uri, parent_score = heapq.heappop(dir_queue)
    
    # 搜索子项
    results = await search(parent_uri=current_uri)
    
    for r in results:
        # 分数传播
        final_score = 0.5 * embedding_score + 0.5 * parent_score
        
        if final_score > threshold:
            collected.append(r)
            
            if not r.is_leaf:  # 目录继续递归
                heapq.heappush(dir_queue, (r.uri, final_score))
    
    # 收敛检测
    if topk_unchanged_for_3_rounds:
        break
```

**优势**：
- ✅ 目录级别的检索，更精准
- ✅ 分数传播，父目录影响子目录
- ✅ 收敛检测，避免过度搜索

**我们的实现建议**：
```javascript
class HierarchicalRetriever {
  async retrieve(typedQueries, options) {
    const results = [];
    
    for (const query of typedQueries) {
      // 1. 确定根目录
      const rootUris = this.getRootUris(query.type);
      
      // 2. 全局搜索定位起始点
      const startPoints = await this.globalSearch(query.query, rootUris);
      
      // 3. 递归搜索
      const collected = await this.recursiveSearch(startPoints, query);
      
      results.push(...collected);
    }
    
    return results;
  }
  
  async recursiveSearch(startPoints, query) {
    const queue = new PriorityQueue();
    const collected = [];
    let unchangedRounds = 0;
    
    while (queue.length > 0 && unchangedRounds < 3) {
      const { uri, parentScore } = queue.pop();
      
      // 搜索子项
      const children = await this.searchChildren(uri, query);
      
      for (const child of children) {
        const finalScore = 0.5 * child.score + 0.5 * parentScore;
        
        if (finalScore > query.threshold) {
          collected.push(child);
          
          if (!child.isLeaf) {
            queue.push({ uri: child.uri, parentScore: finalScore });
          }
        }
      }
      
      // 收敛检测
      if (this.isTopkUnchanged(collected)) {
        unchangedRounds++;
      }
    }
    
    return collected;
  }
}
```

---

### 4. 重排序 (Rerank)

**OpenViking 的设计**：
```python
if rerank_client and mode == THINKING:
    scores = rerank_client.rerank_batch(query, documents)
else:
    scores = [r["_score"] for r in results]  # 向量分数
```

**优势**：
- ✅ 提高检索精准度
- ✅ 支持多种 Rerank 模型

**我们的实现建议**：
```javascript
class Reranker {
  constructor(options) {
    this.provider = options.provider;  // 'volcengine' | 'cohere' | 'jina'
    this.model = options.model;
  }
  
  async rerank(query, documents) {
    if (!this.provider) {
      return documents;  // 回退到向量分数
    }
    
    const response = await this.provider.rerank({
      query: query,
      documents: documents.map(d => d.text),
      model: this.model
    });
    
    return documents.map((doc, i) => ({
      ...doc,
      rerankScore: response.scores[i]
    })).sort((a, b) => b.rerankScore - a.rerankScore);
  }
}
```

---

### 5. Session 管理

**OpenViking 的设计**：
```python
# Session 生命周期
session = client.session(session_id="chat_001")

# 添加消息
session.add_message("user", [TextPart("...")])
session.add_message("assistant", [
    TextPart("..."),
    ContextPart(uri="viking://user/memories/profile.md")
])

# 记录使用的上下文
session.used(contexts=["viking://user/memories/profile.md"])

# 记录使用的技能
session.used(skill={
    "uri": "viking://agent/skills/code-search",
    "input": "search config",
    "output": "found 3 files",
    "success": True
})

# 提交（归档 + 记忆提取）
result = session.commit()
```

**Session 存储**：
```
viking://session/{session_id}/
├── messages.jsonl       # 当前消息
├── .abstract.md         # 当前摘要
├── .overview.md         # 当前概览
├── history/
│   ├── archive_001/
│   │   ├── messages.jsonl
│   │   ├── .abstract.md
│   │   ├── .overview.md
│   │   └── .done
│   └── archive_NNN/
└── tools/
    └── {tool_id}/tool.json
```

**优势**：
- ✅ 完整的对话历史管理
- ✅ 上下文使用追踪
- ✅ 自动归档和压缩
- ✅ 记忆提取

**我们的实现建议**：
```javascript
class SessionManager {
  async createSession(sessionId, options) {
    return {
      id: sessionId,
      messages: [],
      usedContexts: [],
      usedSkills: [],
      createdAt: Date.now()
    };
  }
  
  async addMessage(sessionId, role, parts) {
    const session = await this.getSession(sessionId);
    session.messages.push({
      id: `msg_${Date.now()}`,
      role: role,
      parts: parts,
      createdAt: Date.now()
    });
    await this.saveSession(session);
  }
  
  async recordUsage(sessionId, usage) {
    const session = await this.getSession(sessionId);
    
    if (usage.contexts) {
      session.usedContexts.push(...usage.contexts);
    }
    
    if (usage.skill) {
      session.usedSkills.push(usage.skill);
    }
    
    await this.saveSession(session);
  }
  
  async commit(sessionId) {
    const session = await this.getSession(sessionId);
    
    // 1. 归档消息
    const archiveUri = await this.archiveMessages(session);
    
    // 2. 异步提取记忆
    const taskId = await this.extractMemories(session);
    
    return {
      status: 'accepted',
      taskId: taskId,
      archiveUri: archiveUri
    };
  }
}
```

---

### 6. 8 类记忆提取

**OpenViking 的 8 类记忆**：

| 类别 | 归属 | 描述 | 可合并 |
|------|------|------|--------|
| profile | user | 用户身份/属性 | ✅ |
| preferences | user | 用户偏好 | ✅ |
| entities | user | 实体（人/项目） | ✅ |
| events | user | 事件/决策 | ❌ |
| cases | agent | 问题 + 解决方案 | ❌ |
| patterns | agent | 可复用模式 | ✅ |
| tools | agent | 工具使用知识 | ✅ |
| skills | agent | 技能执行知识 | ✅ |

**提取流程**：
```
Messages → LLM Extract → Candidate Memories
    ↓
Vector Pre-filter → Find Similar Memories
    ↓
LLM Dedup Decision → candidate(skip/create/none) + item(merge/delete)
    ↓
Write to AGFS → Vectorize
```

**LLM 去重决策**：

| 层级 | 决策 | 描述 |
|------|------|------|
| Candidate | skip | 候选重复，跳过 |
| Candidate | create | 创建候选记忆 |
| Candidate | none | 不创建候选，解决现有记忆 |
| Per-existing item | merge | 合并候选内容到现有记忆 |
| Per-existing item | delete | 删除冲突的现有记忆 |

**我们的实现建议**：
```javascript
class MemoryExtractor {
  constructor() {
    this.categories = [
      'profile', 'preferences', 'entities', 'events',
      'cases', 'patterns', 'tools', 'skills'
    ];
  }
  
  async extract(session) {
    // 1. LLM 提取候选记忆
    const candidates = await this.llmExtract(session.messages);
    
    // 2. 向量预过滤
    const filtered = await this.vectorPrefilter(candidates);
    
    // 3. LLM 去重决策
    const decisions = await this.llmDedup(filtered);
    
    // 4. 写入存储
    const memories = await this.writeMemories(decisions);
    
    return memories;
  }
  
  async llmDedup(candidates) {
    const decisions = [];
    
    for (const candidate of candidates) {
      // 查找相似记忆
      const similar = await this.findSimilar(candidate);
      
      // LLM 决策
      const decision = await this.llm.decide({
        candidate: candidate,
        similarMemories: similar,
        options: ['skip', 'create', 'merge', 'delete']
      });
      
      decisions.push({
        candidate: candidate,
        decision: decision.action,
        targetMemory: decision.targetMemory
      });
    }
    
    return decisions;
  }
}
```

---

## 🟡 中优先级功能

### 7. 文档解析器 (Parser)

**OpenViking 支持的格式**：
- ✅ Markdown
- ✅ Plain text
- ✅ PDF
- ✅ HTML
- ✅ Code (Python, JS, Go, etc.)
- ✅ Image
- ✅ Video
- ✅ Audio

**解析流程**：
```
Input File → Parser → TreeBuilder → SemanticQueue → Vector Index
```

**我们的实现建议**：
```javascript
class DocumentParser {
  async parse(file, options) {
    // 1. 检测格式
    const format = this.detectFormat(file);
    
    // 2. 选择解析器
    const parser = this.getParser(format);
    
    // 3. 解析文档
    const result = await parser.parse(file);
    
    // 4. 分段（如果需要）
    if (result.tokens > 1024) {
      result.sections = await this.splitSections(result);
    }
    
    return result;
  }
}
```

---

### 8. AST Code Skeleton

**OpenViking 的设计**：
- 使用 tree-sitter 提取代码骨架
- 支持多种语言：Python, JS/TS, Rust, Go, Java, C/C++
- 作为 LLM 摘要的轻量级替代

**骨架内容**：
- 模块级文档字符串
- 导入语句列表
- 类名、基类、方法签名
- 顶级函数签名

**我们的实现建议**：
```javascript
class CodeSkeletonExtractor {
  constructor() {
    this.languages = {
      python: new PythonExtractor(),
      javascript: new JavaScriptExtractor(),
      typescript: new TypeScriptExtractor(),
      go: new GoExtractor(),
      rust: new RustExtractor()
    };
  }
  
  async extract(code, language) {
    const extractor = this.languages[language];
    
    if (!extractor) {
      return null;  // 回退到 LLM
    }
    
    const skeleton = await extractor.extract(code);
    
    return {
      docstring: skeleton.docstring,
      imports: skeleton.imports,
      classes: skeleton.classes,
      functions: skeleton.functions
    };
  }
}
```

---

### 9. 关系管理

**OpenViking 的设计**：
```python
# 添加关系
await client.link(
    source="viking://resources/docs/api.md",
    target="viking://resources/docs/auth.md",
    relation="related_to"
)

# 查询关系
relations = await client.relations("viking://resources/docs/api.md")

# 删除关系
await client.unlink(source, target, relation)
```

**我们的实现建议**：
```javascript
class RelationManager {
  async link(source, target, relation) {
    await this.storage.addRelation({
      source: source,
      target: target,
      relation: relation,
      createdAt: Date.now()
    });
  }
  
  async relations(uri) {
    return await this.storage.getRelations(uri);
  }
  
  async unlink(source, target, relation) {
    await this.storage.removeRelation(source, target, relation);
  }
}
```

---

## 🟢 低优先级功能

### 10. 导入导出 (ovpack)

**OpenViking 的设计**：
```python
# 导出
await client.export_ovpack(
    uris=["viking://resources/project/"],
    output="/path/to/export.ovpack"
)

# 导入
await client.import_ovpack("/path/to/export.ovpack")
```

**我们的实现建议**：
```javascript
class PackManager {
  async export(uris, output) {
    const pack = {
      version: '1.0',
      exportedAt: Date.now(),
      items: []
    };
    
    for (const uri of uris) {
      const item = await this.readUri(uri);
      pack.items.push(item);
    }
    
    await fs.writeFile(output, JSON.stringify(pack));
  }
  
  async import(packFile) {
    const pack = JSON.parse(await fs.readFile(packFile));
    
    for (const item of pack.items) {
      await this.writeUri(item.uri, item.content);
    }
  }
}
```

---

## 📈 实施优先级建议

### Phase 1：核心检索增强（2-3 周）
1. ✅ 分层压缩器（已完成）
2. 🔥 意图分析 (Intent Analysis)
3. 🔥 类型化查询 (TypedQuery)
4. 🔥 重排序 (Rerank)

### Phase 2：Session 管理（1-2 周）
5. 🔥 Session 生命周期管理
6. 🔥 Message 记录和使用追踪
7. 🔥 Session 归档和压缩

### Phase 3：记忆提取增强（1-2 周）
8. 🔥 8 类记忆提取
9. 🔥 LLM 去重决策

### Phase 4：文件系统范式（2-3 周）
10. 🔥 Viking URI 系统
11. 🔥 文件系统命令 (ls, tree, read)
12. 🔥 层级检索 (Hierarchical Retrieval)

### Phase 5：文档处理（1-2 周）
13. 🟡 文档解析器 (Parser)
14. 🟡 AST Code Skeleton

### Phase 6：扩展功能（1 周）
15. 🟡 关系管理
16. 🟢 导入导出

---

## 🎯 总结

### 我们已经比 OpenViking 更好的地方：
- ✅ 智能去重（4 种去重策略）
- ✅ 生命周期管理（自动归档清理）
- ✅ 分层压缩器（刚实现）

### OpenViking 比我们好的地方：
- 🔥 文件系统范式（直观易用）
- 🔥 意图分析（理解用户真实意图）
- 🔥 层级检索（目录级别检索）
- 🔥 Session 管理（完整的对话管理）
- 🔥 8 类记忆提取（更细粒度）

### 建议实施顺序：
1. **Phase 1**：意图分析 + 重排序（提升检索精准度）
2. **Phase 2**：Session 管理（完善对话管理）
3. **Phase 3**：记忆提取增强（提升记忆质量）
4. **Phase 4**：文件系统范式（提升易用性）
5. **Phase 5-6**：扩展功能（按需实现）

---

**版本**: v5.0.1  
**更新时间**: 2026-04-09  
**参考**: [OpenViking GitHub](https://github.com/volcengine/OpenViking)

---

## v5.0 更新状态

> **2026-04-09**: 所有 OpenViking 核心功能已完整移植到 Unified Memory v5.0

### ✅ 已完成的功能（100%）

| 功能模块 | OpenViking | Unified Memory v5.0 | 状态 |
|---------|-----------|---------------------|------|
| **分层信息模型 (L0/L1/L2)** | ✅ | ✅ | 已实现 |
| **记忆类型系统** | 8 类 | 8 类 | ✅ 已实现 |
| **Viking URI 系统** | ✅ | ✅ | ✅ 已实现 |
| **意图分析 (Intent Analysis)** | ✅ | ✅ | ✅ 已实现 |
| **类型化查询 (TypedQuery)** | ✅ | ✅ | ✅ 已实现 |
| **层级检索 (Hierarchical Retrieval)** | ✅ | ✅ | ✅ 已实现 |
| **重排序 (Rerank)** | ✅ | ✅ | ✅ 已实现 |
| **Session 管理** | ✅ | ✅ | ✅ 已实现 |
| **Message 记录** | ✅ | ✅ | ✅ 已实现 |
| **Context 使用追踪** | ✅ | ✅ | ✅ 已实现 |
| **8 类记忆提取** | ✅ | ✅ | ✅ 已实现 |
| **LLM 去重决策** | ✅ | ✅ | ✅ 已实现 |
| **文件系统范式** | ✅ | ✅ | ✅ 已实现 |
| **文档解析器 (Parser)** | ✅ | ✅ | ✅ 已实现 |
| **TreeBuilder** | ✅ | ✅ | ✅ 已实现 |
| **SemanticQueue** | ✅ | ✅ | ✅ 已实现 |
| **AST Code Skeleton** | ✅ | ✅ | ✅ 已实现 |
| **关系管理** | ✅ | ✅ | ✅ 已实现 |

### 🏆 我们的独特优势

| 功能 | OpenViking | Unified Memory v5.0 | 说明 |
|------|-----------|---------------------|------|
| **智能去重** | ❌ | ✅ | 4 种去重策略 |
| **生命周期管理** | ❌ | ✅ | 自动归档清理 |
| **记忆类型系统** | ❌ | ✅ | 6 种记忆类型自动检测 |
| **四层管线 (L0-L3)** | L0-L2 | ✅ | 多一层 L3 用户画像 |
| **Weibull 衰减** | ❌ | ✅ | 遗忘曲线模拟 |
| **双存储后端** | ❌ | ✅ | LanceDB + SQLite |
| **Benchmark 验证** | ❌ | ✅ | recall@K / precision@K / MRR |
| **插件系统** | ❌ | ✅ | 5 种 Hook 可扩展 |
| **中文分词** | ❌ | ✅ | @node-rs/jieba 原生集成 |

### 🚀 OpenVikingSystem 使用示例

```javascript
import { createOpenVikingSystem } from 'unified-memory';

// 创建系统实例
const system = createOpenVikingSystem({
  enableIntentAnalysis: true,
  enableHierarchicalRetrieval: true,
  enableRerank: true,
  enableSessionManagement: true,
  enableMemoryExtraction: true,
  enableFileSystem: true,
  enableDocumentParsing: true,
  enableRelationManagement: true,
  enableLayeredCompression: true
});

await system.initialize();

// 使用 Viking URI 搜索
const results = await system.find('OAuth authentication');

// 使用复杂查询（自动意图分析）
const results = await system.search('帮我创建一个 RFC 文档', sessionContext, {
  userId: 'ou_123',
  agentId: 'agent_001',
  useRerank: true,
  useLayeredCompression: true
});

// Session 管理
const session = await system.getSession('chat_001', { autoCreate: true });
await system.addMessage('chat_001', 'user', '我偏好使用深色主题');
await system.commitSession('chat_001');
```
