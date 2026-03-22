#!/usr/bin/env python3
"""
Vector Table Repair - 自动检测并修复向量表结构

解决问题:
- There is no vector column in the data
- 表结构不一致
- 缺少向量列
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import lancedb
    import numpy as np
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False


class VectorTableRepair:
    """向量表修复工具"""
    
    def __init__(self, db_path: str = None):
        if not LANCEDB_AVAILABLE:
            raise ImportError("请安装 lancedb: pip install lancedb")
        
        self.db_path = Path(db_path or Path.home() / ".openclaw" / "workspace" / "memory" / "vector")
        self.db = lancedb.connect(self.db_path)
    
    def check_all_tables(self) -> Dict:
        """检查所有表的结构"""
        results = {
            "total": 0,
            "healthy": 0,
            "needs_repair": 0,
            "tables": []
        }
        
        for table_name in self.db.table_names():
            results["total"] += 1
            
            try:
                table = self.db.open_table(table_name)
                df = table.to_pandas()
                
                # 检查是否有向量列
                vector_cols = [col for col in df.columns if 'vector' in col.lower() or 'embedding' in col.lower()]
                
                table_info = {
                    "name": table_name,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "vector_columns": vector_cols,
                    "status": "healthy" if vector_cols else "needs_repair"
                }
                
                if vector_cols:
                    results["healthy"] += 1
                else:
                    results["needs_repair"] += 1
                
                results["tables"].append(table_info)
                
            except Exception as e:
                results["needs_repair"] += 1
                results["tables"].append({
                    "name": table_name,
                    "error": str(e),
                    "status": "error"
                })
        
        return results
    
    def repair_table(self, table_name: str, embedding_func=None) -> bool:
        """修复单个表"""
        try:
            table = self.db.open_table(table_name)
            df = table.to_pandas()
            
            # 检查是否需要修复
            vector_cols = [col for col in df.columns if 'vector' in col.lower() or 'embedding' in col.lower()]
            if vector_cols:
                print(f"✅ {table_name} 已有向量列，无需修复")
                return True
            
            print(f"🔧 修复 {table_name}...")
            
            # 添加向量列
            if embedding_func is None:
                # 默认使用 Ollama
                from unified_memory import get_ollama_embedding
                embedding_func = get_ollama_embedding
            
            # 为每行生成向量
            vectors = []
            for _, row in df.iterrows():
                text = row.get("text", "")
                if text:
                    try:
                        vec = embedding_func(text)
                        vectors.append(vec if vec else [0.0] * 768)
                    except:
                        vectors.append([0.0] * 768)
                else:
                    vectors.append([0.0] * 768)
            
            # 添加向量列
            df["vector"] = vectors
            
            # 删除旧表，创建新表
            self.db.drop_table(table_name)
            self.db.create_table(table_name, df)
            
            print(f"✅ {table_name} 修复完成，添加了 {len(vectors)} 个向量")
            return True
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            return False
    
    def repair_all(self) -> Dict:
        """修复所有需要修复的表"""
        check_result = self.check_all_tables()
        
        repaired = 0
        failed = 0
        
        for table_info in check_result["tables"]:
            if table_info.get("status") == "needs_repair":
                if self.repair_table(table_info["name"]):
                    repaired += 1
                else:
                    failed += 1
        
        return {
            "total": check_result["total"],
            "repaired": repaired,
            "failed": failed
        }
    
    def create_standard_table(self, table_name: str = "memories") -> bool:
        """创建标准格式的向量表"""
        try:
            import pyarrow as pa
            
            # 定义标准 schema
            schema = pa.schema([
                ("id", pa.string()),
                ("text", pa.string()),
                ("category", pa.string()),
                ("created", pa.string()),
                ("vector", pa.list_(pa.float32(), 768)),  # 768 维向量
                ("tags", pa.list_(pa.string())),
                ("confidence", pa.float32()),
                ("access_count", pa.int32()),
                ("last_accessed", pa.string()),
                ("source", pa.string()),
                ("metadata", pa.string())
            ])
            
            # 创建空表
            table = self.db.create_table(table_name, schema=schema, mode="overwrite")
            
            print(f"✅ 创建标准表: {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
    
    def migrate_data(self, from_table: str, to_table: str) -> bool:
        """迁移数据"""
        try:
            source = self.db.open_table(from_table)
            df = source.to_pandas()
            
            # 确保目标表存在
            if to_table not in self.db.table_names():
                self.create_standard_table(to_table)
            
            # 迁移数据
            target = self.db.open_table(to_table)
            target.add(df)
            
            print(f"✅ 迁移完成: {from_table} → {to_table} ({len(df)} 行)")
            return True
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            return False


def health_check():
    """健康检查"""
    print("=" * 60)
    print("向量表健康检查")
    print("=" * 60)
    print()
    
    try:
        repair = VectorTableRepair()
        result = repair.check_all_tables()
        
        print(f"总表数: {result['total']}")
        print(f"健康: {result['healthy']}")
        print(f"需修复: {result['needs_repair']}")
        print()
        
        for table in result["tables"]:
            status = table.get("status")
            name = table.get("name")
            
            if status == "healthy":
                print(f"✅ {name}: {table.get('rows')} 行, {len(table.get('vector_columns', []))} 个向量列")
            elif status == "needs_repair":
                print(f"⚠️ {name}: 缺少向量列")
            else:
                print(f"❌ {name}: {table.get('error', '未知错误')}")
        
        print()
        
        if result["needs_repair"] > 0:
            print("💡 运行修复: python vector_repair.py --repair-all")
        else:
            print("✅ 所有表健康")
        
        return result
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return {"error": str(e)}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="向量表修复工具")
    parser.add_argument("--check", action="store_true", help="健康检查")
    parser.add_argument("--repair-all", action="store_true", help="修复所有表")
    parser.add_argument("--repair", type=str, help="修复指定表")
    parser.add_argument("--create", type=str, help="创建标准表")
    parser.add_argument("--migrate", nargs=2, metavar=("FROM", "TO"), help="迁移数据")
    
    args = parser.parse_args()
    
    if args.check:
        health_check()
    
    elif args.repair_all:
        repair = VectorTableRepair()
        result = repair.repair_all()
        print(f"\n修复完成: {result['repaired']}/{result['total']}")
    
    elif args.repair:
        repair = VectorTableRepair()
        repair.repair_table(args.repair)
    
    elif args.create:
        repair = VectorTableRepair()
        repair.create_standard_table(args.create)
    
    elif args.migrate:
        repair = VectorTableRepair()
        repair.migrate_data(args.migrate[0], args.migrate[1])
    
    else:
        # 默认检查
        health_check()


if __name__ == "__main__":
    main()
