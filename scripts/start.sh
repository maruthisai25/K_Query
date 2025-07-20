#!/bin/bash

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 10

# Pull the Llama model if not already present
echo "Checking for Llama model..."
ollama pull llama2:7b

# Start the FastAPI application
echo "Starting FastAPI application..."
cd /app
export PYTHONPATH=/app:$PYTHONPATH
python -m src.main