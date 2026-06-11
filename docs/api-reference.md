# 🔌 API Reference

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## 📋 General Information

| Field | Value |
|:-----|:---|
| **Base URL** | `http://127.0.0.1:10000` |
| **Authentication** | Bearer Token (Mandatory when `API_KEY` is set) |

---

## 🔑 Authentication

```bash
# Example with Authorization header
curl -H "Authorization: Bearer YOUR_API_KEY" ...
```

---

## 📡 Endpoints

### 1️⃣ Health Check

```http
GET /health
```

**Response Example:**

```json
{
  "status": "ok",
  "backend": true
}
```

---

### 2️⃣ Structured Diagnostics

```http
GET /health/details
```

**Response Example:**

```json
{
  "status": "ok",
  "proxy": true,
  "internal_tools": {
    "config": {
      "allowed_tools": ["web_fetch"],
      "metrics_enabled": true,
      "discovery_fixture": []
    },
    "metrics": {
      "externalBridgeRequests": 0,
      "internalAllowlistRequests": 0,
      "disabledRequests": 1,
      "discoveryFailures": 0,
      "fallbackToDisabled": 0
    },
    "cache": {
      "tool_ids_cached": false,
      "tool_id_count": 0,
      "age_ms": null
    }
  }
}
```

---

### 3️⃣ Prometheus Metrics

```http
GET /metrics
```

**Response Example:**

```text
# HELP opencode_internal_tool_mode_requests_total Count of internal tool mode selections by mode.
# TYPE opencode_internal_tool_mode_requests_total counter
opencode_internal_tool_mode_requests_total{mode="external_bridge"} 0
opencode_internal_tool_mode_requests_total{mode="internal_allowlist"} 0
opencode_internal_tool_mode_requests_total{mode="disabled"} 1
# HELP opencode_internal_tool_discovery_failures_total Count of backend tool discovery failures.
# TYPE opencode_internal_tool_discovery_failures_total counter
opencode_internal_tool_discovery_failures_total 0
# HELP opencode_internal_tool_fallback_disabled_total Count of allowlist resolutions that fell back to disabled.
# TYPE opencode_internal_tool_fallback_disabled_total counter
opencode_internal_tool_fallback_disabled_total 0
# HELP opencode_internal_tool_cache_ids Number of cached backend tool IDs.
# TYPE opencode_internal_tool_cache_ids gauge
opencode_internal_tool_cache_ids 0
```

---

### 4️⃣ Models List

```http
GET /v1/models
```

**Response Example:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "opencode/deepseek-v4-flash-free",
      "object": "model",
      "created": 1709772800,
      "owned_by": "opencode"
    }
  ]
}
```

---

### 5️⃣ Chat Messages (Claude Format)

```http
POST /v1/messages
```

**Request Body:**

| Parameter | Type | Required | Description |
|:-----|:-----|:-----|:-----|
| `model` | string | ✅ | Model ID (e.g. `opencode/deepseek-v4-flash-free`) |
| `messages` | array | ✅ | Messages history, containing `role` and `content` keys |
| `system` | string | - | System instructions prompt |
| `stream` | boolean | - | Stream response back using Server-Sent Events (SSE) |
| `tools` | array | - | Client tools mapping |

**Non-Streaming Example:**

```bash
curl -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

**Non-Streaming Response Example:**

```json
{
  "id": "msg_ses_14a1aaa12ffeKyDslLLR73oVV6",
  "type": "message",
  "role": "assistant",
  "model": "opencode/deepseek-v4-flash-free",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  },
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ]
}
```

**Streaming (SSE) Example:**

```bash
curl -N -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**Streaming (SSE) Response Output:**

```text
event: message_start
data: {"type": "message_start", "message": {"id": "msg_ses_14a1a8531ffeB7tlt2Xuky9PhT", "type": "message", "role": "assistant", "model": "opencode/deepseek-v4-flash-free", "content": [], "stop_reason": null, "stop_sequence": null, "usage": {"input_tokens": 0, "output_tokens": 0}}}

event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_delta
data: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": null}, "usage": {"output_tokens": 0}}

event: message_stop
data: {"type": "message_stop"}
```

---

## ⚠️ Error Responses

### 401 Unauthorized

```json
{
  "error": {
    "message": "Unauthorized"
  }
}
```

### 404 Not Found

```json
{
  "error": {
    "message": "Not found"
  }
}
```
