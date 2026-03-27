#!/usr/bin/env python3
"""
知识图谱可视化 - Knowledge Graph Visualization

生成可视化 HTML 页面
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VISUAL_DIR = MEMORY_DIR / "visual"


class KnowledgeGraphVisualizer:
    """
    知识图谱可视化
    
    输出：交互式 HTML 页面
    """
    
    def __init__(self):
        VISUAL_DIR.mkdir(parents=True, exist_ok=True)
        self.graph_file = VISUAL_DIR / "knowledge_graph.html"
    
    def build_graph(self, memories: List[Dict]) -> Dict:
        """
        从记忆构建图数据
        
        Returns:
            nodes: [{id, label, type, size}]
            edges: [{from, to, type}]
        """
        nodes = []
        edges = []
        node_ids = set()
        
        for mem in memories:
            mem_id = mem.get("id", f"mem_{len(nodes)}")
            
            if mem_id in node_ids:
                continue
            node_ids.add(mem_id)
            
            # 节点
            category = mem.get("category", "unknown")
            
            node = {
                "id": mem_id,
                "label": mem.get("text", "")[:50],
                "type": category,
                "size": mem.get("importance", 0.5) * 20 + 10,
                "confidence": mem.get("confidence", 0.8)
            }
            nodes.append(node)
            
            # 实体关系（简化版）
            text = mem.get("text", "")
            
            # 提取关系
            relations = self._extract_relations(text)
            for rel in relations:
                target_id = f"entity_{rel['target']}"
                
                if target_id not in node_ids:
                    node_ids.add(target_id)
                    nodes.append({
                        "id": target_id,
                        "label": rel["target"],
                        "type": rel["type"],
                        "size": 8,
                        "confidence": 0.5
                    })
                
                edges.append({
                    "from": mem_id,
                    "to": target_id,
                    "type": rel["relation"],
                    "label": rel["relation"]
                })
        
        return {"nodes": nodes, "edges": edges}
    
    def _extract_relations(self, text: str) -> List[Dict]:
        """提取关系"""
        relations = []
        
        import re
        
        # 关系模式
        patterns = [
            (r'使用(.+?)技术', 'uses', 'technology'),
            (r'采用(.+?)架构', 'adopts', 'architecture'),
            (r'(.+?)决定(.+?)。', 'decides', 'decision'),
            (r'(.+?)喜欢(.+?)。', 'likes', 'preference'),
        ]
        
        for pattern, rel, target_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    target = match[0] if match else ""
                else:
                    target = match
                
                relations.append({
                    "relation": rel,
                    "target": target,
                    "type": target_type
                })
        
        return relations
    
    def generate_html(self, graph_data: Dict, output_path: str = None) -> str:
        """生成交互式 HTML"""
        
        nodes_json = json.dumps(graph_data.get("nodes", []), ensure_ascii=False)
        edges_json = json.dumps(graph_data.get("edges", []), ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>知识图谱 - Knowledge Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        h1 {{
            color: #4fc3f7;
            text-align: center;
        }}
        #network {{
            width: 100%;
            height: 600px;
            border: 1px solid #333;
            border-radius: 8px;
            background: #16213e;
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        .controls button {{
            padding: 10px 20px;
            margin: 0 5px;
            background: #4fc3f7;
            border: none;
            border-radius: 4px;
            color: #1a1a2e;
            cursor: pointer;
        }}
        .controls button:hover {{
            background: #29b6f6;
        }}
        .stats {{
            text-align: center;
            color: #888;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <h1>🧠 知识图谱</h1>
    
    <div class="controls">
        <button onclick="focusNodes('preference')">偏好</button>
        <button onclick="focusNodes('decision')">决策</button>
        <button onclick="focusNodes('task')">任务</button>
        <button onclick="focusNodes('fact')">事实</button>
        <button onclick="resetView()">重置</button>
    </div>
    
    <div id="network"></div>
    
    <div class="stats">
        <span id="nodeCount">0</span> 节点 | 
        <span id="edgeCount">0</span> 边
    </div>
    
    <script>
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        
        var options = {{
            nodes: {{
                shape: 'dot',
                font: {{ color: '#eee', size: 14 }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 1,
                color: {{ color: '#4fc3f7', opacity: 0.6 }},
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                smooth: {{ type: 'continuous' }}
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
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200
            }}
        }};
        
        var network = new vis.Network(container, data, options);
        
        // 节点颜色映射
        var colors = {{
            'preference': '#e91e63',
            'decision': '#ff9800',
            'task': '#4caf50',
            'fact': '#2196f3',
            'unknown': '#9e9e9e',
            'technology': '#9c27b0',
            'architecture': '#3f51b5'
        }};
        
        nodes.forEach(function(node) {{
            node.color = {{
                background: colors[node.type] || colors['unknown'],
                border: colors[node.type] || colors['unknown']
            }};
            if (node.confidence) {{
                node.title = `置信度: ${{(node.confidence * 100).toFixed(0)}}%`;
            }}
            nodes.update(node);
        }});
        
        document.getElementById('nodeCount').textContent = nodes.length;
        document.getElementById('edgeCount').textContent = edges.length;
        
        function focusNodes(type) {{
            var selected = nodes.get({{
                filter: function(node) {{
                    return node.type === type;
                }}
            }});
            
            if (selected.length > 0) {{
                var ids = selected.map(function(n) {{ return n.id; }});
                network.selectNodes(ids);
                network.focus(ids[0], {{ scale: 1.5, animation: true }});
            }}
        }}
        
        function resetView() {{
            network.fit({{ animation: true }});
        }}
    </script>
</body>
</html>"""
        
        output_path = output_path or str(self.graph_file)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return output_path
    
    def generate_from_memories(self, memories: List[Dict], output_path: str = None) -> str:
        """从记忆生成图谱"""
        graph_data = self.build_graph(memories)
        return self.generate_html(graph_data, output_path)


# 全局实例
_visualizer = None

def get_graph_visualizer() -> KnowledgeGraphVisualizer:
    global _visualizer
    if _visualizer is None:
        _visualizer = KnowledgeGraphVisualizer()
    return _visualizer


if __name__ == "__main__":
    print("=" * 50)
    print("知识图谱可视化测试")
    print("=" * 50)
    
    visualizer = KnowledgeGraphVisualizer()
    
    # 测试数据
    memories = [
        {"id": "mem_1", "text": "用户喜欢简洁界面", "category": "preference", "importance": 0.9},
        {"id": "mem_2", "text": "采用微服务架构", "category": "decision", "importance": 0.8},
        {"id": "mem_3", "text": "使用 Python 开发", "category": "fact", "importance": 0.7},
        {"id": "mem_4", "text": "需要完成首页设计", "category": "task", "importance": 0.6},
    ]
    
    # 构建图
    graph = visualizer.build_graph(memories)
    print(f"\n📊 图统计:")
    print(f"  节点: {len(graph['nodes'])}")
    print(f"  边: {len(graph['edges'])}")
    
    # 生成 HTML
    output = visualizer.generate_from_memories(memories)
    print(f"\n🌐 HTML 已生成: {output}")
    
    print("\n✅ 知识图谱可视化测试完成")
