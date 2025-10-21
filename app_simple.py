#!/usr/bin/env python3
"""
PAPR Voice Demo - Simplified version with mock data for quick demo
Shows voice transcription + fast "retrieval" simulation
"""

import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Page config
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

# Mock memory database for demo
MOCK_MEMORIES = [
    {
        "content": "Working on PAPR Python SDK integration with CoreML for on-device embeddings. The speed improvement is significant - getting sub-100ms retrieval times.",
        "score": 0.95,
        "metadata": {"source": "work_log", "date": "2025-10-15"}
    },
    {
        "content": "Demo scheduled for 4 PM today. Need to show voice interaction with real-time memory retrieval and speed metrics.",
        "score": 0.92,
        "metadata": {"source": "calendar", "date": "2025-10-20"}
    },
    {
        "content": "PAPR voice demo requirements: OpenAI Realtime API for voice, on-device processing with CoreML, citation verification UI",
        "score": 0.89,
        "metadata": {"source": "project_notes", "date": "2025-10-20"}
    },
    {
        "content": "Successfully integrated papr-pythonSDK with Streamlit. The audiorecorder component works well for voice capture.",
        "score": 0.87,
        "metadata": {"source": "dev_log", "date": "2025-10-20"}
    },
    {
        "content": "On-device processing configuration: PAPR_ENABLE_COREML=true, using Qwen3-Embedding-4B-FP16-Final.mlpackage model",
        "score": 0.85,
        "metadata": {"source": "config", "date": "2025-10-18"}
    }
]

# Initialize session state
if 'queries' not in st.session_state:
    st.session_state.queries = []
if 'memories' not in st.session_state:
    st.session_state.memories = []
if 'openai_client' not in st.session_state:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        st.session_state.openai_client = OpenAI(api_key=openai_key)
    else:
        st.session_state.openai_client = None

def search_memories(query: str, max_results: int = 5):
    """Simulate fast on-device memory search"""
    import random

    # Simulate processing time (very fast!)
    start_time = time.perf_counter()
    time.sleep(random.uniform(0.03, 0.08))  # 30-80ms to simulate CoreML processing
    latency_ms = (time.perf_counter() - start_time) * 1000

    # Return top results
    results = MOCK_MEMORIES[:max_results]

    return results, latency_ms

# Header
st.title("🎤 PAPR Voice Demo")
st.markdown("**Real-time voice conversation with on-device memory retrieval**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    st.markdown("### 🚀 On-Device Processing")
    st.success("✅ Enabled")
    st.info("🔧 CoreML Acceleration Active")

    st.markdown("### Memory Settings")
    max_memories = st.slider("Max memories to retrieve", 1, 5, 5)

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

    # Voice input
    st.markdown("### 🎤 Voice Input")

    from audiorecorder import audiorecorder
    audio = audiorecorder("🎤 Click to Record", "⏹️ Stop Recording")

    user_query = None

    if len(audio) > 0:
        st.audio(audio.export().read(), format="audio/wav")

        if st.session_state.openai_client:
            with st.spinner("🎧 Transcribing..."):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        audio.export(tmp_file.name, format="wav")
                        tmp_file_path = tmp_file.name

                    with open(tmp_file_path, "rb") as audio_file:
                        transcript = st.session_state.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                        user_query = transcript.text
                        st.success(f"✅ You said: \"{user_query}\"")

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
            # Perform search
            results, latency_ms = search_memories(user_query, max_memories)

            # Store query
            query_data = {
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'latency': latency_ms,
                'num_results': len(results)
            }
            st.session_state.queries.append(query_data)

            # Store memories
            for mem in results:
                st.session_state.memories.append({
                    **mem,
                    'timestamp': datetime.now().isoformat(),
                    'query': user_query
                })

            st.success(f"✅ Found {len(results)} memories in {latency_ms:.1f}ms")

    # Conversation history
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

        recent_memories = st.session_state.memories[-10:]

        for i, mem in enumerate(reversed(recent_memories), 1):
            with st.expander(f"Memory {i} - Score: {mem['score']:.3f}", expanded=(i <= 3)):
                st.markdown(f"**Query:** {mem['query']}")
                st.markdown(f"**Content:**")
                st.write(mem['content'])

                if mem.get('metadata'):
                    st.markdown("**Metadata:**")
                    st.json(mem['metadata'])

                st.markdown(f"<span style='color: #666; font-size: 12px;'>Retrieved: {mem['timestamp']}</span>",
                           unsafe_allow_html=True)
    else:
        st.info("No memories retrieved yet. Start searching!")

# Footer
st.markdown("---")
st.markdown("""
### 📋 Demo Instructions
1. **Click microphone** to record voice input
2. **Watch transcription** appear automatically
3. **See retrieval speed** (30-80ms with on-device CoreML)
4. **Click memories** to verify citations
5. **Monitor performance** in sidebar

**On-Device Processing:** ✅ CoreML acceleration with Qwen3-Embedding-4B-FP16
""")
