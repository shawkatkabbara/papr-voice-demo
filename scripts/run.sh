#!/bin/bash
# Run PAPR Voice Demo with Constellation UI and OpenAI Realtime API

set -e

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ No .env file found. Please run ./scripts/setup.sh first"
    exit 1
fi

echo "🎤 Starting PAPR Voice Demo (Constellation UI)..."
echo "✨ OpenAI Realtime API + On-Device CoreML Search"
echo "🌟 Click on the stars to see retrieved memories!"
echo ""
echo "📍 Opening at: http://localhost:3000"
echo ""

# Run Flask voice server from new location
python src/python/voice_server.py
