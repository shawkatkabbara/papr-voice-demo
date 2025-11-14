#!/bin/bash
# Development startup script for PAPR Voice Demo
# Runs both Python CoreML microservice and TypeScript Fastify server

set -e

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🎤 Starting PAPR Voice Demo Development Environment"
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

# Check if Node modules are installed
if [ ! -d "src/server/node_modules" ]; then
    echo "📦 Installing TypeScript dependencies..."
    cd src/server
    npm install
    cd ../..
fi

echo "🔧 Starting services..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $PYTHON_PID $TS_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Python CoreML microservice (port 3001)
echo "🐍 Starting Python CoreML microservice on port 3001..."
poetry run python src/python/voice_server.py &
PYTHON_PID=$!

# Wait for Python server to be ready
echo "⏳ Waiting for Python microservice to start..."
sleep 3

# Start TypeScript Fastify server (port 3000)
echo "📘 Starting TypeScript Fastify server on port 3000..."
cd src/server
npm run dev &
TS_PID=$!
cd ../..

echo ""
echo "✅ Development environment ready!"
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🎤 PAPR Voice Demo - Development Servers            ║"
echo "║                                                       ║"
echo "║  Frontend:  http://localhost:3000                    ║"
echo "║  API:       http://localhost:3000/api/*              ║"
echo "║  Health:    http://localhost:3000/health             ║"
echo "║                                                       ║"
echo "║  Python:    http://localhost:3001 (CoreML)           ║"
echo "║                                                       ║"
echo "║  Press Ctrl+C to stop all services                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Wait for both processes
wait $PYTHON_PID $TS_PID
