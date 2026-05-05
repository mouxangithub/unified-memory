> 🏗️ **系统架构师** | 步骤 1/6 | 191.0s

---

<think>用户要求我设计 Unified Memory v5 的完整系统架构。这是一个企业级的记忆存储系统，需要覆盖：

1. API Gateway 层
2. 版本控制
3. 多级缓存
4. 监控指标
5. 备份恢复
6. 归档策略
7. 性能基准

用户要求输出：
1. system_architecture.md - 系统架构文档
2. api_spec.yaml - OpenAPI 3.0 规范
3. data_model.md - 数据模型设计
4. 接口约束文件

我需要按照软件架构师的角色来设计这个系统。让我开始：

## 设计思路

### 整体架构
- 使用微服务架构，但保持模块化设计
- 支持水平扩展
- 限界上下文：API Gateway、记忆服务、版本服务、缓存服务、归档服务、备份服务、监控服务

### 技术选型理由
- Python 3.11+: 现代异步支持，性能提升
- FastAPI: 高性能 async API 框架
- Redis: L2 缓存和分布式锁
- PostgreSQL: 主数据存储，支持 JSONB 和版本控制扩展
- Qdrant/Milvus: 向量数据库，用于语义检索

### 模块设计

1. **API Gateway**: 认证、限流、路由
2. **Memory Service**: 记忆的 CRUD 操作
3. **Version Service**: 版本管理和差异计算


4. **Cache Service**: 多级缓存协调
5. **Archive Service**: 冷热数据管理
6. **Backup Service**: 备份恢复
7. **Monitor Service**: 指标收集

现在开始逐个生成文档，从系统架构开始，然后是 OpenAPI 规范、数据模型和接口约束。

系统架构采用分层微服务设计，API Gateway 负责入口流量管理，核心服务层处理业务逻辑，存储层管理各类数据源，基础设施层提供运行时环境。版本控制模块中，数据模型包含 memory_id 作为主键、版本号、内存内容等字段，并通过保留策略和差异算法来管理版本生命周期。多级缓存架构通过 L1 本地缓存、L2 分布式缓存和 L3 向量缓存来提升性能。监控指标体系覆盖 API 响应、缓存效率和系统资源。备份恢复策略包括增量、全量和时间点恢复机制。归档策略则根据数据热度在热、温、冷存储之间自动流转。

性能基准测试涵盖不同场景、并发级别和预热策略，输出格式为 JSON。现在开始实现系统架构设计。
</think>

# Unified Memory v5 系统架构设计

我将为你设计完整的系统架构，包括架构文档、API 规范、数据模型和接口约束文件。

## 1. system_architecture.md

