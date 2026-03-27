#!/usr/bin/env python3
"""
PDF Processor - PDF 文档处理模块

功能:
- PDF 文本提取
- 智能分块
- 自动存储到记忆系统
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


class PDFProcessor:
    """PDF 处理器"""
    
    def __init__(self):
        self.pdf_available = self._check_pdf()
    
    def _check_pdf(self) -> bool:
        """检查 PDF 解析是否可用"""
        try:
            import PyPDF2
            return True
        except ImportError:
            try:
                import fitz  # PyMuPDF
                return True
            except ImportError:
                return False
    
    def process(self, pdf_path: str) -> Dict:
        """
        处理 PDF
        
        Returns:
            {
                "pages": 10,
                "chunks": 15,
                "memory_id": "pdf_xxx",
                "metadata": {...}
            }
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF 不存在: {pdf_path}")
        
        result = {
            "path": str(path),
            "filename": path.name,
            "processed_at": datetime.now().isoformat(),
            "pages": 0,
            "chunks": 0,
            "text": "",
            "memory_id": None,
            "metadata": {
                "size": path.stat().st_size
            }
        }
        
        # 提取文本
        text = self._extract_text(path)
        result["text"] = text
        result["pages"] = text.count("\n\n--- PAGE ---\n\n") + 1
        
        # 智能分块
        chunks = self._chunk_text(text)
        result["chunks"] = len(chunks)
        
        # 存储到记忆系统
        result["memory_id"] = self._store_chunks(path.name, chunks)
        
        return result
    
    def _extract_text(self, pdf_path: Path) -> str:
        """提取 PDF 文本"""
        text_parts = []
        
        # 尝试 PyMuPDF
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"\n\n--- PAGE {i+1} ---\n\n{page_text}")
            doc.close()
            
            return "\n".join(text_parts)
        except:
            pass
        
        # 尝试 PyPDF2
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"\n\n--- PAGE {i+1} ---\n\n{page_text}")
            
            return "\n".join(text_parts)
        except:
            pass
        
        return f"[无法解析 PDF: {pdf_path.name}]"
    
    def _chunk_text(self, text: str) -> List[str]:
        """智能分块"""
        try:
            from smart_chunk import smart_chunk
            return smart_chunk(text, max_tokens=900)
        except:
            # 简单分块
            chunks = []
            for i in range(0, len(text), 4000):
                chunks.append(text[i:i+4000])
            return chunks
    
    def _store_chunks(self, filename: str, chunks: List[str]) -> str:
        """存储分块到记忆系统"""
        try:
            from unified_interface import UnifiedMemory
            um = UnifiedMemory()
            
            memory_ids = []
            for i, chunk in enumerate(chunks):
                text = f"[PDF: {filename} - 第 {i+1}/{len(chunks)} 块]\n\n{chunk}"
                mid = um.quick_store(text, category="document")
                memory_ids.append(mid)
            
            return memory_ids[0] if memory_ids else None
        except Exception as e:
            print(f"存储失败: {e}")
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF 处理")
    parser.add_argument("pdf", help="PDF 路径")
    parser.add_argument("--store", action="store_true", help="存储到记忆系统")
    
    args = parser.parse_args()
    
    processor = PDFProcessor()
    result = processor.process(args.pdf)
    
    print(f"✅ 处理完成:")
    print(f"   文件: {result['filename']}")
    print(f"   页数: {result['pages']}")
    print(f"   分块: {result['chunks']}")
    print(f"   记忆ID: {result['memory_id']}")
    
    if args.store:
        print(f"\n文本预览:")
        print(result['text'][:300])


if __name__ == "__main__":
    main()
