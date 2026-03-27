#!/usr/bin/env python3
"""
Memory Graph - 知识图谱可视化 v0.2.0

功能:
- 记忆关系可视化
- 实体提取和链接
- 生成交互式图表

Usage:
    python3 scripts/memory_graph.py build
    python3 scripts/memory_graph.py export --format html
    python3 scripts/memory_graph.py stats
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
GRAPH_FILE = MEMORY_DIR / "graph.json"

# 实体类型
ENTITY_TYPES = {
    "person": ["用户", "刘总", "我", "你", "他", "她"],
    "project": ["项目", "龙宫", "官网", "重构", "开发"],
    "tool": ["飞书", "微信", "QQ", "钉钉", "Slack"],
    "time": ["今天", "明天", "下周", "月", "日"],
    "action": ["喜欢", "使用", "决定", "创建", "完成"]
}


def load_memories() -> List[Dict]:
    """加载记忆"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        memories = []
        count = len(data.get("id", []))
        for i in range(count):
            memories.append({
                "id": data["id"][i] if i < len(data.get("id", [])) else "",
                "text": data["text"][i] if i < len(data.get("text", [])) else "",
                "category": data["category"][i] if i < len(data.get("category", [])) else "",
                "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5
            })
        return memories
    except Exception as e:
        print(f"加载失败: {e}")
        return []


def extract_entities(text: str) -> List[Dict]:
    """提取实体"""
    entities = []
    
    for entity_type, keywords in ENTITY_TYPES.items():
        for keyword in keywords:
            if keyword in text:
                entities.append({
                    "name": keyword,
                    "type": entity_type,
                    "text": text
                })
    
    return entities


def extract_relations(memories: List[Dict]) -> List[Dict]:
    """提取关系"""
    relations = []
    
    for m in memories:
        text = m.get("text", "")
        
        # 简单关系提取
        # "喜欢" 关系
        if "喜欢" in text or "偏好" in text or "爱用" in text:
            entities = extract_entities(text)
            person = next((e for e in entities if e["type"] == "person"), None)
            tool = next((e for e in entities if e["type"] == "tool"), None)
            
            if person and tool:
                relations.append({
                    "source": person["name"],
                    "target": tool["name"],
                    "relation": "喜欢",
                    "memory_id": m["id"]
                })
        
        # "使用" 关系
        if "使用" in text or "用" in text:
            entities = extract_entities(text)
            person = next((e for e in entities if e["type"] == "person"), None)
            tool = next((e for e in entities if e["type"] == "tool"), None)
            project = next((e for e in entities if e["type"] == "project"), None)
            
            if person:
                target = tool or project
                if target:
                    relations.append({
                        "source": person["name"],
                        "target": target["name"],
                        "relation": "使用",
                        "memory_id": m["id"]
                    })
        
        # "决定" 关系
        if "决定" in text or "确定" in text or "选择" in text:
            entities = extract_entities(text)
            person = next((e for e in entities if e["type"] == "person"), None)
            project = next((e for e in entities if e["type"] == "project"), None)
            tool = next((e for e in entities if e["type"] == "tool"), None)
            
            if person:
                target = project or tool
                if target:
                    relations.append({
                        "source": person["name"],
                        "target": target["name"],
                        "relation": "决定",
                        "memory_id": m["id"]
                    })
    
    return relations


def search_context(query: str, limit: int = 5) -> Dict:
    """搜索与查询相关的实体和关系（用于会话上下文增强）"""
    memories = load_memories()
    query_lower = query.lower()
    
    # 找出相关记忆
    relevant_memories = []
    for m in memories:
        text_lower = m.get("text", "").lower()
        if any(kw in text_lower for kw in query_lower.split()):
            relevant_memories.append(m)
    
    # 提取相关实体
    all_entities = []
    for m in relevant_memories[:limit]:
        entities = extract_entities(m["text"])
        for e in entities:
            e["memory_id"] = m["id"]
            e["memory_text"] = m["text"][:100]
        all_entities.extend(entities)
    
    # 去重
    seen = set()
    unique_entities = []
    for e in all_entities:
        key = e.get("name", "")
        if key and key not in seen:
            seen.add(key)
            unique_entities.append(e)
    
    # 提取相关关系
    relations = extract_relations(relevant_memories)
    
    return {
        "query": query,
        "memories_count": len(relevant_memories),
        "entities": unique_entities[:limit * 2],
        "relations": relations[:limit]
    }


