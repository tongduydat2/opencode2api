# 🚀 Getting Started

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## 📋 Requirements

### 🐳 Docker Method (Recommended)

| Requirement | Details |
|:-----|:-----|
| Docker | 20.10+ |
| Docker Compose | Latest version |

### 💻 Local Python Method

| Requirement | Details |
|:-----|:-----|
| Python | 3.10+ |
| pip | Latest version |

---

## 🏁 Installation

### Option 1: Docker Deployment

| Step | Command |
|:-----|:-----|
| 1. Clone repository | `git clone https://github.com/tongduydat2/opencode2claude.git` |
| 2. Enter folder | `cd opencode2claude` |
| 3. Copy settings template | `cp .env.example .env` |
| 4. Start services | `docker compose up -d` |

### Option 2: Local Python Deployment

| Step | Command |
|:-----|:-----|
| 1. Clone repository | `git clone https://github.com/tongduydat2/opencode2claude.git` |
| 2. Enter folder | `cd opencode2claude` |
| 3. Install packages | `pip install -r requirements.txt` |
| 4. Copy settings template | `cp .env.example .env` |
| 5. Start servers | `bash ./run_python.sh` |

---

## ✅ Service Verification

```bash
# Health Check
curl http://127.0.0.1:10000/health

# List available models
curl -H "Authorization: Bearer $API_KEY" http://127.0.0.1:10000/v1/models
```

---

## 💡 Quick Chat Test

### Messages API (Non-Streaming)

```bash
curl -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": false
  }'
```

### Messages API (Streaming)

```bash
curl -N -X POST http://127.0.0.1:10000/v1/messages \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "opencode/deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": true
  }'
```

---

## ➡️ Next Steps

- ⚙️ Check [Configuration Details](./configuration.md) to explore all env options.
- 🐳 Check [Docker Deployment](./docker.md) for custom volumes and compose templates.
