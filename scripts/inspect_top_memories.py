#!/usr/bin/env python3
"""
Inspect top 20 memories from ChromaDB with full content and metadata
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
print("📊 Top 20 Memories from ChromaDB (synced from tier0)")
print("=" * 100)

try:
    # Get the collection
    collection = client.get_collection("tier0_goals_okrs")

    print(f"\n✅ Collection: {collection.name}")
    print(f"📝 Total documents: {collection.count()}")

    # Get first 20 documents with ALL data
    results = collection.get(
        limit=20,
        include=["documents", "metadatas", "embeddings"]
    )

    output_lines = []
    output_lines.append("=" * 100)
    output_lines.append(f"TOP 20 MEMORIES FROM CHROMADB")
    output_lines.append(f"Total in collection: {collection.count()}")
    output_lines.append("=" * 100)

    for i, (doc_id, document, metadata, embedding) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas'],
        results['embeddings']
    ), 1):
        output_lines.append(f"\n{'#' * 100}")
        output_lines.append(f"MEMORY [{i}]")
        output_lines.append(f"{'#' * 100}")

        output_lines.append(f"\n🔑 ID: {doc_id}")

        # Document field (this is the main content in ChromaDB)
        output_lines.append(f"\n📄 CONTENT (ChromaDB document field):")
        if document:
            # Wrap long content
            content_str = str(document)
            if len(content_str) > 500:
                output_lines.append(f"   {content_str[:500]}...")
                output_lines.append(f"   [Content length: {len(content_str)} characters]")
            else:
                output_lines.append(f"   {content_str}")
        else:
            output_lines.append("   (No content)")

        # Metadata fields
        output_lines.append(f"\n📊 METADATA:")
        if metadata:
            # Display key fields first (if present), then rest sorted
            key_fields = ['id', 'source', 'tier', 'type', 'topics', 'tags', 'updatedAt', 'similarity_score', 'relevance_score']
            displayed_keys = set()
            
            # First, display key fields in order
            for key in key_fields:
                if key in metadata:
                    value_str = str(metadata[key])
                    if len(value_str) > 300:
                        value_str = value_str[:300] + "... (truncated)"
                    output_lines.append(f"   {key}: {value_str}")
                    displayed_keys.add(key)
            
            # Then display any remaining metadata fields sorted
            for key, value in sorted(metadata.items()):
                if key not in displayed_keys:
                    value_str = str(value)
                    if len(value_str) > 300:
                        value_str = value_str[:300] + "... (truncated)"
                    output_lines.append(f"   {key}: {value_str}")
        else:
            output_lines.append("   (No metadata)")

        # Embedding info
        output_lines.append(f"\n🧮 EMBEDDING:")
        if embedding is not None and len(embedding) > 0:
            non_zero = sum(1 for x in embedding if x != 0.0)
            total = len(embedding)
            output_lines.append(f"   Dimension: {total}")
            output_lines.append(f"   Non-zero values: {non_zero}/{total} ({non_zero/total*100:.1f}%)")
            output_lines.append(f"   First 10 values: {embedding[:10]}")
            if non_zero == 0:
                output_lines.append(f"   ⚠️  WARNING: All zeros!")
        else:
            output_lines.append("   (No embedding)")

    output_lines.append(f"\n{'=' * 100}")
    output_lines.append("✅ Inspection complete!")
    output_lines.append(f"{'=' * 100}")

    # Write to file
    output_file = "chromadb_top_20_memories.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n✅ Wrote detailed inspection to: {output_file}")
    print(f"📄 File contains {len(output_lines)} lines")

    # Also print summary to console
    print(f"\n📊 SUMMARY:")
    print(f"   Total memories in ChromaDB: {collection.count()}")
    print(f"   Inspected: 20 memories")
    print(f"   Output saved to: {output_file}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
