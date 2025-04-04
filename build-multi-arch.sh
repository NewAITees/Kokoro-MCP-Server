#!/bin/bash
set -e

# イメージ名とタグの設定
IMAGE_NAME="kokoro-mcp-server"
VERSION="1.0.0"
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-"yourusername"}

# ビルダーインスタンスの作成
echo "Creating multi-architecture builder..."
docker buildx create --name kokoro-mcp-builder --use || echo "Builder already exists"
docker buildx inspect --bootstrap

# マルチアーキテクチャビルドの実行
echo "Building multi-architecture image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION} \
  -t ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest \
  --push \
  .

echo "Multi-architecture build completed successfully!"
echo "Image: ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION}" 