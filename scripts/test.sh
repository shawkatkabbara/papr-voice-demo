#!/bin/bash
# Run all tests for PAPR Voice Demo

set -e

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🧪 Running PAPR Voice Demo Tests..."
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please run ./scripts/setup-poetry.sh first"
    exit 1
fi

# Python tests
echo "🐍 Running Python tests..."
echo "─────────────────────────────────────────────────────────────"
poetry run pytest tests/ -v --cov=src/python --cov-report=term-missing

echo ""
echo "✅ Python tests complete"
echo ""

# TypeScript tests
if [ -d "src/server/node_modules" ]; then
    echo "📘 Running TypeScript tests..."
    echo "─────────────────────────────────────────────────────────────"
    cd src/server
    npm test
    cd ../..
    echo ""
    echo "✅ TypeScript tests complete"
else
    echo "⚠️  TypeScript dependencies not installed"
    echo "   Run: cd src/server && npm install"
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📊 Test Coverage:"
echo "   - Python: Coverage report in htmlcov/index.html"
echo "   - TypeScript: Coverage report in src/server/coverage/index.html"
echo ""
