import os
import chromadb
from sentence_transformers import SentenceTransformer

# -----------------------------
# 1. Initialize Chroma client
# -----------------------------
client = chromadb.PersistentClient(path="./chroma_db")

# Create or load collection
collection = client.get_or_create_collection(
    name="structured_data",
    metadata={"hnsw:space": "cosine"}
)

# -----------------------------
# 2. Load embedding model
# -----------------------------
embedder = SentenceTransformer("intfloat/e5-small-v2")

# -----------------------------
# 3. Read all .txt files
# -----------------------------
folder = "./Structured_Data"

files = [f for f in os.listdir(folder) if f.endswith(".txt")]

if not files:
    print("❌ No .txt files found in Structured_Data folder.")
    exit()

print(f"📁 Found {len(files)} files. Starting embedding...\n")

for idx, filename in enumerate(files):
    filepath = os.path.join(folder, filename)

    # Read file content (UTF-8 now)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print(f"⚠️ Skipped empty file: {filename}")
        continue

    # Create embedding
    embedding = embedder.encode(content).tolist()

    doc_id = f"doc_{idx}"  # unique id

    # Store in Chroma
    collection.add(
        ids=[doc_id],
        documents=[content],
        embeddings=[embedding],
        metadatas=[{"filename": filename}]
    )

    print(f"✅ Added → {filename}")

print("\n🎉 All structured data embedded and added to ChromaDB successfully!")
