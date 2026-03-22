#!/usr/bin/env python3
"""
Quality Assessor - 质量评估引擎

功能:
- 代码质量检查 (语法、复杂度、安全)
- 任务完成度评估
- 自动评分
"""

import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"  # 90+
    GOOD = "good"           # 70-89
    ACCEPTABLE = "acceptable"  # 50-69
    POOR = "poor"           # 30-49
    CRITICAL = "critical"   # <30


@dataclass
class QualityReport:
    score: float  # 0-100
    level: QualityLevel
    issues: List[Dict]
    metrics: Dict
    suggestions: List[str]


class QualityAssessor:
    """质量评估引擎"""
    
    def __init__(self):
        self.rules = {
            "python": self._python_rules,
            "javascript": self._javascript_rules,
            "generic": self._generic_rules
        }
    
    def assess_code(self, code: str, language: str = "python") -> QualityReport:
        """评估代码质量"""
        language = language.lower()
        
        # 选择规则
        rules_func = self.rules.get(language, self._generic_rules)
        
        # 执行检查
        issues = rules_func(code)
        
        # 计算分数
        score = self._calculate_score(issues)
        
        # 确定等级
        level = self._determine_level(score)
        
        # 计算指标
        metrics = self._calculate_metrics(code, language)
        
        # 生成建议
        suggestions = self._generate_suggestions(issues)
        
        return QualityReport(
            score=score,
            level=level,
            issues=issues,
            metrics=metrics,
            suggestions=suggestions
        )
    
    def _python_rules(self, code: str) -> List[Dict]:
        """Python 代码规则"""
        issues = []
        
        # 1. 语法检查
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "severity": "critical",
                "message": f"语法错误: {e.msg}",
                "line": e.lineno
            })
        
        # 2. 行长度
        for i, line in enumerate(code.split("\n"), 1):
            if len(line) > 100:
                issues.append({
                    "type": "style",
                    "severity": "minor",
                    "message": f"行过长 ({len(line)} 字符)",
                    "line": i
                })
        
        # 3. 导入检查
        if "import *" in code:
            issues.append({
                "type": "style",
                "severity": "major",
                "message": "使用 import * 不推荐",
                "line": None
            })
        
        # 4. 空异常处理
        if re.search(r'except\s*:', code) and 'pass' in code:
            issues.append({
                "type": "security",
                "severity": "major",
                "message": "空的异常处理可能隐藏问题",
                "line": None
            })
        
        # 5. 硬编码密码
        if re.search(r'(password|passwd|pwd)\s*=\s*["\']', code, re.I):
            issues.append({
                "type": "security",
                "severity": "critical",
                "message": "检测到硬编码密码",
                "line": None
            })
        
        # 6. TODO/FIXME
        todos = re.findall(r'#\s*(TODO|FIXME):?\s*(.+)', code, re.I)
        for todo_type, todo_msg in todos:
            issues.append({
                "type": "todo",
                "severity": "minor",
                "message": f"{todo_type}: {todo_msg}",
                "line": None
            })
        
        # 7. 复杂度 (嵌套深度)
        max_depth = 0
        current_depth = 0
        for char in code:
            if char == '{' or char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}' or char == ')':
                current_depth -= 1
        
        if max_depth > 4:
            issues.append({
                "type": "complexity",
                "severity": "major",
                "message": f"嵌套深度过大 ({max_depth} 层)",
                "line": None
            })
        
        return issues
    
    def _javascript_rules(self, code: str) -> List[Dict]:
        """JavaScript 代码规则"""
        issues = []
        
        # 1. var 检查
        if re.search(r'\bvar\b', code):
            issues.append({
                "type": "style",
                "severity": "minor",
                "message": "建议使用 let/const 替代 var",
                "line": None
            })
        
        # 2. console.log
        console_logs = len(re.findall(r'console\.log', code))
        if console_logs > 3:
            issues.append({
                "type": "style",
                "severity": "minor",
                "message": f"过多 console.log ({console_logs} 个)",
                "line": None
            })
        
        # 3. == vs ===
        if re.search(r'[^=!]==[^=]', code):
            issues.append({
                "type": "style",
                "severity": "major",
                "message": "建议使用 === 替代 ==",
                "line": None
            })
        
        # 4. 硬编码 API Key
        if re.search(r'(api[_-]?key|apikey)\s*[:=]\s*["\']', code, re.I):
            issues.append({
                "type": "security",
                "severity": "critical",
                "message": "检测到硬编码 API Key",
                "line": None
            })
        
        return issues
    
    def _generic_rules(self, code: str) -> List[Dict]:
        """通用规则"""
        issues = []
        
        # 1. 空文件
        if len(code.strip()) < 10:
            issues.append({
                "type": "content",
                "severity": "critical",
                "message": "代码过短",
                "line": None
            })
        
        # 2. 密码/API Key 模式
        patterns = [
            (r'password\s*=\s*["\']', "硬编码密码"),
            (r'api[_-]?key\s*=\s*["\']', "硬编码 API Key"),
            (r'secret\s*=\s*["\']', "硬编码密钥")
        ]
        
        for pattern, msg in patterns:
            if re.search(pattern, code, re.I):
                issues.append({
                    "type": "security",
                    "severity": "critical",
                    "message": msg,
                    "line": None
                })
        
        return issues
    
    def _calculate_score(self, issues: List[Dict]) -> float:
        """计算分数"""
        if not issues:
            return 100.0
        
        # 权重
        weights = {
            "critical": 20,
            "major": 10,
            "minor": 5
        }
        
        # 扣分
        deduction = 0
        for issue in issues:
            severity = issue.get("severity", "minor")
            deduction += weights.get(severity, 5)
        
        # 分数 (最低 0)
        score = max(0, 100 - deduction)
        
        return score
    
    def _determine_level(self, score: float) -> QualityLevel:
        """确定等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.ACCEPTABLE
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _calculate_metrics(self, code: str, language: str) -> Dict:
        """计算指标"""
        lines = code.split("\n")
        
        return {
            "total_lines": len(lines),
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith("#")]),
            "comment_lines": len([l for l in lines if l.strip().startswith("#")]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "characters": len(code),
            "language": language
        }
    
    def _generate_suggestions(self, issues: List[Dict]) -> List[str]:
        """生成建议"""
        suggestions = []
        
        # 按严重程度分组
        critical = [i for i in issues if i.get("severity") == "critical"]
        major = [i for i in issues if i.get("severity") == "major"]
        
        if critical:
            suggestions.append(f"⚠️ 发现 {len(critical)} 个严重问题，建议优先修复")
        
        if major:
            suggestions.append(f"📋 发现 {len(major)} 个重要问题，建议处理")
        
        # 具体建议
        for issue in critical[:3]:
            suggestions.append(f"  - {issue['message']}")
        
        return suggestions
    
    def assess_task_completion(self, task: Dict, deliverables: List[Dict]) -> Dict:
        """评估任务完成度"""
        # 检查交付物
        expected = task.get("expected_deliverables", [])
        actual = [d.get("type") for d in deliverables]
        
        # 完成度
        completed = len(set(expected) & set(actual))
        total = len(expected)
        
        completion_rate = (completed / total * 100) if total > 0 else 100
        
        # 质量分数
        quality_scores = []
        for deliverable in deliverables:
            if deliverable.get("type") == "code":
                report = self.assess_code(deliverable.get("content", ""))
                quality_scores.append(report.score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 70
        
        return {
            "completion_rate": completion_rate,
            "quality_score": avg_quality,
            "overall_score": (completion_rate * 0.4 + avg_quality * 0.6),
            "missing_deliverables": list(set(expected) - set(actual))
        }


# CLI 入口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="质量评估引擎")
    parser.add_argument("file", nargs="?", help="要评估的文件")
    parser.add_argument("--code", "-c", help="直接评估代码")
    parser.add_argument("--language", "-l", default="python", help="语言")
    
    args = parser.parse_args()
    
    assessor = QualityAssessor()
    
    # 获取代码
    if args.code:
        code = args.code
    elif args.file:
        code = Path(args.file).read_text()
    else:
        # 示例代码
        code = '''
def hello(name):
    print(f"Hello, {name}!")
    
password = "123456"  # 硬编码密码

try:
    something()
except:
    pass  # 空异常处理
'''
        print("📝 使用示例代码演示:\n")
    
    # 评估
    report = assessor.assess_code(code, args.language)
    
    print(f"质量分数: {report.score:.1f} ({report.level})")
    print(f"\n指标:")
    for k, v in report.metrics.items():
        print(f"  {k}: {v}")
    
    if report.issues:
        print(f"\n问题 ({len(report.issues)} 个):")
        for issue in report.issues[:10]:
            severity = issue.get("severity", "minor")
            emoji = {"critical": "🔴", "major": "🟡", "minor": "🟢"}.get(severity, "⚪")
            print(f"  {emoji} {issue['message']}")
    
    if report.suggestions:
        print(f"\n建议:")
        for suggestion in report.suggestions:
            print(f"  {suggestion}")


if __name__ == "__main__":
    main()
