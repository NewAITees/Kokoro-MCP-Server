#!/bin/bash

# Exit on error
set -e

# Configuration
IMAGE_NAME="kokoro-mcp-server"
PLATFORMS="linux/amd64,linux/arm64"
DOCKER_HUB_USERNAME="your-dockerhub-username"  # Replace with your Docker Hub username

# Create a new builder instance
docker buildx create --name multiarch-builder --use || true

# Build and push multi-architecture images
docker buildx build \
  --platform ${PLATFORMS} \
  --tag ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest \
  --push \
  .

# Clean up
docker buildx rm multiarch-builder 