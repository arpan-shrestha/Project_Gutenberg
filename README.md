# GutenRAG: Data-Scrape-to-RAG Pipeline on Project Gutenberg

GutenRAG is a mini end-to-end **"Data-Scrape-to-RAG" lakehouse** system built on public Project Gutenberg texts. It implements a Bronze-Silver-Gold ETL flow, generates embeddings with **Ollama (Mistral)**, and serves responses through a **FastAPI RAG API**

---
## Features

1. **Scraper** : Downloads raw HTML and extracts text from Project Gutenberg books.
2. **Data Lakehouse** : Organizes data into bronze, silver, and gold layers which are stored on MinIO (S3-compatible).
3. **Embedding**: Generates document embeddings using Ollama's `nomic-embed-text` (768-dim) embedding model.
4. **Vector Search**: Stores embeddings in ChromaDB for similarity search.
5. **RAG API**: FastAPI server with `/ask` endpoint to query the knowledge base using **Mistral LLM** from **Ollama**.
6. Dockerized MinIO for object storage.

---
## Project Structure
``` 
├── data/
│   ├── raw/ #Raw HTML
│   ├── bronze/ #Cleaned text
│   ├── silver/ #Normalize text, Remove duplicates
│   └── gold/ #Final chunked parquet files
├── src/
│   ├── scrape.py #Scrape 50-100 pages of Project Gutenberg
│   ├── extract_text.py #Clean and transform to Bronze/Silver
│   ├── gold_chunks.py #Chunking for Gold layer
│   ├── embed_chunks.py #Embedding generation and Chroma DB insert
│   └── rag_api.py #FastAPI RAG endpoint
├── docker-compose.yaml #MinIO service
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone and Install

```bash
git clone https://github.com/arpan-shrestha/
cd Project_Gutenberg
python -m venv env && source env/bin/activate
pip install -r requirements.txt
```
---
### 2. Start Ollama with Mistral
```bash
ollama run mistral
```
- Make sure that Ollama is installed and Mistral is pulled
---
### 3. Run MinIO (if not running)
```bash
docker compose up -d minio
```
Access MinIO Console at http://localhost:9001
Login: admin / password123

---
### 4. Run the Data Pipeline
- step 1: Scrape Gutenberg
  ```bash
      python src/scrape.py
  ```
- step 2: Extract and Transform (Bronze/Silver)
  ```bash
      python src/extract_text.py
  ```
- step 3: Create Golf Layer (Chunks)
   ```bash
      python src/gold_chunks.py
  ```
- step 4: Generate Embeddings and Load in Chroma
  ```bash
      python src/embed_chunks.py
  ```
---

### 5. Start the API server
```bash
uvicorn src.rag_api:app --reload --port 8000
```
---
### 6. Ask a question
```bash
curl "http://localhost:8000/ask?question=Who is Alice?"
```
---
### 7. Response
```json
{
  "question": "Who is Alice?",
  "answer": "Alice is the main character in the story...",
  "sources": [
    {
      "chunk_id": "book_1_chunk_42",
      "book_id": "alice_in_wonderland",
      "title": "Alice's Adventures in Wonderland",
      "text_snippet": "Alice was beginning to get very tired of sitting..."
    }
  ]
}
```
---
