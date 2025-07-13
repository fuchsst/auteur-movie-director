#!/bin/bash
# View logs for Auteur Movie Director

echo "📝 Showing logs (Ctrl+C to exit)..."
echo "=================================="
docker-compose -f docker-compose.dev.yml logs -f