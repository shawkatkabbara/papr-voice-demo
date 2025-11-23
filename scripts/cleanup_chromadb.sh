#!/bin/bash
# Clean ChromaDB and force resync to fix Memory object storage issue

echo "🧹 Cleaning up ChromaDB..."
rm -rf /Users/shawkatkabbara/Documents/GitHub/papr-voice-demo/chroma_db/

echo "✅ ChromaDB deleted"
echo ""
echo "🔄 The SDK will automatically resync when you restart the voice server"
echo ""
echo "To restart:"
echo "  ./venv/bin/python src/python/voice_server.py"
echo ""
echo "This will trigger a fresh sync_tiers call that properly stores content."

