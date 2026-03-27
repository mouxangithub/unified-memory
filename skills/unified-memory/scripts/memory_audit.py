#!/usr/bin/env python3
"""
Memory Audit - 审计日志 v1.0

功能:
- 结构化写入日志
- 时间/来源/Agent 追踪
- 审计查询接口
- 合规报告生成

Usage:
    python3 scripts/memory_audit.py log --action store --id MEM_ID --text "内容"
    python3 scripts/memory_audit.py query --user "刘选权" --from 2026-03-01
    python3 scripts/memory_audit.py report --days 30
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
LOGS_DIR = MEMORY_DIR / "logs"
AUDIT_LOG = LOGS_DIR / "memory_writes.log"
AUDIT_INDEX = LOGS_DIR / "audit_index.json"


class MemoryAudit:
    """记忆审计系统"""
    
    def __init__(self):
        self.logs_dir = LOGS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """加载审计索引"""
        if AUDIT_INDEX.exists():
            with open(AUDIT_INDEX) as f:
                return json.load(f)
        return {
            "by_user": {},
            "by_action": {},
            "by_date": {},
            "by_source": {}
        }
    
    def _save_index(self):
        """保存审计索引"""
        with open(AUDIT_INDEX, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def log_write(self, action: str, mem_id: str, text: str, 
                  source: str = "unknown", user: str = "unknown",
                  session_id: str = "", extra: Dict = None):
        """记录写入操作"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,  # store, update, delete, merge, archive
            "memory_id": mem_id,
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "text_hash": hash(text) % 1000000,  # 简单哈希用于去重检测
            "source": source,  # auto_extractor, manual, integration, etc.
            "user": user,
            "session_id": session_id,
            "extra": extra or {}
        }
        
        # 写入日志文件
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 更新索引
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        self.index["by_user"][user] = self.index["by_user"].get(user, 0) + 1
        self.index["by_action"][action] = self.index["by_action"].get(action, 0) + 1
        self.index["by_date"][date_str] = self.index["by_date"].get(date_str, 0) + 1
        self.index["by_source"][source] = self.index["by_source"].get(source, 0) + 1
        
        self._save_index()
        
        return entry
    
    def query(self, user: str = None, action: str = None, 
              source: str = None, from_date: str = None, 
              to_date: str = None, mem_id: str = None,
              limit: int = 100) -> List[Dict]:
        """查询审计日志"""
        results = []
        
        if not AUDIT_LOG.exists():
            return results
        
        with open(AUDIT_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # 过滤条件
                    if user and entry.get("user") != user:
                        continue
                    if action and entry.get("action") != action:
                        continue
                    if source and entry.get("source") != source:
                        continue
                    if mem_id and entry.get("memory_id") != mem_id:
                        continue
                    if from_date:
                        try:
                            entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                            if entry_date < datetime.fromisoformat(from_date).date():
                                continue
                        except:
                            pass
                    if to_date:
                        try:
                            entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                            if entry_date > datetime.fromisoformat(to_date).date():
                                continue
                        except:
                            pass
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        # 按时间倒序
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results
    
    def get_user_activity(self, user: str, days: int = 30) -> Dict:
        """获取用户活动统计"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        entries = self.query(user=user, from_date=cutoff_str, limit=1000)
        
        # 统计
        actions = Counter(e["action"] for e in entries)
        sources = Counter(e["source"] for e in entries)
        daily = Counter(e["timestamp"][:10] for e in entries)
        
        return {
            "user": user,
            "period_days": days,
            "total_actions": len(entries),
            "actions": dict(actions),
            "sources": dict(sources),
            "daily_activity": dict(sorted(daily.items())),
            "last_activity": entries[0]["timestamp"] if entries else None
        }
    
    def get_memory_history(self, mem_id: str) -> List[Dict]:
        """获取记忆的完整历史"""
        return self.query(mem_id=mem_id, limit=100)
    
    def detect_anomalies(self, days: int = 7) -> Dict:
        """检测异常活动"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        entries = self.query(from_date=cutoff_str, limit=10000)
        
        anomalies = {
            "high_volume_users": [],
            "unusual_sources": [],
            "duplicate_texts": [],
            "rapid_deletions": []
        }
        
        # 检测高频用户
        user_counts = Counter(e["user"] for e in entries)
        avg_count = sum(user_counts.values()) / len(user_counts) if user_counts else 0
        
        for user, count in user_counts.items():
            if count > avg_count * 3:  # 超过平均值 3 倍
                anomalies["high_volume_users"].append({
                    "user": user,
                    "count": count,
                    "avg": round(avg_count, 1)
                })
        
        # 检测重复文本
        text_hashes = Counter(e["text_hash"] for e in entries)
        for h, count in text_hashes.items():
            if count > 3:
                duplicates = [e for e in entries if e["text_hash"] == h]
                anomalies["duplicate_texts"].append({
                    "hash": h,
                    "count": count,
                    "examples": [d["text_preview"][:50] for d in duplicates[:3]]
                })
        
        # 检测快速删除（创建后立即删除）
        stores = {e["memory_id"]: e for e in entries if e["action"] == "store"}
        deletes = [e for e in entries if e["action"] == "delete"]
        
        for d in deletes:
            if d["memory_id"] in stores:
                store_time = datetime.fromisoformat(stores[d["memory_id"]]["timestamp"])
                delete_time = datetime.fromisoformat(d["timestamp"])
                
                if (delete_time - store_time).seconds < 60:  # 1 分钟内
                    anomalies["rapid_deletions"].append({
                        "memory_id": d["memory_id"],
                        "store_time": stores[d["memory_id"]]["timestamp"],
                        "delete_time": d["timestamp"],
                        "seconds_diff": (delete_time - store_time).seconds
                    })
        
        return {
            "period_days": days,
            "total_entries": len(entries),
            "anomalies": anomalies
        }
    
    def generate_compliance_report(self, days: int = 30) -> Dict:
        """生成合规报告"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        entries = self.query(from_date=cutoff_str, limit=10000)
        
        # 用户统计
        user_stats = {}
        for e in entries:
            user = e["user"]
            if user not in user_stats:
                user_stats[user] = {"stores": 0, "updates": 0, "deletes": 0, "last_active": ""}
            
            if e["action"] == "store":
                user_stats[user]["stores"] += 1
            elif e["action"] == "update":
                user_stats[user]["updates"] += 1
            elif e["action"] == "delete":
                user_stats[user]["deletes"] += 1
            
            user_stats[user]["last_active"] = e["timestamp"][:10]
        
        # 来源统计
        source_stats = Counter(e["source"] for e in entries)
        
        # 每日活动
        daily_activity = Counter(e["timestamp"][:10] for e in entries)
        
        # 检测异常
        anomalies = self.detect_anomalies(days)
        
        return {
            "report_date": datetime.now().isoformat(),
            "period_days": days,
            "summary": {
                "total_operations": len(entries),
                "unique_users": len(user_stats),
                "unique_sources": len(source_stats)
            },
            "user_activity": user_stats,
            "source_distribution": dict(source_stats),
            "daily_activity": dict(sorted(daily_activity.items())),
            "anomalies_detected": sum(len(v) for v in anomalies["anomalies"].values()),
            "anomaly_details": anomalies["anomalies"],
            "compliance_status": "PASS" if sum(len(v) for v in anomalies["anomalies"].values()) == 0 else "REVIEW_NEEDED"
        }
    
    def export_audit_trail(self, output_path: str, from_date: str = None, 
                          to_date: str = None, format: str = "json"):
        """导出审计轨迹"""
        entries = self.query(from_date=from_date, to_date=to_date, limit=100000)
        
        output = Path(output_path)
        
        if format == "json":
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
        
        elif format == "csv":
            import csv
            with open(output, 'w', newline='', encoding='utf-8') as f:
                if entries:
                    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                    writer.writeheader()
                    writer.writerows(entries)
        
        elif format == "markdown":
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f"# Memory Audit Trail\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write(f"Total entries: {len(entries)}\n\n")
                
                for e in entries:
                    f.write(f"## {e['timestamp']}\n")
                    f.write(f"- Action: {e['action']}\n")
                    f.write(f"- User: {e['user']}\n")
                    f.write(f"- Source: {e['source']}\n")
                    f.write(f"- Memory ID: {e['memory_id'][:16]}...\n")
                    f.write(f"- Preview: {e['text_preview']}\n\n")
        
        return {
            "output": str(output),
            "format": format,
            "entries": len(entries)
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Audit v1.0")
    parser.add_argument("command", choices=["log", "query", "report", "user", "history", "anomalies", "export"])
    parser.add_argument("--action", "-a", help="操作类型")
    parser.add_argument("--id", "-i", help="记忆 ID")
    parser.add_argument("--text", "-t", default="", help="文本内容")
    parser.add_argument("--source", "-s", default="manual", help="来源")
    parser.add_argument("--user", "-u", default="unknown", help="用户")
    parser.add_argument("--session", help="会话 ID")
    parser.add_argument("--from", dest="from_date", help="开始日期")
    parser.add_argument("--to", dest="to_date", help="结束日期")
    parser.add_argument("--days", "-d", type=int, default=30, help="天数")
    parser.add_argument("--limit", "-l", type=int, default=100, help="限制数量")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--format", "-f", choices=["json", "csv", "markdown"], default="json")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    audit = MemoryAudit()
    
    if args.command == "log":
        if not args.action or not args.id:
            print("❌ 请提供 --action 和 --id")
            return
        
        entry = audit.log_write(
            action=args.action,
            mem_id=args.id,
            text=args.text,
            source=args.source,
            user=args.user,
            session_id=args.session or ""
        )
        
        print(f"✅ 审计日志已记录: {entry['timestamp']}")
        if args.json:
            print(json.dumps(entry, ensure_ascii=False, indent=2))
    
    elif args.command == "query":
        results = audit.query(
            user=args.user,
            action=args.action,
            source=args.source,
            from_date=args.from_date,
            to_date=args.to_date,
            mem_id=args.id,
            limit=args.limit
        )
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"📋 查询结果: {len(results)} 条")
            for r in results[:10]:
                print(f"   {r['timestamp'][:19]} [{r['action']}] {r['user']}: {r['text_preview'][:40]}...")
    
    elif args.command == "report":
        print(f"📊 合规报告 (最近 {args.days} 天)")
        report = audit.generate_compliance_report(args.days)
        
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"\n摘要:")
            print(f"   总操作: {report['summary']['total_operations']}")
            print(f"   用户数: {report['summary']['unique_users']}")
            print(f"   来源数: {report['summary']['unique_sources']}")
            print(f"   异常数: {report['anomalies_detected']}")
            print(f"   状态: {report['compliance_status']}")
    
    elif args.command == "user":
        if not args.user:
            print("❌ 请提供 --user")
            return
        
        activity = audit.get_user_activity(args.user, args.days)
        
        if args.json:
            print(json.dumps(activity, ensure_ascii=False, indent=2))
        else:
            print(f"👤 用户活动: {args.user}")
            print(f"   总操作: {activity['total_actions']}")
            print(f"   操作分布: {activity['actions']}")
            print(f"   来源分布: {activity['sources']}")
    
    elif args.command == "history":
        if not args.id:
            print("❌ 请提供 --id")
            return
        
        history = audit.get_memory_history(args.id)
        
        if args.json:
            print(json.dumps(history, ensure_ascii=False, indent=2))
        else:
            print(f"📜 记忆历史: {args.id[:16]}...")
            for h in history:
                print(f"   {h['timestamp'][:19]} [{h['action']}] {h['source']}")
    
    elif args.command == "anomalies":
        print(f"🔍 异常检测 (最近 {args.days} 天)")
        anomalies = audit.detect_anomalies(args.days)
        
        if args.json:
            print(json.dumps(anomalies, ensure_ascii=False, indent=2))
        else:
            for type_name, items in anomalies["anomalies"].items():
                if items:
                    print(f"\n⚠️ {type_name}: {len(items)} 个")
                    for item in items[:3]:
                        print(f"   - {item}")
    
    elif args.command == "export":
        if not args.output:
            args.output = str(MEMORY_DIR / f"audit_export_{datetime.now().strftime('%Y%m%d')}.{args.format}")
        
        result = audit.export_audit_trail(
            output_path=args.output,
            from_date=args.from_date,
            to_date=args.to_date,
            format=args.format
        )
        
        print(f"📤 导出完成")
        print(f"   文件: {result['output']}")
        print(f"   格式: {result['format']}")
        print(f"   条目: {result['entries']}")


if __name__ == "__main__":
    main()
