#!/usr/bin/env python3
"""
Smart Chunking - 智能分块系统
借鉴 QMD 的断点检测算法，实现自然语义分块

核心功能:
- 识别代码块区域（保护不切断）
- 识别标题边界（优先断点）
- 识别段落边界（次优断点）
- 动态调整分块大小

Usage:
    from smart_chunk import smart_chunk
    
    chunks = smart_chunk(text, max_tokens=900)
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path


@dataclass
class BreakPoint:
    """断点信息"""
    pos: int        # 字符位置
    score: int      # 分数（越高越好）
    type: str       # 类型: h1/h2/codeblock/blank/etc.


@dataclass
class CodeFenceRegion:
    """代码块区域"""
    start: int      # 开始位置
    end: int        # 结束位置


# =============================================================================
# 断点模式（分数越高越适合作为断点）
# =============================================================================

BREAK_PATTERNS: List[Tuple[re.Pattern, int, str]] = [
    # 标题（优先级最高）
    (re.compile(r'\n#{1}(?!#)'), 100, 'h1'),      # # 但不是 ##
    (re.compile(r'\n#{2}(?!#)'), 90, 'h2'),       # ## 但不是 ###
    (re.compile(r'\n#{3}(?!#)'), 80, 'h3'),       # ### 但不是 ####
    (re.compile(r'\n#{4}(?!#)'), 70, 'h4'),       # ####
    (re.compile(r'\n#{5}(?!#)'), 60, 'h5'),       # #####
    (re.compile(r'\n#{6}'), 50, 'h6'),            # ######
    
    # 代码块边界（重要 - 不应切断代码）
    (re.compile(r'\n```'), 80, 'codeblock'),
    
    # 水平线
    (re.compile(r'\n(?:---|\*\*\*|___)\s*\n'), 60, 'hr'),
    
    # 段落边界
    (re.compile(r'\n\n+'), 20, 'blank'),
    
    # 列表项
    (re.compile(r'\n[-*]\s'), 5, 'list'),
    (re.compile(r'\n\d+\.\s'), 5, 'numlist'),
    
    # 最小断点
    (re.compile(r'\n'), 1, 'newline'),
]


def find_code_fences(text: str) -> List[CodeFenceRegion]:
    """
    找出所有代码块区域
    这些区域内的内容不应被切断
    """
    regions = []
    in_fence = False
    fence_start = 0
    
    # 匹配代码块标记
    fence_pattern = re.compile(r'```')
    
    for match in fence_pattern.finditer(text):
        if not in_fence:
            # 开始代码块
            fence_start = match.start()
            in_fence = True
        else:
            # 结束代码块
            regions.append(CodeFenceRegion(fence_start, match.end()))
            in_fence = False
    
    # 处理未闭合的代码块
    if in_fence:
        regions.append(CodeFenceRegion(fence_start, len(text)))
    
    return regions


def scan_break_points(text: str) -> List[BreakPoint]:
    """
    扫描所有潜在断点
    
    返回按位置排序的断点列表
    """
    points = []
    seen = {}  # pos -> BreakPoint（保留最高分）
    
    for pattern, score, btype in BREAK_PATTERNS:
        for match in pattern.finditer(text):
            pos = match.start()
            
            # 如果同一位置已有断点，保留高分
            if pos in seen:
                if score > seen[pos].score:
                    seen[pos] = BreakPoint(pos, score, btype)
            else:
                seen[pos] = BreakPoint(pos, score, btype)
    
    # 转为列表并按位置排序
    points = list(seen.values())
    points.sort(key=lambda x: x.pos)
    
    return points


def is_in_code_fence(pos: int, fences: List[CodeFenceRegion]) -> bool:
    """检查位置是否在代码块内"""
    for fence in fences:
        if fence.start <= pos <= fence.end:
            return True
    return False


def find_best_break_point(
    text: str,
    target_pos: int,
    break_points: List[BreakPoint],
    fences: List[CodeFenceRegion],
    window: int = 800  # 搜索窗口（字符）
) -> Optional[BreakPoint]:
    """
    在目标位置附近找到最佳断点
    
    Args:
        text: 文本
        target_pos: 目标位置
        break_points: 断点列表
        fences: 代码块区域
        window: 搜索窗口大小
    
    Returns:
        最佳断点，如果找不到则返回 None
    """
    candidates = []
    
    for bp in break_points:
        # 在窗口内
        if abs(bp.pos - target_pos) <= window:
            # 不在代码块内
            if not is_in_code_fence(bp.pos, fences):
                candidates.append(bp)
    
    if not candidates:
        return None
    
    # 选择距离目标最近且分数最高的
    # 分数 = 断点分数 - 距离惩罚
    best = max(candidates, key=lambda x: x.score - abs(x.pos - target_pos) * 0.01)
    
    return best


def smart_chunk(
    text: str,
    max_tokens: int = 900,
    overlap_tokens: int = 135,
    prefer_natural_breaks: bool = True
) -> List[str]:
    """
    智能分块
    
    Args:
        text: 要分块的文本
        max_tokens: 每块最大 token 数
        overlap_tokens: 重叠 token 数
        prefer_natural_breaks: 是否优先在自然边界分块
    
    Returns:
        分块列表
    """
    # Token 到字符的近似转换（~4 字符/token）
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4
    
    # 如果文本很短，直接返回
    if len(text) <= max_chars:
        return [text] if text.strip() else []
    
    # 预处理
    text = text.strip()
    
    # 找出代码块区域
    fences = find_code_fences(text)
    
    # 扫描断点
    break_points = scan_break_points(text) if prefer_natural_breaks else []
    
    chunks = []
    pos = 0
    
    while pos < len(text):
        # 计算目标位置
        target_pos = pos + max_chars
        
        if target_pos >= len(text):
            # 剩余部分
            chunk = text[pos:].strip()
            if chunk:
                chunks.append(chunk)
            break
        
        if prefer_natural_breaks and break_points:
            # 找最佳断点
            best_bp = find_best_break_point(
                text, target_pos, break_points, fences,
                window=400  # 较小窗口
            )
            
            if best_bp:
                end_pos = best_bp.pos
            else:
                # 没找到好的断点，用固定位置
                end_pos = target_pos
        else:
            # 固定大小分块
            end_pos = target_pos
        
        # 提取分块
        chunk = text[pos:end_pos].strip()
        
        if chunk:
            chunks.append(chunk)
        
        # 下一块的起始位置（考虑重叠）
        pos = end_pos - overlap_chars if end_pos < len(text) else end_pos
        
        # 确保前进
        if pos <= chunks[-1].find(chunk[:50]) if chunks else 0:
            pos = end_pos
    
    return chunks


def chunk_file(file_path: str, max_tokens: int = 900) -> List[str]:
    """分块文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return smart_chunk(text, max_tokens)


# =============================================================================
# CLI 接口
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Chunking")
    parser.add_argument("file", help="要分块的文件")
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--no-natural-breaks", action="store_true", help="禁用自然边界检测")
    parser.add_argument("--output", "-o", help="输出文件前缀")
    
    args = parser.parse_args()
    
    # 分块
    chunks = chunk_file(args.file, args.max_tokens)
    
    print(f"📄 文件分块结果: {len(chunks)} 块\n")
    
    if args.output:
        # 写入文件
        for i, chunk in enumerate(chunks, 1):
            output_file = f"{args.output}_{i:03d}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
            print(f"  ✅ {output_file} ({len(chunk)} 字符)")
    else:
        # 打印预览
        for i, chunk in enumerate(chunks, 1):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"  {i}. [{len(chunk)} 字符] {preview}\n")


if __name__ == "__main__":
    main()
