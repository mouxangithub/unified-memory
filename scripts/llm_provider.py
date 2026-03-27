#!/usr/bin/env python3
"""
LLM Provider - 统一 LLM 调用接口

支持:
- OpenAI (GPT-4, GPT-3.5)
- Claude (Claude-3 Opus, Sonnet, Haiku)
- 智谱 AI (GLM-4)
- 百度千帆 (ERNIE)
- 阿里通义 (Qwen)

使用:
    from llm_provider import LLMProviderFactory
    
    # 创建提供商
    llm = LLMProviderFactory.create("openai", model="gpt-4")
    
    # 生成响应
    response = llm.generate("写一个贪吃蛇游戏")
    print(response.content)
    
    # 流式生成
    for chunk in llm.stream("写一首诗"):
        print(chunk, end="", flush=True)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Generator, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"
    latency: float = 0.0
    provider: str = "unknown"
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
            "latency": self.latency,
            "provider": self.provider
        }


@dataclass
class Message:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str
    
    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""
    
    name: str = "base"
    
    def __init__(self, 
                 api_key: str = None,
                 model: str = None,
                 base_url: str = None,
                 **kwargs):
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_default_model()
        self.base_url = base_url
        self.config = kwargs
    
    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取 API Key"""
        env_var = f"{self.name.upper()}_API_KEY"
        return os.environ.get(env_var)
    
    @abstractmethod
    def _get_default_model(self) -> str:
        """获取默认模型"""
        pass
    
    @abstractmethod
    def generate(self, 
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        """生成响应"""
        pass
    
    @abstractmethod
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        """流式生成"""
        pass
    
    def _build_messages(self, 
                        prompt: str,
                        system: str = None,
                        messages: List[Message] = None) -> List[dict]:
        """构建消息列表"""
        result = []
        
        if system:
            result.append({"role": "system", "content": system})
        
        if messages:
            result.extend([m.to_dict() for m in messages])
        
        if prompt:
            result.append({"role": "user", "content": prompt})
        
        return result


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商"""
    
    name = "openai"
    
    def _get_default_model(self) -> str:
        return "gpt-4"
    
    def generate(self, 
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        start = time.time()
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            msg_list = self._build_messages(prompt, system, messages)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=msg_list,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason,
                latency=time.time() - start,
                provider=self.name
            )
        
        except ImportError:
            return self._mock_response(prompt, time.time() - start)
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            msg_list = self._build_messages(prompt, system, messages)
            
            stream = client.chat.completions.create(
                model=self.model,
                messages=msg_list,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except ImportError:
            yield self._mock_response(prompt, 0).content
        except Exception as e:
            yield f"[错误] {str(e)}"
    
    def _mock_response(self, prompt: str, latency: float) -> LLMResponse:
        """模拟响应（无依赖时）"""
        return LLMResponse(
            content=f"[模拟响应] 基于提示生成内容...\n\n提示: {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
            model=self.model,
            tokens_used=len(prompt) // 4,
            latency=latency,
            provider=f"{self.name}_mock"
        )


class ClaudeProvider(BaseLLMProvider):
    """Claude 提供商"""
    
    name = "claude"
    
    def _get_default_model(self) -> str:
        return "claude-3-opus-20240229"
    
    def generate(self,
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        start = time.time()
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            msg_list = self._build_messages(prompt, None, messages)
            
            params = {
                "model": self.model,
                "messages": msg_list,
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
            
            if system:
                params["system"] = system
            
            response = client.messages.create(**params)
            
            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                latency=time.time() - start,
                provider=self.name
            )
        
        except ImportError:
            return self._mock_response(prompt, time.time() - start)
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            msg_list = self._build_messages(prompt, None, messages)
            
            params = {
                "model": self.model,
                "messages": msg_list,
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
            
            if system:
                params["system"] = system
            
            with client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        
        except ImportError:
            yield self._mock_response(prompt, 0).content
        except Exception as e:
            yield f"[错误] {str(e)}"
    
    def _mock_response(self, prompt: str, latency: float) -> LLMResponse:
        return LLMResponse(
            content=f"[Claude 模拟] 基于提示生成...\n\n{prompt[:200]}",
            model=self.model,
            tokens_used=len(prompt) // 4,
            latency=latency,
            provider=f"{self.name}_mock"
        )


class ZhipuProvider(BaseLLMProvider):
    """智谱 AI 提供商"""
    
    name = "zhipu"
    
    def _get_default_model(self) -> str:
        return "glm-4"
    
    def generate(self,
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        start = time.time()
        
        try:
            from zhipuai import ZhipuAI
            
            client = ZhipuAI(api_key=self.api_key)
            
            msg_list = self._build_messages(prompt, system, messages)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=msg_list,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason,
                latency=time.time() - start,
                provider=self.name
            )
        
        except ImportError:
            return self._mock_response(prompt, time.time() - start)
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        
        try:
            from zhipuai import ZhipuAI
            
            client = ZhipuAI(api_key=self.api_key)
            
            msg_list = self._build_messages(prompt, system, messages)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=msg_list,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except ImportError:
            yield self._mock_response(prompt, 0).content
        except Exception as e:
            yield f"[错误] {str(e)}"
    
    def _mock_response(self, prompt: str, latency: float) -> LLMResponse:
        return LLMResponse(
            content=f"[智谱模拟] 基于提示生成...\n\n{prompt[:200]}",
            model=self.model,
            tokens_used=len(prompt) // 4,
            latency=latency,
            provider=f"{self.name}_mock"
        )


class QianfanProvider(BaseLLMProvider):
    """百度千帆提供商"""
    
    name = "qianfan"
    
    def _get_default_model(self) -> str:
        return "ERNIE-4.0"
    
    def generate(self,
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        start = time.time()
        
        try:
            import qianfan
            
            client = qianfan.ChatCompletion(api_key=self.api_key)
            
            msg_list = self._build_messages(prompt, system, messages)
            
            response = client.do(
                model=self.model,
                messages=msg_list
            )
            
            return LLMResponse(
                content=response.body.get("result", ""),
                model=self.model,
                tokens_used=response.body.get("usage", {}).get("total_tokens", 0),
                latency=time.time() - start,
                provider=self.name
            )
        
        except ImportError:
            return self._mock_response(prompt, time.time() - start)
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        yield self.generate(prompt, system, messages, **kwargs).content
    
    def _mock_response(self, prompt: str, latency: float) -> LLMResponse:
        return LLMResponse(
            content=f"[千帆模拟] {prompt[:200]}",
            model=self.model,
            tokens_used=len(prompt) // 4,
            latency=latency,
            provider=f"{self.name}_mock"
        )


class DashScopeProvider(BaseLLMProvider):
    """阿里通义提供商"""
    
    name = "dashscope"
    
    def _get_default_model(self) -> str:
        return "qwen-max"
    
    def generate(self,
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        start = time.time()
        
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            msg_list = self._build_messages(prompt, system, messages)
            
            response = Generation.call(
                model=self.model,
                messages=msg_list
            )
            
            return LLMResponse(
                content=response.output.text,
                model=self.model,
                tokens_used=response.usage.total_tokens,
                latency=time.time() - start,
                provider=self.name
            )
        
        except ImportError:
            return self._mock_response(prompt, time.time() - start)
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        yield self.generate(prompt, system, messages, **kwargs).content
    
    def _mock_response(self, prompt: str, latency: float) -> LLMResponse:
        return LLMResponse(
            content=f"[通义模拟] {prompt[:200]}",
            model=self.model,
            tokens_used=len(prompt) // 4,
            latency=latency,
            provider=f"{self.name}_mock"
        )


class OllamaProvider(BaseLLMProvider):
    """Ollama 本地提供商"""
    
    name = "ollama"
    
    def __init__(self, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(base_url=base_url, **kwargs)
    
    def _get_default_model(self) -> str:
        return "llama3"
    
    def generate(self,
                 prompt: str,
                 system: str = None,
                 messages: List[Message] = None,
                 **kwargs) -> LLMResponse:
        
        import time
        import requests
        start = time.time()
        
        try:
            msg_list = self._build_messages(prompt, system, messages)
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": msg_list,
                    "stream": False
                }
            )
            
            data = response.json()
            
            return LLMResponse(
                content=data["message"]["content"],
                model=self.model,
                latency=time.time() - start,
                provider=self.name
            )
        
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {str(e)}",
                model=self.model,
                provider=self.name,
                finish_reason="error"
            )
    
    def stream(self,
               prompt: str,
               system: str = None,
               messages: List[Message] = None,
               **kwargs) -> Generator[str, None, None]:
        
        import requests
        
        try:
            msg_list = self._build_messages(prompt, system, messages)
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": msg_list,
                    "stream": True
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
        
        except Exception as e:
            yield f"[错误] {str(e)}"


class LLMProviderFactory:
    """LLM 提供商工厂"""
    
    _providers = {
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,
        "zhipu": ZhipuProvider,
        "glm": ZhipuProvider,
        "qianfan": QianfanProvider,
        "ernie": QianfanProvider,
        "dashscope": DashScopeProvider,
        "qwen": DashScopeProvider,
        "tongyi": DashScopeProvider,
        "ollama": OllamaProvider,
        "local": OllamaProvider
    }
    
    _model_aliases = {
        "gpt-4": "openai",
        "gpt-3.5": "openai",
        "gpt-4o": "openai",
        "claude-3": "claude",
        "claude-3-opus": "claude",
        "claude-3-sonnet": "claude",
        "glm-4": "zhipu",
        "glm-3": "zhipu",
        "ernie": "qianfan",
        "qwen": "dashscope"
    }
    
    @classmethod
    def create(cls,
               provider: str,
               api_key: str = None,
               model: str = None,
               **kwargs) -> BaseLLMProvider:
        """创建 LLM 提供商"""
        
        # 从模型名推断提供商
        if provider in cls._model_aliases:
            provider = cls._model_aliases[provider]
        
        if provider not in cls._providers:
            raise ValueError(f"不支持的提供商: {provider}。支持: {list(cls._providers.keys())}")
        
        provider_class = cls._providers[provider]
        return provider_class(api_key=api_key, model=model, **kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有支持的提供商"""
        return list(cls._providers.keys())
    
    @classmethod
    def list_models(cls, provider: str = None) -> List[str]:
        """列出支持的模型"""
        models = {
            "openai": ["gpt-4", "gpt-4o", "gpt-3.5-turbo"],
            "claude": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "zhipu": ["glm-4", "glm-3-turbo"],
            "qianfan": ["ERNIE-4.0", "ERNIE-3.5"],
            "dashscope": ["qwen-max", "qwen-plus", "qwen-turbo"],
            "ollama": ["llama3", "llama2", "mistral", "codellama"]
        }
        
        if provider:
            return models.get(provider, [])
        
        return models


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Provider")
    parser.add_argument("command", choices=["list", "demo", "chat"])
    parser.add_argument("--provider", "-p", default="openai", help="提供商")
    parser.add_argument("--model", "-m", help="模型")
    parser.add_argument("--prompt", help="提示词")
    
    args = parser.parse_args()
    
    if args.command == "list":
        print("支持的提供商:")
        for p in LLMProviderFactory.list_providers():
            models = LLMProviderFactory.list_models(p)
            print(f"  - {p}: {', '.join(models)}")
    
    elif args.command == "demo":
        llm = LLMProviderFactory.create(args.provider, model=args.model)
        
        prompt = args.prompt or "用一句话介绍 Python"
        print(f"提示: {prompt}")
        print(f"提供商: {llm.name}")
        print(f"模型: {llm.model}")
        print("-" * 40)
        
        response = llm.generate(prompt)
        print(f"响应: {response.content}")
        print(f"Token: {response.tokens_used}")
        print(f"延迟: {response.latency:.2f}s")
    
    elif args.command == "chat":
        llm = LLMProviderFactory.create(args.provider, model=args.model)
        
        print("聊天模式 (输入 'quit' 退出)")
        print("-" * 40)
        
        while True:
            try:
                prompt = input("你: ")
                if prompt.lower() in ["quit", "exit", "q"]:
                    break
                
                print("AI: ", end="")
                for chunk in llm.stream(prompt):
                    print(chunk, end="", flush=True)
                print("\n")
            
            except KeyboardInterrupt:
                break
        
        print("再见!")
