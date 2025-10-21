#!/usr/bin/env python3
"""
PAPR Voice Orb Demo - Real-time voice conversation with animated orb UI
"""

import streamlit as st
import streamlit.components.v1 as components
from audiorecorder import audiorecorder
import os
import time
import sys
import io
import json
import base64
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import websockets

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
    page_title="PAPR Voice Orb",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Voice Orb HTML/CSS/JS Component
def voice_orb_component(state="idle"):
    """
    Render animated voice orb using WebGL
    States: idle, listening, thinking, speaking
    """
    orb_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #000814 0%, #001d3d 100%);
                overflow: hidden;
            }}
            #orb-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 500px;
                position: relative;
            }}
            canvas {{
                max-width: 100%;
                max-height: 100%;
            }}
            #status {{
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                color: #fff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 18px;
                font-weight: 500;
                text-transform: capitalize;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div id="orb-container">
            <canvas id="orb" width="400" height="400"></canvas>
            <div id="status">{state}</div>
        </div>

        <script>
            const canvas = document.getElementById('orb');
            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;

            // State colors - Papr brand gradient
            const colors = {{
                idle: {{ r: 1, g: 97, b: 224 }},         // #0161E0 - Papr Blue
                listening: {{ r: 0, g: 254, b: 254 }},   // #00FEFE - Bright Cyan (active)
                thinking: {{ r: 12, g: 205, b: 255 }},   // #0CCDFF - Cyan (processing)
                speaking: {{ r: 1, g: 97, b: 224 }}      // #0161E0 - Papr Blue (output)
            }};

            let currentState = '{state}';
            let particles = [];
            let time = 0;

            // Particle system for organic, flowing orb
            class Particle {{
                constructor(angle, radius) {{
                    this.angle = angle;
                    this.radius = radius;
                    this.baseRadius = radius;
                    this.offset = Math.random() * Math.PI * 2;
                    this.flowOffset = Math.random() * Math.PI * 2;
                }}

                update() {{
                    // Organic, flowing animation inspired by Papr logo curves
                    let amplitude = 8;
                    let speed = 0.015;
                    let flowIntensity = 0.3;

                    if (currentState === 'listening') {{
                        amplitude = 25;
                        speed = 0.06;
                        flowIntensity = 0.5;
                    }} else if (currentState === 'thinking') {{
                        amplitude = 18;
                        speed = 0.12;
                        flowIntensity = 0.8;
                    }} else if (currentState === 'speaking') {{
                        amplitude = 22;
                        speed = 0.04;
                        flowIntensity = 0.4;
                    }}

                    // Create flowing, wave-like motion
                    const wave1 = Math.sin(time * speed + this.offset) * amplitude;
                    const wave2 = Math.cos(time * speed * 1.3 + this.flowOffset) * amplitude * flowIntensity;
                    this.radius = this.baseRadius + wave1 + wave2;
                }}

                draw() {{
                    const x = centerX + Math.cos(this.angle) * this.radius;
                    const y = centerY + Math.sin(this.angle) * this.radius;

                    const color = colors[currentState] || colors.idle;

                    // Create gradient that transitions through Papr brand colors
                    const gradient = ctx.createRadialGradient(x, y, 0, x, y, 8);

                    // Gradient stops matching Papr logo gradient
                    if (currentState === 'thinking' || currentState === 'listening') {{
                        // Bright cyan glow for active states
                        gradient.addColorStop(0, `rgba(${{color.r}}, ${{color.g}}, ${{color.b}}, 0.9)`);
                        gradient.addColorStop(0.5, `rgba(12, 205, 255, 0.6)`);
                        gradient.addColorStop(1, `rgba(0, 254, 254, 0)`);
                    }} else {{
                        // Deep blue glow for idle/speaking
                        gradient.addColorStop(0, `rgba(${{color.r}}, ${{color.g}}, ${{color.b}}, 0.8)`);
                        gradient.addColorStop(0.6, `rgba(12, 205, 255, 0.4)`);
                        gradient.addColorStop(1, `rgba(0, 254, 254, 0)`);
                    }}

                    ctx.fillStyle = gradient;
                    ctx.beginPath();
                    ctx.arc(x, y, 6, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }}

            // Initialize particles in circular formation
            function initParticles() {{
                particles = [];
                const numParticles = 60;
                const baseRadius = 100;

                for (let i = 0; i < numParticles; i++) {{
                    const angle = (i / numParticles) * Math.PI * 2;
                    particles.push(new Particle(angle, baseRadius));
                }}
            }}

            // Draw core glow with Papr gradient
            function drawCore() {{
                const color = colors[currentState] || colors.idle;
                const pulseSize = 45 + Math.sin(time * 0.05) * 12;

                // Multi-layer gradient core matching Papr brand
                const gradient = ctx.createRadialGradient(
                    centerX, centerY, 0,
                    centerX, centerY, pulseSize * 1.5
                );

                // Create the blue → cyan → bright cyan gradient
                gradient.addColorStop(0, `rgba(${{color.r}}, ${{color.g}}, ${{color.b}}, 0.7)`);
                gradient.addColorStop(0.3, `rgba(1, 97, 224, 0.5)`);      // #0161E0
                gradient.addColorStop(0.6, `rgba(12, 205, 255, 0.3)`);    // #0CCDFF
                gradient.addColorStop(0.85, `rgba(0, 254, 254, 0.15)`);   // #00FEFE
                gradient.addColorStop(1, `rgba(0, 254, 254, 0)`);

                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.arc(centerX, centerY, pulseSize * 1.5, 0, Math.PI * 2);
                ctx.fill();

                // Add inner bright core
                const innerGradient = ctx.createRadialGradient(
                    centerX, centerY, 0,
                    centerX, centerY, pulseSize * 0.5
                );
                innerGradient.addColorStop(0, `rgba(0, 254, 254, 0.4)`);
                innerGradient.addColorStop(1, `rgba(${{color.r}}, ${{color.g}}, ${{color.b}}, 0)`);

                ctx.fillStyle = innerGradient;
                ctx.beginPath();
                ctx.arc(centerX, centerY, pulseSize * 0.5, 0, Math.PI * 2);
                ctx.fill();
            }}

            // Animation loop
            function animate() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Draw core
                drawCore();

                // Update and draw particles
                particles.forEach(particle => {{
                    particle.update();
                    particle.draw();
                }});

                time += 1;
                requestAnimationFrame(animate);
            }}

            // Initialize and start
            initParticles();
            animate();

            // Listen for state changes from parent
            window.addEventListener('message', (event) => {{
                if (event.data.type === 'updateState') {{
                    currentState = event.data.state;
                    document.getElementById('status').textContent = currentState;
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(orb_html, height=550)

# Initialize session state
if 'queries' not in st.session_state:
    st.session_state.queries = []
if 'memories' not in st.session_state:
    st.session_state.memories = []
if 'orb_state' not in st.session_state:
    st.session_state.orb_state = "idle"
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

if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = os.environ.get("OPENAI_API_KEY")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'last_audio_response' not in st.session_state:
    st.session_state.last_audio_response = None

if 'last_transcript' not in st.session_state:
    st.session_state.last_transcript = None

def search_memories_real(query: str, max_results: int = 30):
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
                # Try to get score from pydantic_extra__ first, then fallback to direct attribute
                score = 0.0
                if hasattr(mem, 'pydantic_extra__') and mem.pydantic_extra__:
                    score = mem.pydantic_extra__.get('similarity_score', 0.0)
                else:
                    score = getattr(mem, 'score', 0.0)

                memories.append({
                    'content': mem.content,
                    'score': score,
                    'metadata': getattr(mem, 'metadata', {}),
                    'id': getattr(mem, 'id', 'N/A')
                })

        return memories, latency_ms

    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")

async def process_voice_with_realtime_api(audio_bytes):
    """
    Process voice using OpenAI Realtime API with audio-to-audio and tool calling.
    Returns: (audio_response_bytes, transcript, memories)
    """

    if not st.session_state.openai_api_key:
        raise Exception("OpenAI API key not configured")

    # WebSocket URL for Realtime API
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
    headers = {
        "Authorization": f"Bearer {st.session_state.openai_api_key}",
        "OpenAI-Beta": "realtime=v1"
    }

    audio_response = b""
    transcript = ""
    memories_found = []

    try:
        async with websockets.connect(url, extra_headers=headers) as ws:

            # 1. Configure session with tool definition
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "You are a helpful memory assistant. When users ask about their memories, use the search_papr_memories tool to find relevant information. Provide detailed citations with memory IDs and similarity scores.",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": None,  # Manual turn-taking
                    "tools": [{
                        "type": "function",
                        "name": "search_papr_memories",
                        "description": "Search the user's personal memory database using PAPR for relevant information. Use this when the user asks questions about their past conversations, meetings, projects, or any stored information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query to find relevant memories"
                                },
                                "max_results": {
                                    "type": "number",
                                    "description": "Maximum number of memories to return (default 30)"
                                }
                            },
                            "required": ["query"]
                        }
                    }],
                    "tool_choice": "auto"
                }
            }
            await ws.send(json.dumps(session_config))

            # 2. Send audio input
            audio_b64 = base64.b64encode(audio_bytes).decode()
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": audio_b64
            }))

            # 3. Commit audio and create response
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await ws.send(json.dumps({"type": "response.create"}))

            # 4. Listen for events
            async for message in ws:
                event = json.loads(message)
                event_type = event.get("type")

                # User speech transcribed
                if event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")

                # Function/tool call requested
                elif event_type == "response.function_call_arguments.done":
                    call_id = event.get("call_id")
                    function_name = event.get("name")
                    args_str = event.get("arguments", "{}")

                    if function_name == "search_papr_memories":
                        # Parse arguments
                        args = json.loads(args_str)
                        query = args.get("query", "")
                        max_results = args.get("max_results", 30)

                        # Execute memory search
                        memories_found, latency_ms = search_memories_real(query, int(max_results))

                        # Format results for LLM
                        formatted_memories = []
                        for mem in memories_found:
                            formatted_memories.append({
                                "content": mem['content'],
                                "score": float(mem['score']),
                                "id": mem['id']
                            })

                        # Send tool result back to API
                        tool_result = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": json.dumps({
                                    "memories": formatted_memories,
                                    "count": len(formatted_memories),
                                    "latency_ms": latency_ms
                                })
                            }
                        }
                        await ws.send(json.dumps(tool_result))

                        # Request continuation of response
                        await ws.send(json.dumps({"type": "response.create"}))

                # Audio response chunks
                elif event_type == "response.audio.delta":
                    audio_chunk = base64.b64decode(event.get("delta", ""))
                    audio_response += audio_chunk

                # Response completed
                elif event_type == "response.done":
                    break

                # Errors
                elif event_type == "error":
                    raise Exception(f"Realtime API error: {event.get('error', {})}")

        return audio_response, transcript, memories_found

    except Exception as e:
        raise Exception(f"Realtime API error: {str(e)}")

