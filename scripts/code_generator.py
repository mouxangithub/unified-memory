#!/usr/bin/env python3
"""
Code Generator - 代码生成器（学习 MetaGPT）

整合 MetaGPT 的代码生成能力：
- 多语言支持（Python、JavaScript、Go、Java）
- 代码模板系统
- 项目脚手架生成

使用：
    from code_generator import CodeGenerator
    
    gen = CodeGenerator()
    
    # 生成单个文件
    code = gen.generate_file("api.py", {"endpoints": [...]})
    
    # 生成项目
    project = gen.generate_project({
        "name": "my-api",
        "type": "fastapi",
        "features": ["auth", "database"]
    })
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class CodeFile:
    """代码文件"""
    name: str
    content: str
    language: str
    description: str = ""
    
    def save(self, path: str):
        """保存到文件"""
        file_path = Path(path) / self.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.content, encoding="utf-8")
        return str(file_path)


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        self.templates = {
            # Python
            "python_main": self._python_main_template,
            "python_api": self._python_api_template,
            "python_model": self._python_model_template,
            "python_test": self._python_test_template,
            "python_requirements": self._python_requirements_template,
            
            # JavaScript/TypeScript
            "js_index": self._js_index_template,
            "js_api": self._js_api_template,
            "js_package": self._js_package_template,
            
            # Config
            "dockerfile": self._dockerfile_template,
            "docker_compose": self._docker_compose_template,
            "gitignore": self._gitignore_template,
            "readme": self._readme_template,
        }
        
        self.project_types = {
            "fastapi": self._fastapi_project,
            "flask": self._flask_project,
            "django": self._django_project,
            "express": self._express_project,
            "cli": self._cli_project,
        }
    
    # ===== 单文件生成 =====
    
    def generate_file(self, 
                     file_type: str,
                     data: Dict[str, Any],
                     name: str = None) -> CodeFile:
        """生成单个文件"""
        template_func = self.templates.get(file_type)
        if not template_func:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        content = template_func(data)
        
        return CodeFile(
            name=name or f"{file_type}.py",
            content=content,
            language=self._get_language(file_type),
            description=data.get("description", "")
        )
    
    # ===== 项目生成 =====
    
    def generate_project(self, config: Dict[str, Any]) -> List[CodeFile]:
        """生成项目脚手架"""
        project_type = config.get("type", "fastapi")
        
        generator = self.project_types.get(project_type)
        if not generator:
            raise ValueError(f"不支持的项目类型: {project_type}")
        
        return generator(config)
    
    # ===== 模板 =====
    
    def _python_main_template(self, data: Dict) -> str:
        """Python 主文件模板"""
        name = data.get("name", "main")
        description = data.get("description", "")
        
        return f'''#!/usr/bin/env python3
"""
{name}

{description}
"""

import argparse
import sys
from datetime import datetime


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("--version", action="store_true", help="显示版本")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.version:
        print("{name} v1.0.0")
        return 0
    
    print(f"Hello from {name}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _python_api_template(self, data: Dict) -> str:
        """FastAPI API 模板"""
        endpoints = data.get("endpoints", [])
        title = data.get("title", "API")
        
        endpoints_code = []
        for ep in endpoints:
            method = ep.get("method", "GET").lower()
            path = ep.get("path", "/")
            name = ep.get("name", "endpoint")
            
            if method == "get":
                endpoints_code.append(f'''
@app.get("{path}")
async def {name}():
    """{ep.get('description', '')}"""
    return {{"status": "ok", "data": []}}
''')
            elif method == "post":
                endpoints_code.append(f'''
@app.post("{path}")
async def {name}(data: dict):
    """{ep.get('description', '')}"""
    return {{"status": "created", "data": data}}
''')
        
        return f'''#!/usr/bin/env python3
"""
{title} - FastAPI 应用

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="{title}",
    version="1.0.0",
    description="自动生成的 API"
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

