#!/bin/bash
# Clean up memory before running voice demo
# Based on papr-pythonSDK/scripts/coreml_models/cleanup_memory.sh

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🧹 Cleaning up memory for PAPR Voice Demo..."
echo

# 1. Stop any running Flask servers
echo "1️⃣ Stopping any running Flask servers..."
pkill -f "python.*voice_server.py" 2>/dev/null && echo "   ✅ Stopped voice_server.py" || echo "   ℹ️  No Flask servers running"

# 2. Clear ChromaDB (will be recreated with correct dimensions)
echo
echo "2️⃣ Clearing ChromaDB..."
rm -rf chroma_db src/python/__pycache__ tests/__pycache__ scripts/__pycache__ .pytest_cache 2>/dev/null
echo "   ✅ Cleared chroma_db and Python caches"

# 3. Clear CoreML cache (safe, recompiled on-demand)
echo
echo "3️⃣ Clearing CoreML cache..."
rm -rf ~/Library/Caches/com.apple.CoreML 2>/dev/null
echo "   ✅ Cleared CoreML cache"

# 4. Force memory purge (frees inactive memory)
echo
echo "4️⃣ Purging inactive memory..."
sudo purge 2>/dev/null && echo "   ✅ Memory purged" || echo "   ⚠️  Run with sudo for full purge"

# 5. Show memory stats
echo
echo "5️⃣ Current memory stats:"
echo "   Physical Memory: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
vm_stat | grep -E "Pages free|Pages inactive|Pages speculative|Pageouts" | awk '{print "   " $0}'

echo
echo "✅ Cleanup complete!"
echo
echo "📊 Memory recommendations:"
echo "   - Close heavy apps (Docker, Chrome, IDEs)"
echo "   - Restart if swap usage > 10GB"
echo "   - First CoreML load will take ~60s (cached after)"
