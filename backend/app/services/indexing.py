import json
from dataclasses import dataclass
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.services.documents import normalize_text
#from app.services.document_loader import load_uploaded_documents


@dataclass(frozen=True)
class BuildIndexResult:
    page_count: int
    chunk_count: int


def _get_embeddings(settings: Settings) -> GoogleGenerativeAIEmbeddings:
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required to build or query the RAG index.")

    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


def load_pdf_documents(settings: Settings) -> list[Document]:
    """Load documents from the original PDF file"""
    if not settings.pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {settings.pdf_path}")

    loader = PyPDFLoader(str(settings.pdf_path))
    documents = loader.load()

    cleaned_documents: list[Document] = []
    for document in documents:
        cleaned = normalize_text(document.page_content)
        if not cleaned:
            continue

        page = document.metadata.get("page")
        page_number = page + 1 if isinstance(page, int) else None
        cleaned_documents.append(
            Document(
                page_content=cleaned,
                metadata={
                    **document.metadata,
                    "source": settings.pdf_path.name,
                    "source_type": "original_pdf",
                    "page_number": page_number,
                },
            )
        )

    return cleaned_documents

def load_uploaded_documents(uploads_dir: Path) -> list[Document]:
    """Load all documents from the uploads folder"""
    documents = []
    
    if not uploads_dir.exists():
        print(f"Uploads directory not found: {uploads_dir}")
        return documents
    
    for file_path in uploads_dir.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            try:
                if ext == '.pdf':
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(str(file_path))
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
                    print(f"  Loaded PDF: {file_path.name}")
                
                elif ext == '.docx':
                    from langchain_community.document_loaders import Docx2txtLoader
                    loader = Docx2txtLoader(str(file_path))
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
                    print(f"  Loaded DOCX: {file_path.name}")
                
                elif ext == '.txt':
                    from langchain_community.document_loaders import TextLoader
                    loader = TextLoader(str(file_path), encoding='utf-8')
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    documents.extend(docs)
                    print(f"  Loaded TXT: {file_path.name}")
            
            except Exception as e:
                print(f"Error loading {file_path.name}: {e}")
    
    return documents

def load_all_documents(settings: Settings) -> list[Document]:
    """Load ALL documents: original PDF + uploaded files"""
    all_documents = []
    
    # 1. Load original PDF
    original_docs = load_pdf_documents(settings)
    all_documents.extend(original_docs)
    print(f"Loaded {len(original_docs)} pages from original PDF")
    
    # 2. Load uploaded documents
    uploads_dir = Path("data/uploads")  # Path to uploads folder
    uploaded_docs = load_uploaded_documents(uploads_dir)
    all_documents.extend(uploaded_docs)
    print(f"Loaded {len(uploaded_docs)} pages from uploaded files")
    
    return all_documents


def split_documents(settings: Settings, documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    chunks = splitter.split_documents(documents)
    enriched_chunks: list[Document] = []

    for index, chunk in enumerate(chunks, start=1):
        source_name = chunk.metadata.get("source", "unknown") # Create unique chunk ID with source info
        chunk_id = f"{source_name}-chunk-{index:04d}"

        enriched_chunks.append(
            Document(
                page_content=normalize_text(chunk.page_content),
                metadata={
                    **chunk.metadata,
                    "chunk_id": f"chunk-{index:04d}",
                },
            )
        )

    return enriched_chunks


def _write_chunk_cache(settings: Settings, chunks: list[Document]) -> None:
    """Save chunk cache for debugging and retrieval"""
    records = [
        {
            "chunk_id": chunk.metadata.get("chunk_id"),
            "page_number": chunk.metadata.get("page_number"),
            "source": chunk.metadata.get("source", settings.pdf_path.name),
            "source_type": chunk.metadata.get("source_type", "unknown"),
            "content": chunk.page_content,
        }
        for chunk in chunks
    ]

    settings.chunk_cache_path.parent.mkdir(parents=True, exist_ok=True)
    settings.chunk_cache_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_index(settings: Settings) -> BuildIndexResult:
    """Build FAISS index from ALL documents (original PDF + uploaded files)"""

    from pathlib import Path
    from langchain_community.document_loaders import PyPDFLoader
    
    all_documents = []

    # 1. Load original PDF
    print("Loading original PDF...")
    documents = load_pdf_documents(settings)
    all_documents.extend(documents)
    print(f"  Loaded {len(documents)} pages from original PDF")

    # 2. Load uploaded PDFs from data/uploads folder
    print("Loading uploaded files...")
    uploads_dir = Path("data/uploads")
    if uploads_dir.exists():
        for file_path in uploads_dir.iterdir():
            if file_path.suffix.lower() == '.pdf':
                try:
                    loader = PyPDFLoader(str(file_path))
                    uploaded_docs = loader.load()
                    for doc in uploaded_docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['source_type'] = 'uploaded'
                    all_documents.extend(uploaded_docs)
                    print(f"  Loaded {len(uploaded_docs)} pages from {file_path.name}")
                except Exception as e:
                    print(f"  Error loading {file_path.name}: {e}")
    
    if not all_documents:
        raise RuntimeError("No documents found to index. Please add PDF files to /pdfs/ or upload via web interface.")

    print(f"Total documents: {len(all_documents)}")

    # 3. Split into chunks
    chunks = split_documents(settings, all_documents)
    print(f"Created {len(chunks)} chunks from {len(all_documents)} documents")

    # 4. Create vector store
    vectorstore = FAISS.from_documents(chunks, _get_embeddings(settings))

    # 5. Save index
    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(settings.vectorstore_dir))

    # 6. Save chunk cache
    _write_chunk_cache(settings, chunks)

    # Count unique sources
    unique_sources = set(chunk.metadata.get("source", "unknown") for chunk in chunks)
    print(f"Indexed sources: {', '.join(unique_sources)}")

    return BuildIndexResult(page_count=len(all_documents), chunk_count=len(chunks))
