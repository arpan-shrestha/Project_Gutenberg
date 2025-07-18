import pandas as pd
from pathlib import Path
from chromadb.config import Settings
from chromadb import PersistentClient
from langchain_ollama import OllamaEmbeddings

base_dir = Path(__file__).resolve().parent.parent
gold_file = base_dir / "data/gold/gold_chunks.parquet"
chroma_path = base_dir/"chroma_db"

df = pd.read_parquet(gold_file)
print(f"[embed] Loaded {len(df)} chunks from {gold_file}")

client = PersistentClient(path=str(chroma_path))
collection_name = "gutenberg_chunks"
collection = client.get_or_create_collection(name=collection_name)

embed_model = OllamaEmbeddings(model="nomic-embed-text")

ids = df["chunk_id"].tolist()
texts = df["chunk_text"].tolist()
metadatas = df.drop(columns=["chunk_text"]).to_dict(orient="records")

print("[embed] Generating embeddings & inserting into Chroma")
embeddings = embed_model.embed_documents(texts)
print(f"[embed] Embedding dimension: {len(embeddings[0])}")
collection.add(
    ids=ids,
    documents=texts,
    metadatas=metadatas,
    embeddings=embeddings
)
print(f"[embed] Stored {len(ids)} chunks in Chroma at {chroma_path}")