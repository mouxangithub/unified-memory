# 任务：用 TypeScript 实现 unified-memory 的 MCP Server

## 目标
用 TypeScript/Node.js 完全重写 unified-memory 的 MCP Server，替代当前的 Python `memory_mcp_server.py`。

## 核心功能（必须实现）

### 1. BM25 搜索引擎
- 完全本地，不调用 LLM
- 倒排索引、TF、IDF 计算
- 中英文分词（中文按字符，英文按单词）
- 参考：`memory_bm25.py`（274行）

### 2. 向量语义搜索
- 使用 Ollama API (`http://localhost:11434`) 生成嵌入
- 模型：`nomic-embed-text:latest`
- 参考：`memory_qmd_search.py`（575行）的向量搜索部分

### 3. RRF 混合融合
- Reciprocal Rank Fusion 合并 BM25 和向量结果
- 无需 LLM，纯算法
- 参考：`memory_qmd_search.py`

### 4. MCP Server 工具
使用 @modelcontextprotocol/sdk 实现，工具列表：

```
memory_search(query: string, topK?: number, mode?: string)
  → BM25+向量混合搜索，返回记忆列表

memory_store(text: string, category?: string, importance?: number)
  → 存储记忆到本地 JSON 文件

memory_list()
  → 返回所有记忆

memory_delete(id: string)
  → 删除指定记忆

memory_stats()
  → 返回统计信息（记忆数量、类别分布等）

memory_health()
  → 健康检查
```

## 技术要求

- 使用 TypeScript
- 使用 @modelcontextprotocol/sdk（已安装在 mcporter 依赖中）
- 数据存储用本地 JSON 文件（`~/.openclaw/workspace/memory/memories.json`）
- 日志写到 `~/.openclaw/workspace/memory/logs/`
- 向量索引缓存 `~/.openclaw/workspace/memory/vector_cache/`
- 配置：`~/.openclaw/workspace/memory/config.json`

## 文件结构

```
unified-memory-ts/
├── src/
│   ├── index.ts          # MCP Server 入口
│   ├── bm25.ts           # BM25 搜索引擎
│   ├── vector.ts         # Ollama 向量搜索
│   ├── fusion.ts         # RRF 混合融合
│   ├── storage.ts        # JSON 文件存储
│   ├── config.ts         # 配置管理
│   └── types.ts          # TypeScript 类型
├── package.json
└── tsconfig.json
```

## 实现顺序

1. 先写 `package.json` + `tsconfig.json`
2. `types.ts` - 定义所有类型
3. `config.ts` - 配置加载
4. `storage.ts` - JSON 存储读写
5. `bm25.ts` - BM25 搜索引擎
6. `vector.ts` - Ollama 向量搜索
7. `fusion.ts` - RRF 融合
8. `index.ts` - MCP Server 入口，组装所有工具
9. 测试运行

## 参考文件（在本目录的父目录）

- `/root/.openclaw/workspace/skills/unified-memory/scripts/memory_qmd_search.py` - QMD 风格搜索
- `/root/.openclaw/workspace/skills/unified-memory/scripts/memory_bm25.py` - BM25 实现
- `/root/.openclaw/workspace/skills/unified-memory/scripts/memory_mcp_server.py` - 当前 Python MCP Server（398行）

## 注意事项

- Ollama 已在 `http://localhost:11434` 运行，模型 `nomic-embed-text:latest` 可用
- minimax-m2.7:cloud 模型也可用于 LLM 调用（如果需要）
- 不要调用外部 API（pip/npm install 都会被阻断），只用本地工具
- 代码要健壮，有错误处理

完成后，运行 `openclaw system event --text "Done: unified-memory TS MCP Server ported" --mode now` 通知。
