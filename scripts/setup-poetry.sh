#!/bin/bash
# Setup script using Poetry for dependency management

set -e

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🚀 Setting up PAPR Voice Demo with Poetry..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed"
    echo "📦 Install Poetry first: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Poetry found"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"

# Install Python dependencies with Poetry
echo "📦 Installing Python dependencies..."
poetry install

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys"
fi

# Setup TypeScript backend
echo ""
echo "📦 Setting up TypeScript backend..."
cd src/server

if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found. Skipping TypeScript setup."
    echo "    Install Node.js to set up the TypeScript backend."
else
    echo "📥 Installing TypeScript dependencies..."
    npm install
fi

cd ../..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY (from platform.openai.com)"
echo "   - PAPR_MEMORY_API_KEY (from dashboard.papr.ai)"
echo ""
echo "2. Run the demo:"
echo "   ./scripts/run.sh"
echo ""
echo "3. Run tests:"
echo "   ./scripts/test.sh"
echo ""
