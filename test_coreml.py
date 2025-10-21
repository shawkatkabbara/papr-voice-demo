#!/usr/bin/env python3
"""
Test script to verify CoreML is loading properly with papr-pythonSDK
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add papr-pythonSDK to path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

try:
    from papr_memory import Papr

    print("✓ Successfully imported Papr")

    # Initialize Papr client
    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")

    client = Papr(x_api_key=api_key, base_url=base_url, timeout=120.0)

    print("✓ Papr client initialized")

    # Try a simple search to trigger model loading
    print("\nAttempting to search memories (this will trigger CoreML model loading)...")

    response = client.memory.search(
        query="test query",
        max_memories=5,
        max_nodes=10,
        enable_agentic_graph=False,
        timeout=180.0
    )

    print(f"✓ Search completed successfully!")
    print(f"  Found {len(response.data.memories) if response and response.data else 0} memories")

    print("\n✓ CoreML is working properly!")

except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
