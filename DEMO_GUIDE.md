# 🎯 Quick Demo Guide - 4 PM Presentation

## ⏰ Timeline (1 hour to prep)

### Now - 15 min: Setup
1. `cd papr-voice-demo`
2. `./setup.sh`
3. Edit `.env` with your API keys
4. `./run.sh` to test

### 15-45 min: Test & Polish
1. Run 5-10 test queries
2. Verify memories are retrieving
3. Check speed metrics look good
4. Clear history for fresh demo

### 45-60 min: Prep Talking Points
1. Have 3-4 example queries ready
2. Know your best retrieval times
3. Pick 1-2 memories to highlight for citations

## 🎤 Demo Script (5 minutes)

### Opening (30 sec)
"Today I'm showing you PAPR's new Python SDK with on-device processing. This demo combines voice interaction with lightning-fast local memory retrieval."

### Show the UI (30 sec)
- Point out the two-column layout
- Highlight the sidebar metrics
- Mention on-device processing is enabled

### First Query (60 sec)
1. Type: "What did I work on recently?"
2. **WAIT** for speed metric to display
3. **HIGHLIGHT**: "Notice the retrieval time - [X]ms"
4. "This is running CoreML embeddings locally, no server calls"

### Show Citations (60 sec)
1. Click to expand top memory
2. Show full content
3. Point out metadata/timestamp
4. "Full citation verification for every result"

### Show Performance (60 sec)
1. Run 2 more quick queries
2. Point to sidebar: "Watch the stats accumulate"
3. Show average latency metric
4. "Consistent sub-100ms retrieval"

### Explain Architecture (60 sec)
1. "Three key components:"
   - On-device CoreML for embeddings
   - PAPR SDK for memory management
   - Real-time UI showing exact performance
2. "Voice integration ready via OpenAI Realtime API"

### Q&A Prep (30 sec)
- Ready to answer technical questions
- Can show code if needed
- Have README open for reference

## 💡 Key Talking Points

1. **Speed**: "Sub-100ms retrieval with on-device processing"
2. **Privacy**: "All embeddings generated locally, nothing leaves device"
3. **Quality**: "Semantic search with citation verification"
4. **Scale**: "Works with thousands of indexed memories"
5. **Simple**: "Just a few lines of Python to integrate"

## 🎯 Example Queries (Pre-tested)

Have these ready (test beforehand):
1. "What did I work on recently?"
2. "Tell me about [your recent project]"
3. "Find information about [specific topic in your memories]"
4. "What are my priorities?"

## ⚠️ Common Issues

**If memories don't show:**
- Check API key is correct
- Verify you have indexed memories
- Try broader queries first

**If speed is slow:**
- First query loads models (may be slower)
- Subsequent queries should be fast
- Clear and restart if needed

**If UI freezes:**
- Refresh browser
- Check terminal for errors
- Restart with `./run.sh`

## 🚀 Last-Minute Checklist (before 4 PM)

- [ ] Environment variables set
- [ ] App running smoothly
- [ ] Test queries work
- [ ] Speed metrics showing good numbers
- [ ] History cleared
- [ ] Example queries written down
- [ ] Browser window sized nicely
- [ ] Terminal hidden or clean

## 🎬 Opening Line

"I'm going to show you how fast on-device memory retrieval can be with PAPR's Python SDK. Watch the millisecond metrics as we search through thousands of memories in real-time."

---

**Good luck! You've got this! 🎉**
