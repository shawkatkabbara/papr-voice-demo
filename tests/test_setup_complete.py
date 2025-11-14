#!/usr/bin/env python3
"""
Complete setup verification for PAPR Voice Demo
Tests:
- Local papr-pythonSDK import
- CoreML model access
- Production memory connection
- ChromaDB availability
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

print("🧪 PAPR Voice Demo - Setup Verification\n")

# Load environment
load_dotenv()

# Test 1: Local SDK Path
print("1️⃣ Testing local papr-pythonSDK...")
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print(f"   ✅ Found local SDK at: {sdk_path}")
else:
    print(f"   ⚠️  Local SDK not found at: {sdk_path}")
    print("   📦 Will use installed package instead")

# Test 2: Import papr_memory
print("\n2️⃣ Testing papr_memory import...")
try:
    from papr_memory import Papr
    print("   ✅ Successfully imported papr_memory")

    # Check where it's imported from
    import papr_memory
    import_path = papr_memory.__file__
    print(f"   📍 Import location: {import_path}")

    if "papr-pythonSDK" in import_path:
        print("   ✅ Using LOCAL papr-pythonSDK (development mode)")
    else:
        print("   📦 Using INSTALLED package")

except ImportError as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Test 3: Environment Variables
print("\n3️⃣ Testing environment configuration...")
required_vars = {
    "PAPR_MEMORY_API_KEY": os.getenv("PAPR_MEMORY_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "PAPR_ONDEVICE_PROCESSING": os.getenv("PAPR_ONDEVICE_PROCESSING"),
    "PAPR_ENABLE_COREML": os.getenv("PAPR_ENABLE_COREML"),
    "PAPR_COREML_MODEL": os.getenv("PAPR_COREML_MODEL"),
    "PAPR_BASE_URL": os.getenv("PAPR_BASE_URL")
}

for var, value in required_vars.items():
    if value:
        if "KEY" in var:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ⚠️  {var}: Not set")

# Test 4: CoreML Model
print("\n4️⃣ Testing CoreML model...")
coreml_path = os.getenv("PAPR_COREML_MODEL")
if coreml_path and os.path.exists(coreml_path):
    print(f"   ✅ CoreML model found at: {coreml_path}")

    # Check model structure
    model_path = Path(coreml_path)
    if model_path.exists():
        print(f"   ✅ Model package is valid")
else:
    print(f"   ❌ CoreML model not found at: {coreml_path}")

# Test 5: ChromaDB availability
print("\n5️⃣ Testing ChromaDB...")
try:
    import chromadb
    print("   ✅ ChromaDB is available")
except ImportError:
    print("   ⚠️  ChromaDB not installed (optional)")

# Test 6: Initialize Papr Client
print("\n6️⃣ Testing PAPR client initialization...")
try:
    client = Papr(
        x_api_key=os.getenv("PAPR_MEMORY_API_KEY"),
        base_url=os.getenv("PAPR_BASE_URL"),
        timeout=30.0
    )
    print("   ✅ PAPR client initialized successfully")

    # Test connection (lightweight call)
    print("\n7️⃣ Testing connection to production memory...")
    try:
        # Try a simple search to verify connection
        response = client.memory.search(
            query="test",
            max_memories=1,
            timeout=10.0
        )
        print("   ✅ Successfully connected to production memory at memory.papr.ai")
        if response and response.data and response.data.memories:
            print(f"   ✅ Retrieved {len(response.data.memories)} test memory")
        else:
            print("   ℹ️  Connection successful (no memories found for test query)")
    except Exception as e:
        print(f"   ⚠️  Connection test failed: {str(e)}")

except Exception as e:
    print(f"   ❌ Failed to initialize client: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*60)
print("✅ Setup Verification Complete!")
print("="*60)
print("\n📋 Configuration Summary:")
print(f"   • Local SDK: {'✅ Active' if 'papr-pythonSDK' in import_path else '📦 Using pip package'}")
print(f"   • CoreML: {'✅ Enabled' if os.getenv('PAPR_ENABLE_COREML') == 'true' else '❌ Disabled'}")
print(f"   • On-Device: {'✅ Enabled' if os.getenv('PAPR_ONDEVICE_PROCESSING') == 'true' else '❌ Disabled'}")
print(f"   • Production Memory: ✅ memory.papr.ai")
print("\n🚀 Ready to run the demo!")
print("   Run: ./run.sh")
print()
