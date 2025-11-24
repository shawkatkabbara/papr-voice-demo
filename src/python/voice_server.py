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
from typing import Any, Protocol

# Load environment variables from project root
# Use find_dotenv() to automatically locate .env file
from pathlib import Path
project_root = Path(__file__).parent.parent.parent

# Ensure SDK logs land in a persistent file for debugging hardware usage
logs_dir = project_root / ".logs"
logs_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PAPR_LOG_FILE", str(logs_dir / "papr_sdk.log"))
os.environ.setdefault("PAPR_LOG_LEVEL", "INFO")

load_dotenv(dotenv_path=project_root / ".env")

# Import tool schema helpers
from tool_schemas import get_search_memory_tool_schema, validate_search_params

# Add papr-pythonSDK to path for local development
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
    print(f"✅ Using local PAPR SDK from: {sdk_path}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Store search history for constellation visualization
# Using deque with maxlen to automatically limit history size
search_history = deque(maxlen=30)  # Keep last 30 searches for constellation


# Protocol for type checking the local embedder
class Embedder(Protocol):
    """Protocol for embedding models with encode method"""
    def encode(self, texts: list[str]) -> Any:
        ...


def _wait_for_coreml_pipeline(client, timeout=180, interval=3):
    """
    Wait for the Papr SDK's CoreML pipeline (sync_tiers + collection + embedder)
    to finish background initialization before issuing warmup searches.
    """
    if not client or not hasattr(client, "memory"):
        return False

    print("🔄 Waiting for CoreML pipeline to finish background initialization...")
    end_time = time.time() + timeout
    get_status = getattr(client.memory, "_get_model_loading_status", None)

    while time.time() < end_time:
        collection_ready = getattr(client.memory, "_chroma_collection", None) is not None
        embedder_ready = getattr(client.memory, "_local_embedder", None) is not None

        status_complete = False
        if callable(get_status):
            try:
                status = get_status() or {}
                status_complete = bool(status.get("complete"))
            except Exception as status_error:
                print(f"   ⚠️  Unable to read model loading status yet: {status_error}")

        if collection_ready and (embedder_ready or status_complete):
            print("✅ CoreML pipeline reports ready state")
            return True

        # Proactively ask SDK for a local embedder once the collection exists
        if collection_ready and not embedder_ready and hasattr(client.memory, "_get_local_embedder"):
            try:
                embedder = client.memory._get_local_embedder()
                if embedder is not None:
                    client.memory._local_embedder = embedder
                    embedder_ready = True
            except Exception as embedder_error:
                print(f"   ⚠️  Local embedder not ready yet: {embedder_error}")

        time.sleep(interval)

    print("⚠️  CoreML pipeline did not report ready before timeout")
    return False


# Initialize PAPR client with CoreML
papr_client = None
local_embedder: Embedder | None = None
local_collection = None
try:
    from papr_memory import Papr  # type: ignore

    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")
    
    # Get user context from environment variables
    # The SDK will auto-detect PAPR_USER_ID and PAPR_EXTERNAL_USER_ID
    # but you can also pass them explicitly here
    user_id = os.environ.get("TEST_USER_ID") or os.environ.get("PAPR_USER_ID")
    external_user_id = os.environ.get("PAPR_EXTERNAL_USER_ID")

    client_kwargs = {
        "x_api_key": api_key,
        "timeout": 300.0  # Increased for CoreML model loading
    }

    if base_url:
        client_kwargs["base_url"] = base_url
    
    # Pass user context to SDK - this will filter sync_tiers and searches
    if user_id:
        client_kwargs["user_id"] = user_id
    if external_user_id:
        client_kwargs["external_user_id"] = external_user_id

    papr_client = Papr(**client_kwargs)
    
    # Log user context if set
    if user_id or external_user_id:
        context_info = []
        if user_id:
            context_info.append(f"user_id={user_id}")
        if external_user_id:
            context_info.append(f"external_user_id={external_user_id}")
        print(f"✅ PAPR SDK initialized with user context: {', '.join(context_info)}")
    else:
        print("✅ PAPR SDK initialized with CoreML!")

    # Check if CoreML is enabled
    coreml_enabled = os.environ.get("PAPR_ENABLE_COREML", "false").lower() in ("true", "1", "yes")
    if coreml_enabled:
        print(f"🚀 CoreML ENABLED: {os.environ.get('PAPR_COREML_MODEL', 'N/A')}")
        print("⏳ Waiting for SDK to complete background initialization...")
        
        # Wait for SDK's internal warmup to complete (it handles this now)
        pipeline_ready = _wait_for_coreml_pipeline(papr_client, timeout=120)
        if pipeline_ready:
            print("✅ SDK background initialization complete - CoreML ready!")
        else:
            print("⚠️  SDK initialization timeout - model will load on first search")

        # Cache local embedder/collection for direct access after warmup attempt
        embedder_obj = getattr(papr_client.memory, "_local_embedder", None)
        local_embedder = embedder_obj if embedder_obj and hasattr(embedder_obj, 'encode') else None  # type: ignore
        if not local_embedder and hasattr(papr_client.memory, "_get_local_embedder"):
            try:
                embedder_obj = papr_client.memory._get_local_embedder()
                local_embedder = embedder_obj if embedder_obj and hasattr(embedder_obj, 'encode') else None  # type: ignore
            except Exception:
                local_embedder = None
        local_collection = getattr(papr_client.memory, "_collection", None) or getattr(
            papr_client.memory, "_chroma_collection", None
        )
        if local_embedder and local_collection:
            print("🧠 Local CoreML embedder + Chroma collection cached for low-latency path\n")

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
        'papr_key': os.environ.get('PAPR_MEMORY_API_KEY', ''),
        'openai_realtime_model': os.environ.get('OPENAI_REALTIME_API_MODEL', 'gpt-realtime-mini-2025-10-06')
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


# Removed _perform_local_coreml_search - the SDK handles all search logic internally
# Including the CoreML fast path. No need to duplicate logic here.


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

        # Use SDK for all searches - it handles CoreML fast path internally
        memories = []
        latency_breakdown = None

        # Time the SDK call
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
        tier0_count = 0
        tier1_count = 0
        
        if response and response.data and response.data.memories:
            for mem in response.data.memories:
                # Get ChromaDB query similarity score (cosine similarity to search query)
                query_similarity = 0.0
                relevance_score = 0.0
                
                # Try to extract scores from various locations
                if hasattr(mem, 'pydantic_extra__') and mem.pydantic_extra__:
                    query_similarity = mem.pydantic_extra__.get('similarity_score', 0.0)
                    relevance_score = mem.pydantic_extra__.get('relevance_score', 0.0)

                # Fallback: Try metadata (cloud API might put it here)
                if query_similarity == 0.0 or relevance_score == 0.0:
                    metadata = getattr(mem, 'metadata', {})
                    if isinstance(metadata, dict):
                        if query_similarity == 0.0:
                            query_similarity = metadata.get('query_similarity', metadata.get('similarity_score', 0.0))
                        if relevance_score == 0.0:
                            relevance_score = metadata.get('relevance_score', 0.0)
                
                # Last fallback: Try custom_metadata
                if query_similarity == 0.0 or relevance_score == 0.0:
                    custom_metadata = getattr(mem, 'custom_metadata', {})
                    if isinstance(custom_metadata, dict):
                        if query_similarity == 0.0:
                            query_similarity = custom_metadata.get('query_similarity', custom_metadata.get('similarity_score', 0.0))
                        if relevance_score == 0.0:
                            relevance_score = custom_metadata.get('relevance_score', 0.0)

                # Get content with null checking
                content = getattr(mem, 'content', None)
                # Handle None, empty string, and string 'None'
                if content is None or (isinstance(content, str) and (content.strip() == '' or content.strip().lower() == 'none')):
                    content = None  # Will be handled in frontend

                # Get tags and topics - ensure they're always arrays
                tags = getattr(mem, 'tags', None) or []
                if not isinstance(tags, list):
                    tags = [tags] if tags else []
                
                topics = getattr(mem, 'topics', None) or []
                if not isinstance(topics, list):
                    topics = [topics] if topics else []

                # Get custom metadata
                custom_metadata = getattr(mem, 'custom_metadata', None)

                # Determine tier from SDK's type field or metadata
                # SDK sets type="tier0" or type="tier1" for local searches
                # For cloud API, check metadata.tier or metadata.sourceType
                memory_type = getattr(mem, 'type', 'unknown')
                
                # Check if type is already set to tier0/tier1 by SDK
                if memory_type in ['tier0', 'tier1']:
                    tier = memory_type
                else:
                    # Fallback: Check metadata for tier information
                    tier = 'tier1'  # Default to tier1
                    metadata = getattr(mem, 'metadata', {})
                    if isinstance(metadata, dict):
                        metadata_tier = metadata.get('tier', None)
                        if metadata_tier == 0 or metadata_tier == '0' or metadata_tier == 'tier0':
                            tier = 'tier0'
                        elif metadata_tier == 1 or metadata_tier == '1' or metadata_tier == 'tier1':
                            tier = 'tier1'
                
                tier_label = 'goals/okrs' if tier == 'tier0' else 'memories'
                
                if tier == 'tier0':
                    tier0_count += 1
                else:
                    tier1_count += 1

                # ✅ IMPORTANT: Only send user-facing fields to OpenAI
                # DO NOT send: memory IDs, scores, tiers, internal metadata, ACLs, etc.
                memory_for_llm = {}
                
                # Always include content (even if None - frontend will handle)
                memory_for_llm['content'] = content
                
                # Helper function to add field only if it exists and is not null/empty
                def add_if_present(field_name, value=None):
                    if value is None:
                        value = getattr(mem, field_name, None)
                    if value is not None:
                        # Skip empty strings, empty lists, empty dicts
                        if isinstance(value, str) and value.strip() == '':
                            return
                        if isinstance(value, (list, dict)) and len(value) == 0:
                            return
                        memory_for_llm[field_name] = value
                
                # Add user-facing fields (only if present and not empty)
                add_if_present('context')
                add_if_present('location')
                add_if_present('hierarchical_structures')
                add_if_present('source_url')
                add_if_present('steps')
                add_if_present('current_step')
                add_if_present('category')
                add_if_present('topics', topics)  # Already extracted above
                add_if_present('tags', tags)  # Already extracted above
                add_if_present('title')
                add_if_present('page_number')
                add_if_present('total_pages')
                add_if_present('file_url')
                add_if_present('page')
                add_if_present('created_at')
                add_if_present('updated_at')
                add_if_present('customMetadata', custom_metadata)  # Already extracted above
                
                # Do NOT send to OpenAI: IDs, scores, tiers, types, internal metadata
                # Keep these for internal logging only
                
                memories.append(memory_for_llm)

        processing_overhead_ms = ((time.perf_counter() - request_start) * 1000) - sdk_latency_ms

        latency_breakdown = {
            'total_ms': round((time.perf_counter() - request_start) * 1000, 1),
            'sdk_processing_ms': round(sdk_latency_ms, 1),
            'embedding_generation_ms': round(estimated_embedding_ms, 1),  # Estimated
            'chromadb_search_ms': round(estimated_search_ms, 1),  # Estimated
            'processing_overhead_ms': round(processing_overhead_ms, 1),  # Python + Flask
            'note': 'SDK search path (estimated embed/search split)'
        }

        # Log memory retrieval summary
        print(f"\n📊 Retrieved {len(memories)} memories from SDK search")
        memories_with_content = sum(1 for m in memories if m['content'] is not None)
        memories_without_content = len(memories) - memories_with_content
        print(f"   ✅ {memories_with_content} with content")
        print(f"   ❌ {memories_without_content} without content")
        
        # Log tier breakdown
        print(f"\n📋 Memories breakdown:")
        print(f"   [Tier0] {tier0_count} results (goals/OKRs/use-cases)")
        print(f"   [Tier1] {tier1_count} results (general memories)")

        # Log all memories (up to 30)
        print(f"\n📋 All {len(memories)} memories:")
        for i, mem in enumerate(memories, 1):
            content_preview = mem['content'][:100] if mem['content'] else "(No content)"
            topics_preview = mem.get('topics', [])
            topics_str = f" [Topics: {', '.join(topics_preview[:3])}]" if topics_preview else ""
            print(f"   [{i}]{topics_str} {content_preview}...")

        # Calculate total end-to-end latency (includes Python/Flask overhead)
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
            # Store summary of top 3 memories for constellation tooltip
            'top_memories_preview': [
                {
                    'content': m['content'][:100] if m['content'] else '(No content)',
                    'topics': m.get('topics', [])[:3]  # First 3 topics
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
