#!/usr/bin/env python3
"""
Context Tree - 项目级上下文管理

模仿 QMD 的 .context/ 结构，提供层级上下文管理。

功能:
- 自动维护 current.md（当前状态）
- 自动记录决策
- 自动提取关键信息
- 快速恢复上下文

Usage:
    ctx = ContextTree(project_path)
    ctx.update_current("实现登录功能", 60, "使用 JWT 认证")
    ctx.record_decision("选择数据库", "使用 PostgreSQL")
    status = ctx.get_current()
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class ContextTree:
    """项目级上下文管理"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.context_dir = self.project_path / ".context"
        self.current_file = self.context_dir / "current.md"
        self.decisions_dir = self.context_dir / "decisions"
        self.architecture_file = self.context_dir / "architecture.md"
        self.summary_file = self.context_dir / "summary.md"
        
        # 确保目录存在
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(exist_ok=True)
    
    def init_project(self, name: str, description: str = ""):
        """初始化项目上下文"""
        # 创建 current.md
        self.update_current(
            task="项目初始化",
            progress=0,
            notes=f"项目: {name}\n描述: {description}"
        )
        
        # 创建 architecture.md
        if not self.architecture_file.exists():
            self.architecture_file.write_text(f"""# {name} 架构

## 技术栈
- 待定

## 目录结构
- 待定

## 关键决策
- 待定
""")
        
        # 创建 summary.md
        if not self.summary_file.exists():
            self.summary_file.write_text(f"""# {name} 项目摘要

## 项目目标
{description}

## 当前进度
0%

## 关键里程碑
- [ ] 项目启动

## 团队成员
- 待添加
""")
    
    def update_current(self, task: str, progress: int, notes: str = ""):
        """更新当前状态"""
        content = f"""# 当前状态

> 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 当前任务
{task}

## 进度
{progress}%

## 备注
{notes}

## 最近决策
"""
        # 添加最近决策
        recent_decisions = self._get_recent_decisions(3)
        for decision in recent_decisions:
            content += f"- [{decision['time']}] {decision['title']}\n"
        
        if not recent_decisions:
            content += "- 暂无\n"
        
        self.current_file.write_text(content)
    
    def record_decision(self, title: str, content: str, tags: List[str] = None):
        """记录决策"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title)[:30]
        filename = f"{timestamp}-{safe_title}.md"
        file = self.decisions_dir / filename
        
        tags_str = ", ".join(tags) if tags else ""
        
        file.write_text(f"""# {title}

> 时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> 标签: {tags_str}

## 决策内容

{content}

## 影响范围
- 待评估

