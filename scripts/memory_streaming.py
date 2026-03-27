#!/usr/bin/env python3
"""
流式摄入 - Streaming Ingest

核心：实时处理，无需等待 batch
支持 WebSocket / SSE / Queue
"""

import asyncio
import json
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from collections import deque

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
STREAM_DIR = MEMORY_DIR / "streaming"


class MemoryStream:
    """
    记忆流处理器
    
    支持：
    - 同步队列
    - 异步队列
    - 实时回调
    """
    
    def __init__(self, max_queue_size: int = 1000):
        STREAM_DIR.mkdir(parents=True, exist_ok=True)
        
        # 同步队列
        self.queue = queue.Queue(maxsize=max_queue_size)
        
        # 缓冲区
        self.buffer = deque(maxlen=100)
        
        # 回调函数
        self.callbacks: List[Callable] = []
        
        # 状态
        self.running = False
        self.processed_count = 0
        
        # 后台线程
        self.worker_thread = None
    
    def add_callback(self, callback: Callable[[Dict], None]):
        """添加处理回调"""
        self.callbacks.append(callback)
    
    def ingest(self, memory: Dict):
        """
        同步摄入（立即处理）
        
        立即处理并触发回调
        """
        # 添加元数据
        memory["_ingested_at"] = datetime.now().isoformat()
        memory["_processed"] = False
        
        # 立即触发回调
        for callback in self.callbacks:
            try:
                callback(memory)
            except Exception as e:
                print(f"Callback error: {e}")
        
        memory["_processed"] = True
        self.processed_count += 1
        
        return memory
    
    def put(self, memory: Dict):
        """
        放入队列（异步处理）
        
        非阻塞，放入队列后立即返回
        """
        memory["_queued_at"] = datetime.now().isoformat()
        try:
            self.queue.put_nowait(memory)
        except queue.Full:
            # 队列满，丢弃最旧的
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(memory)
            except:
                pass
    
    def _worker(self):
        """后台工作线程"""
        while self.running:
            try:
                # 等待消息
                memory = self.queue.get(timeout=1)
                
                # 处理
                memory["_processed_at"] = datetime.now().isoformat()
                
                # 触发回调
                for callback in self.callbacks:
                    try:
                        callback(memory)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                self.processed_count += 1
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def start(self):
        """启动后台处理"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """停止后台处理"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "running": self.running,
            "queue_size": self.queue.qsize(),
            "processed_count": self.processed_count,
            "callbacks_count": len(self.callbacks)
        }


class AsyncMemoryStream:
    """
    异步记忆流
    
    支持 async/await 模式
    """
    
    def __init__(self):
        STREAM_DIR.mkdir(parents=True, exist_ok=True)
        self.queue = asyncio.Queue(maxsize=1000)
        self.callbacks: List[Callable] = []
        self.running = False
        self.processed_count = 0
    
    async def ingest(self, memory: Dict):
        """异步摄入"""
        memory["_ingested_at"] = datetime.now().isoformat()
        
        # 立即触发回调
        for callback in self.callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(memory)
            else:
                callback(memory)
        
        self.processed_count += 1
        return memory
    
    async def put(self, memory: Dict):
        """放入队列"""
        memory["_queued_at"] = datetime.now().isoformat()
        await self.queue.put(memory)
    
    async def _process_queue(self):
        """处理队列"""
        while self.running:
            try:
                memory = await asyncio.wait_for(self.queue.get(), timeout=1)
                memory["_processed_at"] = datetime.now().isoformat()
                
                for callback in self.callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(memory)
                    else:
                        callback(memory)
                
                self.processed_count += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Process error: {e}")
    
    def add_callback(self, callback: Callable):
        """添加回调"""
        self.callbacks.append(callback)
    
    async def start(self):
        """启动"""
        if self.running:
            return
        self.running = True
        asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """停止"""
        self.running = False


# ===== SSE / WebSocket 事件源 =====

class SSEMemoryStream:
    """
    SSE 事件源
    
    用于前端实时推送
    """
    
    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []
    
    async def subscribe(self) -> asyncio.Queue:
        """订阅"""
        q = asyncio.Queue()
        self.subscribers.append(q)
        return q
    
    async def unsubscribe(self, q: asyncio.Queue):
        """取消订阅"""
        if q in self.subscribers:
            self.subscribers.remove(q)
    
    async def broadcast(self, event: Dict):
        """广播事件"""
        for q in self.subscribers:
            await q.put(event)
    
    def publish(self, event: Dict):
        """同步广播（在线程中使用）"""
        import concurrent.futures
        for q in self.subscribers:
            concurrent.futures.ThreadPoolExecutor().submit(
                lambda qq, ee: asyncio.run(qq.put(ee)), q, event
            )


# ===== 便捷函数 =====

_stream = None

def get_memory_stream() -> MemoryStream:
    global _stream
    if _stream is None:
        _stream = MemoryStream()
    return _stream


def ingest_stream(memory: Dict):
    """便捷的流式摄入"""
    return get_memory_stream().ingest(memory)


if __name__ == "__main__":
    print("=" * 50)
    print("流式摄入测试")
    print("=" * 50)
    
    stream = MemoryStream()
    
    # 添加回调
    def on_memory(m):
        print(f"  📝 处理: {m['text'][:30]}...")
    
    stream.add_callback(on_memory)
    
    # 测试同步摄入
    print("\n1. 同步摄入:")
    memories = [
        {"id": "mem_1", "text": "用户说喜欢简洁"},
        {"id": "mem_2", "text": "决定用微服务"},
    ]
    for mem in memories:
        stream.ingest(mem)
    
    # 测试异步队列
    print("\n2. 异步队列:")
    stream.start()
    for mem in memories:
        stream.put(mem)
    
    import time
    time.sleep(1)
    stream.stop()
    
    print(f"\n📊 状态: {stream.get_status()}")
    
    print("\n✅ 流式摄入测试完成")
