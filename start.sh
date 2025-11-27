#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Start docker-compose with environment variables
docker-compose up -d

echo "Services started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "OpenAI model: $OPENAI_DEFAULT_MODEL"
echo "Anthropic model: $ANTHROPIC_DEFAULT_MODEL"
