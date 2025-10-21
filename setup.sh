#!/bin/bash
# Quick setup script for PAPR Voice Demo

set -e

echo "🚀 Setting up PAPR Voice Demo..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY (from platform.openai.com)"
echo "   - PAPR_MEMORY_API_KEY (from dashboard.papr.ai)"
echo ""
echo "2. Run the demo:"
echo "   ./run.sh"
echo ""
