#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Test script to verify URL slug alignment between Terraform Registry and local mkdocs
# Usage: ./scripts/test-registry-url-alignment.sh [provider-dir]
#
# This script validates that local mkdocs URLs match Terraform Registry URLs,
# allowing you to test documentation links before publishing.

set -e

PROVIDER_DIR="${1:-.}"
REGISTRY_URL="${REGISTRY_URL:-https://registry.terraform.io/providers/provide-io/pyvider/latest}"
LOCAL_PORT="${LOCAL_PORT:-8010}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Terraform Registry URL Alignment Test                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Provider directory: $PROVIDER_DIR"
echo "Registry URL: $REGISTRY_URL"
echo "Local server: http://localhost:$LOCAL_PORT"
echo ""

# Change to provider directory
cd "$PROVIDER_DIR"

# Start mkdocs server in background
echo "Starting mkdocs server..."
mkdocs serve --no-livereload --dev-addr "127.0.0.1:$LOCAL_PORT" > /dev/null 2>&1 &
MKDOCS_PID=$!

# Ensure cleanup on exit
cleanup() {
    echo ""
    echo "Stopping mkdocs server..."
    kill $MKDOCS_PID 2>/dev/null || true
    sleep 1
}
trap cleanup EXIT

# Wait for server to start
echo "Waiting for server to start..."
for i in {1..10}; do
    sleep 1
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$LOCAL_PORT" 2>/dev/null | grep -q "200\|404"; then
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Failed to start mkdocs server after 10 seconds${NC}"
        echo "Check that mkdocs.yml exists in $PROVIDER_DIR"
        exit 1
    fi
done

echo -e "${GREEN}✓${NC} Server started successfully"
echo ""

# Define test components
declare -a components=(
    "data-sources/nested_resource_test"
    "data-sources/http_api"
    "data-sources/file_info"
    "resources/file_content"
    "resources/timed_token"
    "functions/add"
    "functions/lens_jq"
    "functions/round"
)

# Run tests
echo "╔════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                          URL ALIGNMENT TEST RESULTS                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""
printf "%-40s %-20s %-20s\n" "COMPONENT" "REGISTRY STATUS" "LOCAL STATUS"
echo "────────────────────────────────────────────────────────────────────────────────────────"

PASS_COUNT=0
FAIL_COUNT=0

for component in "${components[@]}"; do
    # Test registry URL
    registry_status=$(curl -s -o /dev/null -w "%{http_code}" "$REGISTRY_URL/docs/$component" 2>/dev/null || echo "000")

    # Test local URL (extract base path from site_url in mkdocs.yml)
    # Assuming site_url format: https://registry.terraform.io/providers/provide-io/pyvider/latest
    local_url="http://localhost:$LOCAL_PORT/providers/provide-io/pyvider/latest/$component/"
    local_status=$(curl -s -o /dev/null -w "%{http_code}" "$local_url" 2>/dev/null || echo "000")

    if [ "$registry_status" = "200" ] && [ "$local_status" = "200" ]; then
        match="${GREEN}✅${NC}"
        ((PASS_COUNT++))
    else
        match="${RED}❌${NC}"
        ((FAIL_COUNT++))
    fi

    printf "%-40s %-20s %-20s %b\n" "$component" "$registry_status" "$local_status" "$match"
done

echo "────────────────────────────────────────────────────────────────────────────────────────"
echo ""

# Summary
TOTAL_COUNT=$((PASS_COUNT + FAIL_COUNT))
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ACCEPTANCE CRITERIA PASSED${NC}"
    echo ""
    echo "All $TOTAL_COUNT tested components are accessible on both Registry and local server!"
    echo ""
    echo "Copy-Paste Workflow:"
    echo "  1. Copy slug from Registry:"
    echo "     $REGISTRY_URL/docs/[SLUG]"
    echo ""
    echo "  2. Paste into local (adjust path):"
    echo "     http://localhost:$LOCAL_PORT/providers/provide-io/pyvider/latest/[SLUG]/"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ACCEPTANCE CRITERIA FAILED${NC}"
    echo ""
    echo "Passed: $PASS_COUNT/$TOTAL_COUNT"
    echo "Failed: $FAIL_COUNT/$TOTAL_COUNT"
    echo ""
    exit 1
fi
