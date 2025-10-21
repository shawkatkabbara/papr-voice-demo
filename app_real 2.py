#!/usr/bin/env python3
"""
PAPR Voice Demo - REAL on-device processing with papr-pythonSDK and CoreML
"""

import streamlit as st
import os
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Add papr-pythonSDK to path
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

try:
    from papr_memory import Papr
except ImportError:
    st.error("❌ papr_memory not found. Ensure papr-pythonSDK is at ~/Documents/GitHub/papr-pythonSDK/")
    st.stop()

st.set_page_config(
    page_title="PAPR Voice Demo",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .query-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .memory-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .speed-metric {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'queries' not in st.session_state:
    st.session_state.queries = []
if 'memories' not in st.session_state:
    st.session_state.memories = []
if 'papr_client' not in st.session_state:
    # Initialize REAL Papr client
    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")

    client_kwargs = {
        "x_api_key": api_key,
        "timeout": 120.0
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    try:
        st.session_state.papr_client = Papr(**client_kwargs)
    except Exception as e:
        st.error(f"Failed to initialize Papr client: {e}")
        st.session_state.papr_client = None

if 'openai_client' not in st.session_state:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        st.session_state.openai_client = OpenAI(api_key=openai_key)
    else:
        st.session_state.openai_client = None

def search_memories_real(query: str, max_results: int = 5):
    """REAL on-device memory search using papr-pythonSDK"""

    if not st.session_state.papr_client:
        raise Exception("Papr client not initialized")

    # Time the search
    start_time = time.perf_counter()

    try:
        # REAL search using papr-pythonSDK
        response = st.session_state.papr_client.memory.search(
            query=query,
            max_memories=max_results,
            max_nodes=10,
            enable_agentic_graph=False,
            timeout=180.0
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract memories from response
        memories = []
        if response and response.data and response.data.memories:
            for mem in response.data.memories:
                memories.append({
                    'content': mem.content,
                    'score': getattr(mem, 'score', 0.0),
                    'metadata': getattr(mem, 'metadata', {}),
                    'id': getattr(mem, 'id', 'N/A')
                })

        return memories, latency_ms

    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")

# Header
st.title("🎤 PAPR Voice Demo")
st.markdown("**Real-time voice conversation with on-device memory retrieval**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Show on-device processing status
    ondevice_enabled = os.environ.get("PAPR_ONDEVICE_PROCESSING", "false").lower() in ("true", "1", "yes")
    coreml_enabled = os.environ.get("PAPR_ENABLE_COREML", "false").lower() in ("true", "1", "yes")

    st.markdown("### 🚀 On-Device Processing")
    if ondevice_enabled:
        st.success("✅ Enabled")
        if coreml_enabled:
            st.info("🔧 CoreML Acceleration Active")
            coreml_model = os.environ.get("PAPR_COREML_MODEL", "")
            if coreml_model:
                st.caption(f"Model: {os.path.basename(coreml_model)}")
    else:
        st.warning("⚠️ Disabled (Server-side processing)")

    st.markdown("### API Configuration")
    base_url = os.environ.get("PAPR_BASE_URL", "Not set")
    st.caption(f"Server: {base_url}")

    st.markdown("### Memory Settings")
    max_memories = st.slider("Max memories to retrieve", 1, 50, 30)

    st.markdown("### Performance Stats")
    if st.session_state.queries:
        avg_latency = sum(q['latency'] for q in st.session_state.queries) / len(st.session_state.queries)
        st.metric("Avg Retrieval Speed", f"{avg_latency:.1f}ms")
        st.metric("Total Queries", len(st.session_state.queries))

    if st.button("🗑️ Clear History"):
        st.session_state.queries = []
        st.session_state.memories = []
        st.rerun()

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.header("💬 Conversation")

    # Voice input via file upload
    st.markdown("### 🎤 Voice Input")
    st.caption("Upload an audio file (record on phone/computer)")

    uploaded_file = st.file_uploader("Upload audio (mp3, wav, m4a)", type=['mp3', 'wav', 'm4a', 'ogg'])

    user_query = None

    if uploaded_file is not None:
        st.audio(uploaded_file)

        if st.session_state.openai_client:
            if st.button("🎧 Transcribe & Search"):
                with st.spinner("Transcribing..."):
                    try:
                        transcript = st.session_state.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=uploaded_file
                        )
                        user_query = transcript.text
                        st.success(f"✅ Transcription: \"{user_query}\"")

                        # REAL search
                        with st.spinner("🔍 Searching memories with CoreML..."):
                            results, latency_ms = search_memories_real(user_query, max_memories)

                            query_data = {
                                'query': user_query,
                                'timestamp': datetime.now().isoformat(),
                                'latency': latency_ms,
                                'num_results': len(results)
                            }
                            st.session_state.queries.append(query_data)

                            for mem in results:
                                st.session_state.memories.append({
                                    **mem,
                                    'timestamp': datetime.now().isoformat(),
                                    'query': user_query
                                })

                            st.success(f"✅ Found {len(results)} memories in {latency_ms:.1f}ms")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ OpenAI API key not configured")

    # Text input fallback
    st.markdown("---")
    st.markdown("### ⌨️ Or Type Your Query")
    text_query = st.text_input("Type your message:", key="user_input")

    if st.button("🔍 Search with CoreML") and text_query:
        with st.spinner("🔍 Searching memories with CoreML..."):
            try:
                results, latency_ms = search_memories_real(text_query, max_memories)

                query_data = {
                    'query': text_query,
                    'timestamp': datetime.now().isoformat(),
                    'latency': latency_ms,
                    'num_results': len(results)
                }
                st.session_state.queries.append(query_data)

                for mem in results:
                    st.session_state.memories.append({
                        **mem,
                        'timestamp': datetime.now().isoformat(),
                        'query': text_query
                    })

                st.success(f"✅ Found {len(results)} memories in {latency_ms:.1f}ms")

            except Exception as e:
                st.error(f"❌ Search error: {str(e)}")

    # Conversation history
    st.markdown("---")
    st.markdown("### Conversation History")
    for query in reversed(st.session_state.queries[-10:]):
        st.markdown(f"""
        <div class="query-box">
            <strong>Query:</strong> {query['query']}<br>
            <span style="color: #666; font-size: 12px;">{query['timestamp']}</span><br>
            <strong>Results:</strong> {query['num_results']} memories<br>
            <strong>Speed:</strong> <span class="speed-metric">{query['latency']:.1f}ms</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.header("🧠 Retrieved Memories")

    if st.session_state.memories:
        st.markdown(f"**Total memories retrieved:** {len(st.session_state.memories)}")

        recent_memories = st.session_state.memories[-20:]

        for i, mem in enumerate(reversed(recent_memories), 1):
            with st.expander(f"Memory {i} - Score: {mem['score']:.3f}", expanded=(i <= 3)):
                st.markdown(f"**Query:** {mem['query']}")
                st.markdown(f"**Content:**")
                st.write(mem['content'])

                if mem.get('metadata'):
                    st.markdown("**Metadata:**")
                    st.json(mem['metadata'])

                if mem.get('id'):
                    st.markdown(f"**ID:** `{mem['id']}`")

                st.markdown(f"<span style='color: #666; font-size: 12px;'>Retrieved: {mem['timestamp']}</span>",
                           unsafe_allow_html=True)
    else:
        st.info("No memories retrieved yet. Start searching!")

# Footer
st.markdown("---")
st.markdown("""
### 📋 Demo Instructions

**Voice Demo:**
1. Record audio on your phone/device
2. Upload the file
3. Click "Transcribe & Search"
4. Watch REAL CoreML retrieval with speed metrics

**Text Demo:**
1. Type a query
2. Click "Search with CoreML"
3. See REAL on-device retrieval speed

**This uses REAL papr-pythonSDK with CoreML embeddings on your Mac!**
""")