```markdown
# Unified Memory v5 系统架构文档

## 1. 概述

### 1.1 系统目标

Unified Memory 是一个统一记忆存储系统，提供以下核心能力：
- **向量检索**：支持语义相似度搜索
- **时间序列版本控制**：完整的历史版本追踪
- **多级缓存**：L1/L2/L3 三层缓存加速访问
- **企业级可靠性**：备份恢复、归档策略、监控告警

### 1.2 设计原则

| 原则 | 描述 |
|------|------|
| 可用性优先 | 支持多副本部署，单节点故障不影响服务 |
| 性能导向 | 多级缓存 + 向量化索引，确保毫秒级响应 |
| 可观测性 | 全链路追踪，详细指标采集 |
| 可演进性 | 模块化设计，支持独立扩展各组件 |
| 成本效率 | 冷热分层存储，平衡性能与成本 |

## 2. 系统架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Python    │  │     Go      │  │   Rust      │  │   Web UI    │       │
│  │   SDK       │  │   SDK       │  │   SDK       │  │             │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────┘
          │                │                │                │
          └────────────────┴────────┬───────┴────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                            API Gateway 层                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      API Gateway                                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ 认证模块  │  │ 限流模块  │  │ 路由模块  │  │ 协议转换  │            │   │
│  │  │ JWT/API Key│ │令牌桶算法 │  │ REST/WS  │  │HTTP/WS   │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                            服务网格层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Memory    │  │   Version   │  │   Archive   │  │   Backup    │       │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │       │
│  │             │  │             │  │             │  │             │       │
│  │ • CRUD      │  │ • 版本管理   │  │ • 冷热分层  │  │ • 备份调度  │       │
│  │ • 向量检索  │  │ • 差异计算  │  │ • 压缩存储  │  │ • 恢复操作  │       │
│  │ • 缓存协调  │  │ • 版本回滚  │  │ • 生命周期  │  │ • 校验恢复  │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │                │               │
│  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐        │
│  │                      事件总线 (Redis Pub/Sub)                  │        │
│  └────────────────────────────────────────────────────────────────┘        │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                            存储层                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   PostgreSQL    │  │   Qdrant        │  │   Redis         │            │
│  │                 │  │                 │  │                 │            │
│  │ • 主数据存储    │  │ • 向量索引      │  │ • L2 缓存       │            │
│  │ • 版本历史      │  │ • 语义检索     │  │ • 分布式锁      │            │
│  │ • 元数据索引    │  │ • 近似搜索      │  │ • 会话存储      │            │
│  │                 │  │                 │  │ • 消息队列      │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
└───────────┼─────────────────────┼───────────────────┼─────────────────────┘
            │                     │                   │
┌───────────┼─────────────────────┼───────────────────┼─────────────────────┐
│           │            基础设施层 │                   │                     │
│  ┌────────┴────────┐  ┌─────────┴────────┐  ┌────────┴────────┐           │
│  │   S3 Compatible│  │   Vector Index    │  │   Monitoring   │           │
│  │   Storage      │  │   (Qdrant/Milvus) │  │   (Prometheus) │           │
│  │                 │  │                   │  │                 │           │
│  │ • 备份存储     │  │ • SSD 热数据     │  │ • Grafana      │           │
│  │ • 归档存储     │  │ • HDD 温数据     │  │ • Alertmanager │           │
│  │ • 压缩归档     │  │                   │  │                 │           │
│  └─────────────────┘  └───────────────────┘  └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 组件职责矩阵

| 组件 | 职责 | 依赖 | 可独立部署 |
|------|------|------|------------|
| API Gateway | 认证、限流、路由、协议转换 | 所有服务 | 是 |
| Memory Service | 记忆 CRUD、向量检索 | PostgreSQL, Qdrant, Redis | 是 |
| Version Service | 版本管理、差异计算 | PostgreSQL, Redis | 是 |
| Archive Service | 冷热分层、压缩 | PostgreSQL, S3 | 是 |
| Backup Service | 备份调度、恢复 | PostgreSQL, S3 | 是 |
| Monitor Service | 指标采集、告警 | Prometheus, Redis | 是 |

### 2.3 数据流向

```
写入流程：
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
│ Client  │───▶│ Gateway   │───▶│ Memory   │───▶│ PostgreSQL│
└─────────┘    └──────────┘    │ Service  │    └───────────┘
                               │          │    ┌───────────┐
                               │ L1 Cache │───▶│  Qdrant   │
                               └──────────┘    └───────────┘
                                      │
                               ┌──────┴──────┐
                               ▼             ▼
                          ┌────────┐   ┌────────┐
                          │ Redis  │   │Version │
                          │  L2    │   │Service │
                          └────────┘   └────────┘

读取流程：
┌─────────┐    ┌──────────┐    ┌─────────────────┐
│ Client  │───▶│ Gateway   │───▶│   L1 Cache Hit?  │
└─────────┘    └──────────┘    └────────┬─────────┘
                                        │
                            ┌───────────┼───────────┐
                            ▼ No        │           ▼ Yes
                    ┌──────────────┐   │    ┌─────────────┐
                    │ L2 Cache Hit? │   │    │ Return Data │
                    └───────┬──────┘   │    └─────────────┘
                            │          │
                ┌───────────┼───────────┼───────────┐
                ▼ No        ▼           ▼           ▼
        ┌──────────────┐  ┌────────────────────────────┐
        │ DB Fetch +   │  │ L1: Dict (1000 items)      │
        │ Update Cache │  │ L2: Redis (1 hour TTL)     │
        └──────────────┘  │ L3: Qdrant (24 hour TTL)   │
                          └────────────────────────────┘
```

## 3. API Gateway 层

### 3.1 认证机制

```python
# 认证流程
class AuthFlow:
    """
    支持两种认证方式：
    1. JWT Token: 适用于前端应用
    2. API Key: 适用于服务端集成
    """
    
    jwt_config = {
        "algorithm": "RS256",
        "expiration": 3600,  # 1 hour
        "refresh_window": 300  # 5 min before expiry
    }
    
    api_key_config = {
        "header": "X-API-Key",
        "prefix": "um_",
        "length": 32
    }
