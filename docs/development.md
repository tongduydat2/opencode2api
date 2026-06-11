# 💻 Developer Guide

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
</p>

---

## 📋 Prerequisites

### Python Environment

```bash
# Python 3.10+
python3 --version

# pip
pip --version
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install OpenCode CLI

```bash
# Linux/macOS
curl -fsSL https://opencode.ai/install | bash
```

---

## 🚀 Development Mode

### Start Development Server

```bash
bash ./run_python.sh
```

> This automatically spins up the OpenCode CLI server backend (if `OPENCODE_PROXY_MANAGE_BACKEND=true` is set) and launches the FastAPI proxy server.

---

## ✅ Testing

| Command | Description |
|:-----|:-----|
| `pytest tests/test_app.py -v` | Run all Python unit and integration tests |
| `bash tests/test-integration.sh` | Build Docker image and run container-based integration tests |
| `bash tests/test-streaming-real.sh` | Run live streaming test cases against real models |

---

## 📂 Project Structure

```
opencode2claude/
├── python_src/            # Python FastAPI source code
│   ├── __init__.py
│   ├── config.py          # Settings parser using Pydantic Settings
│   ├── main.py            # API routes and proxy controllers
│   ├── opencode_client.py # HTTP client communicating with OpenCode CLI
│   ├── process_manager.py # Subprocess management lifecycle for OpenCode backend
│   └── utils.py           # General utility functions
├── tests/                 # Testing directory
│   ├── test_app.py        # pytest suite
│   ├── test-integration.sh # Docker integration test shell script
│   └── test-streaming-real.sh # Streaming validation test shell script
├── docs/                  # Documentation center
├── Dockerfile             # Python Docker image definition
├── entrypoint.sh          # Container entrypoint script
└── docker-compose.yml     # Docker compose template
```

---

## 🔄 Contribution Workflow

1. ⭐ Fork the project
2. 🌿 Create feature branch: `git checkout -b feature/your-feature`
3. 💾 Commit changes: `git commit -m 'feat: add new feature'`
4. 📤 Push branch: `git push origin feature/your-feature`
5. 🔀 Create a Pull Request

---

## 📄 License

MIT License - Check [LICENSE](../LICENSE.md) for details.
