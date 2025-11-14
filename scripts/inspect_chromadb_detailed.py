#!/usr/bin/env python3
"""
Detailed ChromaDB inspection - shows ALL fields and metadata
"""
import chromadb
from chromadb.config import Settings
import json

# Connect to the persistent ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

print("=" * 100)
print("📊 DETAILED ChromaDB Collection Inspector")
print("=" * 100)

try:
    # Get the collection
    collection = client.get_collection("tier0_goals_okrs")

    print(f"\n✅ Collection: {collection.name}")
    print(f"📝 Total documents: {collection.count()}")

    # Get first 3 documents with ALL data
    results = collection.get(
        limit=3,
        include=["documents", "metadatas", "embeddings"]
    )

    print(f"\n📋 Detailed Inspection of First 3 Documents:")
    print("=" * 100)

    for i, (doc_id, document, metadata, embedding) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas'],
        results['embeddings']
    ), 1):
        print(f"\n{'#' * 100}")
        print(f"DOCUMENT [{i}]")
        print(f"{'#' * 100}")

        print(f"\n🔑 ID: {doc_id}")

        print(f"\n📄 DOCUMENT FIELD (ChromaDB's 'documents'):")
        print(f"   Type: {type(document)}")
        print(f"   Length: {len(document) if document else 0}")
        print(f"   Value: {repr(document)[:500]}")

        print(f"\n📊 METADATA FIELDS:")
        if metadata:
            for key, value in metadata.items():
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "... (truncated)"
                print(f"   - {key}: {repr(value_str)}")
        else:
            print("   (No metadata)")

        print(f"\n🧮 EMBEDDING:")
        print(f"   Dimension: {len(embedding) if embedding else 0}")
        print(f"   First 10 values: {embedding[:10] if embedding else 'None'}")

    print(f"\n{'=' * 100}")

    # Now test a query to see what gets returned
    print(f"\n🔍 QUERY TEST: 'Brian CTO DialPad'")
    print("=" * 100)

    query_results = collection.query(
        query_texts=["Brian CTO DialPad"],
        n_results=2,
        include=["documents", "metadatas", "distances"]
    )

    for i, (doc, metadata, distance) in enumerate(zip(
        query_results['documents'][0],
        query_results['metadatas'][0],
        query_results['distances'][0]
    ), 1):
        similarity = 1.0 - distance
        print(f"\n[{i}] Similarity: {similarity:.4f}")
        print(f"    Document field: {repr(doc)[:200]}")

        if metadata:
            print(f"    Metadata keys: {list(metadata.keys())}")
            if 'content' in metadata:
                content_str = str(metadata['content'])
                print(f"    Metadata['content']: {repr(content_str)[:200]}")
            if 'summary' in metadata:
                print(f"    Metadata['summary']: {metadata.get('summary', 'N/A')[:100]}")

    print(f"\n{'=' * 100}")
    print("✅ Inspection complete!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
