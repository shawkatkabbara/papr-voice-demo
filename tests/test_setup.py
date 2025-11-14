#!/usr/bin/env python3
"""Quick test to verify setup is working"""

import sys
import os
from pathlib import Path

print("🧪 Testing PAPR Voice Demo Setup...\n")

# Test 1: Check Python version
print("1️⃣ Python version:", sys.version.split()[0])
if sys.version_info < (3, 8):
    print("   ❌ Python 3.8+ required")
    sys.exit(1)
print("   ✅ Python version OK")

# Test 2: Check .env file
env_file = Path(".env")
if not env_file.exists():
    print("\n2️⃣ .env file: ❌ NOT FOUND")
    print("   Run: cp .env.example .env")
    print("   Then edit .env and add your API keys")
else:
    print("\n2️⃣ .env file: ✅ Found")

    # Load and check environment
    from dotenv import load_dotenv
    load_dotenv()

    # Check API keys
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    papr_key = os.environ.get("PAPR_MEMORY_API_KEY", "")

    if "your_openai_key" in openai_key or not openai_key:
        print("   ⚠️  OPENAI_API_KEY needs to be set")
    else:
        print(f"   ✅ OPENAI_API_KEY set ({openai_key[:8]}...)")

    if "your_papr_key" in papr_key or not papr_key:
        print("   ⚠️  PAPR_MEMORY_API_KEY needs to be set")
    else:
        print(f"   ✅ PAPR_MEMORY_API_KEY set ({papr_key[:8]}...)")

# Test 3: Check papr-pythonSDK
print("\n3️⃣ PAPR Python SDK:")
sdk_path = Path.home() / "Documents/GitHub/papr-pythonSDK/src"
if sdk_path.exists():
    print(f"   ✅ Found at {sdk_path}")
    sys.path.insert(0, str(sdk_path))
else:
    print(f"   ⚠️  Not found at {sdk_path}")
    print("   Will try to use installed package")

try:
    from papr_memory import Papr
    print("   ✅ papr_memory module imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import papr_memory: {e}")
    print("   Install with: pip install papr-memory")

# Test 4: Check CoreML model
print("\n4️⃣ CoreML Model:")
coreml_path = Path.home() / "Documents/GitHub/papr-pythonSDK/coreml/Qwen3-Embedding-4B-FP16-Final.mlpackage"
if coreml_path.exists():
    print(f"   ✅ Found at {coreml_path}")
else:
    print(f"   ⚠️  Not found at {coreml_path}")
    print("   On-device processing may not work")

# Test 5: Check dependencies
print("\n5️⃣ Dependencies:")
required = ["streamlit", "openai", "dotenv", "websockets"]
for pkg in required:
    try:
        if pkg == "dotenv":
            __import__("dotenv")
        else:
            __import__(pkg)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg} not installed")

print("\n" + "="*60)
print("✅ Setup test complete!")
print("\nNext steps:")
print("1. Ensure .env has your API keys")
print("2. Run: ./run.sh")
print("   or: streamlit run app.py")
print("="*60)
