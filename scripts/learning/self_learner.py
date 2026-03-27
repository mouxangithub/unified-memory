#!/usr/bin/env python3
"""
Self Learner - 自我学习模块

功能:
- 从错误中自动学习
- 自动优化策略
- 自动改进提示词
- 经验积累
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class Learning:
    """学习记录"""
    id: str
    type: str  # error, success, pattern
    trigger: str  # 触发条件
    lesson: str  # 学到的经验
    action: str  # 采取的行动
    impact: float  # 影响分数
    timestamp: str
    applied: bool = False


class SelfLearner:
    """自我学习系统"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or Path.home() / ".openclaw" / "workspace" / "memory" / "learnings.json")
        self.learnings: List[Learning] = []
        self.patterns: Dict[str, List[str]] = {}  # 错误模式 -> 解决方案
        self._load()
    
    def _load(self):
        """加载学习记录"""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            self.learnings = [Learning(**l) for l in data.get("learnings", [])]
            self.patterns = data.get("patterns", {})
    
    def _save(self):
        """保存学习记录"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps({
            "learnings": [asdict(l) for l in self.learnings],
            "patterns": self.patterns
        }, ensure_ascii=False, indent=2))
    
    def learn_from_error(self, error: str, context: Dict = None) -> Optional[Learning]:
        """从错误中学习"""
        import uuid
        
        # 分析错误模式
        error_pattern = self._extract_pattern(error)
        
        # 查找已知模式
        if error_pattern in self.patterns:
            # 已知错误，应用已知解决方案
            solution = self.patterns[error_pattern][0] if self.patterns[error_pattern] else None
            
            if solution:
                learning = Learning(
                    id=str(uuid.uuid4())[:8],
                    type="error",
                    trigger=error_pattern,
                    lesson=f"已知错误模式: {error_pattern}",
                    action=f"应用解决方案: {solution}",
                    impact=0.5,
                    timestamp=datetime.now().isoformat(),
                    applied=True
                )
                
                self.learnings.append(learning)
                self._save()
                
                return learning
        
        # 新错误，生成解决方案
        lesson = self._analyze_error(error, context)
        action = self._suggest_action(error, context)
        
        learning = Learning(
            id=str(uuid.uuid4())[:8],
            type="error",
            trigger=error_pattern,
            lesson=lesson,
            action=action,
            impact=1.0,  # 新错误影响更大
            timestamp=datetime.now().isoformat()
        )
        
        self.learnings.append(learning)
        
        # 添加到模式库
        if error_pattern not in self.patterns:
            self.patterns[error_pattern] = []
        if action:
            self.patterns[error_pattern].append(action)
        
        self._save()
        
        return learning
    
    def learn_from_success(self, operation: str, details: Dict = None) -> Optional[Learning]:
        """从成功中学习"""
        import uuid
        
        lesson = self._extract_lesson(operation, details)
        
        if not lesson:
            return None
        
        learning = Learning(
            id=str(uuid.uuid4())[:8],
            type="success",
            trigger=operation,
            lesson=lesson,
            action="记录最佳实践",
            impact=0.3,
            timestamp=datetime.now().isoformat()
        )
        
        self.learnings.append(learning)
        self._save()
        
        return learning
    
    def optimize_strategy(self, operation: str, metrics: Dict) -> Dict:
        """优化策略"""
        # 分析历史数据
        history = [l for l in self.learnings if l.trigger == operation]
        
        if not history:
            return {"suggestion": "无历史数据"}
        
        # 找到最有效的行动
        actions = {}
        for learning in history:
            if learning.action not in actions:
                actions[learning.action] = []
            actions[learning.action].append(learning.impact)
        
        # 计算平均影响
        avg_impacts = {a: sum(i) / len(i) for a, i in actions.items()}
        
        # 推荐
        best_action = max(avg_impacts, key=avg_impacts.get)
        
        return {
            "operation": operation,
            "history_count": len(history),
            "best_action": best_action,
            "avg_impact": avg_impacts[best_action],
            "suggestion": f"建议采用: {best_action}"
        }
    
    def improve_prompt(self, prompt: str, feedback: str = None) -> str:
        """改进提示词"""
        # 分析提示词问题
        issues = []
        
        # 检查常见问题
        if len(prompt) < 10:
            issues.append("提示词过短，可能不够清晰")
        
        if not any(c.isupper() for c in prompt):
            issues.append("缺少大写字母，可能缺少结构")
        
        if "TODO" in prompt or "FIXME" in prompt:
            issues.append("包含待办事项标记")
        
        # 改进
        improvements = []
        
        if issues:
            improvements.append(f"# 改进建议: {', '.join(issues)}")
        
        if feedback:
            improvements.append(f"# 用户反馈: {feedback}")
        
        # 添加结构
        if not prompt.startswith("#"):
            improved = f"# 任务\n{prompt}"
        else:
            improved = prompt
        
        if improvements:
            improved = "\n".join(improvements) + "\n\n" + improved
        
        return improved
    
    def get_learnings(self, limit: int = 50) -> List[Learning]:
        """获取学习记录"""
        return sorted(self.learnings, key=lambda l: l.timestamp, reverse=True)[:limit]
    
    def _extract_pattern(self, error: str) -> str:
        """提取错误模式"""
        # 简化错误信息，提取关键模式
        pattern = error
        
        # 去除具体数值
        pattern = re.sub(r'\d+', 'N', pattern)
        # 去除文件路径
        pattern = re.sub(r'/[\w/.-]+', '/PATH', pattern)
        # 去除具体标识
        pattern = re.sub(r'[a-f0-9]{8,}', 'ID', pattern)
        
        return pattern[:100]  # 限制长度
    
    def _analyze_error(self, error: str, context: Dict = None) -> str:
        """分析错误"""
        # 常见错误类型
        error_types = {
            "ConnectionRefusedError": "连接被拒绝，检查服务是否启动",
            "FileNotFoundError": "文件不存在，检查路径是否正确",
            "KeyError": "键不存在，检查数据结构",
            "TypeError": "类型错误，检查参数类型",
            "ValueError": "值错误，检查参数值",
            "ImportError": "导入失败，检查依赖是否安装",
            "PermissionError": "权限错误，检查文件权限",
        }
        
        for error_type, lesson in error_types.items():
            if error_type in error:
                return lesson
        
        return f"未知错误类型: {error[:50]}"
    
    def _suggest_action(self, error: str, context: Dict = None) -> str:
        """建议行动"""
        # 根据错误类型建议
        if "ConnectionRefused" in error:
            return "检查服务状态，启动相关服务"
        elif "FileNotFound" in error:
            return "检查文件路径，创建缺失文件"
        elif "KeyError" in error:
            return "检查数据结构，添加默认值"
        elif "Import" in error:
            return "安装缺失依赖"
        else:
            return "记录错误并手动分析"
    
    def _extract_lesson(self, operation: str, details: Dict = None) -> Optional[str]:
        """提取成功经验"""
        if not details:
            return None
        
        # 简单的经验提取
        lessons = []
        
        if details.get("fast"):
            lessons.append("快速完成，策略有效")
        
        if details.get("accurate"):
            lessons.append("结果准确，方法正确")
        
        if details.get("efficient"):
            lessons.append("效率高，资源利用合理")
        
        return "; ".join(lessons) if lessons else None


# 全局实例
learner = SelfLearner()


# ============ CLI 入口 ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="自我学习系统")
    parser.add_argument("command", choices=["learn", "list", "optimize", "patterns"])
    parser.add_argument("--error", "-e", help="错误信息")
    parser.add_argument("--operation", "-o", help="操作名称")
    
    args = parser.parse_args()
    
    if args.command == "learn":
        if args.error:
            learning = learner.learn_from_error(args.error)
            print(f"✅ 学习记录: {learning.lesson}")
            print(f"   行动: {learning.action}")
        else:
            print("❌ 请提供 --error 参数")
    
    elif args.command == "list":
        learnings = learner.get_learnings()
        print(f"📚 学习记录 ({len(learnings)} 条)\n")
        for l in learnings[:10]:
            emoji = "❌" if l.type == "error" else "✅"
            print(f"{emoji} {l.trigger[:30]}: {l.lesson}")
    
    elif args.command == "optimize":
        if args.operation:
            result = learner.optimize_strategy(args.operation)
            print(f"🎯 优化建议\n")
            print(f"操作: {result.get('operation')}")
            print(f"历史记录: {result.get('history_count')} 次")
            print(f"最佳行动: {result.get('best_action')}")
            print(f"建议: {result.get('suggestion')}")
        else:
            print("❌ 请提供 --operation 参数")
    
    elif args.command == "patterns":
        print(f"🔍 错误模式库 ({len(learner.patterns)} 个)\n")
        for pattern, solutions in learner.patterns.items():
            print(f"模式: {pattern[:50]}...")
            for sol in solutions[:3]:
                print(f"  - {sol}")


if __name__ == "__main__":
    main()