```

### 3.2 限流实现

```python
# 令牌桶算法配置
RateLimitConfig = {
    "default": {
        "rate": 1000,        # tokens per minute
        "burst": 100,        # max burst size
        "strategy": "token_bucket"
    },
    "tier_enterprise": {
        "rate": 10000,
        "burst": 1000,
        "strategy": "token_bucket"
    }
}

# 限流响应头
RateLimitHeaders = {
    "X-RateLimit-Limit": "1000",           # 请求限制
    "X-RateLimit-Remaining": "999",         # 剩余请求数
    "X-RateLimit-Reset": "1699574400",      # 重置时间戳
    "Retry-After": "60"                      # retry after seconds (on 429)
}
```

### 3.3 统一错误码体系

| 错误码 | HTTP 状态 | 描述 |
|--------|-----------|------|
| 1000 | 400 | 参数错误 |
| 1001 | 400 | 必需参数缺失 |
| 1002 | 400 | 参数格式错误 |
| 1100 | 401 | 认证失败 |
| 1101 | 401 | Token 过期 |
| 1102 | 401 | 无效的 API Key |
| 1200 | 403 | 权限不足 |
| 1300 | 404 | 记忆不存在 |
| 1301 | 404 | 版本不存在 |
| 1400 | 429 | 请求频率超限 |
| 1500 | 500 | 内部服务错误 |
| 1501 | 503 | 服务不可用 |
| 1502 | 504 | 上游超时 |

## 4. 版本控制系统

### 4.1 数据模型

```sql
-- 记忆表
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    content JSONB NOT NULL,
    embedding VECTOR(1536),  -- For pgvector, or use external Qdrant
    metadata JSONB DEFAULT '{}',
    current_version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active',  -- active/archived/deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 版本表
CREATE TABLE memory_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id),
    version INT NOT NULL,
    content JSONB NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    diff_from_previous JSONB,  -- 增量差异
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(64),
    UNIQUE(memory_id, version)
);

-- 索引
CREATE INDEX idx_memories_namespace ON memories(namespace);
CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_memories_status ON memories(status);
CREATE INDEX idx_versions_memory ON memory_versions(memory_id, version DESC);
CREATE INDEX idx_versions_created ON memory_versions(created_at);
```

### 4.2 保留策略

```python
class RetentionPolicy:
    """
    版本保留规则：
    1. 最多保留最近 30 个版本
    2. 或最近 90 天内的所有版本
    两者取交集
    """
    
    config = {
        "max_versions": 30,
        "max_age_days": 90,
        "archive_before_delete": True,  # 删除前先归档
        "compression": "gzip"           # 归档时压缩
    }
```

### 4.3 版本差异计算

```python
class VersionDiff:
    """
    差异计算策略：
    1. JSON 结构差异（键的增删改）
    2. 向量相似度（内容语义变化）
    """
    
    @staticmethod
    def compute_json_diff(old: dict, new: dict) -> dict:
        """计算 JSON 结构差异"""
        return {
            "added": {k: new[k] for k in new if k not in old},
            "removed": {k: old[k] for k in old if k not in new},
            "modified": {k: {"old": old[k], "new": new[k]} 
                        for k in old if k in new and old[k] != new[k]},
            "unchanged": [k for k in old if k in new and old[k] == new[k]]
        }
    
    @staticmethod
    def compute_semantic_similarity(emb1: list, emb2: list) -> float:
        """计算向量余弦相似度"""
        # 0.0 = 完全不相似, 1.0 = 完全相同
        return cosine_similarity(emb1, emb2)
```

## 5. 多级缓存系统

### 5.1 缓存架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Cache Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  L1: Local Cache (In-Memory)                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Implementation: Python dict + LRU                   │    │
│  │  Capacity: 1000 items max                            │    │
│  │  TTL: No expiration, LRU eviction                   │    │
│  │  Hit Latency: ~0.01ms                               │    │
│  │  Thread-safe: per-worker process                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  L2: Distributed Cache (Redis)                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Implementation: Redis Cluster                       │    │
│  │  TTL: 1 hour                                        │    │
│  │  Max Memory: 10GB per node                           │    │
│  │  Eviction: allkeys-lru                               │    │
│  │  Hit Latency: ~1ms                                   │    │
│  │  Persistence: RDB + AOF                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  L3: Vector Cache (Qdrant)                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Implementation: Qdrant / Milvus                     │    │
│  │  TTL: 24 hours                                      │    │
│  │  Purpose: Semantic search cache                       │    │
│  │  Hit Latency: ~10ms                                  │    │
│  │  Storage: SSD-optimized collection                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  Cold Storage: PostgreSQL + S3                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  PostgreSQL: Active data, recent versions            │    │
│  │  S3: Archived data, backups                          │    │
│  │  Hit Latency: ~50ms - 500ms                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 缓存键设计

```python
class CacheKey:
    """
    缓存键格式：namespace:memory_id:version:data_type
    
    示例：
    - ns1:abc123:1:meta       -> 元数据
    - ns1:abc123:1:content   -> 内容
    - ns1:abc123:1:embedding -> 向量
    - ns1:abc123:latest      -> 最新版本快捷键
    - search:ns1:query_hash  -> 搜索结果缓存
    """
    
    @staticmethod
    def build(namespace: str, memory_id: str, version: int, data_type: str) -> str:
        return f"{namespace}:{memory_id}:{version}:{data_type}"
    
    @staticmethod
    def latest(namespace: str, memory_id: str) -> str:
        return f"{namespace}:{memory_id}:latest"
    
    @staticmethod
    def search(namespace: str, query_hash: str) -> str:
        return f"search:{namespace}:{query_hash}"
