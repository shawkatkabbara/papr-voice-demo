# 🎤 PAPR Voice Demo

Real-time voice conversation with on-device memory retrieval, showcasing the speed and capabilities of PAPR's Python SDK with CoreML-powered on-device processing.

## ✨ Features

- **🎤 Voice Input** - OpenAI Realtime API for natural voice conversations (implementation ready)
- **⚡ On-Device Processing** - CoreML-accelerated embeddings with PAPR Python SDK
- **📊 Real-time Metrics** - Live display of query processing and retrieval speed
- **🔍 Citation Verification** - Click any memory to verify source and full content
- **📈 Performance Dashboard** - Track average latency and query statistics

## 🚀 Quick Start (5 minutes)

### 1. Setup

```bash
cd papr-voice-demo
chmod +x setup.sh run.sh
./setup.sh
```

### 2. Configure API Keys

Edit `.env` file:

```bash
OPENAI_API_KEY=sk-...
PAPR_MEMORY_API_KEY=papr_...
PAPR_ONDEVICE_PROCESSING=true
```

Get your keys:
- OpenAI: https://platform.openai.com/api-keys
- PAPR: https://dashboard.papr.ai

### 3. Run

```bash
./run.sh
```

The app will open in your browser at http://localhost:8501

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
- **Real-time metrics** - See exact retrieval times (typically <100ms)

### Quality of Retrieval
- **Relevant memories** - Semantic search finds contextually relevant info
- **Citation verification** - Full content and metadata available
- **Graph connections** - Optional knowledge graph traversal

### Integration Simplicity
- **Simple SDK** - Just a few lines to search memories
- **Async support** - Non-blocking operations
- **Environment config** - Easy on-device processing toggle

## 🛠️ Architecture

```
┌─────────────┐
│   Voice     │
│   Input     │ ← OpenAI Realtime API
└──────┬──────┘
       │
       v
┌─────────────────────┐
│   Query Processing   │
│   (Streamlit UI)     │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  PAPR Python SDK     │
│  On-Device Search    │ ← CoreML Embeddings
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Memory Retrieval    │
│  + Speed Metrics     │
└─────────────────────┘
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
- Ensure papr-pythonSDK is at `~/Documents/GitHub/papr-pythonSDK/`
- Or install via: `pip install papr-memory`

**"No memories found"**
- Verify PAPR_MEMORY_API_KEY is correct
- Check that you have memories indexed in your account
- Try a broader query

**"Slow retrieval times"**
- Ensure PAPR_ONDEVICE_PROCESSING=true
- Check that CoreML models are installed
- First query may be slower (model loading)

## 📄 License

MIT
