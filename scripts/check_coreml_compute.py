#!/usr/bin/env python3
"""
Check which compute unit CoreML is actually using (ANE/GPU/CPU)
"""
import sys
import os
import time
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
print("🔍 COREML COMPUTE UNIT VERIFICATION")
print("=" * 80)

# Initialize client
api_key = os.environ.get('PAPR_MEMORY_API_KEY')
client = Papr(x_api_key=api_key)

# Force sync to load model and ChromaDB
print("\n📡 Loading CoreML model and ChromaDB...")
import time
time.sleep(2)  # Let background init complete

# Verify ChromaDB is initialized
if not hasattr(client.memory, '_collection') or client.memory._collection is None:
    print("⚠️  ChromaDB not initialized yet, waiting...")
    time.sleep(5)

print("✅ Model loaded and ready")

# Run 5 test queries with timing (use local embedder directly)
test_queries = [
    "test query 1",
    "test query 2",
    "test query 3",
    "test query 4",
    "test query 5"
]

print("\n⏱️  Running 5 test embedding generations to measure latency...\n")

# Get the local embedder directly
embedder = client.memory._get_local_embedder()
if embedder is None:
    print("❌ Local embedder not available!")
    print("   On-device processing may not be enabled")
    sys.exit(1)

latencies = []
for i, query in enumerate(test_queries, 1):
    start = time.perf_counter()
    # Generate embedding directly
    if hasattr(embedder, 'encode'):
        embedding = embedder.encode([query])[0]
    else:
        print("❌ Embedder doesn't support encode!")
        sys.exit(1)
    latency = (time.perf_counter() - start) * 1000
    latencies.append(latency)
    print(f"  [{i}] {latency:.1f}ms")

avg_latency = sum(latencies) / len(latencies)
min_latency = min(latencies)
max_latency = max(latencies)

print(f"\n📊 Results:")
print(f"   Average: {avg_latency:.1f}ms")
print(f"   Min: {min_latency:.1f}ms")
print(f"   Max: {max_latency:.1f}ms")

# Determine compute unit based on latency
print(f"\n🤖 Compute Unit Analysis:")
if avg_latency < 150:
    print(f"   ✅ Using ANE (Neural Engine) - Optimal!")
    print(f"   Expected: 50-100ms, Got: {avg_latency:.1f}ms")
elif avg_latency < 800:
    print(f"   ⚠️  Using GPU - Suboptimal")
    print(f"   Expected ANE: 50-100ms, Got: {avg_latency:.1f}ms")
    print(f"   Potential causes:")
    print(f"   • Thermal throttling")
    print(f"   • ANE compilation not complete")
    print(f"   • macOS security restrictions")
    print(f"   • First-time model loading still warming up")
else:
    print(f"   ❌ Using CPU - Very slow!")
    print(f"   Expected ANE: 50-100ms, Got: {avg_latency:.1f}ms")
    print(f"   Check disk space and memory availability")

print("\n💡 Recommendations:")
if avg_latency > 150:
    print("   1. Restart the server and try again (sometimes helps)")
    print("   2. Let the system warm up - run a few more queries")
    print("   3. Check Activity Monitor for 'kernel_task' CPU usage (thermal throttling)")
    print("   4. Consider using API backend if latency doesn't improve:")
    print("      Set PAPR_ONDEVICE_PROCESSING=false in .env")

print("\n" + "=" * 80)