def build_graph() -> Dict:
    """构建知识图谱"""
    memories = load_memories()
    
    # 提取所有实体
    all_entities = []
    for m in memories:
        entities = extract_entities(m["text"])
        for e in entities:
            e["memory_id"] = m["id"]
        all_entities.extend(entities)
    
    # 提取关系
    relations = extract_relations(memories)
    
    # 统计
    entity_types = {}
    for e in all_entities:
        t = e.get("type", "unknown")
        entity_types[t] = entity_types.get(t, 0) + 1
    
    return {
        "memories_count": len(memories),
        "entities": all_entities,
        "entities_count": len(all_entities),
        "entity_types": entity_types,
        "relations": relations,
        "relations_count": len(relations),
        "built_at": datetime.now().isoformat()
    }


def export_html(graph: Dict) -> str:
    """导出为 HTML 可视化"""
    # 简化版节点和边
    nodes = {}
    for e in graph.get("entities", []):
        name = e.get("name")
        if name and name not in nodes:
            nodes[name] = {
                "id": name,
                "label": name,
                "type": e.get("type", "unknown"),
                "color": {
                    "person": "#667eea",
                    "project": "#10b981",
                    "tool": "#f59e0b",
                    "time": "#ef4444",
                    "action": "#8b5cf6"
                }.get(e.get("type", ""), "#94a3b8")
            }
    
    edges = []
    for r in graph.get("relations", []):
        edges.append({
            "from": r.get("source"),
            "to": r.get("target"),
            "label": r.get("relation")
        })
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Memory Graph - 知识图谱</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ margin: 0; font-family: sans-serif; background: #1e1e1e; }}
        #mynetwork {{ width: 100%; height: 100vh; }}
        .header {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 100;
        }}
        .header h1 {{ margin: 0; font-size: 18px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; color: #aaa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Memory Graph</h1>
        <p>实体: {len(nodes)} | 关系: {len(edges)} | 记忆: {graph.get("memories_count", 0)}</p>
    </div>
    <div id="mynetwork"></div>
    <script>
        const nodes = new vis.DataSet({json.dumps(list(nodes.values()), ensure_ascii=False)});
        const edges = new vis.DataSet({json.dumps(edges, ensure_ascii=False)});
        
        const container = document.getElementById('mynetwork');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            nodes: {{
                shape: 'dot',
                size: 20,
                font: {{ size: 14, color: '#fff' }},
                borderWidth: 2
            }},
            edges: {{
                width: 2,
                color: {{ color: '#848484' }},
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                font: {{ size: 12, color: '#ccc', align: 'middle' }}
            }},
            physics: {{
                forceAtlas2Based: {{
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08
                }},
                maxVelocity: 50,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {{ iterations: 150 }}
            }}
        }};
        
        new vis.Network(container, data, options);
    </script>
</body>
</html>'''
    
    return html


def export_json(graph: Dict) -> str:
    """导出为 JSON"""
    return json.dumps(graph, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Memory Graph 0.2.0")
    parser.add_argument("command", choices=["build", "export", "stats"])
    parser.add_argument("--format", "-f", choices=["html", "json"], default="html")
    parser.add_argument("--output", "-o", help="输出文件")
    
    args = parser.parse_args()
    
    if args.command == "build":
        print("🔨 构建知识图谱...")
        graph = build_graph()
        
        # 保存
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(GRAPH_FILE, 'w') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 图谱已构建:")
        print(f"   记忆: {graph['memories_count']}")
        print(f"   实体: {graph['entities_count']}")
        print(f"   关系: {graph['relations_count']}")
        
        for t, count in graph['entity_types'].items():
            print(f"   - {t}: {count}")
    
    elif args.command == "export":
        # 加载或构建
        if GRAPH_FILE.exists():
            with open(GRAPH_FILE) as f:
                graph = json.load(f)
        else:
            graph = build_graph()
        
        if args.format == "html":
            output = export_html(graph)
            output_file = args.output or "memory_graph.html"
        else:
            output = export_json(graph)
            output_file = args.output or "memory_graph.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"✅ 已导出: {output_file}")
    
    elif args.command == "stats":
        if GRAPH_FILE.exists():
            with open(GRAPH_FILE) as f:
                graph = json.load(f)
            
            print("📊 知识图谱统计:")
            print(f"   记忆: {graph['memories_count']}")
            print(f"   实体: {graph['entities_count']}")
            print(f"   关系: {graph['relations_count']}")
            print(f"   构建时间: {graph['built_at'][:10]}")
        else:
            print("图谱未构建，请先运行 build")


if __name__ == "__main__":
    main()
