#!/bin/bash

# K-Query - Setup Script
# Creates the Qdrant collection and seeds it with the starter DevOps documents.
#
# The seeding itself is done by src.vector_store.VectorStore.initialize_collection(),
# which encodes each document with all-MiniLM-L6-v2. Doing it here in shell would
# mean hand-writing 384-dimension vectors, which is how this script used to silently
# insert nothing.

set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
COLLECTION_NAME="devops_knowledge"
PYTHON_BIN="${PYTHON_BIN:-python3}"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Resolve the repo root so the script works from any directory.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

check_qdrant() {
    print_status "Checking Qdrant at $QDRANT_URL ..."

    # /healthz, not /health -- Qdrant returns 404 for /health.
    if ! curl -fsS "$QDRANT_URL/healthz" >/dev/null; then
        print_error "Cannot reach Qdrant at $QDRANT_URL"
        echo "  Start it with one of:" >&2
        echo "    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant" >&2
        echo "    docker compose up -d qdrant" >&2
        exit 1
    fi

    print_success "Qdrant is reachable"
}

check_python_deps() {
    if ! "$PYTHON_BIN" -c 'import sentence_transformers, qdrant_client' 2>/dev/null; then
        print_error "Python dependencies are missing."
        echo "  Install them first: pip install -r requirements.txt" >&2
        exit 1
    fi
}

seed_collection() {
    print_status "Creating collection '$COLLECTION_NAME' and encoding starter documents..."
    print_status "(first run downloads the all-MiniLM-L6-v2 model, ~90 MB)"

    QDRANT_URL="$QDRANT_URL" "$PYTHON_BIN" - <<'PY'
import asyncio
import os
import sys

from src.vector_store import VectorStore

store = VectorStore(os.environ["QDRANT_URL"])
if not asyncio.run(store.initialize_collection()):
    print("initialize_collection() returned False", file=sys.stderr)
    sys.exit(1)
PY

    print_success "Collection initialized"
}

verify_data() {
    print_status "Verifying collection contents..."

    local info points
    info="$(curl -fsS "$QDRANT_URL/collections/$COLLECTION_NAME")"
    points="$(echo "$info" | grep -o '"points_count":[0-9]*' | head -1 | cut -d':' -f2)"

    if [ -z "$points" ]; then
        print_error "Could not read points_count from Qdrant. Raw response:"
        echo "$info" >&2
        exit 1
    fi

    if [ "$points" -eq 0 ]; then
        print_error "Collection '$COLLECTION_NAME' exists but is empty."
        echo "  If it was created by an earlier run, drop it and re-run:" >&2
        echo "    curl -fsS -X DELETE $QDRANT_URL/collections/$COLLECTION_NAME" >&2
        exit 1
    fi

    print_success "Collection '$COLLECTION_NAME' contains $points documents"
}

main() {
    echo "K-Query setup"
    echo "============="
    echo

    check_qdrant
    check_python_deps
    seed_collection
    verify_data

    echo
    print_success "Setup complete."
    echo
    print_status "Next steps:"
    echo "  1. Put your Slack credentials in .env (see .env.example)"
    echo "  2. Start the app:  python -m src.main"
    echo "  3. Try it:         /devops why are my pods crashing?"
}

main "$@"
