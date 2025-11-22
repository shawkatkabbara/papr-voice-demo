# 🎤 PAPR Voice Demo

Real-time voice conversation with on-device memory retrieval, showcasing the speed and capabilities of PAPR's Python SDK with CoreML-powered on-device processing.

## ✨ Features

- **🎤 Voice Input** - OpenAI Realtime API for natural voice conversations with Constellation UI
- **⚡ On-Device Processing** - CoreML-accelerated embeddings with PAPR Python SDK (<100ms latency)
- **🌟 Constellation Visualization** - Interactive particle system showing search history
- **📊 Real-time Metrics** - Live display of query processing and retrieval speed with latency breakdown
- **🔍 Citation Verification** - Click any constellation point to see retrieved memories
- **📈 Performance Dashboard** - Track embedding, search, and total latency per query

## 📁 Project Structure

```
papr-voice-demo/
├── README.md                  # This file
├── voice.html                 # Constellation UI frontend
├── docs/                      # Documentation
│   ├── TESTING.md            # Comprehensive testing guide
│   ├── DEMO_GUIDE.md         # Demo presentation guide
│   ├── QUICK_START.md        # Quick start guide
│   └── RUN_CONSTELLATION.md  # Constellation UI guide
├── src/
│   ├── python/               # Python microservice (CoreML + Flask)
│   │   ├── voice_server.py   # Flask server with CoreML embeddings
│   │   └── tool_schemas.py   # Pydantic schemas for validation
│   └── server/               # TypeScript backend (Fastify + Pipecat)
│       ├── src/
│       │   ├── index.ts      # Main Fastify server
│       │   ├── services/     # Service layer (PaprMemoryService)
│       │   └── types/        # TypeScript type definitions
│       ├── package.json      # Node.js dependencies
│       └── tsconfig.json     # TypeScript configuration
├── scripts/                   # Utility scripts
│   ├── dev.sh                # Start both Python + TypeScript servers
│   ├── test.sh               # Run all tests (Python + TypeScript)
│   ├── setup-poetry.sh       # Setup Poetry environment
│   ├── warmup_model.py       # Preload CoreML model
│   ├── resource_check.py     # Check system resources
│   └── cleanup_memory.sh     # Clean up memory
├── tests/                     # Python tests
│   ├── test_tool_schemas.py  # Pydantic validation tests (17 tests)
│   └── test_voice_server.py  # Flask endpoint tests (21 tests)
└── pyproject.toml            # Poetry configuration
```

## 🚀 Quick Start

### 1. Easy Setup with Script

```bash
cd papr-voice-demo

# Run setup script (creates venv, installs deps, copies .env)
./scripts/setup.sh

# Edit .env and add your API keys
nano .env
```

### 2. Check System Resources (Recommended)

Before enabling on-device processing, check if your system has enough resources:

```bash
# Activate venv first
source venv/bin/activate

# Check resources
python scripts/resource_check.py
```

This will check:
- **Disk Space**: Need 30GB+ free for CoreML compilation
- **RAM**: Need 6GB+ available for model runtime
- **Memory Pressure**: Should be <85%

The script will recommend either on-device or API backend processing.

### 3. Configure API Keys

Edit `.env` file:

```bash
OPENAI_API_KEY=sk-...
PAPR_MEMORY_API_KEY=papr_...

# Set based on resource_check.py recommendation:
PAPR_ONDEVICE_PROCESSING=true  # or false if insufficient resources

# If using on-device:
PAPR_ENABLE_COREML=true
PAPR_COREML_MODEL=/path/to/Qwen3-Embedding-4B-FP16-Final.mlpackage

# Tier Configuration (syncs from PAPR Cloud to local ChromaDB):
PAPR_MAX_TIER0=200  # Goals/OKRs (high-priority memories)
PAPR_MAX_TIER1=200  # General memories (contextual information)
```

Get your keys:
- OpenAI: https://platform.openai.com/api-keys
- PAPR: https://dashboard.papr.ai

### 4. Run Voice Server

```bash
# Make sure venv is activated
source venv/bin/activate

# Run the server
./scripts/run.sh

# Or manually:
# python src/python/voice_server.py
```

Open http://localhost:3000 in your browser

## 📱 Demo Flow

1. **Type a query** in the input box (voice coming soon)
2. **Watch real-time retrieval** with millisecond-level latency metrics
3. **See retrieved memories** with relevance scores
4. **Click to expand** any memory for citation verification
5. **Monitor performance** stats in the sidebar

## 🎯 What This Demonstrates

### Speed of On-Device Processing
- **CoreML acceleration** - Embeddings generated locally on your device
- **No server latency** - All processing happens on-device
- **Real-time metrics** - See exact retrieval times (typically <100ms on ANE, 200-250ms on GPU)

### Quality of Retrieval
- **Relevant memories** - Semantic search finds contextually relevant info
- **Citation verification** - Full content and metadata available
- **Multi-tier search** - Search both tier0 (goals/OKRs) and tier1 (general memories)
- **Graph connections** - Optional knowledge graph traversal

### Integration Simplicity
- **Simple SDK** - Just a few lines to search memories
- **Async support** - Non-blocking operations
- **Environment config** - Easy on-device processing toggle

## 📚 Memory Tiers