```

### 5.3 缓存协调策略

```python
class CacheCoordinator:
    """
    缓存更新策略：Write-Through + Lazy Loading
    """
    
    async def get(self, key: str) -> Optional[dict]:
        # 1. 尝试 L1
        if data := self.l1_cache.get(key):
            self.metrics.l1_hit()
            return data
        
        # 2. 尝试 L2
        if data := await self.l2_cache.get(key):
            self.metrics.l2_hit()
            self.l1_cache.set(key, data)  # 提升到 L1
            return data
        
        # 3. 尝试 L3 (向量相关)
        if is_vector_key(key):
            if data := await self.l3_cache.get(key):
                self.metrics.l3_hit()
                await self.l2_cache.set(key, data)
                self.l1_cache.set(key, data)
                return data
        
        # 4. 回源
        self.metrics.cache_miss()
        return await self.fetch_from_db(key)
    
    async def set(self, key: str, data: dict, ttl_l2: int = 3600, ttl_l3: int = 86400):
        # 同步写入所有层
        self.l1_cache.set(key, data)
        await self.l2_cache.set(key, data, ttl_l2)
        if is_vector_key(key):
            await self.l3_cache.set(key, data, ttl_l3)
    
    async def invalidate(self, key: str):
        """失效缓存"""
        self.l1_cache.delete(key)
        await self.l2_cache.delete(key)
        if is_vector_key(key):
            await self.l3_cache.delete(key)
```

## 6. 监控指标体系

### 6.1 指标分类

```yaml
# Prometheus metrics configuration
metrics:
  api:
    - name: api_requests_total
      type: counter
      labels: [method, endpoint, status]
      description: Total API requests
      
    - name: api_request_duration_seconds
      type: histogram
      labels: [method, endpoint]
      buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
      description: Request latency
      
    - name: api_errors_total
      type: counter
      labels: [endpoint, error_code]
      description: API errors
      
    - name: api_active_connections
      type: gauge
      description: Active WebSocket connections

  cache:
    - name: cache_hits_total
      type: counter
      labels: [level]  # L1, L2, L3
      description: Cache hits
      
    - name: cache_misses_total
      type: counter
      labels: [level]
      description: Cache misses
      
    - name: cache_hit_ratio
      type: gauge
      labels: [level]
      description: Cache hit ratio (calculated)
      
    - name: cache_operations_total
      type: counter
      labels: [operation, level]  # get, set, delete
      description: Cache operations

  storage:
    - name: storage_operations_total
      type: counter
      labels: [operation, storage_type]  # read, write, delete
      description: Storage operations
      
    - name: storage_latency_seconds
      type: histogram
      labels: [operation, storage_type]
      description: Storage operation latency
      
    - name: storage_size_bytes
      type: gauge
      labels: [storage_type]  # postgres, qdrant, redis, s3
      description: Storage used

  business:
    - name: memories_total
      type: gauge
      labels: [namespace, status]
      description: Total memories count
      
    - name: memory_versions_total
      type: gauge
      labels: [namespace]
      description: Total versions count
      
    - name: archive_ratio
      type: gauge
      labels: [namespace]
      description: Archived memories ratio

  system:
    - name: process_cpu_seconds_total
      type: counter
      description: CPU time
      
    - name: process_resident_memory_bytes
      type: gauge
      description: Memory usage
      
    - name: go_threads
      type: gauge
      description: Goroutine count
