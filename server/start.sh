#!/bin/bash
# Startup script for Aigis server

echo "Starting Aigis..."

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data/outputs
    mkdir -p data/temp
fi

# Check environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Warning: GOOGLE_API_KEY not set. Script generation will fail."
fi

if [ -z "$PEXELS_API_KEY" ]; then
    echo "Warning: PEXELS_API_KEY not set. Video fetching will fail."
fi

# Start the server
echo "Starting Uvicorn server on port ${PORT:-8000}..."
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

