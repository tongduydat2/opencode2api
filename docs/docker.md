# 🐳 Docker Deployment

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## 🚀 Quick Start

### 1️⃣ Clone Project

```bash
git clone https://github.com/tongduydat2/opencode2api.git
cd opencode2api
```

### 2️⃣ Configure Environment

```bash
cp .env.example .env
# Edit the .env file and set your credentials
```

### 3️⃣ Start Services

```bash
docker compose up -d
```

### 4️⃣ Verification

```bash
# Check server health
curl http://127.0.0.1:10000/health

# List active models
curl -H "Authorization: Bearer $API_KEY" http://127.0.0.1:10000/v1/models
```

---

## ⚙️ Configuration File

### .env File Configuration

```env
# Required Configurations
API_KEY=change-me
OPENCODE_SERVER_PASSWORD=change-me-too

# Tool Safety Settings
DISABLE_TOOLS=true

# Optional Configurations
OPENCODE_PROXY_PROMPT_MODE=plugin-inject
OPENCODE_PROXY_OMIT_SYSTEM_PROMPT=true
OPENCODE_PROXY_AUTO_CLEANUP_CONVERSATIONS=true
```

---

## 📦 Volume Mounts

| Volume Name | Container Path | Description |
|:-----|:----------|:-----|
| `opencode-data` | `/home/appuser/.local/share/opencode` | OpenCode data storage path |
| `opencode-config` | `/home/appuser/.config/opencode` | OpenCode configuration path |

---

## 🔨 Custom Build

### Build Docker Image

```bash
docker build -t opencode2api .
```

### Run Standalone Container

```bash
docker run -d \
  -p 10000:10000 \
  -p 10001:10001 \
  -e API_KEY=your-key \
  -e OPENCODE_SERVER_PASSWORD=your-password \
  -v opencode-data:/home/appuser/.local/share/opencode \
  -v opencode-config:/home/appuser/.config/opencode \
  opencode2api
```

---

## 📝 Production Recommendations

### Volume Access Permissions

The container is configured to run under a non-root system user `appuser` (UID: 1000, GID: 1000). Please ensure mapped directory paths in host volumes grant appropriate read/write privileges to this user ID.

---

## 📊 Logs Management

### Watch Container Logs

```bash
docker compose logs -f
```

### Docker Log Rotation

We recommend declaring log rotation options in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## ✅ Health Checks

The compose template includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:10000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

---

## ❓ FAQ

### Container Fails to Start

Verify container output:
```bash
docker compose logs
```

### Permissions Issue on Mounts

Ensure folder path ownership is correctly set for UID 1000.
