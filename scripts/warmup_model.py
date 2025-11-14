#!/usr/bin/env python3
"""
Warm up CoreML model before starting the server
This ensures the model is loaded and ready for fast searches
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment from project root
# Get the directory where this script is located, then go up one level to project root
script_dir = Path(__file__).parent
project_root = script_dir.parent
load_dotenv(dotenv_path=project_root / ".env")

# Add papr-pythonSDK to path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

print("🔥 Warming up CoreML model...")
print("⏳ This will take 1-2 minutes on first run...\n")

try:
    from papr_memory import Papr

    # Initialize client
    papr_client = Papr(
        x_api_key=os.environ.get("PAPR_MEMORY_API_KEY"),
        base_url=os.environ.get("PAPR_BASE_URL", "https://memory.papr.ai"),
        timeout=180.0
    )

    print("✅ PAPR client initialized\n")

    # Do a warmup search to load the model
    print("🔍 Running warmup search to load CoreML model...")
    response = papr_client.memory.search(
        query="test warmup",
        max_memories=10,
        timeout=180.0
    )

    print("✅ CoreML model loaded and ready!")
    print(f"✅ Warmup search completed: {len(response.data.memories) if response and response.data else 0} results\n")
    print("🚀 Model is now cached in memory - all future searches will be fast!\n")

except Exception as e:
    print(f"❌ Warmup failed: {e}")
    print("⚠️  Server will still start, but first search will be slow\n")
    sys.exit(1)

print("✅ Warmup complete! You can now start the server.")
