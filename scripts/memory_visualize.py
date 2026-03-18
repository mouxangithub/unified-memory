#!/usr/bin/env python3
"""
Memory Visualize - 记忆可视化 v1.0

功能:
- 时间线视图
- 词云生成
- 分布图
- 导出为 HTML

Usage:
    python3 scripts/memory_visualize.py timeline --days 30
    python3 scripts/memory_visualize.py wordcloud --output wordcloud.html
    python3 scripts/memory_visualize.py distribution
    python3 scripts/memory_visualize.py report --output report.html
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import os
import re

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
REPORTS_DIR = MEMORY_DIR / "reports"


class MemoryVisualizer:
    """记忆可视化"""
    
    def __init__(self):
        self.memories = self._load_memories()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(len(data.get("id", []))):
                memories.append({
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "category": data.get("category", [""])[i] if i < len(data.get("category", [])) else "",
                    "importance": data.get("importance", [0.5])[i] if i < len(data.get("importance", [])) else 0.5,
                    "tags": data.get("tags", [[]])[i] if i < len(data.get("tags", [])) else [],
                    "timestamp": data.get("timestamp", [""])[i] if i < len(data.get("timestamp", [])) else ""
                })
            return memories
        except Exception as e:
            print(f"⚠️ 加载记忆失败: {e}")
            return []
    
    def generate_timeline(self, days: int = 30) -> Dict:
        """生成时间线"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # 按日期分组
        timeline = {}
        for mem in self.memories:
            try:
                mem_date = datetime.fromisoformat(mem["timestamp"])
                if mem_date < cutoff:
                    continue
                
                date_str = mem_date.strftime("%Y-%m-%d")
                if date_str not in timeline:
                    timeline[date_str] = []
                
                timeline[date_str].append({
                    "id": mem["id"],
                    "text": mem["text"][:100],
                    "category": mem["category"],
                    "importance": mem["importance"],
                    "time": mem_date.strftime("%H:%M")
                })
            except:
                pass
        
        # 统计
        daily_stats = {}
        for date_str, items in timeline.items():
            daily_stats[date_str] = {
                "count": len(items),
                "categories": Counter(item["category"] for item in items),
                "avg_importance": sum(item["importance"] for item in items) / len(items)
            }
        
        return {
            "period_days": days,
            "total_memories": sum(len(items) for items in timeline.values()),
            "timeline": timeline,
            "daily_stats": daily_stats
        }
    
    def generate_wordcloud_data(self, min_length: int = 2) -> Dict:
        """生成词云数据"""
        # 中文停用词
        stopwords = {
            "的", "了", "是", "在", "我", "有", "和", "就",
            "不", "人", "都", "一", "一个", "上", "也", "很", "到",
            "说", "要", "去", "你", "会", "着", "没有", "看", "好",
            "自己", "这", "那", "她", "他", "它", "们", "个", "中",
            "为", "什么", "这", "那", "可以", "这个", "那个", "使用"
        }
        
        # 分词（简单按空格和标点分割）
        all_words = []
        for mem in self.memories:
            # 移除标点
            text = re.sub(r'[，。！？、；：""''（）【】]', ' ', mem["text"])
            words = text.split()
            all_words.extend(words)
        
        # 统计词频
        word_freq = Counter(word for word in all_words 
                          if len(word) >= min_length and word not in stopwords)
        
        # 取前100个高频词
        top_words = word_freq.most_common(100)
        
        return {
            "total_words": len(all_words),
            "unique_words": len(word_freq),
            "top_words": [{"word": word, "count": count} for word, count in top_words]
        }
    
    def generate_distribution(self) -> Dict:
        """生成分布统计"""
        # 类别分布
        category_dist = Counter(m["category"] for m in self.memories)
        
        # 重要性分布
        importance_ranges = {
            "高 (>0.8)": 0,
            "中高 (0.6-0.8)": 0,
            "中 (0.4-0.6)": 0,
            "中低 (0.2-0.4)": 0,
            "低 (<0.2)": 0
        }
        
        for mem in self.memories:
            imp = mem["importance"]
            if imp > 0.8:
                importance_ranges["高 (>0.8)"] += 1
            elif imp > 0.6:
                importance_ranges["中高 (0.6-0.8)"] += 1
            elif imp > 0.4:
                importance_ranges["中 (0.4-0.6)"] += 1
            elif imp > 0.2:
                importance_ranges["中低 (0.2-0.4)"] += 1
            else:
                importance_ranges["低 (<0.2)"] += 1
        
        # 时间分布（按小时）
        hour_dist = Counter()
        for mem in self.memories:
            try:
                hour = datetime.fromisoformat(mem["timestamp"]).hour
                hour_dist[hour] += 1
            except:
                pass
        
        return {
            "total": len(self.memories),
            "category_distribution": dict(category_dist),
            "importance_distribution": importance_ranges,
            "hour_distribution": dict(sorted(hour_dist.items()))
        }
    
    def export_html_report(self, output_path: str = None) -> str:
        """导出 HTML 报告"""
        if not output_path:
            output_path = str(REPORTS_DIR / f"memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        timeline = self.generate_timeline(30)
        wordcloud = self.generate_wordcloud_data()
        distribution = self.generate_distribution()
        
        # 生成 HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px;
            color: #333;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin: 0 0 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .timeline-item {{
            border-left: 3px solid #667eea;
            padding-left: 15px;
            margin-bottom: 15px;
        }}
        .timeline-date {{
            font-weight: bold;
            color: #667eea;
        }}
        .wordcloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .word-tag {{
            background: #f0f0f0;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }}
        .chart-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .chart-label {{
            width: 150px;
            font-size: 14px;
        }}
        .chart-fill {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 20px;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        .chart-value {{
            margin-left: 10px;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 记忆系统报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>总记忆</h3>
            <div class="stat-number">{distribution['total']}</div>
        </div>
        <div class="stat-card">
            <h3>本月新增</h3>
            <div class="stat-number">{timeline['total_memories']}</div>
        </div>
        <div class="stat-card">
            <h3>独立词汇</h3>
            <div class="stat-number">{wordcloud['unique_words']}</div>
        </div>
        <div class="stat-card">
            <h3>类别数</h3>
            <div class="stat-number">{len(distribution['category_distribution'])}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 类别分布</h2>
        {self._generate_category_bars(distribution['category_distribution'])}
    </div>
    
    <div class="section">
        <h2>⭐ 重要性分布</h2>
        {self._generate_importance_bars(distribution['importance_distribution'])}
    </div>
    
    <div class="section">
        <h2>☁️ 热门词汇</h2>
        <div class="wordcloud">
            {self._generate_word_tags(wordcloud['top_words'][:30])}
        </div>
    </div>
    
    <div class="section">
        <h2>📅 最近时间线</h2>
        {self._generate_timeline_html(timeline['timeline'])}
    </div>
    
    <div class="section">
        <h2>⏰ 时间分布（按小时）</h2>
        {self._generate_hour_bars(distribution['hour_distribution'])}
    </div>
</body>
</html>"""
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_category_bars(self, data: Dict) -> str:
        """生成类别分布条形图"""
        if not data:
            return "<p>暂无数据</p>"
        
        max_val = max(data.values())
        bars = []
        
        for cat, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
            width = int((count / max_val) * 200)
            bars.append(f"""
            <div class="chart-bar">
                <div class="chart-label">{cat or '未分类'}</div>
                <div class="chart-fill" style="width: {width}px;"></div>
                <div class="chart-value">{count}</div>
            </div>""")
        
        return "\n".join(bars)
    
    def _generate_importance_bars(self, data: Dict) -> str:
        """生成重要性分布条形图"""
        max_val = max(data.values())
        bars = []
        
        for range_name, count in data.items():
            if count > 0:
                width = int((count / max_val) * 200)
                bars.append(f"""
                <div class="chart-bar">
                    <div class="chart-label">{range_name}</div>
                    <div class="chart-fill" style="width: {width}px;"></div>
                    <div class="chart-value">{count}</div>
                </div>""")
        
        return "\n".join(bars)
    
    def _generate_word_tags(self, words: List[Dict]) -> str:
        """生成词云标签"""
        if not words:
            return "<p>暂无数据</p>"
        
        max_count = words[0]["count"]
        tags = []
        
        for item in words:
            # 根据词频调整字体大小
            size = 12 + int((item["count"] / max_count) * 12)
            tags.append(f'<span class="word-tag" style="font-size: {size}px;">{item["word"]}</span>')
        
        return "\n".join(tags)
    
    def _generate_timeline_html(self, timeline: Dict) -> str:
        """生成时间线 HTML"""
        if not timeline:
            return "<p>暂无数据</p>"
        
        items = []
        for date_str in sorted(timeline.keys(), reverse=True)[:10]:
            day_items = timeline[date_str]
            items_html = "<br>".join([
                f'<span style="color: #666;">{item["time"]}</span> [{item["category"]}] {item["text"][:50]}...'
                for item in day_items[:3]
            ])
            
            items.append(f"""
            <div class="timeline-item">
                <div class="timeline-date">{date_str}</div>
                <div>{len(day_items)} 条记忆</div>
                <div style="margin-top: 5px; font-size: 14px;">{items_html}</div>
            </div>""")
        
        return "\n".join(items)
    
    def _generate_hour_bars(self, data: Dict) -> str:
        """生成小时分布条形图"""
        if not data:
            return "<p>暂无数据</p>"
        
        max_val = max(data.values())
        bars = []
        
        for hour in range(24):
            count = data.get(hour, 0)
            width = int((count / max_val) * 200) if max_val > 0 else 0
            bars.append(f"""
            <div class="chart-bar">
                <div class="chart-label">{hour:02d}:00</div>
                <div class="chart-fill" style="width: {width}px;"></div>
                <div class="chart-value">{count}</div>
            </div>""")
        
        return "\n".join(bars)


def main():
    parser = argparse.ArgumentParser(description="Memory Visualize v1.0")
    parser.add_argument("command", choices=["timeline", "wordcloud", "distribution", "report"])
    parser.add_argument("--days", "-d", type=int, default=30, help="天数")
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    visualizer = MemoryVisualizer()
    
    if args.command == "timeline":
        result = visualizer.generate_timeline(args.days)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📅 时间线 (最近 {args.days} 天)")
            print(f"   总记忆: {result['total_memories']}")
            print()
            
            for date_str, stats in sorted(result['daily_stats'].items(), reverse=True)[:10]:
                print(f"   {date_str}: {stats['count']} 条")
    
    elif args.command == "wordcloud":
        result = visualizer.generate_wordcloud_data()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"☁️ 词云数据")
            print(f"   总词汇: {result['total_words']}")
            print(f"   独立词汇: {result['unique_words']}")
            print()
            print("   Top 20:")
            for item in result['top_words'][:20]:
                print(f"     {item['word']}: {item['count']}")
    
    elif args.command == "distribution":
        result = visualizer.generate_distribution()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📊 分布统计")
            print(f"\n   类别分布:")
            for cat, count in result['category_distribution'].items():
                print(f"     {cat or '未分类'}: {count}")
            
            print(f"\n   重要性分布:")
            for range_name, count in result['importance_distribution'].items():
                if count > 0:
                    print(f"     {range_name}: {count}")
    
    elif args.command == "report":
        output_path = args.output or str(REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        result_path = visualizer.export_html_report(output_path)
        
        print(f"📊 HTML 报告已生成")
        print(f"   文件: {result_path}")


if __name__ == "__main__":
    main()
