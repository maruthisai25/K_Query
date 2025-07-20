#!/bin/bash

# Local development run script
# Runs the application locally without Docker

echo "🚀 Starting K-Query locally..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Copy .env.example to .env and configure it."
    echo "Using default values for now..."
fi

# Set Python path
export PYTHONPATH=$(pwd):$PYTHONPATH

# Start the application
echo "Starting FastAPI application..."
python -m src.main