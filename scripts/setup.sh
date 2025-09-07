#!/bin/bash

# Setup script for the tutoring assistant

echo "Setting up Tutoring Assistant..."

# Create necessary directories
mkdir -p uploads
mkdir -p logs

# Copy environment file
if [ ! -f .env ]; then
    cp env.example .env
    echo "Created .env file from template. Please update with your configuration."
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start services with Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run database migrations (if using Alembic)
# alembic upgrade head

echo "Setup complete!"
echo "The application should be available at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/docs"
