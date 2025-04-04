#!/bin/bash

# Exit on error
set -e

# Configuration
DOCKER_HUB_USERNAME="your-dockerhub-username"  # Replace with your Docker Hub username
IMAGE_NAME="kokoro-mcp-server"
CONTAINER_NAME="kokoro-mcp-server"
CONFIG_FILE="claude_desktop_config.json"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found"
    echo "Please copy claude_desktop_config.json.example to $CONFIG_FILE and update the settings"
    exit 1
fi

# Pull the latest image
echo "Pulling latest image..."
docker pull ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest

# Stop and remove existing container if running
if docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo "Stopping and removing existing container..."
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
fi

# Start the container with the new image
echo "Starting new container..."
docker compose up -d

# Check container status
echo "Checking container status..."
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo "Container started successfully!"
    echo "Container logs:"
    docker logs ${CONTAINER_NAME}
else
    echo "Error: Container failed to start"
    exit 1
fi 