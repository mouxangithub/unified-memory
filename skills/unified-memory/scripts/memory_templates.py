#!/usr/bin/env python3
"""
Memory Templates - 记忆模板系统 v1.0

站在 AI Agent 用户角度：
- 快速创建常用类型的记忆
- 标准化记忆格式
- 提高记忆质量

模板类型：
- 项目信息 (project)
- 会议记录 (meeting)
- 决策记录 (decision)
- 偏好设置 (preference)
- 任务清单 (task)
- 联系人 (contact)
- 学习笔记 (learning)

Usage:
    python3 scripts/memory_templates.py list
    python3 scripts/memory_templates.py create --type project --data '{"name":"龙宫","status":"开发中"}'
    python3 scripts/memory_templates.py fill --type meeting
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
TEMPLATES_FILE = MEMORY_DIR / "templates.json"

# Ollama 配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# 预定义模板
DEFAULT_TEMPLATES = {
    "project": {
        "name": "项目信息",
        "description": "记录项目基本信息",
        "importance": 0.8,
        "category": "entity",
        "fields": [
            {"name": "project_name", "label": "项目名称", "required": True},
            {"name": "status", "label": "状态", "options": ["规划中", "开发中", "测试中", "已上线", "维护中"]},
            {"name": "tech_stack", "label": "技术栈"},
            {"name": "start_date", "label": "开始日期"},
            {"name": "owner", "label": "负责人"},
            {"name": "description", "label": "项目描述"}
        ],
        "template": "{project_name} 项目，状态：{status}，技术栈：{tech_stack}，负责人：{owner}。{description}"
    },
    
    "meeting": {
        "name": "会议记录",
        "description": "记录会议要点",
        "importance": 0.7,
        "category": "event",
        "fields": [
            {"name": "title", "label": "会议主题", "required": True},
            {"name": "date", "label": "日期", "default": "today"},
            {"name": "participants", "label": "参会人"},
            {"name": "decisions", "label": "决策事项"},
            {"name": "action_items", "label": "行动项"},
            {"name": "next_meeting", "label": "下次会议"}
        ],
        "template": "会议：{title}（{date}）。参会：{participants}。决策：{decisions}。行动项：{action_items}。"
    },
    
    "decision": {
        "name": "决策记录",
        "description": "记录重要决策",
        "importance": 0.9,
        "category": "decision",
        "fields": [
            {"name": "topic", "label": "决策主题", "required": True},
            {"name": "decision", "label": "决策内容"},
            {"name": "reason", "label": "决策理由"},
            {"name": "alternatives", "label": "备选方案"},
            {"name": "impact", "label": "影响范围"}
        ],
        "template": "决策：{topic}。选择：{decision}。理由：{reason}。影响：{impact}。"
    },
    
    "preference": {
        "name": "偏好设置",
        "description": "记录用户偏好",
        "importance": 0.8,
        "category": "preference",
        "fields": [
            {"name": "area", "label": "偏好领域", "required": True, "options": ["工具", "沟通", "工作流", "时间", "其他"]},
            {"name": "preference", "label": "偏好内容"},
            {"name": "reason", "label": "原因"},
            {"name": "exceptions", "label": "例外情况"}
        ],
        "template": "偏好：在{area}方面，{preference}。原因：{reason}。"
    },
    
    "task": {
        "name": "任务清单",
        "description": "记录待办任务",
        "importance": 0.6,
        "category": "task",
        "fields": [
            {"name": "task_name", "label": "任务名称", "required": True},
            {"name": "priority", "label": "优先级", "options": ["高", "中", "低"]},
            {"name": "deadline", "label": "截止日期"},
            {"name": "assignee", "label": "负责人"},
            {"name": "status", "label": "状态", "options": ["待开始", "进行中", "已完成", "已延期"]},
            {"name": "notes", "label": "备注"}
        ],
        "template": "任务：{task_name}，优先级：{priority}，截止：{deadline}，状态：{status}。{notes}"
    },
    
    "contact": {
        "name": "联系人",
        "description": "记录联系人信息",
        "importance": 0.7,
        "category": "entity",
        "fields": [
            {"name": "name", "label": "姓名", "required": True},
            {"name": "role", "label": "角色"},
            {"name": "company", "label": "公司"},
            {"name": "contact", "label": "联系方式"},
            {"name": "notes", "label": "备注"}
        ],
        "template": "联系人：{name}，{role}@{company}。联系方式：{contact}。备注：{notes}"
    },
    
    "learning": {
        "name": "学习笔记",
        "description": "记录学习内容",
        "importance": 0.6,
        "category": "learning",
        "fields": [
            {"name": "topic", "label": "学习主题", "required": True},
            {"name": "source", "label": "来源"},
            {"name": "key_points", "label": "关键点"},
            {"name": "questions", "label": "疑问"},
            {"name": "application", "label": "应用场景"}
        ],
        "template": "学习：{topic}（来源：{source}）。要点：{key_points}。应用：{application}。"
    },
    
    "error_solution": {
        "name": "问题解决",
        "description": "记录问题和解决方案",
        "importance": 0.8,
        "category": "learning",
        "fields": [
            {"name": "error", "label": "问题描述", "required": True},
            {"name": "context", "label": "出现场景"},
            {"name": "solution", "label": "解决方案"},
            {"name": "reference", "label": "参考链接"}
        ],
        "template": "问题：{error}。场景：{context}。解决：{solution}。参考：{reference}。"
    }
}


class MemoryTemplates:
    """记忆模板系统"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """加载模板"""
        if TEMPLATES_FILE.exists():
            with open(TEMPLATES_FILE) as f:
                custom = json.load(f)
                # 合并默认模板和自定义模板
                return {**DEFAULT_TEMPLATES, **custom.get("custom", {})}
        return DEFAULT_TEMPLATES
    
    def _save_templates(self):
        """保存模板"""
        TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump({
                "default": DEFAULT_TEMPLATES,
                "custom": {k: v for k, v in self.templates.items() if k not in DEFAULT_TEMPLATES}
            }, f, ensure_ascii=False, indent=2)
    
    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        result = []
        for key, template in self.templates.items():
            result.append({
                "type": key,
                "name": template.get("name", key),
                "description": template.get("description", ""),
                "fields_count": len(template.get("fields", [])),
                "importance": template.get("importance", 0.5),
                "category": template.get("category", "other")
            })
        return result
    
    def get_template(self, template_type: str) -> Optional[Dict]:
        """获取模板详情"""
        return self.templates.get(template_type)
    
    def create_memory(self, template_type: str, data: Dict) -> Dict:
        """根据模板创建记忆"""
        template = self.templates.get(template_type)
        if not template:
            return {"error": f"模板 '{template_type}' 不存在"}
        
        # 验证必填字段
        missing = []
        for field in template.get("fields", []):
            if field.get("required") and not data.get(field["name"]):
                missing.append(field["label"])
        
        if missing:
            return {"error": f"缺少必填字段: {', '.join(missing)}"}
        
        # 填充默认值
        filled_data = {}
        for field in template.get("fields", []):
            field_name = field["name"]
            
            if field_name in data:
                filled_data[field_name] = data[field_name]
            elif field.get("default") == "today":
                filled_data[field_name] = datetime.now().strftime("%Y-%m-%d")
            elif field.get("default"):
                filled_data[field_name] = field["default"]
            else:
                filled_data[field_name] = ""
        
        # 生成文本
        text = template["template"].format(**filled_data)
        
        # 存储到数据库
        memory_id = self._store_memory(
            text=text,
            category=template.get("category", "other"),
            importance=template.get("importance", 0.5),
            tags=[template_type]
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "text": text,
            "template_type": template_type
        }
    
    def _store_memory(self, text: str, category: str, importance: float, tags: List[str]) -> str:
        """存储记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            # 获取嵌入
            vector = self._get_embedding(text) or []
            
            # 生成 ID
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(text) % 10000}"
            
            # 存储
            table.add([{
                "id": memory_id,
                "text": text,
                "category": category,
                "importance": importance,
                "tags": tags,
                "timestamp": datetime.now().isoformat(),
                "vector": vector
            }])
            
            return memory_id
            
        except Exception as e:
            print(f"⚠️ 存储失败: {e}")
            return ""
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取嵌入向量"""
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=10
            )
            if response.ok:
                return response.json().get("embedding", [])
        except:
            pass
        return None
    
    def add_custom_template(self, template_type: str, template: Dict) -> Dict:
        """添加自定义模板"""
        # 验证模板结构
        required_fields = ["name", "template", "fields"]
        for field in required_fields:
            if field not in template:
                return {"error": f"模板缺少必需字段: {field}"}
        
        self.templates[template_type] = template
        self._save_templates()
        
        return {"success": True, "type": template_type}
    
    def get_interactive_prompt(self, template_type: str) -> str:
        """生成交互式提示"""
        template = self.templates.get(template_type)
        if not template:
            return f"模板 '{template_type}' 不存在"
        
        lines = [f"📝 {template['name']}", ""]
        
        for field in template.get("fields", []):
            required = "*" if field.get("required") else ""
            options = f" [{', '.join(field.get('options', []))}]" if field.get("options") else ""
            default = f" (默认: {field.get('default')})" if field.get("default") else ""
            
            lines.append(f"  {required}{field['label']}{options}{default}")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Memory Templates v1.0")
    parser.add_argument("command", choices=["list", "get", "create", "prompt", "add-custom"])
    parser.add_argument("--type", "-t", help="模板类型")
    parser.add_argument("--data", "-d", help="JSON 数据")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    templates = MemoryTemplates()
    
    if args.command == "list":
        result = templates.list_templates()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("📋 可用模板:")
            print()
            for t in result:
                print(f"  {t['type']:15} {t['name']:10} ({t['fields_count']} 字段)")
    
    elif args.command == "get":
        if not args.type:
            print("❌ 请提供 --type")
            return
        
        template = templates.get_template(args.type)
        
        if args.json:
            print(json.dumps(template, ensure_ascii=False, indent=2))
        else:
            print(f"📝 {template['name']}")
            print(f"   描述: {template['description']}")
            print(f"   分类: {template['category']}")
            print(f"   重要性: {template['importance']}")
            print("\n   字段:")
            for field in template.get("fields", []):
                required = " *" if field.get("required") else ""
                print(f"     - {field['label']}{required}")
    
    elif args.command == "create":
        if not args.type or not args.data:
            print("❌ 请提供 --type 和 --data")
            return
        
        try:
            data = json.loads(args.data)
        except:
            print("❌ --data 必须是有效的 JSON")
            return
        
        result = templates.create_memory(args.type, data)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get("success"):
                print(f"✅ 已创建记忆")
                print(f"   ID: {result['memory_id']}")
                print(f"   内容: {result['text']}")
            else:
                print(f"❌ {result.get('error')}")
    
    elif args.command == "prompt":
        if not args.type:
            print("❌ 请提供 --type")
            return
        
        prompt = templates.get_interactive_prompt(args.type)
        print(prompt)
    
    elif args.command == "add-custom":
        if not args.type or not args.data:
            print("❌ 请提供 --type 和 --data")
            return
        
        try:
            template = json.loads(args.data)
        except:
            print("❌ --data 必须是有效的 JSON")
            return
        
        result = templates.add_custom_template(args.type, template)
        
        if result.get("success"):
            print(f"✅ 已添加自定义模板: {args.type}")
        else:
            print(f"❌ {result.get('error')}")


if __name__ == "__main__":
    main()
