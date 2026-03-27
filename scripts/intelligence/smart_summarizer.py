#!/usr/bin/env python3
"""
Smart Summarizer - 智能摘要

自动压缩历史日志，提取关键信息。

功能:
- 压缩 7 天内的日志
- 提取关键决策
- 生成项目摘要
- 提取关键实体

Usage:
    summarizer = SmartSummarizer()
    summarizer.compress_logs(days=7)
    decisions = summarizer.extract_decisions()
    summary = summarizer.generate_summary()
"""

import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter


class SmartSummarizer:
    """智能摘要系统"""
    
    def __init__(self, memory_dir: Path = None):
        self.memory_dir = memory_dir or (Path.home() / ".openclaw" / "workspace" / "memory")
        self.summary_dir = self.memory_dir / "summaries"
        self.summary_dir.mkdir(exist_ok=True)
    
    def compress_logs(self, days: int = 7, output_file: str = None) -> str:
        """压缩指定天数内的日志"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 收集日志文件
        log_files = []
        for file in self.memory_dir.glob("*.md"):
            try:
                # 从文件名提取日期
                date_str = file.stem.split("_")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date >= cutoff_date:
                    log_files.append((file, file_date))
            except:
                pass
        
        if not log_files:
            return "没有找到日志文件"
        
        # 排序
        log_files.sort(key=lambda x: x[1])
        
        # 提取关键信息
        all_events = []
        all_decisions = []
        all_entities = []
        
        for file, file_date in log_files:
            content = file.read_text()
            
            # 提取事件
            events = self._extract_events(content)
            all_events.extend(events)
            
            # 提取决策
            decisions = self._extract_decisions(content)
            all_decisions.extend(decisions)
            
            # 提取实体
            entities = self._extract_entities(content)
            all_entities.extend(entities)
        
        # 生成摘要
        summary = self._generate_compressed_summary(
            days, log_files, all_events, all_decisions, all_entities
        )
        
        # 保存
        if output_file:
            output_path = self.summary_dir / output_file
        else:
            output_path = self.summary_dir / f"summary-{datetime.now().strftime('%Y%m%d')}.md"
        
        output_path.write_text(summary)
        
        return summary
    
    def extract_decisions(self, days: int = 30) -> List[Dict[str, str]]:
        """提取关键决策"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        decisions = []
        
        for file in self.memory_dir.glob("*.md"):
            try:
                date_str = file.stem.split("_")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date >= cutoff_date:
                    content = file.read_text()
                    file_decisions = self._extract_decisions(content)
                    decisions.extend(file_decisions)
            except:
                pass
        
        return decisions
    
    def generate_summary(self) -> str:
        """生成项目摘要"""
        # 读取所有日志
        all_content = ""
        for file in sorted(self.memory_dir.glob("*.md")):
            all_content += file.read_text() + "\n\n"
        
        # 提取关键信息
        events = self._extract_events(all_content)
        decisions = self._extract_decisions(all_content)
        entities = self._extract_entities(all_content)
        
        # 统计
        event_counter = Counter([e.get("type", "other") for e in events])
        
        # 生成摘要
        summary = f"""# 项目摘要

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 统计信息

- 总事件数: {len(events)}
- 总决策数: {len(decisions)}
- 总实体数: {len(entities)}

### 事件类型分布

"""
        
        for event_type, count in event_counter.most_common(10):
            summary += f"- {event_type}: {count}\n"
        
        # 关键决策
        summary += "\n## 关键决策\n\n"
        for i, decision in enumerate(decisions[:20], 1):
            summary += f"{i}. {decision.get('content', '')[:100]}\n"
        
        # 关键实体
        summary += "\n## 关键实体\n\n"
        entity_counter = Counter([e.get("name", "") for e in entities])
        for entity_name, count in entity_counter.most_common(20):
            if entity_name:
                summary += f"- {entity_name}: {count} 次提及\n"
        
        return summary
    
    def _extract_events(self, content: str) -> List[Dict[str, str]]:
        """从内容中提取事件"""
        events = []
        
        # 匹配常见事件模式
        patterns = [
            (r"- \[?\d{2}:\d{2}\]? (.+)", "log"),  # 时间戳日志
            (r"- \[([^\]]+)\] (.+)", "tagged"),    # 标签日志
            (r"### (.+)", "section"),               # 章节标题
            (r"\*\*(.+)\*\*:", "highlight"),        # 高亮内容
        ]
        
        for pattern, event_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    text = " ".join(match)
                else:
                    text = match
                
                events.append({
                    "type": event_type,
                    "content": text[:200]
                })
        
        return events
    
    def _extract_decisions(self, content: str) -> List[Dict[str, str]]:
        """从内容中提取决策"""
        decisions = []
        
        # 匹配决策模式
        patterns = [
            r"决策[：:]\s*(.+)",
            r"决定[：:]\s*(.+)",
            r"选择[：:]\s*(.+)",
            r"使用\s+(.+)\s+实现",
            r"采用\s+(.+)\s+方案",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                decisions.append({
                    "content": match[:200],
                    "pattern": pattern
                })
        
        return decisions
    
    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """从内容中提取实体"""
        entities = []
        
        # 匹配常见实体模式
        patterns = [
            (r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "person"),  # 人名
            (r"([A-Z][A-Z0-9_]+)", "constant"),               # 常量
            (r"([a-z_]+\(\))", "function"),                   # 函数
            (r"([a-z_]+\.[a-z]+)", "file"),                   # 文件
        ]
        
        for pattern, entity_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 过滤常见词
                if match.lower() not in ["the", "a", "an", "is", "are", "was", "were"]:
                    entities.append({
                        "name": match,
                        "type": entity_type
                    })
        
        return entities
    
    def _generate_compressed_summary(
        self, days: int, log_files: List, events: List, decisions: List, entities: List
    ) -> str:
        """生成压缩摘要"""
        start_date = log_files[0][1].strftime("%Y-%m-%d")
        end_date = log_files[-1][1].strftime("%Y-%m-%d")
        
        summary = f"""# 日志压缩摘要

> 压缩时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> 时间范围: {start_date} ~ {end_date} ({days} 天)
> 日志文件: {len(log_files)} 个

## 统计信息

- 总事件数: {len(events)}
- 总决策数: {len(decisions)}
- 总实体数: {len(entities)}

## 关键事件

"""
        
        # 按类型分组
        event_by_type = {}
        for event in events:
            event_type = event.get("type", "other")
            if event_type not in event_by_type:
                event_by_type[event_type] = []
            event_by_type[event_type].append(event)
        
        for event_type, type_events in sorted(event_by_type.items()):
            summary += f"### {event_type}\n\n"
            for event in type_events[:10]:
                summary += f"- {event.get('content', '')[:100]}\n"
            summary += "\n"
        
        # 关键决策
        summary += "## 关键决策\n\n"
        for i, decision in enumerate(decisions[:20], 1):
            summary += f"{i}. {decision.get('content', '')[:100]}\n"
        
        # 关键实体
        summary += "\n## 关键实体\n\n"
        entity_counter = Counter([e.get("name", "") for e in entities])
        for entity_name, count in entity_counter.most_common(20):
            if entity_name:
                summary += f"- {entity_name}: {count} 次\n"
        
        return summary


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Summarizer - 智能摘要")
    subparsers = parser.add_subparsers(dest="command")
    
    # compress
    compress_parser = subparsers.add_parser("compress", help="压缩日志")
    compress_parser.add_argument("--days", "-d", type=int, default=7, help="压缩天数")
    
    # decisions
    decisions_parser = subparsers.add_parser("decisions", help="提取决策")
    decisions_parser.add_argument("--days", "-d", type=int, default=30, help="提取天数")
    
    # summary
    subparsers.add_parser("summary", help="生成摘要")
    
    args = parser.parse_args()
    
    summarizer = SmartSummarizer()
    
    if args.command == "compress":
        summary = summarizer.compress_logs(args.days)
        print(summary[:500] + "...")
        print(f"\n✅ 压缩完成")
    
    elif args.command == "decisions":
        decisions = summarizer.extract_decisions(args.days)
        print(f"📋 关键决策 (最近 {args.days} 天):\n")
        for i, decision in enumerate(decisions[:10], 1):
            print(f"{i}. {decision.get('content', '')[:80]}")
    
    elif args.command == "summary":
        summary = summarizer.generate_summary()
        print(summary)
    
    else:
        parser.print_help()
