#!/bin/bash
# Start PAPR Voice Demo with Pipecat integration
# Runs both Flask CoreML server (port 3001) and Pipecat voice server (port 8000)

set -e

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🎤 Starting PAPR Voice Demo with Pipecat"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please run ./scripts/setup-poetry.sh first"
    exit 1
fi

echo "🔧 Starting services..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $FLASK_PID $PIPECAT_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Flask CoreML microservice (port 3001)
echo "🐍 Starting Flask CoreML server on port 3001..."
poetry run python src/python/voice_server.py &
FLASK_PID=$!

# Wait for Flask server to be ready
echo "⏳ Waiting for Flask CoreML server to start..."
sleep 3

# Check if Flask is running
if ! curl -s http://localhost:3001/api/keys > /dev/null 2>&1; then
    echo "❌ Flask CoreML server failed to start!"
    echo "   Check logs above for errors"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Flask CoreML server is ready"
echo ""

# Start Pipecat voice server (port 8000)
echo "🎙️  Starting Pipecat voice server on port 8000..."
poetry run python src/python/pipecat_server.py &
PIPECAT_PID=$!

# Wait for Pipecat server to be ready
echo "⏳ Waiting for Pipecat server to start..."
sleep 3

# Check if Pipecat is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Pipecat server failed to start!"
    echo "   Check logs above for errors"
    cleanup
    exit 1
fi

echo "✅ Pipecat server is ready"
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🎤 PAPR Voice Demo - Pipecat Integration            ║"
echo "║                                                       ║"
echo "║  Pipecat Voice:  ws://localhost:8000/ws              ║"
echo "║  Health Check:   http://localhost:8000/health        ║"
echo "║                                                       ║"
echo "║  Flask CoreML:   http://localhost:3001               ║"
echo "║                                                       ║"
echo "║  Architecture:                                        ║"
echo "║  Browser → Pipecat (8000) → Flask CoreML (3001)      ║"
echo "║                                                       ║"
echo "║  Next Steps:                                          ║"
echo "║  1. Open voice.html in your browser                  ║"
echo "║  2. Update WebSocket URL to ws://localhost:8000/ws   ║"
echo "║  3. Start speaking and see <100ms memory search!     ║"
echo "║                                                       ║"
echo "║  Press Ctrl+C to stop all services                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Wait for both processes
wait $FLASK_PID $PIPECAT_PID
