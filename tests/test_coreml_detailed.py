#!/usr/bin/env python3
"""
Detailed test to measure CoreML performance with multiple runs
"""

import os
import sys
import time
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

    # Try multiple searches to see if performance improves after warm-up
    print("\n" + "="*60)
    print("Running 5 consecutive searches to measure performance...")
    print("="*60)

    test_queries = [
        "test query 1",
        "product development",
        "customer feedback",
        "technical documentation",
        "project goals"
    ]

    timings = []

    for i, query in enumerate(test_queries, 1):
        print(f"\nSearch {i}/5: '{query}'")
        start_time = time.perf_counter()

        response = client.memory.search(
            query=query,
            max_memories=5,
            max_nodes=10,
            enable_agentic_graph=False,
            timeout=180.0
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        timings.append(elapsed_ms)

        print(f"  Total search time: {elapsed_ms:.1f}ms")
        print(f"  Found {len(response.data.memories) if response and response.data else 0} memories")

    print("\n" + "="*60)
    print("Performance Summary:")
    print("="*60)
    print(f"First search:  {timings[0]:.1f}ms  (may include warm-up)")
    print(f"Second search: {timings[1]:.1f}ms")
    print(f"Third search:  {timings[2]:.1f}ms")
    print(f"Fourth search: {timings[3]:.1f}ms")
    print(f"Fifth search:  {timings[4]:.1f}ms")
    print(f"\nAverage (excluding first): {sum(timings[1:])/4:.1f}ms")
    print(f"Minimum: {min(timings):.1f}ms")
    print(f"Maximum: {max(timings):.1f}ms")

    if min(timings[1:]) < 100:
        print("\n✓ CoreML Neural Engine is working at expected speed!")
    else:
        print("\n✗ Performance is slower than expected (should be <100ms)")
        print("  Expected: ~72ms with Neural Engine")
        print(f"  Actual: {min(timings[1:]):.1f}ms")

except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