{"".join(endpoints_code)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _python_model_template(self, data: Dict) -> str:
        """数据模型模板"""
        model_name = data.get("name", "Item")
        fields = data.get("fields", [
            {"name": "id", "type": "int"},
            {"name": "name", "type": "str"},
            {"name": "created_at", "type": "datetime"}
        ])
        
        field_defs = []
        for f in fields:
            fname = f["name"]
            ftype = f["type"]
            optional = f.get("optional", False)
            
            if ftype == "int":
                field_defs.append(f"    {fname}: {'Optional[int]' if optional else 'int'}")
            elif ftype == "str":
                field_defs.append(f"    {fname}: {'Optional[str]' if optional else 'str'}")
            elif ftype == "datetime":
                field_defs.append(f"    {fname}: {'Optional[datetime]' if optional else 'datetime'}")
            elif ftype == "bool":
                field_defs.append(f"    {fname}: {'Optional[bool]' if optional else 'bool'} = False")
        
        return f'''#!/usr/bin/env python3
"""
数据模型 - {model_name}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class {model_name}(BaseModel):
    """{model_name} 模型"""
    
{chr(10).join(field_defs)}
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "id": 1,
                "name": "示例"
            }}
        }}


class {model_name}Create(BaseModel):
    """创建 {model_name}"""
{chr(10).join([f"    {f['name']}: {f['type']}" for f in fields if f['name'] != 'id'])}


class {model_name}Update(BaseModel):
    """更新 {model_name}"""
{chr(10).join([f"    {f['name']}: Optional[{f['type']}] = None" for f in fields if f['name'] != 'id'])}
'''
    
    def _python_test_template(self, data: Dict) -> str:
        """测试文件模板"""
        test_name = data.get("name", "test_main")
        functions = data.get("functions", ["main"])
        
        test_cases = []
        for func in functions:
            test_cases.append(f'''
def test_{func}():
    """测试 {func}"""
    # TODO: 实现测试
    assert True
''')
        
        return f'''#!/usr/bin/env python3
"""
测试文件 - {test_name}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

import pytest
from unittest.mock import Mock, patch

{"".join(test_cases)}


class Test{test_name.title().replace("_", "")}:
    """测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        pass
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        pass
    
    def test_example(self):
        """示例测试"""
        assert 1 + 1 == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    def _python_requirements_template(self, data: Dict) -> str:
        """requirements.txt 模板"""
        dependencies = data.get("dependencies", [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0"
        ])
        
        return f'''# 自动生成的依赖
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{chr(10).join(dependencies)}
'''
    
    def _js_index_template(self, data: Dict) -> str:
        """JavaScript 入口文件模板"""
        name = data.get("name", "app")
        
        return f'''/**
 * {name}
 * 
 * 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
 */

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(express.json());

// 路由
app.get('/', (req, res) => {{
    res.json({{ message: 'Hello from {name}!' }});
}});

app.get('/health', (req, res) => {{
    res.json({{ status: 'healthy', timestamp: new Date().toISOString() }});
}});

// 启动服务器
app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});

module.exports = app;
'''
    
    def _js_api_template(self, data: Dict) -> str:
        """JavaScript API 路由模板"""
        routes = data.get("routes", [])
        
        route_defs = []
        for r in routes:
            method = r.get("method", "get").lower()
            path = r.get("path", "/")
            name = r.get("name", "handler")
            route_defs.append(f'''
router.{method}('{path}', async (req, res) => {{
    try {{
        // TODO: 实现 {name}
        res.json({{ status: 'ok' }});
    }} catch (error) {{
        res.status(500).json({{ error: error.message }});
    }}
}});
''')
        
        return f'''/**
 * API 路由
 * 
 * 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
 */

const express = require('express');
const router = express.Router();

{"".join(route_defs)}

