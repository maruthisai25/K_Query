#!/bin/bash
set -e

echo "🐳 Building multi-architecture Docker image for K-Query..."

# Configuration
# Fully qualified: a bare "k-query" resolves to docker.io/library/k-query, which
# nobody can push to.
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/maruthisai25/k-query}"
TAG="${TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
PUSH="${PUSH:-false}"

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

# Build (and optionally push) the multi-arch image.
# Pushing is opt-in: PUSH=true requires `docker login ghcr.io` first.
echo "🏗️  Building for platforms: $PLATFORMS"
if [ "$PUSH" = "true" ]; then
    OUTPUT_ARGS="--push"
else
    OUTPUT_ARGS="--output=type=image,push=false"
    echo "ℹ️  PUSH is not set to true; building without pushing."
fi

docker buildx build \
    --platform "$PLATFORMS" \
    --tag "$IMAGE_NAME:$TAG" \
    $OUTPUT_ARGS \
    .

echo "✅ Multi-architecture build completed!"
echo "📦 Image: $IMAGE_NAME:$TAG"
echo "🏗️  Platforms: $PLATFORMS"