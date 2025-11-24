#!/usr/bin/env python3
"""
Inspect tier1 memories stored in ChromaDB to verify content is being stored correctly.
"""

import chromadb
import numpy as np
from pathlib import Path

# ChromaDB location
CHROMA_DB_PATH = "./chroma_db"

def main():
    """Inspect tier1 memories from ChromaDB"""
    
    print("=" * 100)
    print("📊 Inspecting Tier1 Memories from ChromaDB")
    print("=" * 100)
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        # Get tier1 collection
        collection = client.get_collection(name="tier1_memories")
        
        # Get collection info
        count = collection.count()
        print(f"\n✅ Collection: tier1_memories")
        print(f"📝 Total documents: {count}")
        
        if count == 0:
            print("\n❌ Collection is empty!")
            return
        
        # Get first 20 items
        num_to_inspect = min(20, count)
        results = collection.get(
            limit=num_to_inspect,
            include=["documents", "metadatas", "embeddings"]
        )
        
        print(f"\n🔍 Inspecting first {num_to_inspect} memories...")
        print("=" * 100)
        
        output_lines = []
        output_lines.append("=" * 100)
        output_lines.append("TIER1 MEMORIES FROM CHROMADB")
        output_lines.append(f"Total in collection: {count}")
        output_lines.append("=" * 100)
        output_lines.append("")
        
        for i in range(len(results["ids"])):
            memory_id = results["ids"][i]
            document = results["documents"][i] if results.get("documents") else None
            metadata = results["metadatas"][i] if results.get("metadatas") else {}
            embedding = results["embeddings"][i] if results.get("embeddings") is not None else None
            
            print(f"\n{'#' * 100}")
            print(f"TIER1 MEMORY [{i+1}]")
            print(f"{'#' * 100}")
            
            output_lines.append("#" * 100)
            output_lines.append(f"TIER1 MEMORY [{i+1}]")
            output_lines.append("#" * 100)
            output_lines.append("")
            
            # ID
            print(f"\n🔑 ID: {memory_id}")
            output_lines.append(f"🔑 ID: {memory_id}")
            output_lines.append("")
            
            # Document content
            print(f"\n📄 CONTENT (ChromaDB document field):")
            output_lines.append("📄 CONTENT (ChromaDB document field):")
            
            if document:
                content_preview = document[:500] if len(document) > 500 else document
                print(f"   {content_preview}")
                if len(document) > 500:
                    print(f"   [Content length: {len(document)} characters]")
                
                output_lines.append(f"   {content_preview}")
                if len(document) > 500:
                    output_lines.append(f"   [Content length: {len(document)} characters]")
            else:
                print(f"   ❌ NO CONTENT IN DOCUMENT FIELD!")
                output_lines.append(f"   ❌ NO CONTENT IN DOCUMENT FIELD!")
            
            output_lines.append("")
            
            # Metadata
            print(f"\n📊 METADATA:")
            output_lines.append("📊 METADATA:")
            
            # Display key metadata fields in order
            for key in ['id', 'source', 'tier', 'type', 'topics', 'updatedAt', 'similarity_score', 'relevance_score']:
                if key in metadata:
                    print(f"   {key}: {metadata[key]}")
                    output_lines.append(f"   {key}: {metadata[key]}")
            
            # Check if content is in metadata instead
            if 'content' in metadata:
                print(f"\n⚠️  WARNING: 'content' found in METADATA (should be in document field):")
                print(f"   {metadata['content'][:200]}...")
                output_lines.append("")
                output_lines.append(f"⚠️  WARNING: 'content' found in METADATA (should be in document field):")
                output_lines.append(f"   {metadata['content'][:200]}...")
            
            output_lines.append("")
            
            # Embedding info
            if embedding is not None and len(embedding) > 0:
                embedding_array = np.array(embedding)
                non_zero = np.count_nonzero(embedding_array)
                print(f"\n🧮 EMBEDDING:")
                print(f"   Dimension: {len(embedding)}")
                print(f"   Non-zero values: {non_zero}/{len(embedding)} ({non_zero/len(embedding)*100:.1f}%)")
                print(f"   First 10 values: {embedding_array[:10]}")
                
                output_lines.append("🧮 EMBEDDING:")
                output_lines.append(f"   Dimension: {len(embedding)}")
                output_lines.append(f"   Non-zero values: {non_zero}/{len(embedding)} ({non_zero/len(embedding)*100:.1f}%)")
                output_lines.append(f"   First 10 values: {embedding_array[:10]}")
            else:
                print(f"\n❌ NO EMBEDDING!")
                output_lines.append("")
                output_lines.append("❌ NO EMBEDDING!")
            
            output_lines.append("")
        
        # Write to file
        output_file = "chromadb_tier1_memories.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(output_lines))
        
        print("\n" + "=" * 100)
        print(f"✅ Wrote detailed inspection to: {output_file}")
        print(f"📄 File contains {len(output_lines)} lines")
        print("\n📊 SUMMARY:")
        print(f"   Total tier1 memories in ChromaDB: {count}")
        print(f"   Inspected: {num_to_inspect} memories")
        
        # Count how many have content
        docs_with_content = sum(1 for doc in results["documents"] if doc and doc.strip())
        docs_without_content = num_to_inspect - docs_with_content
        
        print(f"   ✅ With content: {docs_with_content}")
        print(f"   ❌ Without content: {docs_without_content}")
        
        if docs_without_content > 0:
            print(f"\n⚠️  WARNING: {docs_without_content}/{num_to_inspect} memories have NO CONTENT in document field!")
            print("   This is why search returns '(No content)' for those items.")
        
        print(f"   Output saved to: {output_file}")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ Error inspecting tier1 collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

