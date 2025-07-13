#!/bin/bash
# Stop Auteur Movie Director

echo "🛑 Stopping Auteur Movie Director..."
docker-compose -f docker-compose.dev.yml down

echo "✅ Services stopped."