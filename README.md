# USB PD Specification Parser - FastAPI Backend (OOP)

A modern web application and CLI for parsing USB Power Delivery
specification PDFs using an OOP architecture.

## 🚀 Features

- **PDF Upload & Parsing**: Upload USB PD specification PDFs and automatically extract TOC and sections
- **Interactive Tables**: View parsed Table of Contents and document sections in organized tables
- **Search Functionality**: Search through sections by content or title
- **Statistics Dashboard**: View parsing statistics and TOC level distribution
- **Export Capabilities**: Export parsed data as JSON files
- **Modern UI**: Beautiful, responsive design with gradient backgrounds
- **Real-time Processing**: Fast PDF parsing with progress indicators

## 🛠️ Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Installation
Make sure you have all required packages:
- FastAPI
- Uvicorn
- pdfplumber
- pandas
- openpyxl
- jinja2

## 🚀 Running the Application

### Option 1: Using the CLI
```bash
python run.py --pdf path/to/USB_PD.pdf --output out/ --title "USB PD"
```

### Option 2: Using uvicorn directly
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using the main app
```bash
python app.py
```

## Artifacts

Generated files (under --output):

- usb_pd_toc.jsonl
- usb_pd_spec.jsonl
- usb_pd_metadata.jsonl
- validation_report.xlsx

## 🌐 Access the Application

Once running, open your browser and navigate to:
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 📁 Project Structure

```
v1/
├── app.py                 # Main FastAPI application
├── usbpd/                # OOP parsing package
│   ├── __init__.py
│   ├── models.py         # TOCEntry, Section dataclasses
│   ├── pdf_parser.py     # PDFParser (raw text/metadata)
│   ├── toc_extractor.py  # TOCExtractor (hierarchy)
│   ├── section_extractor.py # SectionExtractor (sections content)
│   ├── jsonl_writer.py   # JSONLWriter (outputs)
│   └── app_runner.py     # USBPDParserApp (orchestrator)
├── main.py               # Legacy parser (still available)
├── run.py                # Startup script
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # Frontend templates
│   ├── intex.html      # Main HTML page
│   ├── scripts.js      # JavaScript functionality
│   └── style.css       # CSS styling
├── uploads/            # Temporary PDF storage (auto-created)
└── *.jsonl             # Parsed data files

## Tests

```bash
pytest -q
```
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Main application page
- `POST /upload-pdf` - Upload and parse PDF file
- `GET /api/toc` - Get Table of Contents data
- `GET /api/sections` - Get document sections data
- `GET /api/section/{section_id}` - Get specific section by ID

### Search & Analysis
- `GET /api/search` - Search sections by content/title
- `GET /api/stats` - Get parsing statistics

### Export & Management
- `GET /api/export/toc` - Export TOC as JSON
- `GET /api/export/sections` - Export sections as JSON
- `DELETE /api/clear` - Clear all parsed data

## 💻 Usage

### 1. Upload PDF
1. Open the application in your browser
2. Click "Choose File" and select your USB PD specification PDF
3. Click "Upload & Parse PDF"
4. Wait for processing to complete

### 2. View Data
- **Load TOC Data**: Click to populate the Table of Contents table
- **Load Sections Data**: Click to populate the Sections table
- **Refresh Stats**: View parsing statistics and TOC distribution

### 3. Search & Export
- Use the search box to find specific content
- Export data as JSON files for further analysis
- Clear data when needed

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change port in run.py or use different port
   uvicorn app:app --port 8001
   ```

2. **PDF Parsing Errors**
   - Ensure PDF is not corrupted
   - Check if PDF has text content (not just images)
   - Verify PDF is a valid USB PD specification document

3. **Template Errors**
   - Ensure all template files are in the `templates/` folder
   - Check file permissions
   - Verify Jinja2 is installed

### Dependencies Issues
```bash
# Reinstall requirements
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## 🎨 Customization

### Styling
- Modify `templates/style.css` for custom colors and layouts
- Update gradient backgrounds in CSS variables
- Adjust responsive breakpoints as needed

### Functionality
- Add new API endpoints in `app.py`
- Extend search capabilities in the JavaScript
- Modify PDF parsing logic in `main.py`

## 📊 Data Format

### TOC Entry Structure
```json
{
  "doc_title": "USB Power Delivery Specification",
  "section_id": "1.2.3",
  "title": "Power Negotiation",
  "page": 45,
  "level": 3,
  "parent_id": "1.2",
  "full_path": "1.2.3 Power Negotiation",
  "tags": ["power", "negotiation"]
}
```

### Section Structure
```json
{
  "doc_title": "USB Power Delivery Specification",
  "section_id": "1.2.3",
  "title": "Power Negotiation",
  "page": 45,
  "content": "Power negotiation is the process...",
  "tables": null,
  "figures": null
}
```

## 🔒 Security Notes

- The application runs on localhost by default
- File uploads are temporarily stored and cleaned up
- No authentication is implemented (add if needed for production)
- CORS is enabled for all origins (restrict for production)

## 🚀 Production Deployment

For production use:
1. Set `host="0.0.0.0"` for external access
2. Add authentication and authorization
3. Implement proper file storage (S3, etc.)
4. Add logging and monitoring
5. Use HTTPS with proper certificates
6. Restrict CORS origins
7. Add rate limiting

## 📝 License

This project is part of the USB Power Delivery specification analysis toolkit.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Happy Parsing! 🎉**
