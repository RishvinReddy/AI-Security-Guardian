#!/bin/bash
# AI Security Guardian - Setup Script

echo "Initializing AI Security Guardian Deployment..."

if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose could not be found. Please install it."
    exit
fi

echo "Copying environment template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please update .env with your specific API keys."
else
    echo ".env already exists, skipping."
fi

echo "Setting up PostgreSQL storage..."
mkdir -p .docker-data/postgres
chmod 700 .docker-data/postgres

echo "Stack is ready. Run 'docker-compose up -d' to start."
