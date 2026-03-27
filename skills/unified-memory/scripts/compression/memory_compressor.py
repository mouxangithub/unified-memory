#!/usr/bin/env python3
"""
Memory Compressor - 记忆压缩模块

功能:
- 聚合相似记忆
- 生成摘要
- 归档旧记忆
- 节省存储空间
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))


class MemoryCompressor:
    """记忆压缩器"""
    
    def __init__(self):
        self.memory_dir = Path.home() / ".openclaw" / "workspace" / "memory"
        self.archive_dir = self.memory_dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def compress_old_memories(self, days: int = 30) -> Dict:
        """
        压缩旧记忆
        
        Args:
            days: 压缩多少天前的记忆
        
        Returns:
            {
                "processed": 100,
                "merged": 25,
                "saved_bytes": 50000
            }
        """
        result = {
            "processed": 0,
            "merged": 0,
            "saved_bytes": 0,
            "archives_created": 0
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 1. 扫描旧记忆
        old_memories = self._scan_old_memories(cutoff_date)
        result["processed"] = len(old_memories)
        
        if not old_memories:
            return result
        
        # 2. 聚类相似记忆
        clusters = self._cluster_similar(old_memories)
        
        # 3. 为每个聚类生成摘要
        for cluster in clusters:
            if len(cluster) > 1:
                # 多条相似记忆，合并
                summary = self._generate_summary(cluster)
                archive_id = self._archive_cluster(cluster, summary)
                
                result["merged"] += len(cluster) - 1
                result["saved_bytes"] += sum(len(m.get("text", "")) for m in cluster) - len(summary)
                result["archives_created"] += 1
        
        return result
    
    def _scan_old_memories(self, cutoff_date: datetime) -> List[Dict]:
        """扫描旧记忆"""
        memories = []
        
        # 扫描向量数据库
        vector_dir = self.memory_dir / "vector"
        if vector_dir.exists():
            try:
                import lancedb
                db = lancedb.connect(vector_dir)
                
                for table_name in db.table_names():
                    try:
                        table = db.open_table(table_name)
                        df = table.to_pandas()
                        
                        for _, row in df.iterrows():
                            created = row.get("created", "")
                            if created:
                                try:
                                    created_date = datetime.fromisoformat(created)
                                    if created_date < cutoff_date:
                                        memories.append({
                                            "id": row.get("id", ""),
                                            "text": row.get("text", ""),
                                            "category": row.get("category", ""),
                                            "created": created
                                        })
                                except:
                                    pass
                    except:
                        continue
            except:
                pass
        
        return memories
    
    def _cluster_similar(self, memories: List[Dict]) -> List[List[Dict]]:
        """聚类相似记忆"""
        if not memories:
            return []
        
        clusters = []
        used = set()
        
        for i, mem1 in enumerate(memories):
            if i in used:
                continue
            
            cluster = [mem1]
            used.add(i)
            
            for j, mem2 in enumerate(memories):
                if j in used:
                    continue
                
                # 简单的相似度判断（可以改用 embedding）
                if self._is_similar(mem1.get("text", ""), mem2.get("text", "")):
                    cluster.append(mem2)
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """判断两个文本是否相似"""
        # 简单的 Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union > threshold
    
    def _generate_summary(self, cluster: List[Dict]) -> str:
        """生成摘要"""
        texts = [m.get("text", "") for m in cluster]
        
        # 提取关键词
        all_words = " ".join(texts).lower().split()
        keywords = [w for w, c in Counter(all_words).most_common(10) if len(w) > 2]
        
        # 生成摘要
        summary = f"[聚合记忆 - {len(cluster)} 条]\n"
        summary += f"关键词: {', '.join(keywords)}\n"
        summary += f"时间范围: {cluster[0].get('created', '')} ~ {cluster[-1].get('created', '')}\n\n"
        
        # 添加原文摘要
        for i, text in enumerate(texts[:5], 1):
            summary += f"{i}. {text[:100]}...\n"
        
        return summary
    
    def _archive_cluster(self, cluster: List[Dict], summary: str) -> str:
        """归档聚类"""
        import json
        
        archive_id = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_file = self.archive_dir / f"{archive_id}.json"
        
        archive_data = {
            "id": archive_id,
            "created": datetime.now().isoformat(),
            "count": len(cluster),
            "summary": summary,
            "memories": cluster
        }
        
        archive_file.write_text(json.dumps(archive_data, ensure_ascii=False, indent=2))
        
        return archive_id
    
    def get_compression_stats(self) -> Dict:
        """获取压缩统计"""
        stats = {
            "total_memories": 0,
            "archived_memories": 0,
            "saved_bytes": 0,
            "compression_ratio": 0
        }
        
        # 统计归档
        if self.archive_dir.exists():
            for archive_file in self.archive_dir.glob("*.json"):
                import json
                try:
                    data = json.loads(archive_file.read_text())
                    stats["archived_memories"] += data.get("count", 0)
                except:
                    pass
        
        return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="记忆压缩")
    parser.add_argument("--days", type=int, default=30, help="压缩多少天前的记忆")
    parser.add_argument("--stats", action="store_true", help="查看压缩统计")
    
    args = parser.parse_args()
    
    compressor = MemoryCompressor()
    
    if args.stats:
        stats = compressor.get_compression_stats()
        print("📊 压缩统计:")
        print(f"   已归档: {stats['archived_memories']} 条")
        print(f"   节省空间: {stats['saved_bytes']} bytes")
    else:
        print(f"🗜️ 压缩 {args.days} 天前的记忆...")
        result = compressor.compress_old_memories(args.days)
        print(f"✅ 压缩完成:")
        print(f"   处理: {result['processed']} 条")
        print(f"   合并: {result['merged']} 条")
        print(f"   节省: {result['saved_bytes']} bytes")


if __name__ == "__main__":
    main()
