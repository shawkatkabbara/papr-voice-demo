#!/usr/bin/env python3
"""
Test sync_tiers response to diagnose empty memories issue
"""
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "python"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")

# Add local SDK path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print(f"✅ Using local PAPR SDK from: {sdk_path}")

from papr_memory import Papr

print("\n" + "=" * 80)
print("🔍 TESTING SYNC_TIERS RESPONSE")
print("=" * 80)

api_key = os.environ.get('PAPR_MEMORY_API_KEY')
base_url = os.environ.get('PAPR_BASE_URL')
user_id = os.environ.get('TEST_USER_ID') or os.environ.get('PAPR_USER_ID')
external_user_id = os.environ.get('PAPR_EXTERNAL_USER_ID')

if not api_key:
    print("❌ PAPR_MEMORY_API_KEY not found!")
    sys.exit(1)

print(f"✅ API Key: {api_key[:20]}...")
print(f"✅ Base URL: {base_url}")
print(f"✅ User ID: {user_id}")
print(f"✅ External User ID: {external_user_id}")

# Initialize client with user context
client_kwargs = {"x_api_key": api_key, "timeout": 300.0}
if base_url:
    client_kwargs["base_url"] = base_url
if user_id:
    client_kwargs["user_id"] = user_id
if external_user_id:
    client_kwargs["external_user_id"] = external_user_id

try:
    client = Papr(**client_kwargs)
    print("✅ PAPR client initialized")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    sys.exit(1)

# Test sync_tiers with minimal params
print("\n🔄 Calling sync_tiers(max_tier0=10, max_tier1=10)...")
try:
    # Call the SDK's sync_tiers directly (without auto-storage)
    import httpx
    
    # Make direct API call to see raw response
    headers = {"X-API-Key": api_key}
    
    payload = {
        "max_tier0": 10,
        "max_tier1": 10,
        "include_embeddings": False
    }
    
    # Add user context to payload
    if user_id:
        payload["user_id"] = user_id
    if external_user_id:
        payload["external_user_id"] = external_user_id
    
    print(f"\n📤 Request payload: {json.dumps(payload, indent=2)}")
    
    with httpx.Client(timeout=60.0) as http_client:
        response = http_client.post(
            f"{base_url}/v1/sync/tiers",
            headers=headers,
            json=payload
        )
        
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error response: {response.text}")
            sys.exit(1)
        
        data = response.json()
        
        print(f"\n✅ Response keys: {list(data.keys())}")
        print(f"   - status: {data.get('status')}")
        print(f"   - code: {data.get('code')}")
        
        tier0 = data.get('tier0', [])
        tier1 = data.get('tier1', [])
        
        print(f"\n📊 Tier0: {len(tier0)} items")
        print(f"📊 Tier1: {len(tier1)} items")
        
        # Inspect first tier0 item
        if tier0:
            print(f"\n🔍 First Tier0 item:")
            first = tier0[0]
            print(f"   - Type: {type(first)}")
            print(f"   - Keys: {list(first.keys()) if isinstance(first, dict) else 'N/A'}")
            print(f"   - id: {first.get('id') if isinstance(first, dict) else 'N/A'}")
            print(f"   - type: {first.get('type') if isinstance(first, dict) else 'N/A'}")
            print(f"   - content: {(first.get('content') if isinstance(first, dict) else 'N/A')[:100]}...")
            print(f"   - topics: {first.get('topics') if isinstance(first, dict) else 'N/A'}")
            
            print(f"\n📄 Full first item:")
            print(json.dumps(first, indent=2, default=str))
        else:
            print("\n⚠️  Tier0 is empty!")
        
        # Inspect first tier1 item
        if tier1:
            print(f"\n🔍 First Tier1 item:")
            first = tier1[0]
            print(f"   - Type: {type(first)}")
            print(f"   - Keys: {list(first.keys()) if isinstance(first, dict) else 'N/A'}")
            print(f"   - id: {first.get('id') if isinstance(first, dict) else 'N/A'}")
            print(f"   - type: {first.get('type') if isinstance(first, dict) else 'N/A'}")
            print(f"   - content: {(first.get('content') if isinstance(first, dict) else 'N/A')[:100]}...")
            print(f"   - topics: {first.get('topics') if isinstance(first, dict) else 'N/A'}")
        else:
            print("\n⚠️  Tier1 is empty!")
        
        # Check for None/null values
        print(f"\n🔍 Checking for null values in tier0...")
        null_count = 0
        for i, item in enumerate(tier0[:5]):
            if item is None:
                null_count += 1
                print(f"   ❌ Item {i} is None!")
            elif isinstance(item, dict):
                if not item.get('id'):
                    print(f"   ⚠️  Item {i} has null/empty id")
                if not item.get('content'):
                    print(f"   ⚠️  Item {i} has null/empty content")
                if not item.get('type'):
                    print(f"   ⚠️  Item {i} has null/empty type")
        
        if null_count == 0:
            print(f"   ✅ No None items found in first 5")
        
except Exception as e:
    print(f"❌ Sync test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ TEST COMPLETE!")
print("=" * 80)

