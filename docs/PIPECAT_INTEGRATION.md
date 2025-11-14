# Pipecat Integration Guide

## Overview

This guide explains how the PAPR Voice Demo integrates with [Pipecat](https://github.com/pipecat-ai/pipecat), a framework for building voice and multimodal conversational AI applications.

## Architecture

```
┌─────────────┐      WebSocket       ┌──────────────────┐      HTTP        ┌─────────────────┐
│   Browser   │ ───────────────────> │ Pipecat Server   │ ──────────────> │ Flask CoreML    │
│ (voice.html)│  ws://localhost:8000 │   (port 8000)    │  localhost:3001  │  (port 3001)    │
└─────────────┘                       └──────────────────┘                  └─────────────────┘
                                             │                                      │
                                             │                                      ├─> CoreML
                                             │                                      │   Embeddings
                                             ├─> OpenAI Realtime API               │   (<100ms)
                                             │   (gpt-realtime-mini)                │
                                             │   • STT + LLM + TTS integrated       ├─> ChromaDB
                                             ├─> PAPR Memory Search                 │   Search
                                             └─> PAPR Cloud /v1/messages ───────────┘
```

## Key Components

### 1. PaprMemoryService

Custom Pipecat service that integrates with PAPR memory system:

```python
class PaprMemoryService(FrameProcessor):
    """
    - Searches memories using Flask CoreML server (localhost:3001)
    - Stores conversations using PAPR Cloud /v1/messages API
    - Injects relevant memories into LLM context
    """
```

**Features:**
- ✅ **Fast Memory Search** - Calls Flask CoreML at localhost:3001 for <100ms latency
- ✅ **Automatic Storage** - Stores all conversations via PAPR Cloud `/v1/messages` API
- ✅ **Context Injection** - Adds relevant memories before sending to LLM
- ✅ **Configurable** - Adjust search limit, similarity threshold

### 2. Pipecat Pipeline

The voice pipeline processes frames in this order:

```python
Pipeline([
    transport.input(),       # WebSocket audio input
    user_context,            # User message aggregation
    memory,                  # PAPR memory search & storage
    realtime,                # OpenAI Realtime API (gpt-realtime-mini-2025-10-06)
                             # Handles STT, LLM, and TTS in one service
    transport.output(),      # WebSocket audio output
    assistant_context        # Assistant response aggregation
])
```

## Installation

### 1. Install Dependencies

```bash
cd papr-voice-demo
poetry lock
poetry install
```

This installs:
- `pipecat-ai[silero,openai,whisper]` - Voice pipeline framework
- `fastapi` + `uvicorn` - WebSocket server
- All existing dependencies (Flask, PAPR SDK, etc.)

### 2. Configure Environment

Update your `.env` file:

```bash
# API Keys (required)
OPENAI_API_KEY=sk-...
PAPR_MEMORY_API_KEY=papr_...

# Server URLs
PYTHON_SERVICE_URL=http://localhost:3001  # Flask CoreML server
PAPR_CLOUD_URL=https://memory.papr.ai     # PAPR Cloud API

# CoreML Configuration (for Flask server)
PAPR_ENABLE_COREML=true
PAPR_COREML_MODEL=/path/to/Qwen3-Embedding-4B-FP16-Final.mlpackage
```

## Usage

### Start Servers

Use the startup script to run both servers:

```bash
./scripts/run-pipecat.sh
```

This starts:
1. **Flask CoreML Server** (port 3001) - Fast on-device embeddings
2. **Pipecat Voice Server** (port 8000) - WebSocket voice interface

### Connect from Browser

Update `voice.html` to connect to Pipecat WebSocket:

```javascript
// Replace existing OpenAI Realtime connection with:
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected to Pipecat voice server');
};

ws.onmessage = (event) => {
    // Handle audio frames from Pipecat
    const data = ProtobufDecoder.decode(event.data);
    // ... process audio
};
```

### Test the Integration

1. Open voice.html in your browser
2. Click the microphone button
3. Say: *"What are my current tasks?"*
4. Watch the console:
   - ✅ Memory search: X results in <100ms
   - ✅ Message stored: msg_xyz (queued: true)

## How It Works

### Memory Search Flow

1. **User speaks** → Browser sends audio via WebSocket
2. **OpenAI Realtime API (STT)** → Converts speech to text: "What are my tasks?"
3. **PAPR Memory Search**:
   ```python
   POST http://localhost:3001/api/search
   {
     "query": "What are my tasks?",
     "max_memories": 5,
     "rank_results": true
   }
   ```
4. **Flask CoreML** → Generates embeddings on-device (<100ms)
5. **ChromaDB** → Searches local vector database
6. **Memory Injection** → Adds context:
   ```
   [MEMORY CONTEXT]
   Relevant information from previous conversations:
   1. "Finish Q4 roadmap by Friday" (relevance: 0.92)
   2. "Review pull requests for voice demo" (relevance: 0.87)
   [END CONTEXT]
   ```
7. **LLM Response** → gpt-realtime-mini uses context to answer
8. **Audio Output** → Realtime API generates speech, sent back via WebSocket

### Conversation Storage

Every message is automatically stored:

```python
POST https://memory.papr.ai/v1/messages
Headers: { "X-API-Key": "papr_..." }
{
  "content": "What are my tasks?",
  "role": "user",
  "sessionId": "voice_session_12345",
  "process_messages": true
}
```

This triggers:
- ✅ Message storage in PostMessage class
- ✅ Background AI analysis
- ✅ Automatic memory creation with tags/topics
- ✅ Role-based categorization (user: task, preference, goal, etc.)

## Performance

### Latency Breakdown

**Total end-to-end latency: ~150-250ms**

```
Component                        Latency
──────────────────────────────────────────
OpenAI Realtime API              50-100ms
  ├─ STT (integrated)            ~20-30ms
  ├─ LLM (gpt-realtime-mini)     ~20-40ms
  └─ TTS (integrated)            ~10-30ms
Memory Search (CoreML)           80-110ms
  ├─ Embeddings                  50-75ms
  └─ ChromaDB Search             20-30ms
Audio Encoding                   10-20ms
──────────────────────────────────────────
Total                            ~150-250ms
```

**Key Optimizations**:
- **Flask CoreML runs on localhost**, avoiding network latency for memory search (3-5x faster than cloud-based embedding services)
- **gpt-realtime-mini-2025-10-06** is optimized for low-latency voice (cheaper and faster than gpt-4o: $0.60/1M vs $1.25/1M input tokens)
- **Integrated STT/TTS** in Realtime API reduces overhead compared to separate services

## Customization

### Adjust Search Parameters

```python
memory = PaprMemoryService(
    user_id=user_id,
    session_id=session_id,
    search_limit=5,        # Max memories to retrieve
    search_threshold=0.7   # Minimum similarity score (0.0-1.0)
)
```

### Change Voice Model

```python
realtime = OpenAIRealtimeService(
    api_key=OPENAI_API_KEY,
    model="gpt-realtime-mini-2025-10-06",  # Cost-efficient ($0.60/1M tokens)
    # Or use "gpt-4o-realtime-preview" for higher quality (more expensive)
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    temperature=0.8,
    system_prompt="Your custom prompt here..."
)
```

### Disable Message Storage

```python
async def _store_message(self, content: str, role: str):
    # Comment out to disable storage
    # return

    response = await self._httpx_client.post(...)
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Flask CoreML Not Responding

```bash
# Check Flask server status
curl http://localhost:3001/api/keys

# View Flask logs in terminal
# (Started by run-pipecat.sh)
```

### Memory Search Fails

Check the Pipecat server logs for:
```
⚠️  Memory search failed: 500
❌ Memory search error: Connection refused
```

Solution:
1. Ensure Flask CoreML server is running (port 3001)
2. Check `PYTHON_SERVICE_URL` in `.env`
3. Verify CoreML model is loaded

### No Memories Returned

If search returns 0 results:
- Lower `search_threshold` (default: 0.7)
- Add more memories to your database
- Check query relevance

## Next Steps

- [ ] Update voice.html to use Pipecat WebSocket
- [ ] Add visual indicators for memory search
- [ ] Display latency breakdown in UI
- [ ] Implement session history viewer
- [ ] Add support for voice interruptions

## Resources

- [Pipecat Documentation](https://github.com/pipecat-ai/pipecat)
- [PAPR Memory API Docs](https://docs.papr.ai)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
