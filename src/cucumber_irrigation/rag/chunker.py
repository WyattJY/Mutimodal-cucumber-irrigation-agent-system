"""文档分块处理器

P7-03: 文献分块处理
支持 PDF/TXT/Markdown 格式分块
"""

import os
import re
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from loguru import logger


class DocumentFormat(str, Enum):
    """文档格式"""
    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "md"
    UNKNOWN = "unknown"


@dataclass
class DocumentChunk:
    """文档分块"""
    chunk_id: str
    content: str
    source_id: str
    page: Optional[int] = None
    chunk_index: int = 0
    source_type: str = "user"  # "system" or "user"
    is_user: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "source_id": self.source_id,
            "page": self.page,
            "chunk_index": self.chunk_index,
            "source_type": self.source_type,
            "is_user": self.is_user,
            "metadata": self.metadata
        }


@dataclass
class ChunkingConfig:
    """分块配置"""
    chunk_size: int = 512        # 目标分块大小 (字符数)
    overlap: int = 50            # 重叠字符数
    min_chunk_size: int = 100    # 最小分块大小
    max_chunk_size: int = 1024   # 最大分块大小
    preserve_paragraphs: bool = True  # 保留段落完整性


class DocumentChunker:
    """文档分块处理器

    支持:
    - PDF 解析与分块
    - TXT 文本分块
    - Markdown 分块
    - 语义感知分块
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        初始化分块器

        Args:
            config: 分块配置
        """
        self.config = config or ChunkingConfig()
        logger.info("DocumentChunker 初始化完成")

    def chunk_file(
        self,
        file_path: str,
        source_id: Optional[str] = None,
        is_user: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        分块处理文件

        Args:
            file_path: 文件路径
            source_id: 文献 ID
            is_user: 是否为用户文献
            metadata: 附加元数据

        Returns:
            分块列表
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 生成 source_id
        if source_id is None:
            source_id = self._generate_source_id(file_path)

        # 确定文件格式
        format_type = self._detect_format(path)
        logger.info(f"处理文件: {path.name}, 格式: {format_type.value}")

        # 根据格式处理
        if format_type == DocumentFormat.PDF:
            text, pages = self._parse_pdf(file_path)
        elif format_type == DocumentFormat.MARKDOWN:
            text = self._parse_markdown(file_path)
            pages = None
        else:  # TXT or UNKNOWN
            text = self._parse_txt(file_path)
            pages = None

        # 分块
        chunks = self._chunk_text(
            text=text,
            source_id=source_id,
            is_user=is_user,
            pages=pages,
            metadata=metadata or {}
        )

        logger.info(f"文件 {path.name} 分块完成: {len(chunks)} 个分块")
        return chunks

    def chunk_text(
        self,
        text: str,
        source_id: str,
        is_user: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        分块处理文本

        Args:
            text: 文本内容
            source_id: 文献 ID
            is_user: 是否为用户文献
            metadata: 附加元数据

        Returns:
            分块列表
        """
        return self._chunk_text(
            text=text,
            source_id=source_id,
            is_user=is_user,
            metadata=metadata or {}
        )

    def _detect_format(self, path: Path) -> DocumentFormat:
        """检测文件格式"""
        suffix = path.suffix.lower()

        format_map = {
            ".pdf": DocumentFormat.PDF,
            ".txt": DocumentFormat.TXT,
            ".md": DocumentFormat.MARKDOWN,
            ".markdown": DocumentFormat.MARKDOWN
        }

        return format_map.get(suffix, DocumentFormat.UNKNOWN)

    def _generate_source_id(self, file_path: str) -> str:
        """生成文献 ID"""
        path = Path(file_path)
        content = f"{path.name}_{path.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _parse_pdf(self, file_path: str) -> Tuple[str, Dict[int, str]]:
        """解析 PDF 文件"""
        try:
            import pdfplumber

            text_parts = []
            pages = {}

            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""

                    # 提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        table_text = self._format_table(table)
                        page_text += f"\n{table_text}"

                    text_parts.append(page_text)
                    pages[i + 1] = page_text

            return "\n\n".join(text_parts), pages

        except ImportError:
            logger.warning("pdfplumber 未安装，尝试使用 PyPDF2")
            return self._parse_pdf_pypdf2(file_path)

    def _parse_pdf_pypdf2(self, file_path: str) -> Tuple[str, Dict[int, str]]:
        """使用 PyPDF2 解析 PDF"""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            text_parts = []
            pages = {}

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
                pages[i + 1] = page_text

            return "\n\n".join(text_parts), pages

        except ImportError:
            logger.error("PyPDF2 也未安装，无法解析 PDF")
            raise ImportError("需要安装 pdfplumber 或 PyPDF2 来解析 PDF")

    def _parse_txt(self, file_path: str) -> str:
        """解析 TXT 文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(f"无法解码文件: {file_path}")

    def _parse_markdown(self, file_path: str) -> str:
        """解析 Markdown 文件"""
        return self._parse_txt(file_path)

    def _format_table(self, table: List[List[str]]) -> str:
        """格式化表格为文本"""
        if not table:
            return ""

        rows = []
        for row in table:
            cells = [str(cell) if cell else "" for cell in row]
            rows.append(" | ".join(cells))

        return "\n".join(rows)

    def _chunk_text(
        self,
        text: str,
        source_id: str,
        is_user: bool,
        pages: Optional[Dict[int, str]] = None,
        metadata: Dict[str, Any] = None
    ) -> List[DocumentChunk]:
        """分块文本"""
        metadata = metadata or {}
        chunks = []

        # 首先尝试按标题分割
        sections = self._split_by_headers(text)

        if len(sections) > 1:
            # 按标题分割成功
            chunk_index = 0
            for section in sections:
                section_chunks = self._split_into_chunks(section)
                for chunk_text in section_chunks:
                    chunk = DocumentChunk(
                        chunk_id=f"{source_id}_{chunk_index:04d}",
                        content=chunk_text,
                        source_id=source_id,
                        chunk_index=chunk_index,
                        source_type="user" if is_user else "system",
                        is_user=is_user,
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)
                    chunk_index += 1
        else:
            # 按固定大小分块
            chunk_texts = self._split_into_chunks(text)
            for i, chunk_text in enumerate(chunk_texts):
                # 尝试找到对应页码
                page_num = None
                if pages:
                    for page, page_text in pages.items():
                        if chunk_text[:100] in page_text:
                            page_num = page
                            break

                chunk = DocumentChunk(
                    chunk_id=f"{source_id}_{i:04d}",
                    content=chunk_text,
                    source_id=source_id,
                    page=page_num,
                    chunk_index=i,
                    source_type="user" if is_user else "system",
                    is_user=is_user,
                    metadata=metadata.copy()
                )
                chunks.append(chunk)

        return chunks

    def _split_by_headers(self, text: str) -> List[str]:
        """按标题分割文本"""
        header_patterns = [
            r'^#{1,6}\s+',          # Markdown headers
            r'^Chapter\s+\d+',      # Chapter N
            r'^Section\s+\d+',      # Section N
            r'^\d+\.\s+[A-Z]',      # 1. Title
            r'^[一二三四五六七八九十]+[、.]\s*',  # 中文数字标题
        ]

        lines = text.split('\n')
        sections = []
        current_section = []

        for line in lines:
            is_header = any(
                re.match(pattern, line.strip())
                for pattern in header_patterns
            )

            if is_header and current_section:
                section_text = '\n'.join(current_section).strip()
                if len(section_text) >= self.config.min_chunk_size:
                    sections.append(section_text)
                current_section = [line]
            else:
                current_section.append(line)

        # 添加最后一个部分
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if len(section_text) >= self.config.min_chunk_size:
                sections.append(section_text)

        return sections if len(sections) > 1 else []

    def _split_into_chunks(self, text: str) -> List[str]:
        """将文本分割成固定大小的块"""
        if len(text) <= self.config.chunk_size:
            return [text] if len(text) >= self.config.min_chunk_size else []

        chunks = []

        if self.config.preserve_paragraphs:
            # 按段落分割
            paragraphs = text.split('\n\n')
            current_chunk = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if len(current_chunk) + len(para) + 2 <= self.config.max_chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

            if current_chunk:
                chunks.append(current_chunk)
        else:
            # 固定大小分割
            step = self.config.chunk_size - self.config.overlap

            for i in range(0, len(text), step):
                chunk = text[i:i + self.config.chunk_size]
                if len(chunk) >= self.config.min_chunk_size:
                    chunks.append(chunk)

        return chunks
