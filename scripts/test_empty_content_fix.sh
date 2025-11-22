#!/bin/bash

echo "🧹 Cleaning old ChromaDB and caches..."
cd /Users/shawkatkabbara/Documents/GitHub/papr-voice-demo
rm -rf chroma_db/
rm -rf ~/Library/Caches/com.apple.CoreML/

echo ""
echo "✅ Cleaned!"
echo ""
echo "🚀 Now restart the server:"
echo ""
echo "   poetry run python src/python/voice_server.py"
echo ""
echo "📊 Look for these SKIP logs during sync:"
echo ""
echo "   [DEBUG] Skipping tier1 item X (id: fL9dJE8DTH) with no/empty content"
echo "   [DEBUG] Skipping tier1 item Y (id: hxeODxfwer) with no/empty content"
echo ""
echo "🔍 After server starts, verify with:"
echo ""
echo "   poetry run python scripts/inspect_tier1_memories.py"
echo ""
echo "Expected: ✅ With content: 20 | ❌ Without content: 0"
echo ""
echo "🎯 Then test search - ALL results should have content!"

