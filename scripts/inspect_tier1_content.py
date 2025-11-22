#!/usr/bin/env python3
"""
Inspect tier1 collection content to debug why it's empty
"""

import chromadb
from chromadb.config import Settings

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=False,
        is_persistent=True,
    ),
)

# Get tier1 collection
try:
    tier1_collection = chroma_client.get_collection(name="tier1_memories")
    print(f"✅ Found tier1_memories collection")
    print(f"📄 Document count: {tier1_collection.count()}")
    
    # Get first 5 documents to inspect
    results = tier1_collection.get(limit=5, include=["documents", "metadatas", "embeddings"])
    
    print(f"\n🔍 First 5 documents:")
    print(f"   IDs: {results['ids'][:5]}")
    print(f"   Documents (content):")
    for i, doc in enumerate(results["documents"][:5]):
        if doc:
            print(f"      [{i}] {doc[:100]}..." if len(doc) > 100 else f"      [{i}] {doc}")
        else:
            print(f"      [{i}] ❌ EMPTY or None")
    
    print(f"\n   Metadatas:")
    for i, meta in enumerate(results["metadatas"][:5]):
        print(f"      [{i}] {meta}")
    
    print(f"\n   Embeddings:")
    for i, emb in enumerate(results["embeddings"][:5]):
        if emb:
            print(f"      [{i}] ✅ Has embedding (dim: {len(emb)})")
        else:
            print(f"      [{i}] ❌ No embedding")
    
    # Check if any documents have content
    all_results = tier1_collection.get(include=["documents"])
    docs_with_content = [d for d in all_results["documents"] if d and d.strip()]
    print(f"\n📊 Summary:")
    print(f"   Total documents: {len(all_results['documents'])}")
    print(f"   Documents with content: {len(docs_with_content)}")
    print(f"   Documents WITHOUT content: {len(all_results['documents']) - len(docs_with_content)}")
    
except Exception as e:
    print(f"❌ Error: {e}")

