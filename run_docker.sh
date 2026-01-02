#!/bin/bash
# Run LEGO Architect in Docker

set -e

echo "🐳 Running AI-Powered LEGO Architect in Docker..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create .env file with: ANTHROPIC_API_KEY=your_key_here"
    echo "   Using .env.example as template..."
    cp .env.example .env
fi

# Build Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Run interactive shell
echo "🚀 Starting container..."
docker-compose run --rm lego-architect

echo "✅ Done!"
