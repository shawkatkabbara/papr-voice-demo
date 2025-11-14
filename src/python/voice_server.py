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
from pydantic import ValidationError
from datetime import datetime
from collections import deque

# Load environment variables from project root
# Path adjusted for new src/python/ location
load_dotenv(dotenv_path="../../.env")

# Import tool schema helpers
from tool_schemas import get_search_memory_tool_schema, validate_search_params

# Add papr-pythonSDK to path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Store search history for constellation visualization
# Using deque with maxlen to automatically limit history size
search_history = deque(maxlen=30)  # Keep last 30 searches for constellation

# Initialize PAPR client with CoreML
papr_client = None
try:
    from papr_memory import Papr

    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")

    client_kwargs = {
        "x_api_key": api_key,
        "timeout": 300.0  # Increased for CoreML model loading
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
    # Path adjusted for new src/python/ location
    return send_file('../../voice.html')


@app.route('/logo.svg')
def logo():
    """Serve the Papr logo"""
    # Path adjusted for new src/python/ location
    return send_file('../../voice.html.logo.svg')


@app.route('/api/keys')
def get_keys():
    """Return API keys for the frontend"""
    return jsonify({
        'openai_key': os.environ.get('OPENAI_API_KEY', ''),
        'papr_key': os.environ.get('PAPR_MEMORY_API_KEY', '')
    })


@app.route('/api/tool-schema')
def get_tool_schema():
    """
    Return OpenAI-compatible tool schema for memory search.

    This schema is generated from Pydantic models that match the PAPR SDK types,
    ensuring consistency between frontend tool calls and backend validation.
    """
    return jsonify(get_search_memory_tool_schema())


@app.route('/api/search-history')
def get_search_history():
    """
    Return search history for constellation visualization.

    Returns the last 30 searches with:
    - Query text
    - Result count
    - Latency breakdown (total, embedding, search, overhead)
    - Top scores
    - Preview of top memories
    - Timestamp

    This data powers the constellation UI, allowing users to:
    - See search history as particles
    - Click on particles to see latency details
    - Hover to see query and top results
    """
    return jsonify({
        'searches': list(search_history),  # Convert deque to list for JSON serialization
        'count': len(search_history)
    })


@app.route('/api/search', methods=['POST'])
def search_memories():
    """ON-DEVICE memory search using PAPR SDK with CoreML"""
    if not papr_client:
        return jsonify({'error': 'PAPR SDK not initialized'}), 500

    try:
        data = request.json

        # Validate parameters using Pydantic schema
        try:
            validated_params = validate_search_params({
                'query': data.get('query', ''),
                'enable_agentic_graph': data.get('enable_agentic_graph', False)
            })
            query = validated_params.query
            enable_agentic_graph = validated_params.enable_agentic_graph
        except ValidationError as e:
            return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400

        max_memories = data.get('max_memories', 30)

        print(f"\n🔍 Search request: query='{query}', max_memories={max_memories}, agentic_graph={enable_agentic_graph}")

        # Detailed timing breakdown
        request_start = time.perf_counter()

        # Time the SDK call separately
        sdk_start = time.perf_counter()

        response = papr_client.memory.search(
            query=query,
            max_memories=max_memories,
            max_nodes=10,
            enable_agentic_graph=enable_agentic_graph,  # Use validated parameter
            rank_results=True,  # Enable additional ranking for CoreML embeddings
            timeout=300.0  # Increased timeout for first CoreML model load
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
                # Get ChromaDB query similarity score (cosine similarity to search query)
                query_similarity = 0.0
                if hasattr(mem, 'pydantic_extra__') and mem.pydantic_extra__:
                    query_similarity = mem.pydantic_extra__.get('similarity_score', 0.0)
                else:
                    query_similarity = getattr(mem, 'score', 0.0)

                # Get server-side relevance score (goals/transitions/hotness composite)
                # This comes from metadata when the memory was synced from tier0
                metadata = getattr(mem, 'metadata', {})
                relevance_score = metadata.get('similarity_score', 0.0) if isinstance(metadata, dict) else 0.0

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

                memories.append({
                    'content': content,
                    'query_similarity': query_similarity,  # ChromaDB cosine similarity
                    'relevance_score': relevance_score,    # Server composite score
                    'score': query_similarity,             # Keep for backward compatibility
                    'similarity_score': query_similarity,  # Keep for backward compatibility
                    'tags': tags,
                    'topics': topics,
                    'custom_metadata': custom_metadata,
                    'metadata': metadata,
                    'id': getattr(mem, 'id', 'N/A')
                })

        # Log memory retrieval summary
        print(f"\n📊 Retrieved {len(memories)} memories from API")
        memories_with_content = sum(1 for m in memories if m['content'] is not None)
        memories_without_content = len(memories) - memories_with_content
        print(f"   ✅ {memories_with_content} with content")
        print(f"   ❌ {memories_without_content} without content")

        # Log all memories (up to 30)
        print(f"\n📋 All {len(memories)} memories:")
        for i, mem in enumerate(memories, 1):
            content_preview = mem['content'][:100] if mem['content'] else "(No content)"
            query_sim = mem['query_similarity']
            rel_score = mem['relevance_score']
            if rel_score > 0:
                print(f"   [{i}] Query: {query_sim:.4f} | Relevance: {rel_score:.4f} | {content_preview}...")
            else:
                print(f"   [{i}] Query: {query_sim:.4f} | {content_preview}...")

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

        # Store search in history for constellation visualization
        search_entry = {
            'id': f"search_{int(time.time() * 1000)}",  # Unique ID based on timestamp
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'result_count': len(memories),
            'enable_agentic_graph': enable_agentic_graph,
            'latency': latency_breakdown,
            'top_score': memories[0]['query_similarity'] if memories else 0,
            # Store summary of top 3 memories for constellation tooltip
            'top_memories_preview': [
                {
                    'content': m['content'][:100] if m['content'] else '(No content)',
                    'score': m['query_similarity']
                }
                for m in memories[:3]
            ]
        }
        search_history.append(search_entry)

        return jsonify({
            'data': {
                'memories': memories
            },
            'latency_ms': latency_breakdown['total_ms'],
            'latency_breakdown': latency_breakdown,
            'search_id': search_entry['id']  # Return ID for constellation tracking
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
