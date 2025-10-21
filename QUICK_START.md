# ⚡ QUICK START - Ready in 5 Minutes

## 🎯 You have 1 hour until you need to leave. Here's what to do:

### Step 1: Setup (2 minutes)

```bash
cd papr-voice-demo
./setup.sh
```

### Step 2: Configure .env (1 minute)

The `.env` file should already exist. Verify it has:

```bash
# Your actual API keys (replace if needed)
OPENAI_API_KEY=sk-...
PAPR_MEMORY_API_KEY=papr_...

# These should already be set correctly
PAPR_BASE_URL=https://31d9327a7bc0.ngrok.app
PAPR_ONDEVICE_PROCESSING=true
PAPR_ENABLE_COREML=true
PAPR_COREML_MODEL=/Users/shawkatkabbara/Documents/GitHub/papr-pythonSDK/coreml/Qwen3-Embedding-4B-FP16-Final.mlpackage
```

### Step 3: Run (30 seconds)

```bash
./run.sh
```

Browser will open at http://localhost:8501

### Step 4: Test (5-10 minutes)

Try these queries:
1. "What did I work on recently?"
2. "Tell me about PAPR"
3. "Find my latest project updates"

**Watch the speed metrics!** This is what you'll demo.

### Step 5: Clear for Demo (10 seconds)

Before your 4 PM demo:
```bash
# In the Streamlit UI, click "Clear History" button in sidebar
```

---

## 🎤 Demo Checklist (Use this at 3:55 PM)

- [ ] App is running at http://localhost:8501
- [ ] History is cleared
- [ ] Sidebar shows "On-Device Processing: ✅ Enabled"
- [ ] You have 2-3 test queries written down
- [ ] Browser window is sized nicely
- [ ] You know what speed metrics to expect (~50-100ms)

---

## 🎬 Your Demo Script

**Opening:** "I'm showing PAPR's Python SDK with on-device processing. Watch how fast we can search memories locally."

**Action 1:** Type a query → Point to speed metric when it appears

**Action 2:** Click to expand a memory → Show citation verification

**Action 3:** Run another query → Point to accumulating stats in sidebar

**Closing:** "All embeddings generated locally with CoreML. No server calls for search."

---

## 🆘 If Something Breaks

**Can't import papr_memory?**
```bash
source venv/bin/activate
pip install papr-memory
```

**No memories found?**
- Check your PAPR_MEMORY_API_KEY
- Try broader queries

**App won't start?**
```bash
# Restart everything
./run.sh
```

---

## 📱 What You Built

✅ Streamlit UI showing real-time search
✅ PAPR SDK integration with on-device processing
✅ Speed metrics display (ms-level latency)
✅ Citation verification (expandable memory cards)
✅ Performance dashboard (avg latency, query count)

**Total Time:** Built in ~45 minutes, ready to demo! 🚀

---

**Good luck at 4 PM! 🎉**
