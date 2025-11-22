#!/usr/bin/env python3
"""
Sync memories from PAPR Cloud to local ChromaDB
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "python"))

from dotenv import load_dotenv

# Load environment with absolute path
load_dotenv(dotenv_path=project_root / ".env")

# Add local SDK path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print(f"✅ Using local PAPR SDK from: {sdk_path}")

from papr_memory import Papr

print("\n" + "=" * 80)
print("🔄 SYNCING MEMORIES FROM PAPR CLOUD")
print("=" * 80)

api_key = os.environ.get('PAPR_MEMORY_API_KEY')
if not api_key:
    print("❌ PAPR_MEMORY_API_KEY not found in environment!")
    sys.exit(1)

print(f"✅ API Key loaded: {api_key[:20]}...")

# Initialize client
client = Papr(x_api_key=api_key, timeout=300.0)
print("✅ PAPR client initialized")

# Sync tier0 memories with embeddings
print("\n🔄 Syncing tier0 memories (max 200)...")
try:
    result = client.memory.sync_tiers(
        include_embeddings=True,
        max_tier0=200,
        max_tier1=0,
        embed_limit=200
    )
    
    if result and result.data and result.data.memories:
        count = len(result.data.memories)
        print(f"✅ Synced {count} memories successfully!")
        
        # Show first 3 memory previews
        print(f"\n📋 First 3 memories:")
        for i, mem in enumerate(result.data.memories[:3], 1):
            content = getattr(mem, 'content', 'N/A')
            preview = content[:100] if content else "(No content)"
            print(f"   [{i}] {preview}...")
    else:
        print("⚠️  No memories returned from sync")
        
except Exception as e:
    print(f"❌ Sync failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ SYNC COMPLETE!")
print("=" * 80)

