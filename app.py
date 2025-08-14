#!/usr/bin/env python3
"""
FastAPI Backend for USB PD Specification Parser
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from main import USBPDParser, TOCEntry, Section

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("intex.html", {"request": request})

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and parse a PDF file"""
    global toc_entries, sections, current_pdf_path
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Parse the PDF
        parser = USBPDParser(str(file_path), "USB Power Delivery Specification")
        toc_entries, sections, validation_report = parser.process_pdf()
        
        # Save parsed data
        parser.save_jsonl(toc_entries, "usb_pd_toc.jsonl")
        parser.save_jsonl(sections, "usb_pd_spec.jsonl")
        
        current_pdf_path = str(file_path)
        
        return {
            "message": "PDF parsed successfully",
            "toc_count": len(toc_entries),
            "sections_count": len(sections),
            "filename": file.filename
        }
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

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
        "current_pdf": current_pdf_path
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
    
    # Clean up temporary files
    upload_dir = Path("uploads")
    if upload_dir.exists():
        for file_path in upload_dir.glob("*.pdf"):
            try:
                file_path.unlink()
            except:
                pass
    
    return {"message": "All data cleared successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
