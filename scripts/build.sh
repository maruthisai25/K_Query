#!/bin/bash

# Infra Copilot - Multi-arch Docker Build Script
# Builds Docker images for multiple architectures (AMD64, ARM64)

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-k-query}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
PUSH="${PUSH:-false}"
BUILD_CONTEXT="${BUILD_CONTEXT:-.}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    echo "🐳 Infra Copilot - Multi-arch Docker Build"
    echo "=========================================="
    echo
    echo "Configuration:"
    echo "  Image Name: $IMAGE_NAME"
    echo "  Tag: $IMAGE_TAG"
    echo "  Registry: ${REGISTRY:-<none>}"
    echo "  Platforms: $PLATFORMS"
    echo "  Push: $PUSH"
    echo "  Build Context: $BUILD_CONTEXT"
    echo
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker version
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker version: $DOCKER_VERSION"
    
    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        print_error "Docker Buildx is not available"
        print_status "Please install Docker Buildx or use a newer version of Docker"
        exit 1
    fi
    
    print_success "Docker Buildx is available"
    
    # Check if Dockerfile exists
    if [ ! -f "$BUILD_CONTEXT/Dockerfile" ]; then
        print_error "Dockerfile not found in $BUILD_CONTEXT"
        exit 1
    fi
    
    print_success "Dockerfile found"
}

# Setup buildx builder
setup_builder() {
    print_status "Setting up multi-arch builder..."
    
    BUILDER_NAME="infra-copilot-builder"
    
    # Check if builder already exists
    if docker buildx ls | grep -q "$BUILDER_NAME"; then
        print_warning "Builder '$BUILDER_NAME' already exists, using existing builder"
    else
        # Create new builder
        docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
        print_success "Created builder '$BUILDER_NAME'"
    fi
    
    # Use the builder
    docker buildx use "$BUILDER_NAME"
    print_success "Using builder '$BUILDER_NAME'"
    
    # Inspect builder
    print_status "Builder capabilities:"
    docker buildx inspect --bootstrap
}

# Build the image
build_image() {
    print_status "Building multi-arch Docker image..."
    
    # Construct full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    fi
    
    print_status "Building image: $FULL_IMAGE_NAME"
    print_status "Platforms: $PLATFORMS"
    
    # Build arguments
    BUILD_ARGS=(
        "buildx" "build"
        "--platform" "$PLATFORMS"
        "--tag" "$FULL_IMAGE_NAME"
        "--file" "$BUILD_CONTEXT/Dockerfile"
    )
    
    # Add push flag if requested
    if [ "$PUSH" = "true" ]; then
        BUILD_ARGS+=("--push")
        print_status "Will push to registry after build"
    else
        BUILD_ARGS+=("--load")
        print_warning "Image will be loaded locally (single platform only)"
    fi
    
    # Add build context
    BUILD_ARGS+=("$BUILD_CONTEXT")
    
    # Execute build
    print_status "Executing: docker ${BUILD_ARGS[*]}"
    echo
    
    if docker "${BUILD_ARGS[@]}"; then
        print_success "Build completed successfully!"
    else
        print_error "Build failed!"
        exit 1
    fi
}

# Tag additional versions
tag_additional_versions() {
    if [ "$PUSH" = "false" ]; then
        print_status "Tagging additional versions..."
        
        # Tag as latest if not already
        if [ "$IMAGE_TAG" != "latest" ]; then
            if [ -n "$REGISTRY" ]; then
                docker tag "$REGISTRY/$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY/$IMAGE_NAME:latest"
                print_success "Tagged as $REGISTRY/$IMAGE_NAME:latest"
            else
                docker tag "$IMAGE_NAME:$IMAGE_TAG" "$IMAGE_NAME:latest"
                print_success "Tagged as $IMAGE_NAME:latest"
            fi
        fi
        
        # Tag with git commit if in git repo
        if git rev-parse --git-dir > /dev/null 2>&1; then
            GIT_COMMIT=$(git rev-parse --short HEAD)
            if [ -n "$REGISTRY" ]; then
                docker tag "$REGISTRY/$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY/$IMAGE_NAME:$GIT_COMMIT"
                print_success "Tagged as $REGISTRY/$IMAGE_NAME:$GIT_COMMIT"
            else
                docker tag "$IMAGE_NAME:$IMAGE_TAG" "$IMAGE_NAME:$GIT_COMMIT"
                print_success "Tagged as $IMAGE_NAME:$GIT_COMMIT"
            fi
        fi
    fi
}

# Push to registry
push_to_registry() {
    if [ "$PUSH" = "true" ] && [ -n "$REGISTRY" ]; then
        print_status "Images have been pushed to registry during build"
    elif [ "$PUSH" = "true" ] && [ -z "$REGISTRY" ]; then
        print_warning "PUSH=true but no REGISTRY specified, skipping push"
    fi
}

# Cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Remove builder if created by this script
    BUILDER_NAME="infra-copilot-builder"
    if [ "$CLEANUP_BUILDER" = "true" ]; then
        docker buildx rm "$BUILDER_NAME" || true
        print_success "Removed builder '$BUILDER_NAME'"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -n, --name NAME        Image name (default: k-query)"
    echo "  -t, --tag TAG          Image tag (default: latest)"
    echo "  -r, --registry REG     Registry URL (optional)"
    echo "  -p, --platforms PLAT   Target platforms (default: linux/amd64,linux/arm64)"
    echo "  --push                 Push to registry after build"
    echo "  --no-cache             Build without cache"
    echo "  --cleanup              Remove builder after build"
    echo "  -h, --help             Show this help message"
    echo
    echo "Environment variables:"
    echo "  IMAGE_NAME             Same as --name"
    echo "  IMAGE_TAG              Same as --tag"
    echo "  REGISTRY               Same as --registry"
    echo "  PLATFORMS              Same as --platforms"
    echo "  PUSH                   Set to 'true' to push"
    echo
    echo "Examples:"
    echo "  $0                                    # Build locally"
    echo "  $0 --push --registry myregistry.com  # Build and push"
    echo "  $0 --tag v1.0.0 --platforms linux/amd64  # Single platform"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -p|--platforms)
                PLATFORMS="$2"
                shift 2
                ;;
            --push)
                PUSH="true"
                shift
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --cleanup)
                CLEANUP_BUILDER="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    parse_args "$@"
    print_banner
    check_prerequisites
    setup_builder
    build_image
    tag_additional_versions
    push_to_registry
    
    if [ "$CLEANUP_BUILDER" = "true" ]; then
        cleanup
    fi
    
    echo
    print_success "🎉 Multi-arch build completed successfully!"
    echo
    
    if [ "$PUSH" = "true" ]; then
        print_status "Image pushed to registry and ready for deployment"
    else
        print_status "Image built locally and ready for testing"
        print_status "To run: docker run -p 8000:8000 $IMAGE_NAME:$IMAGE_TAG"
    fi
    
    echo
    print_status "Build summary:"
    if [ -n "$REGISTRY" ]; then
        echo "  Image: $REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        echo "  Image: $IMAGE_NAME:$IMAGE_TAG"
    fi
    echo "  Platforms: $PLATFORMS"
    echo "  Pushed: $PUSH"
}

# Handle script interruption
trap cleanup EXIT

# Run main function with all arguments
main "$@"