#!/bin/bash
set -e

echo "🚀 Running K-Query locally..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual credentials"
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if required services are running
echo "🔍 Checking required services..."

# Check Qdrant (/healthz -- Qdrant 404s on /health)
if ! curl -fs http://localhost:6333/healthz > /dev/null; then
    echo "❌ Qdrant is not running. Please start it with:"
    echo "   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant"
    exit 1
fi

# Check Ollama
if ! curl -fs http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start it with:"
    echo "   ollama serve"
    exit 1
fi

echo "✅ All services are running"

# Set Python path
export PYTHONPATH=$PWD:$PYTHONPATH

# Start the application
echo "🚀 Starting K-Query application..."
python -m src.main