The SDK organizes memories into **two tiers** that are synced from PAPR Cloud to local ChromaDB:

### Tier 0: Goals & OKRs (High Priority)
- **Purpose**: Strategic goals, objectives, and key results
- **Use Case**: Long-term context, user objectives, project goals
- **Collection Name**: `tier0_goals_okrs`
- **Config**: `PAPR_MAX_TIER0=200` (max items to sync)

### Tier 1: General Memories (Contextual)
- **Purpose**: Conversation history, contextual information, facts
- **Use Case**: Recent interactions, learned preferences, domain knowledge
- **Collection Name**: `tier1_memories`  
- **Config**: `PAPR_MAX_TIER1=200` (max items to sync)

### How Search Works
1. **Single embedding** generated for query (one CoreML call)
2. **Both collections searched** in parallel using same embedding
3. **Results merged** and sorted by relevance score
4. **Top N returned** to application (configurable via `max_memories`)

This ensures you get the most relevant context from **both** strategic goals and recent memories!

## 🛠️ Architecture

**Current (Phase 1): Python + HTML**
```
Browser (voice.html)
    ↓ WebSocket
OpenAI Realtime API + Constellation UI
    ↓ HTTP POST
Python Flask Server (:3000)
    ↓ Direct call (in-process)
PAPR Python SDK
    ↓ Direct call (in-process)
CoreML Embeddings (on-device, 50-75ms)
    ↓ Direct call (in-process)
ChromaDB Vector Search (local, 20-30ms)
```

**Planned (Phase 5): TypeScript + Pipecat + Python Microservice**
```
Browser (voice.html → React)
    ↓ WebSocket/WebRTC
TypeScript/Fastify Server (:3000) + Pipecat
    ↓ HTTP call (localhost, ~1-5ms)
Python Flask/FastAPI Microservice (:3001)
    ↓ Direct call (in-process)
CoreML Embeddings (on-device, 50-75ms) ← STAYS IN PYTHON FOR PERFORMANCE
    ↓ Direct call (in-process)
ChromaDB Vector Search (local, 20-30ms)

Total latency: ~80-110ms (within <100ms target!)
```

## 📊 Demo Talking Points

1. **Speed**: "Notice the retrieval speed - under 100ms for on-device processing"
2. **Quality**: "Click any memory to verify the citation and see full context"
3. **Scale**: "This works with thousands of indexed memories"
4. **Privacy**: "All processing happens locally - no data leaves your device"
5. **Integration**: "Just a few lines of code to add memory to any application"

## 🎥 Using for Presentation

### Pre-Demo Checklist
- [ ] Run `./setup.sh` and configure `.env`
- [ ] Test a few queries to warm up the models
- [ ] Clear history for clean demo start
- [ ] Have 2-3 example queries ready that show good results

### Example Queries
- "What did I work on recently?"
- "Tell me about [specific project]"
- "What are my priorities?"
- "Find information about [topic]"

### During Demo
1. Start with sidebar showing on-device processing enabled
2. Type first query and highlight the speed metric
3. Expand a memory to show citation verification
4. Show performance stats accumulating
5. Demonstrate graph connections if enabled

## 🔧 Advanced Configuration

### Enable Graph Retrieval
In sidebar, check "Enable graph retrieval" to traverse knowledge connections.

### Adjust Memory Count
Use slider to control how many memories are retrieved (1-20).

### Performance Tuning
Edit `app.py` to adjust:
- `timeout` - Search timeout duration
- `max_nodes` - Graph traversal depth
- `enable_agentic_graph` - Graph-based retrieval

## 📝 Notes

- Voice integration via OpenAI Realtime API is implemented in `realtime_voice.py`
- Currently using text input for demo reliability
- On-device processing requires papr-pythonSDK with CoreML models
- Works best with pre-indexed personal data

## 🆘 Troubleshooting

**"ModuleNotFoundError: No module named 'papr_memory'"**
- Activate virtual environment: `source venv/bin/activate`
- Ensure papr-pythonSDK is at `~/Documents/GitHub/papr-pythonSDK/`
- Or install via: `pip install papr-memory`

**"No memories found"**
- Verify PAPR_MEMORY_API_KEY is correct
- Check that you have memories indexed in your account
- Try a broader query

**"Slow retrieval times (>2 seconds)"**
- **Root Cause**: CoreML falling back to CPU instead of using Neural Engine (ANE)
- **Check Disk Space**: CoreML needs 30-50GB free for ANE compilation
  ```bash
  df -h /  # Should show >30GB available
  ```
- **Symptoms**:
  - Logs show "Model: Qwen3-4B on cpu" instead of ANE
  - Embedding generation takes 2-3 seconds instead of 50-100ms
  - "LLVM ERROR: IO failure on output stream: No space left on device"
- **Solutions**:
  1. Free up disk space (delete old files, Xcode cache, Docker images)
  2. Check `PAPR_ONDEVICE_PROCESSING=true` in `.env`
  3. First query may be slower (model loading, should be <5 minutes)
  4. If disk space < 30GB, set `PAPR_ONDEVICE_PROCESSING=false` to use API backend

**"Memory pressure warnings"**
- CoreML models use 4-6GB RAM
- Close other memory-intensive apps
- Consider using API backend if RAM < 8GB available

## 📄 License

MIT
