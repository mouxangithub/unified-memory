"""
Prometheus 导出器
"""
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from .metrics import MetricsCollector


class PrometheusHandler(BaseHTTPRequestHandler):
    """Prometheus 指标处理器"""
    
    collector: Optional[MetricsCollector] = None
    
    def do_GET(self):
        if self.path == "/metrics":
            metrics = self.collector.render_prometheus()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(metrics.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 静默日志


class PrometheusExporter:
    """Prometheus 导出器"""
    
    def __init__(self, collector: MetricsCollector, port: int = 9090):
        self.collector = collector
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """启动导出器"""
        PrometheusHandler.collector = self.collector
        
        self._server = HTTPServer(("0.0.0.0", self.port), PrometheusHandler)
        
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
        print(f"Prometheus exporter started on :{self.port}")
    
    def _run(self) -> None:
        self._server.serve_forever()
    
    def stop(self) -> None:
        """停止导出器"""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
