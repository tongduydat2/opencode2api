# 🔧 Troubleshooting Guide

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## ❓ Common Issues

### 1️⃣ Request Hanging / Stalling

| Item | Details |
|:-----|:-----|
| **Symptom** | `/v1/models` works instantly, but chat queries stay pending forever with no stream or text output |
| **Solution** | Set `USE_ISOLATED_HOME=false` so that the runtime can reuse active system credentials |

```bash
USE_ISOLATED_HOME=false
# or
OPENCODE_USE_ISOLATED_HOME=false
```

---

### 2️⃣ Model Not Found

| Item | Details |
|:-----|:-----|
| **Symptom** | Returns a `Not found` / `model_not_found` error |
| **Solution** | Retrieve list of models and check if ID exactly matches |

```bash
curl http://127.0.0.1:10000/v1/models
```

---

### 3️⃣ Port Conflict

| Item | Details |
|:-----|:-----|
| **Symptom** | `Address already in use` error message on launch |
| **Solution** | Check which process holds the port and change configurations |

```bash
# Verify active ports usage
lsof -i :10000
lsof -i :10001

# Choose another port (e.g. edit your .env file)
OPENCODE_PROXY_PORT=10002
OPENCODE_SERVER_PORT=10003
```

---

### 4️⃣ OpenCode CLI Not Found

| Item | Details |
|:-----|:-----|
| **Symptom** | `Found no OpenCode executable` error during backend startup checks |
| **Solution** | Install the OpenCode executable CLI manually |

```bash
# Linux/macOS
curl -fsSL https://opencode.ai/install | bash
```

---

### 5️⃣ Docker Container Fails to Start

| Item | Details |
|:-----|:-----|
| **Symptom** | Docker container exits immediately after running `docker compose up` |
| **Solution** | Inspect container logs to look for detailed configuration or dependency failures |

```bash
docker compose logs
```

---

### 6️⃣ Unauthorized Responses

| Item | Details |
|:-----|:-----|
| **Symptom** | API requests return `401 Unauthorized` status code |
| **Solution** | Set the `API_KEY` header using the correct bearer authorization token format |

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" ...
```

---

## 🔍 Debugging Mode

Enable detailed logging:

```bash
# Set environment variable
DEBUG=true
# or
OPENCODE_PROXY_DEBUG=true
```

---

## 🆘 Getting Help

- 🐛 [Report Issues on GitHub](https://github.com/tongduydat2/opencode2claude/issues)
