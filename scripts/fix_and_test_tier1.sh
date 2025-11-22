#!/bin/bash

# Complete fix and test script for tier1 content issue

echo "🧹 Cleaning old ChromaDB..."
cd /Users/shawkatkabbara/Documents/GitHub/papr-voice-demo
rm -rf chroma_db/

echo ""
echo "✅ ChromaDB deleted"
echo ""
echo "🚀 Now restart the server:"
echo ""
echo "   source venv/bin/activate"
echo "   python src/python/voice_server.py"
echo ""
echo "📊 Look for these SUCCESS indicators in the logs:"
echo ""
echo "   ✅ [INFO] Generated local embedding for tier1 item 0 (dim: 2560)"
echo "   ✅ [INFO] Generated 200 local tier1 embeddings in ~25s"
echo "   ✅ [INFO] ✅ Added 200 tier1 documents with embeddings"
echo ""
echo "❌ If you see this, the fix didn't work:"
echo ""
echo "   ⚠️  [INFO] ⚠️  Added 200 tier1 documents WITHOUT embeddings"
echo ""
echo "🔍 Test search at http://localhost:3000 with:"
echo "   'discussion with Bryant, the founder and CTO of Dialpad'"
echo ""
echo "Expected: Content from tier1 should now display!"

