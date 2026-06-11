#!/bin/bash

set -e

echo "--- Real Streaming Test ---"

BASE_URL="${BASE_URL:-http://localhost:10000}"
API_KEY="${API_KEY:-test-key}"

echo "Base URL: $BASE_URL"
echo ""

# Get first available model
MODEL_ID=$(curl -sf -H "Authorization: Bearer $API_KEY" "$BASE_URL/v1/models" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data["data"][0]["id"])')
echo "Using model: $MODEL_ID"
echo ""

echo "Test 1: Streaming"
echo "-----------------------------------"
RESPONSE=$(curl -s -N -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"$MODEL_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with 3 words\"}],
    \"stream\": true
  }")

if echo "$RESPONSE" | grep -q "message_start"; then
    echo "✓ SSE message_start found"
else
    echo "✗ No message_start event"
    exit 1
fi

if echo "$RESPONSE" | grep -q "content_block_delta"; then
    echo "✓ SSE content_block_delta found"
else
    echo "✗ No content_block_delta event"
    exit 1
fi

if echo "$RESPONSE" | grep -q "message_stop"; then
    echo "✓ Stream finished with message_stop"
else
    echo "✗ Stream not finished correctly"
    exit 1
fi

echo ""
echo "Test 2: Non-Streaming"
echo "-----------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"$MODEL_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}],
    \"stream\": false
  }")

if echo "$RESPONSE" | grep -q '"role":"assistant"'; then
    echo "✓ Valid JSON response with assistant role"
else
    echo "✗ Invalid JSON response"
    exit 1
fi

if echo "$RESPONSE" | grep -q '"usage"'; then
    echo "✓ Usage field present"
else
    echo "✗ Usage field missing"
    exit 1
fi

echo ""
echo "--- All tests passed! ---"