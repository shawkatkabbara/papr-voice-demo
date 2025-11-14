#!/usr/bin/env python3
"""
Debug version of voice server to see where it's hanging
"""

import sys
import os

print("🔍 DEBUG: Starting imports...")
sys.stdout.flush()

from dotenv import load_dotenv
print("✅ Loaded dotenv")
sys.stdout.flush()

# Load environment
load_dotenv()
print("✅ Environment loaded")
sys.stdout.flush()

# Add papr-pythonSDK to path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print(f"✅ Added SDK path: {sdk_path}")
    sys.stdout.flush()

print("🔍 DEBUG: Importing Flask...")
sys.stdout.flush()
from flask import Flask

print("🔍 DEBUG: Importing papr_memory...")
sys.stdout.flush()
from papr_memory import Papr

print("✅ All imports complete!")
print("🔍 DEBUG: Initializing PAPR client...")
sys.stdout.flush()

# Initialize client
api_key = os.environ.get("PAPR_MEMORY_API_KEY")
base_url = os.environ.get("PAPR_BASE_URL", "https://memory.papr.ai")

print(f"   API Key: {api_key[:8]}..." if api_key else "   API Key: None")
print(f"   Base URL: {base_url}")
sys.stdout.flush()

try:
    papr_client = Papr(
        x_api_key=api_key,
        base_url=base_url,
        timeout=300.0
    )
    print("✅ PAPR client initialized!")
    sys.stdout.flush()
except Exception as e:
    print(f"❌ PAPR client init failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ Server ready - this is where Flask would start")
print("   The hang is probably during Papr() initialization")
