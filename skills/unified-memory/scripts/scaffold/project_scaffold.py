#!/usr/bin/env python3
"""
Project Scaffold - 项目脚手架生成器

支持生成:
- FastAPI 项目
- Flask 项目
- Django 项目
- React 项目
- Vue 项目
- Next.js 项目
- CLI 工具
- Python 库
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class ProjectScaffold:
    """项目脚手架生成器"""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
    
    def create_fastapi(self, name: str, description: str = "") -> bool:
        """创建 FastAPI 项目"""
        project_dir = self.output_dir / name
        
        try:
            # 创建目录结构
            (project_dir / "app" / "api" / "v1").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "core").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "models").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "schemas").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "services").mkdir(parents=True, exist_ok=True)
            (project_dir / "tests").mkdir(parents=True, exist_ok=True)
            
            # main.py
            (project_dir / "main.py").write_text(f'''#!/usr/bin/env python3
"""
{name} - {description}
FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{name}",
    description="{description}",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {{"message": "Hello {name}"}}


@app.get("/health")
async def health():
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')
            
            # app/__init__.py
            (project_dir / "app" / "__init__.py").write_text("")
            
            # app/main.py
            (project_dir / "app" / "main.py").write_text(f'''from fastapi import FastAPI, APIRouter
from app.api.v1 import api_router

app = FastAPI(title="{name}")

app.include_router(api_router, prefix="/api/v1")
''')
            
            # app/api/v1/__init__.py
            (project_dir / "app" / "api" / "__init__.py").write_text("")
            (project_dir / "app" / "api" / "v1" / "__init__.py").write_text('''from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
async def health():
    return {"status": "ok"}
''')
            
            # app/core/config.py
            (project_dir / "app" / "core" / "__init__.py").write_text("")
            (project_dir / "app" / "core" / "config.py").write_text('''from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "{name}"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
''')
            
            # requirements.txt
            (project_dir / "requirements.txt").write_text('''fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
''')
            
            # pytest.ini
            (project_dir / "pytest.ini").write_text('''[pytest]
testpaths = tests
python_files = test_*.py
''')
            
            # tests/__init__.py
            (project_dir / "tests" / "__init__.py").write_text("")
            
            # tests/test_main.py
            (project_dir / "tests" / "test_main.py").write_text('''from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
''')
            
            # .gitignore
            (project_dir / ".gitignore").write_text('''__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env
*.egg-info/
dist/
build/
.pytest_cache/
''')
            
            # README.md
            (project_dir / "README.md").write_text(f'''# {name}

{description}

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 或
uvicorn main:app --reload
```

## API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

```bash
pytest
```
''')
            
            print(f"✅ 创建 FastAPI 项目: {name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
    
    def create_flask(self, name: str, description: str = "") -> bool:
        """创建 Flask 项目"""
        project_dir = self.output_dir / name
        
        try:
            # 创建目录结构
            (project_dir / "app" / "routes").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "templates").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "static" / "css").mkdir(parents=True, exist_ok=True)
            (project_dir / "app" / "static" / "js").mkdir(parents=True, exist_ok=True)
            (project_dir / "tests").mkdir(parents=True, exist_ok=True)
            
            # app.py
            (project_dir / "app.py").write_text(f'''#!/usr/bin/env python3
"""
{name} - {description}
Flask Application
"""

from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({{"status": "healthy"}})


if __name__ == "__main__":
    app.run(debug=True)
''')
            
            # app/__init__.py
            (project_dir / "app" / "__init__.py").write_text("")
            
            # templates/index.html
            (project_dir / "app" / "templates" / "index.html").write_text(f'''<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
</head>
<body>
    <h1>Welcome to {name}</h1>
    <p>{description}</p>
</body>
</html>
''')
            
            # requirements.txt
            (project_dir / "requirements.txt").write_text('''flask>=2.3.0
python-dotenv>=1.0.0
''')
            
            # README.md
            (project_dir / "README.md").write_text(f'''# {name}

{description}

## 快速开始

```bash
pip install -r requirements.txt
python app.py
```
''')
            
            print(f"✅ 创建 Flask 项目: {name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
    
    def create_react(self, name: str, description: str = "") -> bool:
        """创建 React 项目（简化版）"""
        project_dir = self.output_dir / name
        
        try:
            # 创建目录结构
            (project_dir / "src" / "components").mkdir(parents=True, exist_ok=True)
            (project_dir / "src" / "pages").mkdir(parents=True, exist_ok=True)
            (project_dir / "public").mkdir(parents=True, exist_ok=True)
            
            # package.json
            (project_dir / "package.json").write_text(f'''{{
  "name": "{name.lower().replace(' ', '-')}",
  "version": "0.1.0",
  "description": "{description}",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }}
}}
''')
            
            # vite.config.ts
            (project_dir / "vite.config.ts").write_text('''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''')
            
            # index.html
            (project_dir / "index.html").write_text(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{name}</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
</body>
</html>
''')
            
            # src/main.tsx
            (project_dir / "src" / "main.tsx").write_text('''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''')
            
            # src/App.tsx
            (project_dir / "src" / "App.tsx").write_text(f'''import React from 'react'

function App() {{
  return (
    <div className="App">
      <h1>{name}</h1>
      <p>{description}</p>
    </div>
  )
}}

export default App
''')
            
            # tsconfig.json
            (project_dir / "tsconfig.json").write_text('''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
''')
            
            print(f"✅ 创建 React 项目: {name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
    
    def create_cli(self, name: str, description: str = "") -> bool:
        """创建 CLI 工具项目"""
        project_dir = self.output_dir / name
        
        try:
            # 创建目录结构
            (project_dir / "src" / name.lower().replace("-", "_")).mkdir(parents=True, exist_ok=True)
            (project_dir / "tests").mkdir(parents=True, exist_ok=True)
            
            # pyproject.toml
            (project_dir / "pyproject.toml").write_text(f'''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name.lower().replace(' ', '-')}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.8"
dependencies = [
    "click>=8.0.0",
]

[project.scripts]
{name.lower().replace(' ', '-')} = "{name.lower().replace('-', '_')}.cli:main"
''')
            
            # src/__init__.py
            init_file = project_dir / "src" / name.lower().replace("-", "_") / "__init__.py"
            init_file.write_text(f'"""{name} - {description}"""')
            
            # cli.py
            cli_file = project_dir / "src" / name.lower().replace("-", "_") / "cli.py"
            cli_file.write_text(f'''#!/usr/bin/env python3
"""
{name} CLI
"""

import click

@click.group()
def main():
    """{description}"""
    pass


@main.command()
def hello():
    """Say hello"""
    click.echo("Hello from {name}!")


if __name__ == "__main__":
    main()
''')
            
            # README.md
            (project_dir / "README.md").write_text(f'''# {name}

{description}

## 安装

```bash
pip install -e .
```

## 使用

```bash
{name.lower().replace(' ', '-')} hello
```
''')
            
            print(f"✅ 创建 CLI 项目: {name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="项目脚手架生成器")
    parser.add_argument("type", choices=["fastapi", "flask", "react", "cli"], help="项目类型")
    parser.add_argument("name", help="项目名称")
    parser.add_argument("--desc", "-d", default="", help="项目描述")
    parser.add_argument("--output", "-o", default=".", help="输出目录")
    
    args = parser.parse_args()
    
    scaffold = ProjectScaffold(args.output)
    
    if args.type == "fastapi":
        scaffold.create_fastapi(args.name, args.desc)
    elif args.type == "flask":
        scaffold.create_flask(args.name, args.desc)
    elif args.type == "react":
        scaffold.create_react(args.name, args.desc)
    elif args.type == "cli":
        scaffold.create_cli(args.name, args.desc)


if __name__ == "__main__":
    main()
