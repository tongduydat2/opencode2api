# opencode2claude

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-orange" alt="Python">
</p>

> 📖 [Documentation](./docs/README.md) | 🚀 [Quick Start](#-quick-start)

Convert your local [OpenCode](https://opencode.ai) runtime into a Claude-compatible API gateway. Use free models (GPT, Nemotron, MiniMax) in any Claude/Anthropic client.

---

## ✨ Features

| Feature | Description |
|:-----|:-----|
| 🟢 **Claude Compatible** | Support for `/v1/models` and `/v1/messages` |
| 📡 **Streaming Output** | Full SSE streaming and Thinking/Reasoning block support for Messages API |
| 🐳 **Docker Deployment** | One-click deployment with automatic backend OpenCode startup |
| 🛡️ **Tool Security** | Tool execution disabled by default |
| 🔧 **External Tool Bridge** | Bridge client-provided `tools` into OpenCode compatible tool instructions to prevent conflict |
| 🌐 **Built-in web_fetch Pass-through** | Only allow OpenCode's built-in `web_fetch` to participate when client `tools` are omitted and features are explicitly enabled |

---

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/tongduydat2/opencode2claude.git
cd opencode2claude
cp .env.example .env

# 2. Edit .env and set your configuration
# Required: API_KEY, OPENCODE_SERVER_PASSWORD

# 3. Start
docker compose up -d

# 4. Test
curl http://127.0.0.1:10000/health
```

### Python (Local Development)

```bash
# 1. Install OpenCode CLI
# Linux/macOS: curl -fsSL https://opencode.ai/install | bash

# 2. Clone and run
git clone https://github.com/tongduydat2/opencode2claude.git
cd opencode2claude
pip install -r requirements.txt
cp .env.example .env
bash ./run_python.sh
```

---

## 💡 Usage Examples

### Messages (Non-Streaming)

```bash
curl -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### Messages (Streaming)

```bash
curl -N -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "Greet me in one sentence."}],
    "stream": true
  }'
```

---

## 📦 Deployment Methods

| Mode | Description | Scenario |
|:-----|:-----|:---------|
| 🐳 **Docker** | Full-stack setup with automatic OpenCode backend lifecycle management | Production, easiest configuration |
| 💻 **Standalone Python** | Fast API / Uvicorn server, manual backend management | Development, custom integration |

---

## ⚙️ Configuration

### Quick Reference

| Environment Variable | Default Value | Description |
|:--------|:-------|:------|
| `PORT` / `OPENCODE_PROXY_PORT` | `10000` | Proxy server port |
| `OPENCODE_SERVER_PORT` | `10001` | OpenCode backend port |
| `API_KEY` | - | Bearer Token authorization key |
| `BIND_HOST` | `0.0.0.0` | Bind address |
| `DISABLE_TOOLS` | `true` | Disable OpenCode native tool invocation |
| `OPENCODE_EXTERNAL_TOOLS_MODE` | `proxy-bridge` | External tools bridge mode; currently only `proxy-bridge` is supported |
| `OPENCODE_EXTERNAL_TOOLS_CONFLICT_POLICY` | `namespace` | Conflict isolation policy; currently only `namespace` is supported |
| `OPENCODE_INTERNAL_WEB_FETCH_ENABLED` | `false` | Legacy compatibility flag; default-enables `web_fetch` when no allowlist is configured |
| `OPENCODE_INTERNAL_ALLOWED_TOOLS` | `(none)` | Allowed built-in tool list when client `tools` are omitted, comma-separated |
| `OPENCODE_INTERNAL_TOOL_METRICS_ENABLED` | `true` | Log debug info and collect telemetry for internal allowlist mode |
| `OPENCODE_TOOL_DISCOVERY_FIXTURE` | `(none)` | Mock tool ID list for integration tests / local debug, comma-separated |
| `OPENCODE_HEALTH_DETAILS_ENABLED` | `true` | Expose `/health/details` endpoint |
| `OPENCODE_HEALTH_DETAILS_REQUIRE_AUTH` | `true` | Enable Bearer token requirement for `/health/details` |
| `OPENCODE_METRICS_ENABLED` | `false` | Expose Prometheus `/metrics` endpoint |
| `OPENCODE_METRICS_REQUIRE_AUTH` | `true` | Enable Bearer token requirement for `/metrics` |
| `USE_ISOLATED_HOME` | `false` | Use isolated home directory for OpenCode configuration |
| `OPENCODE_PROXY_PROMPT_MODE` | `standard` | Prompt processing mode |
| `OPENCODE_PROXY_OMIT_SYSTEM_PROMPT` | `false` | Ignore incoming system prompt |
| `OPENCODE_PROXY_AUTO_CLEANUP_CONVERSATIONS` | `false` | Automatically clean up inactive conversations |
| `OPENCODE_PROXY_CLEANUP_INTERVAL_MS` | `43200000` | Cleanup interval (milliseconds) |
| `OPENCODE_PROXY_CLEANUP_MAX_AGE_MS` | `86400000` | Maximum conversation age (milliseconds) |
| `OPENCODE_PROXY_REQUEST_TIMEOUT_MS` | `180000` | Request timeout duration (milliseconds) |
| `OPENCODE_SERVER_URL` | `http://127.0.0.1:10001` | OpenCode server base URL |
| `OPENCODE_SERVER_PASSWORD` | - | OpenCode server basic auth password |
| `OPENCODE_PATH` | `opencode` | Path to the OpenCode executable CLI binary |
| `OPENCODE_ZEN_API_KEY` | - | Zen API Key pass-through |
| `DEBUG` / `OPENCODE_PROXY_DEBUG` | `false` | Enable verbose logging |

> 📄 For a complete description of all options, check the [Configuration Details](./docs/configuration.md) document.

### Recommended Production Environment Variables

```env
API_KEY=your-secret-key
OPENCODE_SERVER_PASSWORD=your-password
DISABLE_TOOLS=true
OPENCODE_EXTERNAL_TOOLS_MODE=proxy-bridge
OPENCODE_EXTERNAL_TOOLS_CONFLICT_POLICY=namespace
OPENCODE_INTERNAL_ALLOWED_TOOLS=web_fetch
OPENCODE_INTERNAL_TOOL_METRICS_ENABLED=true
OPENCODE_TOOL_DISCOVERY_FIXTURE=
OPENCODE_HEALTH_DETAILS_ENABLED=true
OPENCODE_HEALTH_DETAILS_REQUIRE_AUTH=true
OPENCODE_METRICS_ENABLED=false
OPENCODE_METRICS_REQUIRE_AUTH=true
OPENCODE_PROXY_PROMPT_MODE=plugin-inject
OPENCODE_PROXY_OMIT_SYSTEM_PROMPT=true
OPENCODE_PROXY_AUTO_CLEANUP_CONVERSATIONS=true
```

---

## 🔌 API Reference

### Endpoints

| Method | Path | Description |
|:-----|:-----|:-----|
| `GET` | `/health` | Server health status check |
| `GET` | `/health/details` | Diagnostics/operational metrics (auth gates apply) |
| `GET` | `/metrics` | Prometheus telemetry metrics (auth gates apply) |
| `GET` | `/v1/models` | List available models |
| `POST` | `/v1/messages` | Claude-compatible messages API (supports SSE streams) |

---

## 🔧 Troubleshooting

- Check [Troubleshooting Guide](./docs/troubleshooting.md) for details.

---

## 🔨 Development

```bash
# Run tests
pytest tests/test_app.py -v

# Run with docker compose local build
docker compose up -d --build
```

---

## 📄 License

MIT · Check [LICENSE](./LICENSE.md) for details.
