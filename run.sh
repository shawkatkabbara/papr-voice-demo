#!/bin/bash
# Run PAPR Voice Demo

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

echo "🎤 Starting PAPR Voice Demo..."
echo ""

# Run Streamlit app
streamlit run app.py
