#!/bin/bash
set -e  # Exit on any error

# Function to check if Ollama is ready
check_ollama() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama is ready!"
            return 0
        fi
        echo "⏳ Waiting for Ollama... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Ollama failed to start within expected time"
    return 1
}

# Start Ollama server in the background
echo "🚀 Starting Ollama server..."
OLLAMA_HOST=0.0.0.0 ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
if ! check_ollama; then
    echo "❌ Failed to start Ollama"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
fi

# Pull the Llama model if not already present
echo "📦 Checking for Llama model..."
MODEL_PATH=${MODEL_PATH:-"llama2:7b"}
if ! ollama list | grep -q "$MODEL_PATH"; then
    echo "📥 Pulling model $MODEL_PATH..."
    ollama pull "$MODEL_PATH"
else
    echo "✅ Model $MODEL_PATH already available"
fi

# Start the FastAPI application
echo "🚀 Starting FastAPI application..."
cd /app
export PYTHONPATH=/app:$PYTHONPATH

# Trap to cleanup Ollama process on exit
trap 'echo "🛑 Shutting down..."; kill $OLLAMA_PID 2>/dev/null || true' EXIT

# Start the main application
exec python -m src.main