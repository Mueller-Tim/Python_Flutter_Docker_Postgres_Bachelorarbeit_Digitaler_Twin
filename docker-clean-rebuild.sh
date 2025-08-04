#!/bin/bash
echo "🧹 Cleaning Docker..."
docker-compose down -v --remove-orphans
docker system prune -a --volumes -f
docker-compose build --no-cache
docker-compose up
