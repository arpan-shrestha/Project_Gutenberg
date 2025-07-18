from chromadb.config import Settings
from chromadb import PersistentClient

client = PersistentClient(path="chroma_db")
collection = client.get_collection("gutenberg_chunks")
print(collection.count())