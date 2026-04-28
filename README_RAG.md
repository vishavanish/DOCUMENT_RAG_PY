# RAG System Module 2

## Overview
This module implements a complete Retrieval-Augmented Generation (RAG) system integrated with the existing news collection system (Module 1).

## Architecture Components

### Phase 1: Indexing & Preparation
1. **Document Loading** - PDF text extraction using PyPDF2
2. **Text Splitting** - Chunking with overlap for context preservation
3. **Embedding Generation** - Sentence transformers for semantic vectors
4. **Vector Database** - FAISS for efficient similarity search

### Phase 2: Retrieval & Generation
1. **Query Embedding** - Convert user questions to vectors
2. **Semantic Search** - Find most relevant document chunks
3. **Context Assembly** - Combine retrieved chunks
4. **Answer Generation** - LLM-ready response formatting

## API Endpoints

### RAG System
- `POST /upload` - Upload and index PDF documents
- `GET /documents` - List all uploaded documents
- `POST /query` - Query documents using RAG
- `DELETE /documents/<doc_id>` - Delete documents

### News System (Module 1)
- `GET /` - Health check
- `GET /fetch-news` - Manual news fetch
- `GET /articles` - View latest articles
- `GET /init-db` - Initialize all database tables

## Setup & Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Initialize database:**
```bash
curl http://localhost:5001/init-db
```

3. **Start services:**
```bash
./run_services.sh
```

## Usage Examples

### Upload Document
```bash
curl -X POST -F "file=@document.pdf" http://localhost:5001/upload
```

### Query Document
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"document_id":"doc-id","question":"What is this about?"}' \
  http://localhost:5001/query
```

### Web Interface
Visit: `http://localhost:5001/` and open `rag_demo.html`

## File Structure
```
backend/
├── rag_system.py          # Core RAG implementation
├── document_manager.py    # Document lifecycle management
├── app.py                 # Flask app with both modules
├── rag_demo.html         # Web interface
├── test_rag.py           # Testing script
└── uploads/              # Document storage directory
```

## Testing
Run the test script:
```bash
python test_rag.py
```

## Integration Notes
- Both Module 1 (news) and Module 2 (RAG) share the same Flask app
- Database tables are created for both systems
- All services run on the same port (5001)
- Document uploads are stored in `uploads/` directory
- Vector indices are saved for persistence across restarts