#!/usr/bin/env python3
"""
Inspect ChromaDB embeddings to check if they're zeros
"""
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection("tier0_goals_okrs")

# Get first 5 documents with embeddings
results = collection.get(
    limit=5,
    include=["documents", "embeddings"]
)

print("=" * 80)
print("📊 Embedding Inspection")
print("=" * 80)

for i, (doc, embedding) in enumerate(zip(results['documents'], results['embeddings']), 1):
    print(f"\n[{i}] Document: {doc[:100]}...")
    
    if embedding is not None and len(embedding) > 0:
        # Check if all zeros
        non_zero = sum(1 for x in embedding if x != 0.0)
        total = len(embedding)
        
        print(f"    Embedding dim: {total}")
        print(f"    Non-zero values: {non_zero}/{total}")
        print(f"    First 10 values: {embedding[:10]}")
        print(f"    Sum: {sum(embedding):.4f}")
        
        if non_zero == 0:
            print(f"    ⚠️  WARNING: All zeros!")
        elif non_zero < total * 0.1:
            print(f"    ⚠️  WARNING: Mostly zeros ({non_zero/total*100:.1f}% non-zero)")
        else:
            print(f"    ✅ Valid embedding ({non_zero/total*100:.1f}% non-zero)")
    else:
        print(f"    ❌ No embedding!")

print("\n" + "=" * 80)
