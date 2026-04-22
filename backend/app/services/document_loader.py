from pathlib import Path
from typing import List
from langchain_core.documents import Document
import os

def load_uploaded_documents(uploads_dir: Path) -> List[Document]:
    """Load all documents from the uploads folder"""
    documents = []
    
    if not uploads_dir.exists():
        return documents
    
    for file_path in uploads_dir.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            try:
                if ext == '.pdf':
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(str(file_path))
                    docs = loader.load()
                    # Add source metadata
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
                
                elif ext == '.docx':
                    from langchain_community.document_loaders import Docx2txtLoader
                    loader = Docx2txtLoader(str(file_path))
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
                
                elif ext == '.txt':
                    from langchain_community.document_loaders import TextLoader
                    loader = TextLoader(str(file_path), encoding='utf-8')
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
            
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return documents