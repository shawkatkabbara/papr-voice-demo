# 🌟 PAPR Voice Constellation Demo

The **real-time voice experience with constellation visualization** that you wanted!

## What This Is

- **OpenAI Realtime API** - Real-time voice conversation (like Siri)
- **Search Box** - Type or speak your queries
- **Constellation Stars** - Each dot/star represents a memory search
- **Clickable Memories** - Click any star to see retrieved memories in detail
- **On-Device CoreML** - Fast local memory search with your papr-pythonSDK

## Quick Start

```bash
cd /Users/shawkatkabbara/Documents/GitHub/papr-voice-demo
./run.sh
```

Then open: **http://localhost:3000**

## The Experience

1. **Type or speak** your query in the search box
2. **See stars appear** on the constellation canvas (each star = a search)
3. **Click any star** to open a modal with:
   - The query that was asked
   - Retrieval latency metrics
   - All memories retrieved for that search
   - Similarity scores, tags, topics
4. **Voice interaction** with OpenAI Realtime API

## Architecture

```
voice.html (Frontend)
    ↓
OpenAI Realtime API (Voice) ← → voice_server.py (Flask Backend)
    ↓                                       ↓
Constellation Canvas              papr-pythonSDK (Local)
(Stars/Dots UI)                           ↓
                                   CoreML + ChromaDB
                                   (On-Device Search)
```

## Features

- ✅ Real-time voice with OpenAI
- ✅ Search box for text input
- ✅ Constellation visualization (stars/dots)
- ✅ Clickable stars show memory details
- ✅ On-device CoreML acceleration
- ✅ Production memory sync (memory.papr.ai)
- ✅ Latency metrics and breakdown

## Alternative Apps

If you want to try other versions:

```bash
# Streamlit app with simple UI
streamlit run app.py

# Streamlit with animated orb
streamlit run app_voice_orb.py

# Real-time demo (simpler)
streamlit run app_real.py
```

But the **constellation experience** is served by `voice_server.py` → `voice.html`!

## Troubleshooting

**Port 3000 already in use?**
```bash
lsof -ti:3000 | xargs kill -9
./run.sh
```

**Voice not working?**
- Check OpenAI API key in `.env`
- Allow microphone access in browser
- Use Chrome/Edge (best WebRTC support)

**No memories found?**
- Verify PAPR_MEMORY_API_KEY is correct
- Check you have memories at dashboard.papr.ai
- First query may take longer (CoreML model loading)