## 替代方案
- 待记录
""")
        
        # 更新 current.md
        self._update_current_decisions(title, content)
        
        return file
    
    def add_milestone(self, milestone: str, completed: bool = False):
        """添加里程碑"""
        summary_content = self.summary_file.read_text() if self.summary_file.exists() else ""
        
        if "## 关键里程碑" in summary_content:
            lines = summary_content.split("\n")
            milestone_section = False
            new_lines = []
            
            for line in lines:
                if "## 关键里程碑" in line:
                    milestone_section = True
                
                if milestone_section and line.startswith("## "):
                    milestone_section = False
                    # 插入新里程碑
                    status = "x" if completed else " "
                    new_lines.append(f"- [{status}] {milestone}")
                
                new_lines.append(line)
            
            self.summary_file.write_text("\n".join(new_lines))
    
    def complete_milestone(self, milestone: str):
        """完成里程碑"""
        summary_content = self.summary_file.read_text() if self.summary_file.exists() else ""
        
        if "## 关键里程碑" in summary_content:
            summary_content = summary_content.replace(
                f"- [ ] {milestone}",
                f"- [x] {milestone}"
            )
            self.summary_file.write_text(summary_content)
    
    def get_current(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.current_file.exists():
            return {
                "task": "未初始化",
                "progress": 0,
                "notes": ""
            }
        
        content = self.current_file.read_text()
        
        # 解析内容
        task = ""
        progress = 0
        notes = ""
        
        lines = content.split("\n")
        section = None
        
        for line in lines:
            if "## 当前任务" in line:
                section = "task"
            elif "## 进度" in line:
                section = "progress"
            elif "## 备注" in line:
                section = "notes"
            elif line.startswith("## "):
                section = None
            elif section == "task" and line.strip():
                task = line.strip()
            elif section == "progress" and line.strip():
                try:
                    progress = int(line.strip().replace("%", ""))
                except:
                    pass
            elif section == "notes" and line.strip():
                notes += line + "\n"
        
        return {
            "task": task,
            "progress": progress,
            "notes": notes.strip()
        }
    
    def get_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策列表"""
        decisions = []
        
        for file in sorted(self.decisions_dir.glob("*.md"), reverse=True)[:limit]:
            content = file.read_text()
            title = content.split("\n")[0].replace("# ", "")
            time_match = content.split("\n")[2] if len(content.split("\n")) > 2 else ""
            time = time_match.replace("> 时间: ", "").strip()
            
            decisions.append({
                "title": title,
                "time": time,
                "file": file.name,
                "content": content
            })
        
        return decisions
    
    def _get_recent_decisions(self, limit: int = 3) -> List[Dict[str, str]]:
        """获取最近决策"""
        decisions = []
        
        for file in sorted(self.decisions_dir.glob("*.md"), reverse=True)[:limit]:
            content = file.read_text()
            title = content.split("\n")[0].replace("# ", "")
            time_match = content.split("\n")[2] if len(content.split("\n")) > 2 else ""
            time = time_match.replace("> 时间: ", "").strip()
            
            decisions.append({
                "title": title,
                "time": time
            })
        
        return decisions
    
    def _update_current_decisions(self, title: str, content: str):
        """更新 current.md 的决策部分"""
        if not self.current_file.exists():
            return
        
        current_content = self.current_file.read_text()
        
        # 在"最近决策"部分添加新决策
        lines = current_content.split("\n")
        new_lines = []
        in_decisions = False
        
        for line in lines:
            if "## 最近决策" in line:
                in_decisions = True
                new_lines.append(line)
                # 添加新决策
                new_lines.append(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {title}")
            elif in_decisions and line.startswith("## "):
                in_decisions = False
                new_lines.append(line)
            elif in_decisions and line.startswith("- 暂无"):
                # 跳过"暂无"
                pass
            else:
                new_lines.append(line)
        
        self.current_file.write_text("\n".join(new_lines))
    
    def export_context(self) -> str:
        """导出上下文为 Markdown"""
        output = f"""# 项目上下文

> 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}

"""
        
        # 当前状态
        current = self.get_current()
        output += f"""## 当前状态

- 任务: {current['task']}
- 进度: {current['progress']}%
- 备注: {current['notes']}

"""
        
        # 决策列表
        output += "## 决策列表\n\n"
        decisions = self.get_decisions(20)
        for i, decision in enumerate(decisions, 1):
            output += f"{i}. [{decision['time']}] {decision['title']}\n"
        
        # 架构
        if self.architecture_file.exists():
            output += f"\n## 架构\n\n{self.architecture_file.read_text()}"
        
        # 摘要
        if self.summary_file.exists():
            output += f"\n## 摘要\n\n{self.summary_file.read_text()}"
        
        return output


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Tree - 项目级上下文管理")
    subparsers = parser.add_subparsers(dest="command")
    
    # init
    init_parser = subparsers.add_parser("init", help="初始化项目")
    init_parser.add_argument("name", help="项目名称")
    init_parser.add_argument("--desc", "-d", default="", help="项目描述")
    
    # update
    update_parser = subparsers.add_parser("update", help="更新当前状态")
    update_parser.add_argument("task", help="当前任务")
    update_parser.add_argument("--progress", "-p", type=int, default=0, help="进度 (0-100)")
    update_parser.add_argument("--notes", "-n", default="", help="备注")
    
    # decision
    decision_parser = subparsers.add_parser("decision", help="记录决策")
    decision_parser.add_argument("title", help="决策标题")
    decision_parser.add_argument("content", help="决策内容")
    decision_parser.add_argument("--tags", "-t", default="", help="标签（逗号分隔）")
    
    # status
    subparsers.add_parser("status", help="查看当前状态")
    
    # export
    subparsers.add_parser("export", help="导出上下文")
    
    args = parser.parse_args()
    
    ctx = ContextTree()
    
    if args.command == "init":
        ctx.init_project(args.name, args.desc)
        print(f"✅ 项目初始化完成: {args.name}")
    
    elif args.command == "update":
        ctx.update_current(args.task, args.progress, args.notes)
        print(f"✅ 状态已更新: {args.task} ({args.progress}%)")
    
    elif args.command == "decision":
        tags = args.tags.split(",") if args.tags else []
        ctx.record_decision(args.title, args.content, tags)
        print(f"✅ 决策已记录: {args.title}")
    
    elif args.command == "status":
        current = ctx.get_current()
        print(f"📋 当前任务: {current['task']}")
        print(f"📊 进度: {current['progress']}%")
        print(f"📝 备注: {current['notes']}")
    
    elif args.command == "export":
        print(ctx.export_context())
    
    else:
        parser.print_help()
