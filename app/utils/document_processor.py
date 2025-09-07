"""Document processing utilities for content ingestion."""

import os
import uuid
from typing import List, Dict, Any, Optional
import PyPDF2
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
import markdown
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document types and extract text content."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_document(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Process a document and return extracted content and metadata."""
        
        try:
            if content_type == "application/pdf":
                return self._process_pdf(file_path)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._process_docx(file_path)
            elif content_type == "text/plain":
                return self._process_txt(file_path)
            elif content_type == "text/markdown":
                return self._process_markdown(file_path)
            elif content_type == "text/html":
                return self._process_html(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF documents."""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            metadata = {
                "pages": len(reader.pages),
                "title": reader.metadata.get("/Title", "") if reader.metadata else "",
                "author": reader.metadata.get("/Author", "") if reader.metadata else ""
            }
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        
        return {
            "content": text,
            "metadata": metadata
        }
    
    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """Process DOCX documents."""
        doc = DocxDocument(file_path)
        text = ""
        metadata = {
            "title": doc.core_properties.title or "",
            "author": doc.core_properties.author or "",
            "created": str(doc.core_properties.created) if doc.core_properties.created else ""
        }
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return {
            "content": text,
            "metadata": metadata
        }
    
    def _process_txt(self, file_path: str) -> Dict[str, Any]:
        """Process plain text documents."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return {
            "content": content,
            "metadata": {"encoding": "utf-8"}
        }
    
    def _process_markdown(self, file_path: str) -> Dict[str, Any]:
        """Process Markdown documents."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Convert markdown to HTML for better text extraction
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        return {
            "content": text,
            "metadata": {"format": "markdown"}
        }
    
    def _process_html(self, file_path: str) -> Dict[str, Any]:
        """Process HTML documents."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Extract title if available
        title = soup.find('title')
        title_text = title.get_text() if title else ""
        
        return {
            "content": text,
            "metadata": {"title": title_text}
        }
    
    def chunk_content(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split content into chunks for vector storage."""
        
        # Simple chunking by character count
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings within the last 100 characters
                search_start = max(start, end - 100)
                for i in range(end - 1, search_start, -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": chunk_index,
                    "start_position": start,
                    "end_position": end,
                    "metadata": {
                        **metadata,
                        "chunk_size": len(chunk_content)
                    }
                })
                chunk_index += 1
            
            start = end - self.chunk_overlap
            if start >= len(content):
                break
        
        return chunks
    
    def process_and_chunk(self, file_path: str, content_type: str, document_id: str) -> List[Dict[str, Any]]:
        """Process a document and return chunked content ready for vector storage."""
        
        # Process document
        doc_data = self.process_document(file_path, content_type)
        
        # Create chunks
        chunks = self.chunk_content(doc_data["content"], doc_data["metadata"])
        
        # Add document ID to each chunk
        for chunk in chunks:
            chunk["document_id"] = document_id
        
        return chunks
