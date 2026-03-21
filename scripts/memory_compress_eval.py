#!/usr/bin/env python3
"""
L3 压缩质量评估 v1.0

功能:
- 评估压缩摘要质量
- 检测关键信息丢失
- 计算压缩比和可读性

Usage:
    mem compress-eval              # 评估所有压缩记忆
    mem compress-eval --id <ID>    # 评估指定记忆
    mem compress-eval --report     # 生成质量报告
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
COMPRESS_LOG = MEMORY_DIR / "compress_log.json"
EVAL_FILE = MEMORY_DIR / "compress_evaluation.json"


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    if MEMORIES_FILE.exists():
        return json.loads(MEMORIES_FILE.read_text())
    return []


def load_compress_log() -> List[Dict]:
    """加载压缩日志"""
    if COMPRESS_LOG.exists():
        return json.loads(COMPRESS_LOG.read_text())
    return []


def calculate_compression_ratio(original: str, compressed: str) -> float:
    """计算压缩比"""
    if not original:
        return 0
    return round(len(compressed) / len(original) * 100, 1)


def count_key_info(text: str) -> int:
    """计算关键信息数量（数字、日期、专有名词）"""
    # 数字
    numbers = len(re.findall(r'\d+', text))
    # 日期格式
    dates = len(re.findall(r'\d{4}-\d{2}-\d{2}|\d{1,2}月\d{1,2}日', text))
    # 中文专有名词（简单规则：2-4字大写开头）
    proper_nouns = len(re.findall(r'[\u4e00-\u9fff]{2,4}(?:项目|系统|平台|模块)', text))
    
    return numbers + dates + proper_nouns


def calculate_info_retention(original: str, compressed: str) -> float:
    """计算信息保留率"""
    if not original:
        return 0
    
    orig_info = count_key_info(original)
    comp_info = count_key_info(compressed)
    
    if orig_info == 0:
        return 100  # 无关键信息，视为完全保留
    
    return round(comp_info / orig_info * 100, 1)


def calculate_readability(text: str) -> float:
    """计算可读性分数（简单版）"""
    if not text:
        return 0
    
    score = 50  # 基础分
    
    # 长度适中（50-200字）
    length = len(text)
    if 50 <= length <= 200:
        score += 20
    elif length < 20:
        score -= 20
    
    # 句子完整（有句号）
    sentences = len(re.findall(r'[。！？]', text))
    if sentences >= 1:
        score += 10
    
    # 无截断
    if not text.endswith('...') and not text.endswith('…'):
        score += 10
    
    # 有结构（有序号或分隔符）
    if re.search(r'[1-9][、.]|[-•]', text):
        score += 10
    
    return min(100, max(0, score))


def evaluate_compression(original: str, compressed: str) -> Dict:
    """评估单条压缩质量"""
    compression_ratio = calculate_compression_ratio(original, compressed)
    info_retention = calculate_info_retention(original, compressed)
    readability = calculate_readability(compressed)
    
    # 综合质量分 = 信息保留 * 0.5 + 可读性 * 0.3 + 压缩效率 * 0.2
    # 压缩效率：理想压缩比30-50%
    if 30 <= compression_ratio <= 50:
        efficiency_score = 100
    elif compression_ratio < 30:
        efficiency_score = compression_ratio * 3.3  # 太压缩，信息丢失风险
    else:
        efficiency_score = max(0, 100 - (compression_ratio - 50) * 2)  # 压缩不够
    
    quality_score = round(
        info_retention * 0.5 + 
        readability * 0.3 + 
        efficiency_score * 0.2, 
        1
    )
    
    return {
        "compression_ratio": compression_ratio,
        "info_retention": info_retention,
        "readability": readability,
        "efficiency_score": round(efficiency_score, 1),
        "quality_score": quality_score,
        "issues": detect_issues(original, compressed)
    }


def detect_issues(original: str, compressed: str) -> List[str]:
    """检测压缩问题"""
    issues = []
    
    # 检查长度
    if len(compressed) < 20:
        issues.append("摘要过短，可能丢失信息")
    elif len(compressed) > len(original) * 0.7:
        issues.append("压缩不足，摘要过长")
    
    # 检查关键信息
    orig_info = count_key_info(original)
    comp_info = count_key_info(compressed)
    if orig_info > 0 and comp_info < orig_info * 0.5:
        issues.append(f"关键信息丢失严重（保留{comp_info}/{orig_info}）")
    
    # 检查可读性
    if compressed.endswith('...'):
        issues.append("摘要截断，不完整")
    
    if not re.search(r'[。！？]', compressed):
        issues.append("缺少标点，影响阅读")
    
    return issues


def evaluate_all_memories(memories: List[Dict]) -> Dict:
    """评估所有压缩记忆"""
    results = {
        "evaluated_at": datetime.now().isoformat(),
        "total_compressed": 0,
        "average_quality": 0,
        "quality_distribution": {
            "excellent": 0,  # >= 90
            "good": 0,       # 70-89
            "fair": 0,       # 50-69
            "poor": 0        # < 50
        },
        "evaluations": []
    }
    
    quality_scores = []
    
    for mem in memories:
        # 检查是否是压缩记忆
        if not mem.get("compressed") and not mem.get("original_text"):
            continue
        
        original = mem.get("original_text", mem.get("text", ""))
        compressed = mem.get("text", "")
        
        if not original or not compressed:
            continue
        
        results["total_compressed"] += 1
        
        eval_result = evaluate_compression(original, compressed)
        eval_result["memory_id"] = mem.get("id")
        eval_result["category"] = mem.get("category")
        
        quality_scores.append(eval_result["quality_score"])
        
        # 分类
        score = eval_result["quality_score"]
        if score >= 90:
            results["quality_distribution"]["excellent"] += 1
        elif score >= 70:
            results["quality_distribution"]["good"] += 1
        elif score >= 50:
            results["quality_distribution"]["fair"] += 1
        else:
            results["quality_distribution"]["poor"] += 1
        
        results["evaluations"].append(eval_result)
    
    if quality_scores:
        results["average_quality"] = round(sum(quality_scores) / len(quality_scores), 1)
    
    return results


def print_report(results: Dict):
    """打印质量报告"""
    print("📊 L3 压缩质量评估报告\n")
    print("=" * 50)
    
    print(f"\n📈 总体统计")
    print(f"   评估数量: {results['total_compressed']}")
    print(f"   平均质量分: {results['average_quality']}")
    
    print(f"\n🎯 质量分布")
    dist = results["quality_distribution"]
    total = results["total_compressed"] or 1
    
    for level, count in dist.items():
        pct = count / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        level_name = {"excellent": "优秀", "good": "良好", "fair": "一般", "poor": "较差"}[level]
        print(f"   {level_name}: {bar} {count} ({pct:.0f}%)")
    
    # 显示质量最差的3条
    poor_evals = [e for e in results["evaluations"] if e["quality_score"] < 70]
    if poor_evals:
        print(f"\n⚠️ 需要改进的压缩（{len(poor_evals)}条）:")
        for e in poor_evals[:3]:
            print(f"   [{e['memory_id'][:8]}] 质量分: {e['quality_score']}")
            for issue in e.get("issues", []):
                print(f"      - {issue}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="L3 压缩质量评估")
    parser.add_argument("--id", "-i", help="评估指定记忆ID")
    parser.add_argument("--report", "-r", action="store_true", help="生成详细报告")
    parser.add_argument("--save", "-s", action="store_true", help="保存评估结果")
    
    args = parser.parse_args()
    
    memories = load_memories()
    
    if args.id:
        # 评估单个记忆
        mem = next((m for m in memories if m.get("id", "").startswith(args.id)), None)
        if not mem:
            print(f"❌ 未找到记忆: {args.id}")
            return
        
        original = mem.get("original_text", mem.get("text", ""))
        compressed = mem.get("text", "")
        
        if not original or original == compressed:
            print("❌ 该记忆未压缩")
            return
        
        result = evaluate_compression(original, compressed)
        print(f"📊 压缩质量评估\n")
        print(f"   原文长度: {len(original)} 字")
        print(f"   摘要长度: {len(compressed)} 字")
        print(f"   压缩比: {result['compression_ratio']}%")
        print(f"   信息保留: {result['info_retention']}%")
        print(f"   可读性: {result['readability']}/100")
        print(f"   综合质量: {result['quality_score']}/100")
        
        if result["issues"]:
            print(f"\n⚠️ 问题:")
            for issue in result["issues"]:
                print(f"   - {issue}")
    
    else:
        # 评估所有
        results = evaluate_all_memories(memories)
        
        if args.report:
            print_report(results)
        else:
            print(f"📊 评估了 {results['total_compressed']} 条压缩记忆")
            print(f"   平均质量分: {results['average_quality']}")
        
        if args.save:
            EVAL_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False))
            print(f"\n💾 评估结果已保存: {EVAL_FILE}")


if __name__ == "__main__":
    main()
