#!/usr/bin/env python3
"""
Test query embedding generation
"""
import sys
sys.path.insert(0, "/Users/shawkatkabbara/Documents/GitHub/papr-pythonSDK/src")

import os
os.environ["PAPR_MEMORY_API_KEY"] = "YQnxXIZPT0M9JVH3L0S0MNLicDaqJ4Vd"
os.environ["PAPR_ENABLE_COREML"] = "true"
os.environ["PAPR_COREML_MODEL"] = "/Users/shawkatkabbara/Documents/GitHub/papr-pythonSDK/coreml/Qwen3-Embedding-4B-FP16-Final.mlpackage"

from papr_memory import Papr

client = Papr(x_api_key=os.environ["PAPR_MEMORY_API_KEY"])

# Get the local embedder
embedder = client.memory._get_local_embedder()

print("=" * 80)
print("🔍 Query Embedding Test")
print("=" * 80)

query = "test query"
print(f"\nQuery: '{query}'")

# Generate embedding
if hasattr(embedder, 'encode'):
    embedding = embedder.encode([query])[0]
    print(f"Embedding type: {type(embedding)}")
    print(f"Embedding shape: {embedding.shape if hasattr(embedding, 'shape') else len(embedding)}")
    
    emb_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
    non_zero = sum(1 for x in emb_list if x != 0.0)
    total = len(emb_list)
    
    print(f"Non-zero values: {non_zero}/{total} ({non_zero/total*100:.1f}%)")
    print(f"First 10 values: {emb_list[:10]}")
    print(f"Sum: {sum(emb_list):.4f}")
    
    if non_zero == 0:
        print("\n⚠️  WARNING: Query embedding is all zeros!")
    elif non_zero < total * 0.1:
        print(f"\n⚠️  WARNING: Query embedding mostly zeros!")
    else:
        print(f"\n✅ Valid query embedding!")
else:
    print("❌ Embedder doesn't have 'encode' method!")

print("\n" + "=" * 80)
