"""
PAPR Voice Demo - Pipecat Voice Server

This server provides real-time voice conversations with PAPR memory integration:
- Voice input/output via OpenAI Realtime API
- Memory search using local Flask CoreML server (<100ms latency)
- Automatic conversation storage via PAPR Cloud /v1/messages API
- WebSocket connection for browser-based voice interface
"""

import asyncio
import os
import httpx
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket
from pipecat.frames.frames import TextFrame, Frame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.services.openai import (
    OpenAILLMService,
    OpenAIUserContextAggregator,
    OpenAIAssistantContextAggregator,
    OpenAIRealtimeService
)
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams
)
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

# Load environment variables
load_dotenv()

# Configuration
FLASK_COREML_URL = os.getenv("PYTHON_SERVICE_URL", "http://localhost:3001")
PAPR_CLOUD_URL = os.getenv("PAPR_CLOUD_URL", "https://memory.papr.ai")
PAPR_API_KEY = os.getenv("PAPR_MEMORY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()


class PaprMemoryService(FrameProcessor):
    """
    Custom Pipecat service that integrates with PAPR memory system.

    - Searches memories using Flask CoreML server (localhost:3001) for <100ms latency
    - Stores conversations using PAPR Cloud /v1/messages API
    - Injects relevant memories into LLM context
    """

    def __init__(
        self,
        user_id: str,
        session_id: str,
        flask_url: str = FLASK_COREML_URL,
        papr_cloud_url: str = PAPR_CLOUD_URL,
        papr_api_key: Optional[str] = None,
        search_limit: int = 5,
        search_threshold: float = 0.7,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.session_id = session_id
        self.flask_url = flask_url
        self.papr_cloud_url = papr_cloud_url
        self.papr_api_key = papr_api_key or PAPR_API_KEY
        self.search_limit = search_limit
        self.search_threshold = search_threshold
        self._httpx_client = httpx.AsyncClient(timeout=5.0)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and inject memory context when needed"""

        # When we get user text, search for relevant memories
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            user_message = frame.text

            # Search for relevant memories using Flask CoreML server
            memories = await self._search_memories(user_message)

            # Store the user message via PAPR Cloud
            await self._store_message(user_message, role="user")

            # If we found relevant memories, inject them as context
            if memories:
                memory_context = self._format_memories(memories)
                # Create a system message with memory context
                context_frame = TextFrame(f"[MEMORY CONTEXT]\n{memory_context}\n[END CONTEXT]")
                # Push context frame before the user message
                await self.push_frame(context_frame, direction)

        # Pass the original frame through
        await self.push_frame(frame, direction)

    async def _search_memories(self, query: str) -> list:
        """Search memories using Flask CoreML server (fast, on-device)"""
        try:
            response = await self._httpx_client.post(
                f"{self.flask_url}/api/search",
                json={
                    "query": query,
                    "max_memories": self.search_limit,
                    "enable_agentic_graph": False,  # Fast semantic search only
                    "rank_results": True,  # CoreML optimization
                }
            )

            if response.status_code == 200:
                data = response.json()
                memories = data.get("data", {}).get("memories", [])
                latency_ms = data.get("latency_ms", 0)

                print(f"✅ Memory search: {len(memories)} results in {latency_ms:.1f}ms")

                # Filter by similarity threshold
                filtered = [
                    m for m in memories
                    if m.get("query_similarity", 0) >= self.search_threshold
                ]

                return filtered
            else:
                print(f"⚠️  Memory search failed: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Memory search error: {e}")
            return []

    async def _store_message(self, content: str, role: str):
        """Store conversation message via PAPR Cloud /v1/messages API"""
        if not self.papr_api_key:
            print("⚠️  No PAPR API key, skipping message storage")
            return

        try:
            response = await self._httpx_client.post(
                f"{self.papr_cloud_url}/v1/messages",
                headers={"X-API-Key": self.papr_api_key},
                json={
                    "content": content,
                    "role": role,
                    "sessionId": self.session_id,
                    "process_messages": True,  # Enable AI analysis
                }
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Message stored: {data.get('message_id')} (queued: {data.get('queued_for_processing')})")
            else:
                print(f"⚠️  Message storage failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Message storage error: {e}")

    def _format_memories(self, memories: list) -> str:
        """Format memories for LLM context injection"""
        if not memories:
            return "No relevant memories found."

        context_parts = ["Relevant information from previous conversations:"]

        for i, memory in enumerate(memories[:self.search_limit], 1):
            content = memory.get("content", "")
            similarity = memory.get("query_similarity", 0)
            tags = memory.get("tags", [])

            context_parts.append(
                f"\n{i}. {content} (relevance: {similarity:.2f})"
            )
            if tags:
                context_parts.append(f"   Tags: {', '.join(tags)}")

        return "\n".join(context_parts)

    async def cleanup(self):
        """Cleanup HTTP client"""
        await self._httpx_client.aclose()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice conversation with PAPR memory"""
    await websocket.accept()

    # Generate session ID from client or use default
    user_id = "demo_user"  # Could be extracted from query params
    session_id = f"voice_session_{asyncio.get_event_loop().time()}"

    print(f"🎤 New voice session: {session_id}")

    try:
        # Configure WebSocket transport with VAD
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=ProtobufFrameSerializer(),
            )
        )

        # Context aggregators
        user_context = OpenAIUserContextAggregator()
        assistant_context = OpenAIAssistantContextAggregator()

        # PAPR Memory Service (calls Flask CoreML + PAPR Cloud)
        memory = PaprMemoryService(
            user_id=user_id,
            session_id=session_id,
            search_limit=5,
            search_threshold=0.7
        )

        # OpenAI Realtime API service (handles both STT and LLM)
        # Using gpt-realtime-mini-2025-10-06 for cost-efficient real-time voice
        realtime = OpenAIRealtimeService(
            api_key=OPENAI_API_KEY,
            model="gpt-realtime-mini-2025-10-06",
            system_prompt=(
                "You are a helpful voice assistant with access to the user's memory. "
                "When you receive MEMORY CONTEXT, use it to provide personalized responses. "
                "Be conversational and natural."
            ),
            voice="alloy",  # OpenAI voice option
            temperature=0.8,
        )

        # Build pipeline: input → user_context → MEMORY → Realtime API → output
        # Note: Realtime API handles both STT and TTS internally
        pipeline = Pipeline([
            transport.input(),
            user_context,
            memory,  # PAPR memory integration
            realtime,  # Integrated STT + LLM + TTS
            transport.output(),
            assistant_context
        ])

        # Create and run task
        runner = PipelineRunner()
        task = PipelineTask(pipeline)

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            """Send welcome message when client connects"""
            await task.queue_frame(
                TextFrame("Hello! I'm your voice assistant with memory. How can I help you today?")
            )

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            """Cleanup when client disconnects"""
            print(f"🛑 Client disconnected from session: {session_id}")
            await memory.cleanup()
            await task.cancel()

        # Run the pipeline
        await runner.run(task)

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await websocket.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Flask CoreML server
    flask_healthy = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{FLASK_COREML_URL}/api/keys")
            flask_healthy = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy" if flask_healthy else "degraded",
        "pipecat_server": "up",
        "flask_coreml": "up" if flask_healthy else "down",
        "papr_cloud": "configured" if PAPR_API_KEY else "not_configured"
    }


if __name__ == "__main__":
    import uvicorn

    print("""
╔═══════════════════════════════════════════════════════╗
║  🎤 PAPR Voice Demo - Pipecat Server                 ║
║                                                       ║
║  WebSocket:  ws://localhost:8000/ws                  ║
║  Health:     http://localhost:8000/health            ║
║                                                       ║
║  Flask CoreML: {FLASK_COREML_URL}              ║
║  PAPR Cloud:   {PAPR_CLOUD_URL}   ║
╚═══════════════════════════════════════════════════════╝
    """.format(
        FLASK_COREML_URL=FLASK_COREML_URL,
        PAPR_CLOUD_URL=PAPR_CLOUD_URL
    ))

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
