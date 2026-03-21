
## v0.8.0 (2026-03-21)

### ✨ 新增功能

#### 1. 敏感信息加密 (`mem encrypt/decrypt/sensitive`)
- 自动检测 8 种敏感信息（密码、API Key、Token、手机号、身份证、邮箱、信用卡、私钥）
- AES-256 加密存储
- 访问日志记录
- 权限控制
- 文件: `memory_sensitive.py`

#### 2. 记忆预测 (`mem predict`)
- 时间模式预测（工作日早上看日程、周五下午看周末计划）
- 行为模式预测（基于访问历史）
- 项目预测（截止日期临近提醒）
- 可配置置信度阈值
- 静默时段支持
- 文件: `memory_predict.py`

#### 3. 多模态记忆 (`mem multimodal`)
- **OCR** - 图片转文字（PaddleOCR / Tesseract，可配置）
- **STT** - 语音转文字（Whisper / 讯飞API，可配置）
- **CLIP** - 多模态搜索（可选）
- 所有功能默认禁用，按需启用
- 文件: `memory_multimodal.py`

### 📦 命令统计
- 总命令: 24 个（新增 4 个）
- 新增: `encrypt`, `decrypt`, `sensitive`, `predict`, `multimodal`

### 🎯 配置说明

#### 多模态功能启用
```bash
mem multimodal config          # 查看配置
mem multimodal enable ocr      # 启用OCR
mem multimodal enable stt      # 启用STT
mem multimodal enable clip     # 启用CLIP
```

#### 敏感信息检测
```bash
mem sensitive detect           # 检测敏感信息
mem sensitive scan             # 扫描并自动加密
mem sensitive audit            # 查看访问日志
```

#### 记忆预测
```bash
mem predict today              # 预测今日需求
mem predict train              # 训练预测模型
mem predict --enable-push      # 启用主动推送
```

---

## v0.7.0 (2026-03-21)

### 🔧 修复
- 修复 ClawHub 发布版本冲突问题

---

## v0.6.0 (2026-03-21)

### ✨ 新增功能

#### 1. 决策追溯链 (`mem trace`)
- 追溯记忆来源和决策背景
- 时间线视图 (`--timeline`)
- 相关记忆发现（关键词重叠）
- 文件: `memory_trace.py`

#### 2. 记忆访问热力图 (`mem heatmap`)
- 访问频率统计
- 自动提升高频记忆权重 (`--boost`)
- 热度分数可视化
- 文件: `memory_heatmap.py`

#### 3. 协作效率可视化 (`mem collab`)
- 小智+小刘任务统计
- 交接效率分析
- HTML 报告生成 (`--html`)
- 文件: `memory_collab.py`

#### 4. L3 压缩质量评估 (`mem compress-eval`)
- 压缩比、信息保留率、可读性
- 质量分布统计
- 问题检测
- 文件: `memory_compress_eval.py`

#### 5. 跨 Agent 记忆共享 (`mem realtime share`)
- 实时同步守护进程（30秒间隔）
- 优先级控制 (normal/high)
- 目标节点指定
- 文件: `memory_realtime_sync.py`

### 📦 命令统计
- 总命令: 20 个（新增 2 个）
- 新增: `collab`, `compress-eval`

### 🎯 落实小刘建议
- ✅ 决策追溯链（高优先级）
- ✅ 记忆访问热力图（高优先级）
- ✅ 主动感知缓存
- ⏳ 协作效率可视化（已实现）
- ⏳ L3压缩质量评估（已实现）

---

## v0.5.1 (2026-03-21)

### ✨ 新增
- **QMD 风格搜索** (`memory_qmd_search.py`)
  - BM25 关键词搜索（完全本地，0 Token）
  - 向量语义搜索（本地 Ollama）
  - RRF 混合融合（无需 LLM）
  - 片段级返回（省 Token）
  - 本地重排器（可选）

### 📊 Token 对比
| 模式 | Token | 速度 |
|------|-------|------|
| BM25 | 0 | ~1s |
| Vector | ~100 | ~30ms |
| Hybrid | ~100 | ~8ms |

### 🎯 与 QMD 对比
| 功能 | unified-memory | QMD |
|------|---------------|-----|
| BM25 | ✅ | ✅ |
| 向量搜索 | ✅ | ✅ |
| RRF 融合 | ✅ | ✅ |
| 本地重排 | ⚠️ 可选 | ✅ |
| 片段返回 | ✅ | ✅ |
| Agent 记忆 | ✅ | ❌ |
| 用户画像 | ✅ | ❌ |

