#!/bin/bash
set -e

echo "🐳 Building multi-architecture Docker image for K-Query..."

# Configuration
IMAGE_NAME="k-query"
TAG="${TAG:-latest}"
PLATFORMS="linux/amd64,linux/arm64"

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker buildx is not available. Please install Docker Desktop or enable buildx."
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="k-query-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    echo "🔧 Creating buildx builder..."
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
fi

# Use the builder
docker buildx use "$BUILDER_NAME"

# Build and push multi-arch image
echo "🏗️  Building for platforms: $PLATFORMS"
docker buildx build \
    --platform "$PLATFORMS" \
    --tag "$IMAGE_NAME:$TAG" \
    --push \
    .

echo "✅ Multi-architecture build completed!"
echo "📦 Image: $IMAGE_NAME:$TAG"
echo "🏗️  Platforms: $PLATFORMS"