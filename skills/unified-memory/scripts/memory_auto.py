#!/usr/bin/env python3
"""
Memory Auto - 完全自动化记忆 v0.2.0

功能:
- 自动判断什么该存
- 智能提取重要信息
- 自动去重和合并
- 无需手动触发

Usage:
    # 由 Agent 自动调用，不需要手动运行
    from memory_auto import MemoryAuto
    
    auto = MemoryAuto()
    auto.process_conversation("对话内容")
    auto.should_store("内容") -> bool
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
AUTO_LOG = MEMORY_DIR / "auto_log.json"

# 重要信息模式
IMPORTANT_PATTERNS = {
    "preference": [
        r"我(喜欢|偏好|爱用|习惯用)",
        r"(最好|建议|希望|想要)",
        r"(用|选择|决定).{1,10}(进行|做|处理)",
    ],
    "decision": [
        r"(决定|确定|选择|采用|使用)",
        r"(必须|需要|应该|要)",
    ],
    "event": [
        r"(明天|下周|下月|周[一二三四五六日])",
        r"(会议|约会|面试|电话|通话)",
        r"(生日|纪念日|节日)",
        r"(截止|到期|完成)",
    ],
    "learning": [
        r"(学到|学会|掌握|发现|意识到)",
        r"(重要|关键|注意|记住)",
    ],
    "project": [
        r"(项目|任务|工作)",
        r"(开始|进行|完成|暂停|取消)",
    ]
}

# 无关信息模式
SKIP_PATTERNS = [
    r"^(嗯|好|好的|可以|行|OK|ok)$",
    r"^(哈哈|呵呵|嗯哼)$",
    r"^(谢谢|感谢|thx)$",
    r"^[\s\n]*$",
]

# 敏感词
SENSITIVE_WORDS = [
    "password", "密码", "token", "密钥", "secret", "api_key",
    "信用卡", "银行卡", "身份证", "验证码"
]


class MemoryAuto:
    """自动化记忆管理器"""
    
    def __init__(self):
        self.session_log = []
    
    def is_sensitive(self, text: str) -> bool:
        """检查是否包含敏感信息"""
        text_lower = text.lower()
        for word in SENSITIVE_WORDS:
            if word.lower() in text_lower:
                return True
        return False
    
    def should_skip(self, text: str) -> bool:
        """判断是否应该跳过"""
        text = text.strip()
        
        # 太短
        if len(text) < 5:
            return True
        
        # 匹配跳过模式
        for pattern in SKIP_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # 敏感信息
        if self.is_sensitive(text):
            return True
        
        return False
    
    def extract_importance(self, text: str) -> Tuple[bool, Optional[str], float]:
        """
        提取重要信息和分类
        
        Returns:
            (是否重要, 分类, 重要性分数)
        """
        if self.should_skip(text):
            return False, None, 0.0
        
        # 检查匹配模式
        for category, patterns in IMPORTANT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    # 计算重要性分数
                    importance = 0.5
                    
                    # 时间敏感加分
                    if category == "event":
                        importance += 0.3
                    
                    # 决策加分
                    if category == "decision":
                        importance += 0.2
                    
                    # 学习加分
                    if category == "learning":
                        importance += 0.2
                    
                    return True, category, min(importance, 1.0)
        
        # 默认不太重要
        return False, "general", 0.3
    
    def should_store(self, text: str) -> bool:
        """判断是否应该存储"""
        important, _, _ = self.extract_importance(text)
        return important
    
    def extract_core_content(self, text: str) -> str:
        """提取核心内容"""
        # 移除前缀
        text = re.sub(r'^(用户|我|我):?\s*', '', text)
        
        # 移除语气词
        text = re.sub(r'(吧|呢|啊|哦|呀)+$', '', text)
        
        # 如果有冒号，取冒号后的内容
        if '：' in text:
            text = text.split('：', 1)[1].strip()
        elif ':' in text:
            text = text.split(':', 1)[1].strip()
        
        return text.strip()
    
    def deduplicate(self, text: str) -> bool:
        """检查是否重复"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            text_lower = text.lower().strip()
            
            for stored in data.get("text", []):
                stored_lower = stored.lower().strip()
                
                # 完全相同
                if text_lower == stored_lower:
                    return True
                
                # 高度相似
                if len(text_lower) > 20 and text_lower in stored_lower:
                    return True
                if len(stored_lower) > 20 and stored_lower in text_lower:
                    return True
            
        except:
            pass
        
        return False
    
    def process_conversation(
        self,
        conversation: str,
        auto_store: bool = True
    ) -> Dict:
        """
        处理对话，自动提取和存储
        
        Args:
            conversation: 对话内容
            auto_store: 是否自动存储
        
        Returns:
            处理结果
        """
        results = {
            "total_lines": 0,
            "important_lines": 0,
            "stored": 0,
            "skipped": 0,
            "duplicates": 0,
            "items": []
        }
        
        lines = conversation.split('\n')
        results["total_lines"] = len(lines)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 提取重要性
            important, category, importance = self.extract_importance(line)
            
            if not important:
                results["skipped"] += 1
                continue
            
            results["important_lines"] += 1
            
            # 提取核心内容
            core = self.extract_core_content(line)
            
            if len(core) < 5:
                continue
            
            # 检查重复
            if self.deduplicate(core):
                results["duplicates"] += 1
                continue
            
            # 存储
            if auto_store:
                try:
                    import lancedb
                    import uuid
                    
                    db = lancedb.connect(str(VECTOR_DB_DIR))
                    table = db.open_table("memories")
                    
                    table.add([{
                        "id": str(uuid.uuid4()),
                        "text": core,
                        "category": category,
                        "importance": importance,
                        "timestamp": datetime.now().isoformat(),
                        "vector": []
                    }])
                    
                    results["stored"] += 1
                    results["items"].append({
                        "text": core[:50],
                        "category": category,
                        "importance": importance
                    })
                    
                except Exception as e:
                    print(f"存储失败: {e}")
        
        # 记录日志
        self._log_session(results)
        
        return results
    
    def _log_session(self, results: Dict):
        """记录会话日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": results["total_lines"],
                "important": results["important_lines"],
                "stored": results["stored"]
            }
        }
        
        self.session_log.append(log_entry)
        
        # 保存到文件
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        
        existing = []
        if AUTO_LOG.exists():
            with open(AUTO_LOG) as f:
                existing = json.load(f)
        
        existing.append(log_entry)
        
        with open(AUTO_LOG, 'w') as f:
            json.dump(existing[-100:], f, ensure_ascii=False, indent=2)  # 保留最近100条


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Auto 0.2.0")
    parser.add_argument("command", choices=["process", "should-store"])
    parser.add_argument("text", nargs="?", help="文本内容")
    parser.add_argument("--file", "-f", help="文件路径")
    parser.add_argument("--dry-run", action="store_true", help="不实际存储")
    
    args = parser.parse_args()
    
    auto = MemoryAuto()
    
    if args.command == "should-store":
        if not args.text:
            print("请提供文本")
            return
        
        should = auto.should_store(args.text)
        important, category, importance = auto.extract_importance(args.text)
        
        print(f"应该存储: {should}")
        print(f"分类: {category}")
        print(f"重要性: {importance}")
    
    elif args.command == "process":
        conversation = ""
        
        if args.file:
            with open(args.file, encoding='utf-8') as f:
                conversation = f.read()
        elif args.text:
            conversation = args.text
        else:
            print("请提供对话内容或文件")
            return
        
        results = auto.process_conversation(conversation, auto_store=not args.dry_run)
        
        print(f"📊 处理结果:")
        print(f"   总行数: {results['total_lines']}")
        print(f"   重要行: {results['important_lines']}")
        print(f"   已存储: {results['stored']}")
        print(f"   已跳过: {results['skipped']}")
        print(f"   重复: {results['duplicates']}")
        
        if results['items']:
            print(f"\n✅ 已存储:")
            for item in results['items'][:5]:
                print(f"   [{item['category']}] {item['text']}...")


if __name__ == "__main__":
    main()
