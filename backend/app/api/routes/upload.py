from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from typing import List
import zipfile
import tempfile
from pathlib import Path

router = APIRouter()

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple files (PDF, DOCX, TXT, or ZIP)"""
    
    processed_files = []
    
    for file in files:
        # Check file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File {file.filename} exceeds 5MB limit")
        
        # Check extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS and ext != '.zip':
            raise HTTPException(400, f"Unsupported file type: {ext}")
        
        # Handle ZIP file
        if ext == '.zip':
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / file.filename
                with open(zip_path, 'wb') as f:
                    f.write(content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Process each extracted file
                for extracted_file in Path(tmpdir).iterdir():
                    if extracted_file.suffix.lower() in ALLOWED_EXTENSIONS:
                        processed = await process_single_file(extracted_file)
                        processed_files.append(processed)
        else:
            # Save and process single file
            save_path = Path("data/uploads") / file.filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(content)
            
            processed = await process_single_file(save_path)
            processed_files.append(processed)
    
    # Rebuild the index with all new files - FIXED
    try:
        from app.services.indexing import build_index
        from app.core.config import get_settings
        settings = get_settings()
        build_index(settings)
    except Exception as e:
        print(f"Error rebuilding index: {e}")

    # Rebuild the index with all new files
    # from app.services.indexing import build_index
    # from app.core.config import get_settings
    # settings = get_settings()
    # build_index(settings)
    
    return JSONResponse({
        "message": f"Successfully processed {len(processed_files)} files",
        "files": processed_files
    })

async def process_single_file(file_path: Path):
    """Extract text from PDF, DOCX, or TXT file"""
    ext = file_path.suffix.lower()
    
    if ext == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join([page.extract_text() for page in reader.pages])
    
    elif ext == '.docx':
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    else:
        text = ""
    
    # Store extracted text
    text_path = Path("data/extracted") / f"{file_path.stem}.txt"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return {
        "filename": file_path.name,
        "size": file_path.stat().st_size,
        "type": ext,
        "extracted_text_length": len(text)
    }

@router.get("/files")
async def list_uploaded_files():
    """List all uploaded files"""
    uploads_dir = Path("data/uploads")
    if not uploads_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in uploads_dir.iterdir():
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
    
    return {"files": files}

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    file_path = Path("data/uploads") / filename
    if file_path.exists():
        file_path.unlink()
        # Rebuild index without this file - FIXED
        from app.services.indexing import build_index
        from app.core.config import get_settings
        settings = get_settings()
        build_index(settings)
        return {"message": f"Deleted {filename}"}
    else:
        raise HTTPException(404, "File not found")