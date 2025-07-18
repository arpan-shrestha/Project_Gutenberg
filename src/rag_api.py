import os
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from chromadb import PersistentClient
from langchain_ollama import OllamaEmbeddings, OllamaLLM

#configure
base_dir = Path(__file__).resolve().parent.parent
ollama_llm = os.getenv("ollama_llm","mistral")
ollama_embed_model = os.getenv("ollama_embed_model", "nomic-embed-text")
chroma_path= os.getenv("chroma_path", str(base_dir/"chroma_db"))
chroma_collection = os.getenv("chroma_collection", "gutenberg_chunks")
rag_default_k = int(os.getenv("rag_default_k","5"))
rag_max_context_chars = int(os.getenv("rag_max_context_chars","6000"))

chroma_client = PersistentClient(path=chroma_path)
collection = chroma_client.get_or_create_collection(name=chroma_collection)
embed_model = OllamaEmbeddings(model=ollama_embed_model)
llm = OllamaLLM(model=ollama_llm, temperature=0.0)

class SourceChunk(BaseModel):
    chunk_id:str
    book_id:str
    title: Optional[str] = None
    text_snippet: str

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]

def retrieve(question: str, k: int)-> List[SourceChunk]:
    emb = embed_model.embed_query(question)
    results = collection.query(
        query_embeddings=[emb],
        n_results=k,
        include=["documents","metadatas"]
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    chunks: List[SourceChunk]= []
    for doc_text, meta in zip(docs,metas):
        snippet = doc_text[:300].replace("\n"," ").strip()
        chunks.append(SourceChunk(
            chunk_id=meta.get("chunk_id",""),
            book_id=meta.get("book_id",""),
            title=meta.get("title",""),
            text_snippet=snippet
        ))
    return chunks

prompt = (
    "You are a helpful assistant. Use the provided context to answer the question. "
    "If the answer cannot be found in the context, say 'I don't know based on the given information.'"
)

def build_prompt(question: str, chunks: List[SourceChunk]) -> str:
    context_blocks = []
    total_chars = 0
    for c in chunks:
        block = f"[{c.title or c.book_id} | {c.chunk_id}]\n{c.text_snippet}\n"
        if total_chars + len(block) > rag_max_context_chars:
            break
        context_blocks.append(block)
        total_chars += len(block)

    context_text = "\n---\n".join(context_blocks)
    return f"{prompt}\n\nContext:\n{context_text}\n\nQuestion: {question}\nAnswer:"

def answer_question(question: str, k: int) -> AskResponse:
    chunks = retrieve(question, k)
    if not chunks:
        raise HTTPException(status_code=404, detail="No context available.")
    prompt = build_prompt(question, chunks)
    llm_response = llm.invoke(prompt)
    return AskResponse(question=question, answer=llm_response, sources=chunks)

app = FastAPI(title="GutenRAG (Mistral)")

@app.get("/ask", response_model=AskResponse)
def ask(question: str = Query(..., description="Your question"),
        k: int = Query(rag_default_k, ge=1,le=20, description="Number of Context chunks")):
    return answer_question(question,k)

@app.get("/health")
def health():
    return {"status": "ok"}