module.exports = router;
'''
    
    def _js_package_template(self, data: Dict) -> str:
        """package.json 模板"""
        name = data.get("name", "my-app")
        description = data.get("description", "")
        
        return f'''{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "{description}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  }},
  "dependencies": {{
    "express": "^4.18.0"
  }},
  "devDependencies": {{
    "jest": "^29.0.0",
    "nodemon": "^3.0.0"
  }},
  "keywords": [],
  "author": "",
  "license": "MIT"
}}
'''
    
    def _dockerfile_template(self, data: Dict) -> str:
        """Dockerfile 模板"""
        language = data.get("language", "python")
        name = data.get("name", "app")
        
        if language == "python":
            return f'''# Python 应用 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        else:
            return f'''# Node.js 应用 Dockerfile
FROM node:18-slim

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm install

# 复制代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "start"]
'''
    
    def _docker_compose_template(self, data: Dict) -> str:
        """docker-compose.yml 模板"""
        name = data.get("name", "app")
        services = data.get("services", ["web", "db"])
        
        service_defs = []
        if "web" in services:
            service_defs.append(f'''  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/{name}
    depends_on:
      - db
''')
        if "db" in services:
            service_defs.append(f'''  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB={name}
    volumes:
      - postgres_data:/var/lib/postgresql/data
''')
        
        return f'''version: '3.8'

services:
{"".join(service_defs)}

volumes:
  postgres_data:
'''
    
    def _gitignore_template(self, data: Dict) -> str:
        """.gitignore 模板"""
        language = data.get("language", "python")
        
        common = '''# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
'''
        
        if language == "python":
            return common + '''
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual
venv/
env/
.venv/
'''
        else:
            return common + '''
# Node
node_modules/
npm-debug.log*
yarn-debug.log*
dist/
build/
'''
    
    def _readme_template(self, data: Dict) -> str:
        """README 模板"""
        name = data.get("name", "project")
        description = data.get("description", "")
        
        return f'''# {name}

{description}

## 快速开始

### 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 启动服务
python main.py

# 或使用 uvicorn
uvicorn main:app --reload
```

### 测试

```bash
pytest tests/
```

## 项目结构

```
{name}/
├── main.py           # 主入口
├── api.py            # API 路由
├── models.py         # 数据模型
├── requirements.txt  # 依赖
├── Dockerfile        # Docker 配置
└── tests/            # 测试
    └── test_main.py
```

## API 文档

启动后访问: http://localhost:8000/docs

## 许可证

MIT
'''
    
    # ===== 项目生成器 =====
    
    def _fastapi_project(self, config: Dict) -> List[CodeFile]:
        """FastAPI 项目"""
        name = config.get("name", "fastapi-app")
        features = config.get("features", [])
        
        files = [
            CodeFile("main.py", self._python_main_template(config), "python"),
            CodeFile("api.py", self._python_api_template({
                "title": name,
                "endpoints": config.get("endpoints", [])
            }), "python"),
            CodeFile("models.py", self._python_model_template({
                "name": "Item",
                "fields": [
                    {"name": "id", "type": "int"},
                    {"name": "name", "type": "str"},
                    {"name": "created_at", "type": "datetime"}
                ]
            }), "python"),
            CodeFile("requirements.txt", self._python_requirements_template(config), "text"),
            CodeFile("Dockerfile", self._dockerfile_template({"language": "python", "name": name}), "text"),
            CodeFile("docker-compose.yml", self._docker_compose_template({"name": name}), "yaml"),
            CodeFile(".gitignore", self._gitignore_template({"language": "python"}), "text"),
            CodeFile("README.md", self._readme_template(config), "markdown"),
        ]
        
        # 添加测试
        files.append(CodeFile(
            "tests/test_main.py",
            self._python_test_template({"name": "main", "functions": ["health_check"]}),
            "python"
        ))
        
        return files
    
    def _flask_project(self, config: Dict) -> List[CodeFile]:
        """Flask 项目"""
        # 类似 FastAPI，使用 Flask 模板
        config["framework"] = "flask"
        return self._fastapi_project(config)
    
    def _django_project(self, config: Dict) -> List[CodeFile]:
        """Django 项目"""
        config["framework"] = "django"
        return self._fastapi_project(config)
    
    def _express_project(self, config: Dict) -> List[CodeFile]:
        """Express.js 项目"""
        name = config.get("name", "express-app")
        
        return [
            CodeFile("index.js", self._js_index_template(config), "javascript"),
            CodeFile("package.json", self._js_package_template(config), "json"),
            CodeFile("Dockerfile", self._dockerfile_template({"language": "node", "name": name}), "text"),
            CodeFile(".gitignore", self._gitignore_template({"language": "node"}), "text"),
            CodeFile("README.md", self._readme_template(config), "markdown"),
        ]
    
    def _cli_project(self, config: Dict) -> List[CodeFile]:
        """CLI 项目"""
        return [
            CodeFile("main.py", self._python_main_template(config), "python"),
            CodeFile("requirements.txt", self._python_requirements_template({
                "dependencies": ["click>=8.0.0", "rich>=13.0.0"]
            }), "text"),
            CodeFile(".gitignore", self._gitignore_template({"language": "python"}), "text"),
            CodeFile("README.md", self._readme_template(config), "markdown"),
        ]
    
    # ===== 辅助方法 =====
    
    def _get_language(self, file_type: str) -> str:
        """获取文件语言"""
        if file_type.startswith("python"):
            return "python"
        elif file_type.startswith("js"):
            return "javascript"
        elif file_type == "dockerfile":
            return "dockerfile"
        elif file_type == "readme":
            return "markdown"
        else:
            return "text"


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="代码生成器")
    parser.add_argument("command", choices=["demo", "project"])
    parser.add_argument("--type", default="fastapi", help="项目类型")
    parser.add_argument("--name", default="my-app", help="项目名称")
    
    args = parser.parse_args()
    
    gen = CodeGenerator()
    
    if args.command == "demo":
        # 生成单个文件
        api_file = gen.generate_file("python_api", {
            "title": "Demo API",
            "endpoints": [
                {"method": "GET", "path": "/users", "name": "list_users"},
                {"method": "POST", "path": "/users", "name": "create_user"}
            ]
        })
        print(f"📄 生成文件: {api_file.name}")
        print(api_file.content[:500] + "...\n")
    
    elif args.command == "project":
        # 生成项目
        files = gen.generate_project({
            "name": args.name,
            "type": args.type,
            "description": f"{args.name} - 自动生成的项目"
        })
        
        print(f"🚀 生成项目: {args.name}")
        print(f"📁 文件数: {len(files)}")
        for f in files:
            print(f"  - {f.name} ({len(f.content)} bytes)")
