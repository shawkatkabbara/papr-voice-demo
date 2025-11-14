#!/usr/bin/env python3
"""
PAPR Voice Demo - Real-time voice conversation with on-device memory retrieval
Demo showcasing:
- On-device processing with CoreML (PAPR Python SDK)
- Real-time memory search with speed metrics
- Citation verification
- Clean UI for query → retrieval → response flow
"""

import streamlit as st
import asyncio
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import sys
from typing import List, Dict, Any
from openai import OpenAI

# Try to use local papr-pythonSDK if available (for development)
# Otherwise fall back to installed package
sdk_path = os.path.expanduser("~/Documents/GitHub/papr-pythonSDK/src")
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)

try:
    from papr_memory import Papr
except ImportError:
    st.error("❌ papr_memory not found. Install with: pip install papr-memory")
    st.stop()

# Load environment variables
load_dotenv()

# Ensure on-device processing environment variables are set
if not os.environ.get("PAPR_ONDEVICE_PROCESSING"):
    os.environ["PAPR_ONDEVICE_PROCESSING"] = "true"

# Page config
st.set_page_config(
    page_title="PAPR Voice Demo",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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
    .timestamp {
        color: #666;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'queries' not in st.session_state:
    st.session_state.queries = []
if 'memories' not in st.session_state:
    st.session_state.memories = []
if 'papr_client' not in st.session_state:
    # Initialize Papr client with on-device processing
    api_key = os.environ.get("PAPR_MEMORY_API_KEY")
    base_url = os.environ.get("PAPR_BASE_URL")

    client_kwargs = {
        "x_api_key": api_key,
        "timeout": 120.0
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    st.session_state.papr_client = Papr(**client_kwargs)
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'openai_client' not in st.session_state:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        st.session_state.openai_client = OpenAI(api_key=openai_key)
    else:
        st.session_state.openai_client = None

# Header
st.title("🎤 PAPR Voice Demo")
st.markdown("**Real-time voice conversation with on-device memory retrieval**")

# Sidebar for settings
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
    else:
        st.warning("⚠️ Disabled (Server-side processing)")

    st.markdown("### API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    papr_key = st.text_input("PAPR API Key", type="password", value=os.environ.get("PAPR_MEMORY_API_KEY", ""))

    base_url = os.environ.get("PAPR_BASE_URL", "https://memory.papr.ai")
    st.caption(f"Server: {base_url}")

    st.markdown("### Memory Settings")
    max_memories = st.slider("Max memories to retrieve", 1, 20, 5)
    enable_graph = st.checkbox("Enable graph retrieval", value=False)

    st.markdown("### Performance Stats")
    if st.session_state.queries:
        avg_latency = sum(q['latency'] for q in st.session_state.queries) / len(st.session_state.queries)
        st.metric("Avg Retrieval Speed", f"{avg_latency:.1f}ms")
        st.metric("Total Queries", len(st.session_state.queries))

    if st.button("🗑️ Clear History"):
        st.session_state.queries = []
        st.session_state.memories = []
        st.session_state.conversation_history = []
        st.rerun()

# Main layout - two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("💬 Conversation")

    # Voice input
    st.markdown("### 🎤 Voice Input")

    # Import audio recorder
    from audiorecorder import audiorecorder

    # Audio recorder
    audio = audiorecorder("🎤 Click to Record", "⏹️ Stop Recording")

    user_query = None

    if len(audio) > 0:
        # Show audio player
        st.audio(audio.export().read(), format="audio/wav")

        # Transcribe with OpenAI Whisper
        if st.session_state.openai_client:
            with st.spinner("🎧 Transcribing..."):
                try:
                    # Save audio to temp file
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        audio.export(tmp_file.name, format="wav")
                        tmp_file_path = tmp_file.name

                    # Transcribe
                    with open(tmp_file_path, "rb") as audio_file:
                        transcript = st.session_state.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                        user_query = transcript.text
                        st.success(f"✅ You said: \"{user_query}\"")

                    # Clean up temp file
                    os.unlink(tmp_file_path)

                except Exception as e:
                    st.error(f"❌ Transcription error: {str(e)}")
        else:
            st.warning("⚠️ OpenAI API key not configured")

    # Fallback text input
    st.markdown("### ⌨️ Or Type Your Query")
    text_query = st.text_input("Type your message:", key="user_input")

    if text_query and not user_query:
        user_query = text_query

    if st.button("🔍 Search & Respond") and user_query:
        with st.spinner("Searching memories..."):
            # Time the search
            start_time = time.perf_counter()

            try:
                # Search memories using Papr SDK
                response = st.session_state.papr_client.memory.search(
                    query=user_query,
                    max_memories=max_memories,
                    max_nodes=10,
                    enable_agentic_graph=enable_graph,
                    timeout=180.0
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                # Store query info
                query_data = {
                    'query': user_query,
                    'timestamp': datetime.now().isoformat(),
                    'latency': latency_ms,
                    'num_results': len(response.data.memories) if response and response.data else 0
                }
                st.session_state.queries.append(query_data)

                # Store retrieved memories
                if response and response.data and response.data.memories:
                    for mem in response.data.memories:
                        st.session_state.memories.append({
                            'content': mem.content,
                            'score': getattr(mem, 'score', 0.0),
                            'metadata': getattr(mem, 'metadata', {}),
                            'timestamp': datetime.now().isoformat(),
                            'query': user_query
                        })

                st.success(f"✅ Found {query_data['num_results']} memories in {latency_ms:.1f}ms")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Display conversation history
    st.markdown("### Conversation History")
    for query in reversed(st.session_state.queries[-10:]):  # Show last 10
        st.markdown(f"""
        <div class="query-box">
            <strong>Query:</strong> {query['query']}<br>
            <span class="timestamp">{query['timestamp']}</span><br>
            <strong>Results:</strong> {query['num_results']} memories<br>
            <strong>Speed:</strong> <span class="speed-metric">{query['latency']:.1f}ms</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.header("🧠 Retrieved Memories")

    if st.session_state.memories:
        st.markdown(f"**Total memories retrieved:** {len(st.session_state.memories)}")

        # Show memories grouped by query
        recent_memories = st.session_state.memories[-20:]  # Show last 20

        for i, mem in enumerate(reversed(recent_memories), 1):
            with st.expander(f"Memory {i} - Score: {mem['score']:.3f}", expanded=(i <= 3)):
                st.markdown(f"**Query:** {mem['query']}")
                st.markdown(f"**Content:**")
                st.write(mem['content'])

                if mem['metadata']:
                    st.markdown("**Metadata:**")
                    st.json(mem['metadata'])

                st.markdown(f"<span class='timestamp'>Retrieved: {mem['timestamp']}</span>",
                           unsafe_allow_html=True)
    else:
        st.info("No memories retrieved yet. Start searching!")

# Footer with instructions
st.markdown("---")
st.markdown("""
### 📋 Demo Instructions
1. **Configure API keys** in the sidebar
2. **Type a query** or use voice input (coming soon)
3. **Watch real-time retrieval** with speed metrics
4. **Click memories** to verify citations and see full content
5. **Monitor performance** stats in the sidebar

**On-device Processing:** ✅ Enabled (using CoreML for fast local embeddings)
""")
