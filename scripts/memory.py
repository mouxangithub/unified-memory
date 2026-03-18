#!/usr/bin/env python3
"""
Memory System 0.1.0 - Unified Entry (Complete)

Features:
- Hierarchical Cache (MemoryHierarchy)
- Knowledge Merging (KnowledgeMerger)
- Predictive Loading (PredictiveLoader)
- Confidence Validation (ConfidenceValidator)
- Feedback Learning (FeedbackLearner)
- Smart Forget (SmartForgetter)
- Auto Extraction (AutoExtractor)
- Quality Metrics (MemoryQuality)
- Data Import/Export (MemoryIO)
- Advanced Search (MemorySearch)
- Agent Integration (AgentIntegration)

Usage:
    # Core
    memory.py status                 # System status
    memory.py init                   # Initialize
    memory.py rebuild                # Rebuild hierarchy
    memory.py merge                  # Merge knowledge
    memory.py stats                  # Detailed stats
    
    # Context & Search
    memory.py context --query "query" # Get context
    memory.py analyze --query "query" # Analyze & preload
    memory.py search --query "query"  # Advanced search
    
    # Quality & Validation
    memory.py validate               # Validate memories
    memory.py quality                # Quality report
    memory.py feedback               # Feedback learning
    
    # Maintenance
    memory.py forget                 # Smart forget
    memory.py extract --conversation "text" # Auto extract
    
    # Data
    memory.py export --format json   # Export memories
    memory.py import --file backup.json # Import memories
    
    # Agent Integration
    memory.py agent-start --context "task"   # Agent start
    memory.py agent-end                     # Agent end
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入 v7.0 模块
from memory_hierarchy import MemoryHierarchy
from knowledge_merger import KnowledgeMerger
from predictive_loader import PredictiveLoader
from confidence_validator import ConfidenceValidator
from feedback_learner import FeedbackLearner
from smart_forgetter import SmartForgetter

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MEMORY_FILE = MEMORY_DIR / "memories.json"

# 向量数据库
HAS_LANCEDB = False
try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    pass


class MemorySystemV7:
    """统一记忆系统 0.1.0 (完整版)"""
    
    def __init__(self):
        # 核心模块
        self.hierarchy = MemoryHierarchy()
        self.merger = KnowledgeMerger()
        self.predictor = PredictiveLoader()
        self.validator = ConfidenceValidator()
        self.learner = FeedbackLearner()
        self.forgetter = SmartForgetter()
        
        self._load_memories()
    
    def _load_memories(self):
        """加载所有记忆"""
        self.memories = []
        
        # 从向量数据库加载
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                if result:
                    count = len(result.get("id", []))
                    self.memories = [
                        {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        for i in range(count)
                    ]
                print(f"📚 从向量数据库加载 {len(self.memories)} 条记忆")
            except Exception as e:
                print(f"⚠️ 向量数据库加载失败: {e}")
        
        # 从 JSON 文件加载
        if MEMORY_FILE.exists():
            try:
                file_memories = json.loads(MEMORY_FILE.read_text())
                self.memories.extend(file_memories)
                print(f"📚 从文件加载 {len(file_memories)} 条记忆")
            except Exception as e:
                print(f"⚠️ 文件加载失败: {e}")
        
        # 去重
        seen_ids = set()
        unique = []
        for m in self.memories:
            mid = m.get("id")
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                unique.append(m)
        self.memories = unique
        
        # 添加置信度信息
        for mem in self.memories:
            mem["confidence"] = self.validator.get_confidence(mem.get("id"))
        
        print(f"✅ 共 {len(self.memories)} 条唯一记忆")
    
    def init(self):
        """初始化系统"""
        print("🔄 初始化 Memory v7.0...")
        
        # 重建分层
        if self.memories:
            self.hierarchy.rebuild_from_memories(self.memories)
        
        # 检测冲突
        conflicts = self.validator.detect_conflicts(self.memories)
        if conflicts:
            print(f"⚠️ 发现 {len(conflicts)} 个矛盾记忆")
        
        print("✅ 初始化完成")
    
    def rebuild(self):
        """重建分层"""
        if not self.memories:
            print("⚠️ 没有记忆")
            return
        
        self.hierarchy.rebuild_from_memories(self.memories)
        print("✅ 重建完成")
    
    def merge_knowledge(self):
        """合并知识块"""
        if not self.memories:
            print("⚠️ 没有记忆")
            return
        
        blocks = self.merger.merge_all(self.memories)
        print(f"✅ 生成 {len(blocks)} 条知识块")
    
    def analyze(self, query: str) -> Dict:
        """分析查询并预加载"""
        result = self.predictor.analyze_and_preload(query, self.memories)
        context = self.hierarchy.get_context(query)
        
        return {
            "prediction": result["prediction"],
            "preloaded": result["preloaded_count"],
            "context_from_hierarchy": len(context),
            "total_context": len(context) + result["preloaded_count"]
        }
    
    def get_context(self, query: str, max_memories: int = 10) -> List[Dict]:
        """获取上下文记忆"""
        context = self.hierarchy.get_context(query, max_memories)
        
        if len(context) < max_memories:
            prediction = self.predictor.predict_topic(query)
            related = self.predictor.get_related_memories(
                prediction["current_keywords"], 
                self.memories
            )
            
            existing_ids = {m.get("id") for m in context}
            for mem in related:
                if mem.get("id") not in existing_ids:
                    context.append(mem)
                    if len(context) >= max_memories:
                        break
        
        # 添加置信度信息
        for mem in context:
            mem["confidence"] = self.validator.get_confidence(mem.get("id"))
            mem["score"] = self.learner.get_memory_score(mem.get("id"))
        
        return context
    
    def validate(self):
        """验证记忆"""
        # 扫描过时记忆
        stale = self.validator.scan_stale(self.memories)
        print(f"📋 发现 {len(stale)} 条可能过时的记忆")
        
        # 检测冲突
        conflicts = self.validator.detect_conflicts(self.memories)
        print(f"📋 发现 {len(conflicts)} 个矛盾")
        
        return {"stale": len(stale), "conflicts": len(conflicts)}
    
    def feedback(self):
        """应用反馈调整"""
        adjustments = self.learner.adjust_importance(self.memories)
        
        # 保存调整后的记忆
        if adjustments:
            MEMORY_FILE.write_text(json.dumps(self.memories, ensure_ascii=False, indent=2))
        
        return adjustments
    
    def forget(self, dry_run: bool = True):
        """智能遗忘"""
        # 找出可遗忘的记忆
        forgettable = self.forgetter.find_forgettable(self.memories)
        
        # 找出重复记忆
        duplicates = self.forgetter.find_duplicates(self.memories)
        
        result = {
            "forgettable": len(forgettable),
            "duplicate_groups": len(duplicates),
            "total_to_remove": len(forgettable) + sum(len(g)-1 for g in duplicates)
        }
        
        if not dry_run and result["total_to_remove"] > 0:
            # 执行遗忘
            forget_ids = {f["id"] for f in forgettable}
            remaining = [m for m in self.memories if m.get("id") not in forget_ids]
            
            # 合并重复（保留每组第一条）
            for group in duplicates:
                for mem_id in group[1:]:
                    remaining = [m for m in remaining if m.get("id") != mem_id]
            
            MEMORY_FILE.write_text(json.dumps(remaining, ensure_ascii=False, indent=2))
            self.memories = remaining
        
        return result
    
    def stats(self) -> Dict:
        """详细统计"""
        hierarchy_stats = self.hierarchy.stats()
        merger_stats = self.merger.stats()
        predictor_status = self.predictor.status()
        validator_stats = self.validator.stats()
        learner_stats = self.learner.stats()
        forgetter_stats = self.forgetter.stats()
        
        return {
            "system": "Memory 0.1.0",
            "version": "0.1.0",
            "total_memories": len(self.memories),
            "hierarchy": hierarchy_stats,
            "knowledge_merger": merger_stats,
            "predictor": predictor_status,
            "validator": validator_stats,
            "learner": learner_stats,
            "forgetter": forgetter_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def status(self) -> str:
        """简洁状态"""
        h = self.hierarchy.stats()
        m = self.merger.stats()
        v = self.validator.stats()
        l = self.learner.stats()
        f = self.forgetter.stats()
        
        lines = [
            "🧠 Memory 0.1.0 完整状态",
            "=" * 50,
            f"📚 总记忆: {len(self.memories)} 条",
            "",
            "📊 分层缓存:",
            f"  🔥 L1 热: {h['L1_hot']['count']}/{h['L1_hot']['max_size']} (avg: {h['L1_hot']['avg_importance']})",
            f"  🌡️ L2 温: {h['L2_warm']['count']}/{h['L2_warm']['max_size']} (avg: {h['L2_warm']['avg_importance']})",
            f"  ❄️ L3 冷: {h['L3_cold']['count']}",
            "",
            "📦 知识合并:",
            f"  知识块: {m['total_knowledge_blocks']}",
            f"  Token 节省: ~{m['estimated_tokens_saved']}",
            "",
            "✅ 置信度:",
            f"  已验证: {v['by_confidence'].get('✅ 已验证', 0)}",
            f"  可能过时: {v['by_confidence'].get('⚠️ 可能过时', 0)}",
            f"  矛盾: {v['by_confidence'].get('❌ 矛盾', 0)}",
            "",
            "📝 反馈学习:",
            f"  总反馈: {l['total_feedback']}",
            f"  修正: {l['total_corrections']}",
            "",
            "🗑️ 智能遗忘:",
            f"  已遗忘: {f['state'].get('forgotten_count', 0)}",
            f"  已归档: {f['state'].get('archived_count', 0)}",
            f"  已压缩: {f['state'].get('compressed_count', 0)}",
            "=" * 50
        ]
        
        return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Memory System 0.1.0 (完整版)")
    parser.add_argument("command", choices=[
        "status", "init", "rebuild", "merge", "analyze", "context", 
        "validate", "feedback", "forget", "stats", "webui"
    ])
    parser.add_argument("--query", "-q", help="查询内容")
    parser.add_argument("--max", type=int, default=10, help="最大记忆数")
    parser.add_argument("--dry-run", action="store_true", help="仅预览")
    parser.add_argument("--port", "-p", type=int, default=38080, help="Web UI 端口")
    
    args = parser.parse_args()
    
    print("🚀 启动 Memory 0.1.0 (完整版)...")
    mem = MemorySystemV7()
    
    if args.command == "status":
        print(mem.status())
    
    elif args.command == "init":
        mem.init()
    
    elif args.command == "rebuild":
        mem.rebuild()
    
    elif args.command == "merge":
        mem.merge_knowledge()
    
    elif args.command == "analyze":
        if not args.query:
            print("❌ 请指定 --query")
            sys.exit(1)
        result = mem.analyze(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "context":
        if not args.query:
            print("❌ 请指定 --query")
            sys.exit(1)
        context = mem.get_context(args.query, args.max)
        print(json.dumps(context, ensure_ascii=False, indent=2))
    
    elif args.command == "validate":
        result = mem.validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "feedback":
        result = mem.feedback()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "forget":
        result = mem.forget(args.dry_run)
        if args.dry_run:
            print(f"📋 预览: 将删除 {result['total_to_remove']} 条记忆")
        else:
            print(f"✅ 已删除 {result['total_to_remove']} 条记忆")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "stats":
        stats = mem.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.command == "webui":
        import subprocess
        import webbrowser
        import os
        
        port = args.port
        script_dir = os.path.dirname(os.path.abspath(__file__))
        webui_script = os.path.join(script_dir, "memory_webui.py")
        
        print(f"🌐 启动 Memory Web UI...")
        print(f"   端口: {port}")
        print(f"   地址: http://localhost:{port}")
        
        # 后台启动
        subprocess.Popen(
            ["python3", webui_script, "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 自动打开浏览器
        webbrowser.open(f"http://localhost:{port}")
        
        print("✅ Web UI 已启动，浏览器已打开")
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