```

### 6.2 告警规则

```yaml
alerts:
  - name: HighErrorRate
    expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.05
    for: 5m
    severity: critical
    annotations:
      summary: "API error rate above 5%"
      
  - name: HighLatency
    expr: histogram_quantile(0.95, api_request_duration_seconds) > 1.0
    for: 5m
    severity: warning
    annotations:
      summary: "P95 latency above 1 second"
      
  - name: LowCacheHitRate
    expr: cache_hits_total{level="L2"} / (cache_hits_total{level="L2"} + cache_misses_total{level="L2"}) < 0.7
    for: 10m
    severity: warning
    annotations:
      summary: "L2 cache hit rate below 70%"
      
  - name: StorageNearCapacity
    expr: storage_size_bytes / storage_max_bytes > 0.85
    for: 5m
    severity: warning
    annotations:
      summary: "Storage usage above 85%"
```

## 7. 备份恢复系统

### 7.1 备份策略

```python
class BackupStrategy:
    """
    备份计划：
    - 增量备份：每小时执行，备份过去 1 小时的数据变更
    - 全量备份：每日凌晨 2:00 UTC 执行
    - 保留周期：
      - 增量：保留 7 天
      - 全量：保留 30 天
    """
    
    config = {
        "incremental": {
            "schedule": "0 * * * *",  # 每小时
            "retention_days": 7,
            "type": "xtrabackup" if using_mysql else "pg_basebackup"
        },
        "full": {
            "schedule": "0 2 * * *",  # 每日凌晨2点
            "retention_days": 30,
            "time_of_day": "02:00 UTC"
        },
        "vector_db": {
            "schedule": "0 3 * * *",  # 每日凌晨3点
            "type": "qdrant_backup",
            "retention_days": 14
        }
    }
```

### 7.2 恢复能力指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RPO (Recovery Point Objective) | 1 小时 | 最近 1 小时数据可恢复 |
| RTO (Recovery Time Objective) | 15 分钟 | 15 分钟内恢复服务 |
| 恢复粒度 | 记忆级别 | 支持单条记忆恢复 |

### 7.3 恢复类型

```python
class RecoveryType(Enum):
    FULL = "full"                    # 全量恢复
    POINT_IN_TIME = "point_in_time"  # 时间点恢复
    SINGLE_MEMORY = "single_memory"  # 单条记忆恢复
    CROSS_VERSION = "cross_version" # 跨版本恢复（合并）
```

## 8. 归档策略

### 8.1 分层存储架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Lifecycle Management                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  HOT TIER (0-30 days)                                        │   │
│  │  ────────────────────                                        │   │
│  │  Storage: NVMe SSD                                           │   │
│  │  Access: < 10ms                                              │   │
│  │  Replication: 3 copies                                       │   │
│  │  Compression: None (for speed)                              │   │
│  │  Full-text index: Yes                                        │   │
│  │  Vector index: Yes (HNSW)                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  WARM TIER (30-90 days)                                       │   │
│  │  ────────────────────                                        │   │
│  │  Storage: HDD / S3 Standard                                   │   │
│  │  Access: < 100ms                                              │   │
│  │  Replication: 2 copies                                        │   │
│  │  Compression: lz4 (lightweight)                              │   │
│  │  Full-text index: Yes (optimized)                            │   │
│  │  Vector index: Yes (IVF)                                      │   │
│  │  Trigger: auto-transition via scheduled job                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  COLD TIER (90+ days)                                         │   │
│  │  ──────────────────                                           │   │
│  │  Storage: S3 Glacier / Archive                                │   │
│  │  Access: minutes to hours (restore required)                  │   │
│  │  Replication: 1 copy + 1 cross-region                         │   │
│  │  Compression: gzip (high ratio)                               │   │
│  │  Full-text index: Metadata only                              │   │
│  │  Vector index: No (regenerate on access)                     │   │
│  │  Restore cost: $0.01 per GB                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 归档触发规则

```python
class ArchiveRules:
    """
    归档决策矩阵
    """
    rules = [
        {
            "name": "age_based",
            "condition": "days_since_access >= 90",
            "action": "archive_to_cold",
            "priority": 1
        },
        {
            "name": "access_frequency",
            "condition": "days_since_access >= 30 AND access_count < 5",
            "action": "move_to_warm",
            "priority": 2
        },
        {
            "name": "explicit_archive",
            "condition": "user_requested == true",
            "action": "archive_immediately",
            "priority": 0  # highest
        }
    ]
