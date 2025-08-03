#!/bin/bash
set -e

echo "🧪 Running K-Query component tests..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx

# Set Python path
export PYTHONPATH=$PWD:$PYTHONPATH

# Run tests with coverage
echo "🏃 Running tests with coverage..."
python -m pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    -v

echo "✅ Tests completed!"
echo "📊 Coverage report generated in htmlcov/index.html"