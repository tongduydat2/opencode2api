# ⚙️ Configuration Reference

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## 📌 Config Resolution

> Priority hierarchy: **Environment Variables > config.json > Defaults**

---

## 🔧 Environment Variables

### Core Configurations

| Variable | Default Value | Description |
|:-----|:-------|:-----|
| `PORT` / `OPENCODE_PROXY_PORT` | `10000` | Proxy server port |
| `OPENCODE_SERVER_PORT` | `10001` | OpenCode backend port |
| `API_KEY` | - | Authorization API Key (Bearer token) |
| `BIND_HOST` | `0.0.0.0` | IP binding address |
| `OPENCODE_SERVER_URL` | `http://127.0.0.1:10001` | URL of the OpenCode backend instance |
| `OPENCODE_SERVER_PASSWORD` | - | OpenCode basic auth password |

### Feature Flags

| Variable | Default Value | Description |
|:-----|:-------|:-----|
| `DISABLE_TOOLS` | `true` | Disable OpenCode native tool invocation |
| `OPENCODE_EXTERNAL_TOOLS_MODE` | `proxy-bridge` | Mode for mapping incoming client `tools`. Currently only `proxy-bridge` |
| `OPENCODE_EXTERNAL_TOOLS_CONFLICT_POLICY` | `namespace` | Isolation policy for同名 tools. Currently only `namespace` |
| `OPENCODE_INTERNAL_WEB_FETCH_ENABLED` | `false` | Fallback compatibility switch; enables `web_fetch` if allowlist is unspecified |
| `OPENCODE_INTERNAL_ALLOWED_TOOLS` | `(none)` | Allowed built-in tool IDs list when client `tools` are omitted, comma-separated |
| `OPENCODE_INTERNAL_TOOL_METRICS_ENABLED` | `true` | Logs information on internal tool selection |
| `OPENCODE_TOOL_DISCOVERY_FIXTURE` | `(none)` | Static mocked tool ID list to return in testing, comma-separated |
| `OPENCODE_HEALTH_DETAILS_ENABLED` | `true` | Enable `/health/details` diagnostic endpoint |
| `OPENCODE_HEALTH_DETAILS_REQUIRE_AUTH` | `true` | Secure `/health/details` behind the `API_KEY` auth gate |
| `OPENCODE_METRICS_ENABLED` | `false` | Enable Prometheus metrics `/metrics` endpoint |
| `OPENCODE_METRICS_REQUIRE_AUTH` | `true` | Secure `/metrics` behind the `API_KEY` auth gate |
| `USE_ISOLATED_HOME` | `false` | Run OpenCode CLI server using isolated settings folder |
| `PROMPT_MODE` | `standard` | Mode for mapping prompting instructions |
| `OMIT_SYSTEM_PROMPT` | `false` | Discard incoming system prompting payloads |
| `AUTO_CLEANUP_CONVERSATIONS` | `false` | Automatically delete inactive open sessions |
| `CLEANUP_INTERVAL_MS` | `43200000` | Inactive sessions pruning loop interval |
| `CLEANUP_MAX_AGE_MS` | `86400000` | Lifetime age of stored conversations |
| `REQUEST_TIMEOUT_MS` | `180000` | HTTP proxy request timeout duration |

### Diagnostics & Debugging

| Variable | Default Value | Description |
|:-----|:-------|:-----|
| `DEBUG` / `OPENCODE_PROXY_DEBUG` | `false` | Log verbose execution details |
| `OPENCODE_PATH` | `opencode` | Path location to the `opencode` binary executable CLI |
| `OPENCODE_ZEN_API_KEY` | - | Pass-through credentials to the Zen platform |

---

## 📄 config.json Example

```json
{
    "PORT": 10000,
    "API_KEY": "your-secret-api-key",
    "BIND_HOST": "0.0.0.0",
    "DISABLE_TOOLS": true,
    "EXTERNAL_TOOLS_MODE": "proxy-bridge",
    "EXTERNAL_TOOLS_CONFLICT_POLICY": "namespace",
    "INTERNAL_WEB_FETCH_ENABLED": false,
    "INTERNAL_ALLOWED_TOOLS": ["web_fetch"],
    "INTERNAL_TOOL_METRICS_ENABLED": true,
    "INTERNAL_TOOL_DISCOVERY_FIXTURE": [],
    "USE_ISOLATED_HOME": false,
    "PROMPT_MODE": "standard",
    "OMIT_SYSTEM_PROMPT": false,
    "AUTO_CLEANUP_CONVERSATIONS": false,
    "CLEANUP_INTERVAL_MS": 43200000,
    "CLEANUP_MAX_AGE_MS": 86400000,
    "DEBUG": false,
    "OPENCODE_SERVER_URL": "http://127.0.0.1:10001",
    "OPENCODE_PATH": "opencode",
    "REQUEST_TIMEOUT_MS": 180000
}
```

---

## 🛠️ External Tool Bridging

opencode2api supports virtualization of client-provided `tools`. This translates standard Claude `tools` request definitions into system prompt instructions, routing tool outputs back cleanly without registering items directly inside the OpenCode environment.

### Supported Properties

| Setting Name | Values | Description |
|:------|:------|:-----|
| `OPENCODE_EXTERNAL_TOOLS_MODE` | `proxy-bridge` | Virtualize tool schemas and maps execution states back |
| `OPENCODE_EXTERNAL_TOOLS_CONFLICT_POLICY` | `namespace` | Prevent namespace overlap by appending internally mapped namespaces |

### Built-in Tool Allowlist

- When requests **omit** `tools` array payloads, the proxy evaluates the internal allowlist defined in `OPENCODE_INTERNAL_ALLOWED_TOOLS`.
- `OPENCODE_INTERNAL_WEB_FETCH_ENABLED=true` acts as a shortcut compatibility flag: it adds `web_fetch` automatically if the allowlist variable is left empty.
- Available tools are fetched from the CLI backend. The proxy resolves matching schemas using postfix matching rules.
- If none of the configurations resolve, the proxy defaults to the tool-disabled safety mode.
- Request-level overrides can be supplied in the request body under the `opencode.internal_allowed_tools` key. Note that this override can only intersect (narrow down) permissions, not expand them.

**Example Override Request Payload:**
```json
{
  "model": "opencode/deepseek-v4-flash-free",
  "messages": [{"role": "user", "content": "Retrieve this page"}],
  "opencode": {
    "internal_allowed_tools": ["web_fetch"]
  }
}
```

---

## 📊 Operational Telemetry

### Diagnostic Status (`GET /health/details`)

Returns operational diagnostics as JSON. Secured using `API_KEY` if `HEALTH_DETAILS_REQUIRE_AUTH=true`.

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

### Prometheus Metrics (`GET /metrics`)

Outputs metric counters in Prometheus plain text format. Secured using `API_KEY` if `METRICS_REQUIRE_AUTH=true`.

Supported metrics:
- `opencode_internal_tool_mode_requests_total`
- `opencode_internal_tool_discovery_failures_total`
- `opencode_internal_tool_fallback_disabled_total`
- `opencode_internal_tool_cache_ids`
