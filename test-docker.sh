#!/bin/bash

# Test Docker container locally
echo "🧪 Testing Docker container locally..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it first:"
    echo "cp env.example .env"
    echo "Then edit .env with your actual values"
    exit 1
fi

# Load environment variables
source .env

# Set default values for missing variables
export OUTPUT_DIRECTORY=${OUTPUT_DIRECTORY:-"articles"}
export ARTICLES_PER_PAGE=${ARTICLES_PER_PAGE:-"30"}

# Run the container
echo "🚀 Running container..."
docker run --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e OPENAI_API_BASE_URL="$OPENAI_API_BASE_URL" \
    -e VECTOR_STORE_ID="$VECTOR_STORE_ID" \
    -e OPTISIGNS_API_BASE_URL="$OPTISIGNS_API_BASE_URL" \
    -e OUTPUT_DIRECTORY="$OUTPUT_DIRECTORY" \
    -e ARTICLES_PER_PAGE="$ARTICLES_PER_PAGE" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/articles:/app/articles" \
    -v "$(pwd)/upload_tracking.json:/app/upload_tracking.json" \
    help-center-sync:latest

echo "✅ Test completed!"
echo "📁 Check logs in: ./logs/" 