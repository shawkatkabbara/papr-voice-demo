#!/bin/bash
# Run PAPR Voice Orb Demo with OpenAI Realtime API

set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ No .env file found. Please run ./setup.sh first"
    exit 1
fi

echo "🎤 Starting PAPR Voice Orb Demo (OpenAI Realtime API)..."
echo "✨ Real-time voice with animated orb UI"
echo ""

# Run Streamlit app with voice orb UI
streamlit run app_voice_orb.py