```

## 9. 性能基准测试

### 9.1 测试场景设计

```python
class BenchmarkScenarios:
    """
    性能测试场景定义
    """
    
    scenarios = {
        "crud_iterations": {
            "description": "1000次 CRUD 迭代",
            "operations": ["create", "read", "update", "delete"],
            "iterations": 1000,
            "payload_sizes": [1, 10, 100, 1000]  # KB
        },
        "concurrency_levels": {
            "description": "不同并发级别测试",
            "levels": [1, 10, 100, 1000],
            "requests_per_level": 10000,
            "distributed": True  # 分布式压测
        },
        "cache_warmup": {
            "description": "缓存预热模拟",
            "memory_count": 100000,
            "warmup_rounds": 3,
            "sampling_rate": 0.1  # 10% 采样
        },
        "vector_search": {
            "description": "向量搜索性能",
            "collection_sizes": [10000, 100000, 1000000],
            "queries": 1000,
            "top_k": [10, 100]
        }
    }
```

### 9.2 性能目标

| 场景 | 指标 | 目标值 | 警告阈值 |
|------|------|--------|----------|
| 单次写入 | P50 延迟 | < 50ms | > 100ms |
| 单次读取 | P50 延迟 | < 10ms | > 50ms |
| 向量检索 | P99 延迟 | < 200ms | > 500ms |
| 100 并发 | QPS | > 5000 | < 3000 |
| 1000 并发 | QPS | > 20000 | < 10000 |
| 缓存命中率 | L2 命中率 | > 85% | < 70% |
| 可用性 | SLA | 99.9% | < 99.5% |

### 9.3 输出报告格式

```json
{
  "benchmark": {
    "name": "Unified Memory v5 Performance",
    "timestamp": "2024-11-20T10:30:00Z",
    "version": "5.0.0",
    "environment": {
      "cpu": "AMD EPYC 7763 64-Core",
      "memory": "128GB DDR4",
      "storage": "NVMe SSD 2TB"
    }
  },
  "results": {
    "crud": {
      "total_operations": 4000,
      "duration_seconds": 45.23,
      "throughput_ops_per_sec": 88.45,
      "latency": {
        "p50_ms": 8.5,
        "p95_ms": 25.3,
        "p99_ms": 48.7,
        "max_ms": 156.2
      }
    },
    "concurrency": {
      "1_user": {"qps": 120, "avg_latency_ms": 8.2},
      "10_users": {"qps": 1100, "avg_latency_ms": 9.1},
      "100_users": {"qps": 8500, "avg_latency_ms": 11.8},
      "1000_users": {"qps": 22000, "avg_latency_ms": 45.5}
    },
    "cache": {
      "warmup_duration_seconds": 120,
      "hit_rate": {
        "L1": 0.95,
        "L2": 0.88,
        "L3": 0.72
      }
    }
  },
  "summary": {
    "passed": true,
    "recommendations": [
      "Consider increasing L2 cache TTL to 2 hours",
      "L1 cache size could be increased to 2000 items"
    ]
  }
}
```

## 10. 安全架构

### 10.1 安全层次

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Network Layer                                           │
│     - VPC / Private Subnets                                 │
│     - Security Groups                                       │
│     - Network ACLs                                          │
│     - DDoS Protection (Cloudflare/WAF)                      │
│                                                              │
│  2. Transport Layer                                         │
│     - TLS 1.3 required                                     │
│     - Certificate pinning                                   │
│     - Perfect forward secrecy                               │
│                                                              │
│  3. Application Layer                                       │
│     - JWT / API Key authentication                          │
│     - Rate limiting                                         │
│     - Input validation                                      │
│     - SQL injection prevention                              │
│                                                              │
│  4. Data Layer                                              │
│     - Encryption at rest (AES-256)                         │
│     - Field-level encryption for sensitive data             │
│     - Secrets management (HashiCorp Vault)                  │
│     - Regular key rotation                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 加密配置

```python
encryption_config = {
    "at_rest": {
        "algorithm": "AES-256-GCM",
        "key_source": "aws_kms",  # or hashicorp_vault
        "rotation_period_days": 90
    },
    "in_transit": {
        "tls_version": "1.3",
        "cipher_suites": [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256"
        ]
    },
    "field_level": {
        "sensitive_fields": ["content", "metadata"],
        "encryption": "optional",
        "key_per_field": False
    }
}
```

## 11. 部署架构

### 11.1 Kubernetes 部署

```yaml
# deployment.yaml structure
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unified-memory-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    spec:
      containers:
        - name: api
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
          livenessProbe:
            httpGet:
              path: /health/live
