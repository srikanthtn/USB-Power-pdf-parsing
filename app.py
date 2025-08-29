#!/usr/bin/env python3
"""
FastAPI Backend for USB PD Specification Parser
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from usbpd import USBPDParserApp, TOCEntry, Section
import logging
from fastapi.logger import logger
logging.getLogger("multipart").setLevel(logging.WARNING)

# Initialize FastAPI app
app = FastAPI(
    title="USB PD Specification Parser",
    description="FastAPI backend for parsing USB Power Delivery specifications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Global variables to store parsed data
toc_entries: List[TOCEntry] = []
sections: List[Section] = []
current_pdf_path: Optional[str] = None
pdf_metadata: Optional[Dict[str, Any]] = None


def _human_size(num_bytes: int) -> str:
	units = ["B", "KB", "MB", "GB", "TB"]
	idx = 0
	value = float(num_bytes)
	while value >= 1024 and idx < len(units) - 1:
		value /= 1024.0
		idx += 1
	return f"{value:.2f} {units[idx]}"


def _parse_pdf_date(raw: Optional[str]) -> Optional[str]:
	"""Convert PDF date strings like 'D:20241028153000+05' to ISO if possible."""
	if not raw:
		return None
	try:
		# Remove leading 'D:' if present
		s = raw[2:] if raw.startswith('D:') else raw
		# Pad to at least YYYYMMDDHHmmSS
		s = (s + '0'*14)[:14]
		year = int(s[0:4]); mon = int(s[4:6]); day = int(s[6:8])
		hh = int(s[8:10]); mm = int(s[10:12]); ss = int(s[12:14])
		from datetime import datetime
		return datetime(year, mon, day, hh, mm, ss).isoformat()
	except Exception:
		return raw


def extract_pdf_metadata(path: Path) -> Dict[str, Any]:
	import fitz
	doc = fitz.open(str(path))
	meta = doc.metadata or {}
	info: Dict[str, Any] = {
		"file_name": path.name,
		"file_size_bytes": path.stat().st_size,
		"file_size": _human_size(path.stat().st_size),
		"page_count": doc.page_count,
		"title": meta.get("title"),
		"author": meta.get("author"),
		"subject": meta.get("subject"),
		"keywords": meta.get("keywords"),
		"creator": meta.get("creator"),
		"producer": meta.get("producer"),
		"creation_date": _parse_pdf_date(meta.get("creationDate") or meta.get("creation_date")),
		"mod_date": _parse_pdf_date(meta.get("modDate") or meta.get("mod_date")),
	}
	return info

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    start_page: int = Form(1),
    end_page: Optional[int] = Form(None)
):
    """Upload and parse a PDF file with page range"""
    global toc_entries, sections, current_pdf_path
    
    logger.info(f"Received file: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    try:
        logger.info(f"Saving file to: {file_path}")
        with file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Initializing parser with page range: {start_page}-{end_page}")
        # Use orchestrator to run and generate outputs
        app_runner = USBPDParserApp(str(file_path))
        toc_entries, sections, _ = app_runner.run()
        current_pdf_path = str(file_path)
        # Extract and store PDF metadata
        globals()['pdf_metadata'] = extract_pdf_metadata(file_path)
        
        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "page_range": f"{start_page}-{end_page if end_page else 'end'}",
            "toc_entries": len(toc_entries),
            "sections": len(sections)
        }
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        # Clean up the file if there was an error
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up file: {str(cleanup_error)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/api/toc")
async def get_toc():
    """Get Table of Contents data"""
    if not toc_entries:
        raise HTTPException(status_code=404, detail="No TOC data available. Please upload a PDF first.")
    
    return {
        "toc_entries": [entry.__dict__ for entry in toc_entries],
        "total_count": len(toc_entries)
    }

@app.get("/api/sections")
async def get_sections():
    """Get document sections data"""
    if not sections:
        raise HTTPException(status_code=404, detail="No sections data available. Please upload a PDF first.")
    
    return {
        "sections": [section.__dict__ for section in sections],
        "total_count": len(sections)
    }

@app.get("/api/metadata")
async def get_metadata():
	"""Return metadata for the last uploaded PDF."""
	if not pdf_metadata:
		raise HTTPException(status_code=404, detail="No PDF metadata available. Please upload a PDF first.")
	return pdf_metadata

@app.get("/api/section/{section_id}")
async def get_section_by_id(section_id: str):
    """Get a specific section by ID"""
    if not sections:
        raise HTTPException(status_code=404, detail="No sections data available")
    
    section = next((s for s in sections if s.section_id == section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")
    
    return section.__dict__

@app.get("/api/search")
async def search_sections(query: str, limit: int = 10):
    """Search sections by content or title"""
    if not sections:
        raise HTTPException(status_code=404, detail="No sections data available")
    
    query_lower = query.lower()
    results = []
    
    for section in sections:
        if (query_lower in section.title.lower() or 
            query_lower in section.content.lower()):
            results.append({
                "section_id": section.section_id,
                "title": section.title,
                "page": section.page,
                "content_preview": section.content[:200] + "..." if len(section.content) > 200 else section.content
            })
            
            if len(results) >= limit:
                break
    
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@app.get("/api/stats")
async def get_stats():
    """Get parsing statistics"""
    if not toc_entries and not sections:
        return {
            "status": "No data",
            "message": "Please upload a PDF first"
        }
    
    # Calculate some basic stats
    toc_levels = {}
    for entry in toc_entries:
        level = entry.level
        toc_levels[level] = toc_levels.get(level, 0) + 1
    
    return {
        "status": "Data available",
        "toc_entries_count": len(toc_entries),
        "sections_count": len(sections),
        "toc_levels_distribution": toc_levels,
        "current_pdf": current_pdf_path,
        "page_count": pdf_metadata.get("page_count") if pdf_metadata else None,
        "file_size": pdf_metadata.get("file_size") if pdf_metadata else None,
    }

@app.get("/api/export/toc")
async def export_toc():
    """Export TOC data as JSON"""
    if not toc_entries:
        raise HTTPException(status_code=404, detail="No TOC data available")
    
    return JSONResponse(
        content=[entry.__dict__ for entry in toc_entries],
        media_type="application/json"
    )

@app.get("/api/export/sections")
async def export_sections():
    """Export sections data as JSON"""
    if not sections:
        raise HTTPException(status_code=404, detail="No sections data available")
    
    return JSONResponse(
        content=[section.__dict__ for section in sections],
        media_type="application/json"
    )

@app.delete("/api/clear")
async def clear_data():
    """Clear all parsed data"""
    global toc_entries, sections, current_pdf_path
    
    toc_entries = []
    sections = []
    current_pdf_path = None
    globals()['pdf_metadata'] = None
    
    # Clean up temporary files
    upload_dir = Path("uploads")
    if upload_dir.exists():
        for file_path in upload_dir.glob("*.pdf"):
            try:
                file_path.unlink()
            except:
                pass
    
    return {"message": "All data cleared successfully"}


from fastapi.responses import FileResponse
import os

@app.get("/download/toc-jsonl")
async def download_toc_jsonl():
    """Download TOC data as JSONL file"""
    file_path = Path("usb_pd_toc.jsonl").absolute()
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="TOC JSONL file not found. Please upload and parse a PDF first."
        )
    return FileResponse(
        path=str(file_path),
        media_type='application/jsonl',
        filename="usb_pd_toc.jsonl"
    )

@app.get("/download/sections-jsonl")
async def download_sections_jsonl():
    """Download sections data as JSONL file"""
    file_path = Path("usb_pd_spec.jsonl").absolute()
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Sections JSONL file not found. Please upload and parse a PDF first."
        )
    return FileResponse(
        path=str(file_path),
        media_type='application/jsonl',
        filename="usb_pd_spec.jsonl"
    )




if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
