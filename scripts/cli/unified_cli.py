#!/usr/bin/env python3
"""
Unified CLI v1.2 - 统一命令行入口

整合所有模块:
- 记忆管理
- 多模态 (OCR/STT)
- 智能分类
- Agent 调度
- 质量评估
- Web UI
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_ocr(args):
    """OCR 文字识别"""
    print(f"🔍 OCR 识别: {args.image}")
    
    try:
        from multimodal.ocr_engine import OCREngine
        
        ocr = OCREngine(args.engine)
        result = ocr.extract_text(args.image)
        
        print(f"\n来源: {result.source}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"\n文本:\n{result.text}")
    except ImportError:
        print("❌ OCR 模块未安装")
        print("请安装: pip install paddleocr 或 tesseract")


def cmd_stt(args):
    """语音转文字"""
    print(f"🎤 语音转录: {args.audio}")
    
    try:
        from multimodal.stt_engine import STTEngine
        
        stt = STTEngine(args.engine)
        result = stt.transcribe(args.audio, args.language)
        
        print(f"\n来源: {result.source}")
        print(f"语言: {result.language}")
        print(f"\n文本:\n{result.text}")
    except ImportError:
        print("❌ STT 模块未安装")
        print("请安装: pip install openai-whisper")


def cmd_classify(args):
    """智能分类"""
    print(f"🧠 智能分类: {args.text[:50]}...")
    
    try:
        from intelligence.smart_classifier import IntelligenceEngine
        
        engine = IntelligenceEngine()
        result = engine.classify(args.text)
        
        print(f"\n分类: {result.category} ({result.confidence:.0%})")
        print(f"标签: {', '.join(result.tags)}")
        print(f"相关记忆: {len(result.related_ids)} 条")
    except Exception as e:
        print(f"❌ 分类失败: {e}")


def cmd_schedule(args):
    """Agent 调度演示"""
    print("🤖 Agent 调度演示\n")
    
    try:
        from scheduler.agent_scheduler import AgentScheduler, Agent, Task, TaskType, TaskPriority
        
        scheduler = AgentScheduler()
        
        # 注册 Agent
        scheduler.register_agent(Agent(
            id="pm", name="产品经理", role="pm",
            capabilities=["communication", "documentation", "research"]
        ))
        scheduler.register_agent(Agent(
            id="architect", name="架构师", role="architect",
            capabilities=["architecture", "python", "javascript"]
        ))
        scheduler.register_agent(Agent(
            id="engineer", name="工程师", role="engineer",
            capabilities=["python", "javascript", "testing"]
        ))
        scheduler.register_agent(Agent(
            id="qa", name="测试工程师", role="qa",
            capabilities=["testing", "review"]
        ))
        
        # 提交任务
        scheduler.submit_task(Task(
            id="t1", type=TaskType.CODE, priority=TaskPriority.HIGH,
            required_capabilities=["python"], estimated_time=60,
            description="开发用户登录功能"
        ))
        scheduler.submit_task(Task(
            id="t2", type=TaskType.TEST, priority=TaskPriority.MEDIUM,
            required_capabilities=["testing"], estimated_time=30,
            description="编写登录功能测试用例"
        ))
        scheduler.submit_task(Task(
            id="t3", type=TaskType.DOCUMENT, priority=TaskPriority.LOW,
            required_capabilities=["documentation"], estimated_time=20,
            description="编写 API 文档"
        ))
        
        # 调度
        print("已注册 Agent:")
        for agent in scheduler.agents.values():
            print(f"  - {agent.name}: {agent.capabilities}")
        
        print("\n调度结果:")
        assignments = scheduler.schedule()
        for task_id, agent_id in assignments.items():
            task = scheduler.tasks[task_id]
            agent = scheduler.agents[agent_id]
            print(f"  ✅ {task.description} → {agent.name}")
        
        print("\n负载情况:")
        for agent_id, info in scheduler.get_agent_workload().items():
            print(f"  {info['name']}: {info['current_load']}/{info['max_load']}")
    
    except Exception as e:
        print(f"❌ 调度失败: {e}")


def cmd_quality(args):
    """代码质量评估"""
    print(f"📊 质量评估: {args.file or '示例代码'}\n")
    
    try:
        from quality.quality_assessor import QualityAssessor
        
        assessor = QualityAssessor()
        
        # 获取代码
        if args.file:
            code = Path(args.file).read_text()
        else:
            code = '''
def hello(name):
    print(f"Hello, {name}!")

password = "123456"  # 硬编码密码

try:
    something()
except:
    pass  # 空异常处理
'''
        
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
    
    except Exception as e:
        print(f"❌ 评估失败: {e}")


def cmd_serve(args):
    """启动 Web 服务"""
    port = args.port
    
    print(f"🌐 启动 Web UI: http://localhost:{port}")
    print(f"📚 API 文档: http://localhost:{port}/docs")
    print("按 Ctrl+C 停止\n")
    
    try:
        import uvicorn
        from web.auth_server import app
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        print("❌ FastAPI 未安装")
        print("请安装: pip install fastapi uvicorn")


def cmd_docs(args):
    """生成 API 文档"""
    print(f"📝 生成 API 文档: {args.output}\n")
    
    try:
        from docs.api_docs_generator import generate_unified_memory_docs
        
        docs = generate_unified_memory_docs()
        
        output_path = Path(args.output)
        output_path.write_text(docs, encoding="utf-8")
        
        print(f"✅ 文档已保存: {output_path}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="统一记忆系统 CLI v1.2",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ocr
    ocr_parser = subparsers.add_parser("ocr", help="OCR 文字识别")
    ocr_parser.add_argument("image", help="图片路径")
    ocr_parser.add_argument("--engine", "-e", default="auto", choices=["auto", "tesseract", "paddle", "qwen"])
    
    # stt
    stt_parser = subparsers.add_parser("stt", help="语音转文字")
    stt_parser.add_argument("audio", help="音频路径")
    stt_parser.add_argument("--engine", "-e", default="auto", choices=["auto", "whisper", "aliyun"])
    stt_parser.add_argument("--language", "-l", default=None)
    
    # classify
    classify_parser = subparsers.add_parser("classify", help="智能分类")
    classify_parser.add_argument("text", help="要分类的文本")
    
    # schedule
    subparsers.add_parser("schedule", help="Agent 调度演示")
    
    # quality
    quality_parser = subparsers.add_parser("quality", help="代码质量评估")
    quality_parser.add_argument("file", nargs="?", help="代码文件")
    quality_parser.add_argument("--language", "-l", default="python")
    
    # serve
    serve_parser = subparsers.add_parser("serve", help="启动 Web 服务")
    serve_parser.add_argument("--port", "-p", type=int, default=38080)
    
    # docs
    docs_parser = subparsers.add_parser("docs", help="生成 API 文档")
    docs_parser.add_argument("--output", "-o", default="API_DOCS.md")
    
    args = parser.parse_args()
    
    # 路由
    if args.command == "ocr":
        cmd_ocr(args)
    elif args.command == "stt":
        cmd_stt(args)
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "quality":
        cmd_quality(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "docs":
        cmd_docs(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
