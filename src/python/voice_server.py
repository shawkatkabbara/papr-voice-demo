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
local_embedder = None
local_collection = None
try:
    from papr_memory import Papr  # type: ignore

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
        print("⏳ Waiting for SDK to complete background initialization...")
        
        # Wait for SDK's internal warmup to complete (it handles this now)
        pipeline_ready = _wait_for_coreml_pipeline(papr_client, timeout=120)
        if pipeline_ready:
            print("✅ SDK background initialization complete - CoreML ready!")
        else:
            print("⚠️  SDK initialization timeout - model will load on first search")

        # Cache local embedder/collection for direct access after warmup attempt
        local_embedder = getattr(papr_client.memory, "_local_embedder", None)
        if not local_embedder and hasattr(papr_client.memory, "_get_local_embedder"):
            try:
                local_embedder = papr_client.memory._get_local_embedder()
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


def _perform_local_coreml_search(query: str, max_memories: int, search_tier0: bool = True, search_tier1: bool = True):
    """
    Use the cached CoreML embedder + Chroma collections directly to avoid SDK overhead.
    Searches both tier0 (goals/okrs) and tier1 (memories) collections and merges results.
    
    Args:
        query: Search query string
        max_memories: Maximum number of results to return
        search_tier0: Whether to search tier0 collection (default: True)
        search_tier1: Whether to search tier1 collection (default: True)
    
    Returns:
        (memories, latency_breakdown) or raises on failure.
    """
    if not local_embedder:
        raise RuntimeError("Local embedder not available yet")

    # Measure embed time precisely (one embedding for both collections)
    embed_start = time.perf_counter()
    embedding = local_embedder.encode([query])[0]
    embed_ms = (time.perf_counter() - embed_start) * 1000

    all_memories = []
    total_chroma_ms = 0.0
    collections_searched = []

    # Search tier0 collection (goals/okrs)
    if search_tier0 and local_collection is not None:
        try:
            chroma_start = time.perf_counter()
            tier0_results = local_collection.query(
                query_embeddings=[embedding],
                n_results=max_memories,  # Get max from tier0
                include=["documents", "metadatas", "distances"]
            )
            tier0_chroma_ms = (time.perf_counter() - chroma_start) * 1000
            total_chroma_ms += tier0_chroma_ms

            if tier0_results.get("ids"):
                docs = tier0_results["documents"][0]
                metas = tier0_results["metadatas"][0]
                dists = tier0_results["distances"][0]
                ids = tier0_results["ids"][0]

                for idx, doc in enumerate(docs):
                    metadata = metas[idx] or {}
                    # ChromaDB stores content in the 'document' field, not in metadata
                    content = doc or metadata.get("content") or "(No content)"
                    query_similarity = 1.0 - dists[idx] if dists[idx] is not None else 0.0
                    all_memories.append({
                        'content': content,
                        'query_similarity': query_similarity,
                        'relevance_score': metadata.get('similarity_score', 0.0),
                        'score': query_similarity,
                        'similarity_score': query_similarity,
                        'tags': metadata.get('tags', []),
                        'topics': metadata.get('topics', []),
                        'custom_metadata': metadata.get('custom_metadata'),
                        'metadata': metadata,
                        'id': ids[idx] if ids else 'N/A',
                        'tier': 0,  # Mark as tier0
                        'tier_label': 'goals/okrs'
                    })
                collections_searched.append(f"tier0 ({len(docs)} results, {tier0_chroma_ms:.1f}ms)")
        except Exception as tier0_error:
            print(f"⚠️  Tier0 search failed: {tier0_error}")

    # Search tier1 collection (memories)
    if search_tier1:
        try:
            # Try to get tier1 collection from SDK client
            tier1_collection = None
            if hasattr(papr_client.memory, '_chroma_tier1_collection'):
                tier1_collection = papr_client.memory._chroma_tier1_collection
            
            if tier1_collection is not None:
                chroma_start = time.perf_counter()
                tier1_results = tier1_collection.query(
                    query_embeddings=[embedding],
                    n_results=max_memories,  # Get max from tier1
                    include=["documents", "metadatas", "distances"]
                )
                tier1_chroma_ms = (time.perf_counter() - chroma_start) * 1000
                total_chroma_ms += tier1_chroma_ms

                if tier1_results.get("ids"):
                    docs = tier1_results["documents"][0]
                    metas = tier1_results["metadatas"][0]
                    dists = tier1_results["distances"][0]
                    ids = tier1_results["ids"][0]

                    for idx, doc in enumerate(docs):
                        metadata = metas[idx] or {}
                        # ChromaDB stores content in the 'document' field, not in metadata
                        content = doc or metadata.get("content") or "(No content)"
                        query_similarity = 1.0 - dists[idx] if dists[idx] is not None else 0.0
                        all_memories.append({
                            'content': content,
                            'query_similarity': query_similarity,
                            'relevance_score': metadata.get('similarity_score', 0.0),
                            'score': query_similarity,
                            'similarity_score': query_similarity,
                            'tags': metadata.get('tags', []),
                            'topics': metadata.get('topics', []),
                            'custom_metadata': metadata.get('custom_metadata'),
                            'metadata': metadata,
                            'id': ids[idx] if ids else 'N/A',
                            'tier': 1,  # Mark as tier1
                            'tier_label': 'memories'
                        })
                    collections_searched.append(f"tier1 ({len(docs)} results, {tier1_chroma_ms:.1f}ms)")
        except Exception as tier1_error:
            print(f"⚠️  Tier1 search failed: {tier1_error}")

    # Sort merged results by query_similarity (descending) and limit to max_memories
    all_memories.sort(key=lambda x: x['query_similarity'], reverse=True)
    final_memories = all_memories[:max_memories]

    latency_breakdown = {
        'total_ms': round(embed_ms + total_chroma_ms, 1),
        'sdk_processing_ms': round(embed_ms + total_chroma_ms, 1),
        'embedding_generation_ms': round(embed_ms, 1),
        'chromadb_search_ms': round(total_chroma_ms, 1),
        'processing_overhead_ms': 0.0,
        'note': f'Local CoreML fast path (searched: {", ".join(collections_searched) if collections_searched else "no collections"})'
    }

    tier_breakdown = f" [{len([m for m in final_memories if m.get('tier') == 0])} tier0, {len([m for m in final_memories if m.get('tier') == 1])} tier1]"
    print(f"⚡ Local CoreML fast path → Embedding: {embed_ms:.1f}ms | Chroma: {total_chroma_ms:.1f}ms | Total: {latency_breakdown['total_ms']:.1f}ms{tier_breakdown}")
    return final_memories, latency_breakdown


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

        use_fast_path = local_embedder is not None and local_collection is not None
        memories = []
        latency_breakdown = None

        if use_fast_path:
            try:
                memories, latency_breakdown = _perform_local_coreml_search(query, max_memories)
            except Exception as fast_path_error:
                print(f"⚠️  Local CoreML fast path failed: {fast_path_error}. Falling back to SDK search.")
                use_fast_path = False

        if not use_fast_path:
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
        print(f"\n📊 Retrieved {len(memories)} memories from {'local fast path' if use_fast_path else 'SDK search'}")
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