# Header with logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("logo.png", width=80)
with col_title:
    st.title("PAPR Voice Orb")
    st.markdown("**Talk to your memories with real-time voice and visual feedback**")

# Sidebar
with st.sidebar:
    st.header("Settings")

    # Show on-device processing status
    ondevice_enabled = os.environ.get("PAPR_ONDEVICE_PROCESSING", "false").lower() in ("true", "1", "yes")
    coreml_enabled = os.environ.get("PAPR_ENABLE_COREML", "false").lower() in ("true", "1", "yes")

    st.markdown("### On-Device Processing")
    if ondevice_enabled:
        st.success("✅ Enabled")
        if coreml_enabled:
            st.info("⚡ CoreML Acceleration Active")
            coreml_model = os.environ.get("PAPR_COREML_MODEL", "")
            if coreml_model:
                st.caption(f"Model: {os.path.basename(coreml_model)}")
    else:
        st.warning("⚠️ Disabled (Server-side processing)")

    st.markdown("### Performance Stats")
    if st.session_state.queries:
        # Deduplicate queries by timestamp
        unique_queries = {q['timestamp']: q for q in st.session_state.queries}.values()
        unique_queries_list = list(unique_queries)

        avg_latency = sum(q['latency'] for q in unique_queries_list) / len(unique_queries_list)
        st.metric("Avg Retrieval Speed", f"{avg_latency:.1f}ms")
        st.metric("Total Queries", len(unique_queries_list))

    if st.button("Clear History"):
        st.session_state.queries = []
        st.session_state.memories = []
        st.rerun()

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Voice Orb")

    # Render voice orb
    voice_orb_component(st.session_state.orb_state)

    st.markdown("---")

    # Voice controls
    st.markdown("### Voice Input")
    st.caption("Click to speak, the orb will respond to your voice")

    # Audio recorder
    audio_bytes = audiorecorder("Click to record", "Recording...")

    if audio_bytes:
        st.session_state.orb_state = "listening"

        with st.spinner("Processing voice with Realtime API..."):
            try:
                # Process with Realtime API
                st.session_state.orb_state = "thinking"

                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_response, transcript, memories = loop.run_until_complete(
                    process_voice_with_realtime_api(audio_bytes)
                )
                loop.close()

                # Store results
                st.session_state.last_transcript = transcript
                st.session_state.last_audio_response = audio_response

                # Save conversation
                if transcript and memories:
                    st.session_state.conversation_history.append({
                        'transcript': transcript,
                        'timestamp': datetime.now().isoformat(),
                        'num_memories': len(memories)
                    })

                    # Save memories
                    for mem in memories:
                        st.session_state.memories.append({
                            **mem,
                            'timestamp': datetime.now().isoformat(),
                            'query': transcript
                        })

                    if transcript not in [q['query'] for q in st.session_state.queries]:
                        st.session_state.queries.append({
                            'query': transcript,
                            'timestamp': datetime.now().isoformat(),
                            'latency': 0,  # Handled by Realtime API
                            'num_results': len(memories)
                        })

                st.session_state.orb_state = "speaking"

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.orb_state = "idle"

    # Display transcript and audio response
    if st.session_state.last_transcript:
        st.markdown("---")
        st.markdown("**You said:**")
        st.info(st.session_state.last_transcript)

    if st.session_state.last_audio_response:
        st.markdown("**AI Response:**")
        st.audio(st.session_state.last_audio_response, format="audio/wav", sample_rate=24000)
        st.session_state.orb_state = "idle"

    # Text input fallback
    st.markdown("---")
    st.markdown("### Or Type Your Query")
    text_query = st.text_input("Type your message:", key="user_input")

    if st.button("🔍 Search", use_container_width=True) and text_query:
        st.session_state.orb_state = "thinking"

        with st.spinner("Searching memories..."):
            try:
                results, latency_ms = search_memories_real(text_query, 30)

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
                st.session_state.orb_state = "idle"

            except Exception as e:
                st.error(f"❌ Search error: {str(e)}")
                st.session_state.orb_state = "idle"

with col2:
    st.header("Retrieved Memories")

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
        st.info("💡 No memories retrieved yet. Ask a question to see your memories!")

# Footer
st.markdown("---")
st.markdown("""
### How It Works

**Voice Orb States:**
- 🔵 **Idle** - Papr Blue (#0161E0), ready and waiting
- 💎 **Listening** - Bright Cyan (#00FEFE), actively capturing
- ⚡ **Thinking** - Cyan (#0CCDFF), searching memories with CoreML
- 🔵 **Speaking** - Papr Blue (#0161E0), delivering insights

**Demo:**
1. Type a query (voice input coming soon)
2. Watch the orb animate as it searches
3. See real similarity scores from CoreML embeddings
4. Get instant access to your personal memories

**Powered by:**
- 🧠 PAPR Memory SDK with Apple Neural Engine
- 🎨 Papr Brand Design System
- ⚡ CoreML Qwen3-4B Embeddings (~70-220ms)
- 🎤 OpenAI Realtime API (voice integration in progress)
""")
