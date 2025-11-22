#!/usr/bin/env python3
"""
Fix tier1 ChromaDB collection dimension mismatch.
The tier1 collection was created with 384-dim embeddings (default sentence-transformers)
but should use 2560-dim embeddings (Qwen3-4B) like tier0.
"""

import chromadb
from pathlib import Path

def fix_tier1_collection():
    """Delete tier1 collection so it can be recreated with correct dimensions"""
    
    # Path to ChromaDB
    project_root = Path(__file__).parent.parent
    chroma_path = project_root / "chroma_db"
    
    print("=" * 80)
    print("🔧 Fixing tier1 Collection Dimension Mismatch")
    print("=" * 80)
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=str(chroma_path))
        
        # List all collections
        collections = client.list_collections()
        print(f"\n📊 Found {len(collections)} collections:")
        for coll in collections:
            count = coll.count()
            print(f"   - {coll.name}: {count} documents")
        
        # Check if tier1_memories exists
        tier1_exists = any(c.name == "tier1_memories" for c in collections)
        
        if tier1_exists:
            tier1_coll = client.get_collection("tier1_memories")
            tier1_count = tier1_coll.count()
            
            # Get sample to check dimension
            if tier1_count > 0:
                sample = tier1_coll.get(limit=1, include=["embeddings"])
                embeddings = sample.get("embeddings") if sample else None
                if embeddings is not None and len(embeddings) > 0:
                    actual_dim = len(embeddings[0])
                    print(f"\n⚠️  Tier1 collection has {actual_dim}-dimensional embeddings")
                    print(f"   Expected: 2560 dimensions (Qwen3-4B)")
                    print(f"   Actual: {actual_dim} dimensions (wrong!)")
                else:
                    print(f"\n✅ Tier1 collection exists but has no embeddings")
                    actual_dim = None
            else:
                print(f"\n✅ Tier1 collection exists but is empty")
                actual_dim = None
            
            # Delete the collection
            print(f"\n🗑️  Deleting tier1_memories collection...")
            client.delete_collection("tier1_memories")
            print(f"✅ Deleted tier1_memories")
            print(f"\n💡 The collection will be recreated with correct dimensions (2560)")
            print(f"   when you next run voice_server.py with PAPR_MAX_TIER1 > 0")
            
        else:
            print(f"\n✅ Tier1 collection doesn't exist yet (will be created correctly)")
        
        print("\n" + "=" * 80)
        print("✅ Fix complete! Restart voice_server.py to recreate tier1 with correct dimensions")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    fix_tier1_collection()

