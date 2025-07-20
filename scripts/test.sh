#!/bin/bash

# Infra Copilot - Test Script
# Validates that all components are working correctly

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test health endpoint
test_health() {
    print_status "Testing health endpoint..."
    
    if curl -s "$API_URL/health" | grep -q "healthy"; then
        print_success "Health endpoint is working"
        return 0
    else
        print_error "Health endpoint failed"
        return 1
    fi
}

# Test metrics endpoint
test_metrics() {
    print_status "Testing metrics endpoint..."
    
    if curl -s "$API_URL/metrics" | grep -q "http_requests_total"; then
        print_success "Metrics endpoint is working"
        return 0
    else
        print_error "Metrics endpoint failed"
        return 1
    fi
}

# Test chat endpoint
test_chat() {
    print_status "Testing chat endpoint..."
    
    RESPONSE=$(curl -s -X POST "$API_URL/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "test question about pods"}')
    
    if echo "$RESPONSE" | grep -q "response"; then
        print_success "Chat endpoint is working"
        return 0
    else
        print_error "Chat endpoint failed"
        echo "Response: $RESPONSE"
        return 1
    fi
}

# Test Qdrant connection
test_qdrant() {
    print_status "Testing Qdrant connection..."
    
    if curl -s "$QDRANT_URL/health" > /dev/null 2>&1; then
        print_success "Qdrant is accessible"
        
        # Check if collection exists
        if curl -s "$QDRANT_URL/collections/devops_knowledge" | grep -q "ok"; then
            print_success "Knowledge base collection exists"
            return 0
        else
            print_warning "Knowledge base collection not found (run ./setup.sh)"
            return 1
        fi
    else
        print_error "Qdrant is not accessible"
        return 1
    fi
}

# Test Prometheus connection
test_prometheus() {
    print_status "Testing Prometheus connection..."
    
    if curl -s "$PROMETHEUS_URL/api/v1/query?query=up" | grep -q "success"; then
        print_success "Prometheus is accessible"
        return 0
    else
        print_warning "Prometheus is not accessible (optional for testing)"
        return 1
    fi
}

# Run all tests
run_tests() {
    echo "🧪 Infra Copilot - Component Tests"
    echo "=================================="
    echo
    
    PASSED=0
    FAILED=0
    
    # Test each component
    if test_health; then ((PASSED++)); else ((FAILED++)); fi
    if test_metrics; then ((PASSED++)); else ((FAILED++)); fi
    if test_chat; then ((PASSED++)); else ((FAILED++)); fi
    if test_qdrant; then ((PASSED++)); else ((FAILED++)); fi
    if test_prometheus; then ((PASSED++)); else ((FAILED++)); fi
    
    echo
    echo "Test Results:"
    echo "============="
    print_success "Passed: $PASSED"
    if [ $FAILED -gt 0 ]; then
        print_error "Failed: $FAILED"
    else
        print_success "Failed: $FAILED"
    fi
    
    echo
    if [ $FAILED -eq 0 ]; then
        print_success "🎉 All tests passed! Infra Copilot is ready to use."
    else
        print_warning "⚠️  Some tests failed. Check the output above for details."
        echo
        echo "Common issues:"
        echo "- Make sure all services are running (docker-compose up)"
        echo "- Run ./setup.sh to initialize the knowledge base"
        echo "- Check that ports 8000, 6333, 9090 are not blocked"
    fi
    
    return $FAILED
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --api-url URL      API URL (default: http://localhost:8000)"
    echo "  --qdrant-url URL   Qdrant URL (default: http://localhost:6333)"
    echo "  --prometheus-url URL Prometheus URL (default: http://localhost:9090)"
    echo "  -h, --help         Show this help message"
    echo
    echo "Examples:"
    echo "  $0                                    # Test with default URLs"
    echo "  $0 --api-url http://localhost:8080   # Test with custom API URL"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-url)
                API_URL="$2"
                shift 2
                ;;
            --qdrant-url)
                QDRANT_URL="$2"
                shift 2
                ;;
            --prometheus-url)
                PROMETHEUS_URL="$2"
                shift 2
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
    run_tests
}

# Run main function with all arguments
main "$@"