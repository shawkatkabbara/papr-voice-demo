#!/usr/bin/env python3
"""
PAPR Voice Server with ON-DEVICE CoreML search
Uses papr-pythonSDK with CoreML for fast local memory retrieval
"""

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize PAPR client with CoreML
papr_client = None
try:
    from papr_memory import Papr

    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")

    client_kwargs = {
        "x_api_key": api_key,
        "timeout": 120.0
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    papr_client = Papr(**client_kwargs)
    print("✅ PAPR SDK initialized with CoreML!")

    # Check if CoreML is enabled
    coreml_enabled = os.environ.get("PAPR_ENABLE_COREML", "false").lower() in ("true", "1", "yes")
    if coreml_enabled:
        print(f"🚀 CoreML ENABLED: {os.environ.get('PAPR_COREML_MODEL', 'N/A')}")

except ImportError as e:
    print(f"⚠️  PAPR SDK not found: {e}")
    print("    Memory searches will fail!")
except Exception as e:
    print(f"❌ Failed to initialize PAPR client: {e}")


@app.route('/')
def index():
    """Serve the voice.html page"""
    return send_file('voice.html')


@app.route('/logo.svg')
def logo():
    """Serve the Papr logo"""
    return send_file('voice.html.logo.svg')


@app.route('/api/keys')
def get_keys():
    """Return API keys for the frontend"""
    return jsonify({
        'openai_key': os.environ.get('OPENAI_API_KEY', ''),
        'papr_key': os.environ.get('PAPR_MEMORY_API_KEY', '')
    })


@app.route('/api/search', methods=['POST'])
def search_memories():
    """ON-DEVICE memory search using PAPR SDK with CoreML"""
    if not papr_client:
        return jsonify({'error': 'PAPR SDK not initialized'}), 500

    try:
        data = request.json
        query = data.get('query', '')
        max_memories = data.get('max_memories', 30)

        print(f"\n🔍 Search request: query='{query}', max_memories={max_memories}")

        # Detailed timing breakdown
        request_start = time.perf_counter()

        # Time the SDK call separately
        sdk_start = time.perf_counter()

        response = papr_client.memory.search(
            query=query,
            max_memories=max_memories,
            max_nodes=10,
            enable_agentic_graph=False,
            timeout=180.0
        )

        sdk_end = time.perf_counter()

        # SDK latency (embedding + ChromaDB search)
        sdk_latency_ms = (sdk_end - sdk_start) * 1000

        # Estimate: ~70-80% is embedding, ~20-30% is search for CoreML
        estimated_embedding_ms = sdk_latency_ms * 0.75
        estimated_search_ms = sdk_latency_ms * 0.25

        # Extract memories from response with proper null handling
        memories = []
        if response and response.data and response.data.memories:
            for mem in response.data.memories:
                # Get similarity score
                score = 0.0
                if hasattr(mem, 'pydantic_extra__') and mem.pydantic_extra__:
                    score = mem.pydantic_extra__.get('similarity_score', 0.0)
                else:
                    score = getattr(mem, 'score', 0.0)

                # Get content with null checking
                content = getattr(mem, 'content', None)
                # Handle None, empty string, and string 'None'
                if content is None or (isinstance(content, str) and (content.strip() == '' or content.strip().lower() == 'none')):
                    content = None  # Will be handled in frontend

                # Get tags and topics
                tags = getattr(mem, 'tags', None) or []
                topics = getattr(mem, 'topics', None) or []

                # Get custom metadata
                custom_metadata = getattr(mem, 'custom_metadata', None)

                # Build metadata dict
                metadata = getattr(mem, 'metadata', {})

                memories.append({
                    'content': content,
                    'similarity_score': score,
                    'score': score,
                    'tags': tags,
                    'topics': topics,
                    'custom_metadata': custom_metadata,
                    'metadata': metadata,
                    'id': getattr(mem, 'id', 'N/A')
                })

        # Calculate total end-to-end latency (includes Python/Flask overhead)
        total_latency_ms = (time.perf_counter() - request_start) * 1000

        # Python/Flask processing overhead (time outside SDK call)
        processing_overhead_ms = total_latency_ms - sdk_latency_ms

        latency_breakdown = {
            'total_ms': round(total_latency_ms, 1),
            'sdk_processing_ms': round(sdk_latency_ms, 1),
            'embedding_generation_ms': round(estimated_embedding_ms, 1),  # Estimated
            'chromadb_search_ms': round(estimated_search_ms, 1),  # Estimated
            'processing_overhead_ms': round(processing_overhead_ms, 1),  # Python + Flask
            'note': 'Embedding and search times are estimated (75%/25% split). Processing overhead includes Python and Flask. Ngrok network latency not measured.'
        }

        print(f"⏱️  Total latency: {latency_breakdown['total_ms']:.1f}ms")
        print(f"   ├─ SDK processing: {latency_breakdown['sdk_processing_ms']:.1f}ms")
        print(f"   │  ├─ Embedding (est): {latency_breakdown['embedding_generation_ms']:.1f}ms")
        print(f"   │  └─ ChromaDB (est): {latency_breakdown['chromadb_search_ms']:.1f}ms")
        print(f"   └─ Processing overhead: {latency_breakdown['processing_overhead_ms']:.1f}ms (Python + Flask)")
        print(f"✅ CoreML search: {len(memories)} results in {latency_breakdown['total_ms']:.1f}ms")

        return jsonify({
            'data': {
                'memories': memories
            },
            'latency_ms': latency_breakdown['total_ms'],
            'latency_breakdown': latency_breakdown
        })

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n🎤 PAPR Voice Server Starting...")
    print("📍 Open: http://localhost:3000")

    ondevice = os.environ.get("PAPR_ONDEVICE_PROCESSING", "false").lower() in ("true", "1", "yes")
    if ondevice:
        print("🚀 ON-DEVICE CoreML search enabled!")

    print("\n")
    app.run(host='0.0.0.0', port=3000, debug=False)
