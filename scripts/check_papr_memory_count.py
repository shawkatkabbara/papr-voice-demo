#!/usr/bin/env python3
"""
Check how many memories exist in PAPR Cloud account
"""
import sys
import os
from pathlib import Path

# Add local SDK path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    
project_root = Path(__file__).parent.parent
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")

from papr_memory import Papr

print("\n" + "=" * 80)
print("📊 PAPR CLOUD MEMORY COUNT CHECK")
print("=" * 80)

# Initialize client
api_key = os.environ.get('PAPR_MEMORY_API_KEY')
if not api_key:
    print("❌ PAPR_MEMORY_API_KEY not found!")
    sys.exit(1)

print(f"\n🔑 API Key: {api_key[:20]}...")

client = Papr(x_api_key=api_key)

# Try different sync limits to see what's available
print("\n🔍 Checking memory counts in PAPR Cloud...\n")

for max_count in [5, 10, 20, 50, 100, 200]:
    try:
        result = client.memory.sync_tiers(
            include_embeddings=False,  # Don't need embeddings, just count
            max_tier0=max_count,
            max_tier1=0,
            embed_limit=0
        )
        
        # Handle different response structures (local SDK vs PyPI)
        memories = []
        if hasattr(result, 'data') and result.data:
            memories = result.data.memories if hasattr(result.data, 'memories') else []
        elif hasattr(result, 'memories'):
            memories = result.memories
        elif isinstance(result, list):
            memories = result
        
        if memories:
            count = len(memories)
            if count < max_count:
                print(f"   Requested {max_count}, Got {count} ← **This is your total**")
                break
            else:
                print(f"   Requested {max_count}, Got {count}")
        else:
            print(f"   Requested {max_count}, Got 0")
            break
    except Exception as e:
        print(f"   Error at {max_count}: {e}")
        break

print("\n📋 Current Memories in PAPR Cloud:")

# Handle different response structures
memories = []
if hasattr(result, 'data') and result.data:
    memories = result.data.memories if hasattr(result.data, 'memories') else []
elif hasattr(result, 'memories'):
    memories = result.memories
elif isinstance(result, list):
    memories = result

if memories:
    print(f"\n   Total: {len(memories)} memories")
    print(f"\n   First 3 memory previews:")
    for i, mem in enumerate(memories[:3], 1):
        content = getattr(mem, 'content', 'N/A')
        if isinstance(mem, dict):
            content = mem.get('content', 'N/A')
        preview = content[:80] if content else "(No content)"
        print(f"   [{i}] {preview}...")
else:
    print("   No memories found!")

print("\n💡 To add more memories:")
print("   1. Use the PAPR web dashboard to upload memories")
print("   2. Use the PAPR API to programmatically add memories:")
print("      client.memory.create(content='Your memory text here')")
print("   3. Import from existing data sources")

print("\n" + "=" * 80)

