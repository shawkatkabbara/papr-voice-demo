#!/usr/bin/env python3
"""
Inspect ChromaDB collection contents to debug "Content: None" issue
"""
import chromadb
from chromadb.config import Settings
import json

# Connect to the persistent ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

print("=" * 80)
print("📊 ChromaDB Collection Inspector")
print("=" * 80)

try:
    # Get the collection
    collection = client.get_collection("tier0_goals_okrs")

    print(f"\n✅ Collection found: {collection.name}")
    print(f"📝 Total documents: {collection.count()}")

    # Get all documents (limit to first 10 for inspection)
    results = collection.get(
        limit=10,
        include=["documents", "metadatas", "embeddings"]
    )

    print(f"\n📋 First 10 Documents:")
    print("=" * 80)

    for i, (doc_id, document, metadata) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ), 1):
        print(f"\n[{i}] ID: {doc_id[:50]}...")
        print(f"    Document (first 200 chars): {document[:200] if document else 'None'}")
        print(f"    Metadata keys: {list(metadata.keys()) if metadata else 'None'}")

        # Check if content is in metadata
        if metadata:
            if 'content' in metadata:
                print(f"    Metadata.content (first 200 chars): {str(metadata['content'])[:200]}")
            if 'summary' in metadata:
                print(f"    Metadata.summary: {metadata.get('summary', 'N/A')[:100]}")
            if 'topics' in metadata:
                print(f"    Metadata.topics: {metadata.get('topics', 'N/A')}")

    print("\n" + "=" * 80)

    # Check embedding dimension
    if results['embeddings'] and len(results['embeddings']) > 0:
        embedding_dim = len(results['embeddings'][0])
        print(f"\n✅ Embedding dimension: {embedding_dim}")

    # Query test
    print("\n🔍 Testing query search...")
    query_results = collection.query(
        query_texts=["Brian CTO DialPad"],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n📊 Query Results (top 5):")
    print("=" * 80)

    for i, (doc, metadata, distance) in enumerate(zip(
        query_results['documents'][0],
        query_results['metadatas'][0],
        query_results['distances'][0]
    ), 1):
        similarity = 1.0 - distance
        print(f"\n[{i}] Similarity: {similarity:.4f} (distance: {distance:.4f})")
        print(f"    Document: {doc[:200] if doc else 'None'}")
        if metadata and 'content' in metadata:
            print(f"    Metadata.content: {str(metadata['content'])[:200]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
