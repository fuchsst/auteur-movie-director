#!/bin/bash
# Start Auteur Movie Director with Docker Compose

echo "🎬 Starting Auteur Movie Director..."
echo "=================================="

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

# Create workspace directory if it doesn't exist
if [ ! -d "workspace" ]; then
    echo "📁 Creating workspace directory..."
    mkdir -p workspace
fi

# Create models directory if it doesn't exist
if [ ! -d "models" ]; then
    echo "📁 Creating models directory..."
    mkdir -p models
fi

# Start the services
echo "🚀 Starting services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "📁 Volume mounts:"
echo "   Projects: ./workspace"
echo "   Models: ./models"
echo ""
echo "📝 To view logs: ./logs.sh"
echo "🛑 To stop: ./stop.sh"