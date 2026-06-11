import os
import sys
import time
import asyncio
from pathlib import Path
import subprocess
from .config import settings
from .opencode_client import opencode_client

OPENCODE_BASENAME = "opencode"

def get_candidate_names():
    if sys.platform == "win32":
        return [f"{OPENCODE_BASENAME}.cmd", f"{OPENCODE_BASENAME}.exe", f"{OPENCODE_BASENAME}.bat", OPENCODE_BASENAME]
    return [OPENCODE_BASENAME]

def find_executable_in_dirs(dirs, names):
    for d in dirs:
        if not d:
            continue
        for name in names:
            full = Path(d) / name
            if full.exists() and full.is_file():
                return str(full)
    return None

def resolve_opencode_path(requested_path):
    input_path = (requested_path or "").strip()
    names = get_candidate_names()

    if input_path:
        # Check if it looks like a path
        if os.path.isabs(input_path) or "/" in input_path or "\\" in input_path:
            p = Path(input_path)
            if p.exists():
                return {"path": str(p), "source": "config"}
            resolved = Path.cwd() / input_path
            if resolved.exists():
                return {"path": str(resolved), "source": "config"}

    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    from_path = find_executable_in_dirs(path_dirs, names)
    if from_path:
        return {"path": from_path, "source": "PATH"}

    extra_dirs = []
    if os.environ.get("OPENCODE_HOME"):
        extra_dirs.append(str(Path(os.environ["OPENCODE_HOME"]) / "bin"))
    if os.environ.get("OPENCODE_DIR"):
        extra_dirs.append(str(Path(os.environ["OPENCODE_DIR"]) / "bin"))
        
    prefix = os.environ.get("npm_config_prefix") or os.environ.get("NPM_CONFIG_PREFIX")
    if prefix:
        extra_dirs.append(prefix if sys.platform == "win32" else str(Path(prefix) / "bin"))
        
    if os.environ.get("PNPM_HOME"):
        extra_dirs.append(os.environ["PNPM_HOME"])
    if os.environ.get("YARN_GLOBAL_FOLDER"):
        extra_dirs.append(str(Path(os.environ["YARN_GLOBAL_FOLDER"]) / "bin"))
    if os.environ.get("VOLTA_HOME"):
        extra_dirs.append(str(Path(os.environ["VOLTA_HOME"]) / "bin"))
    if os.environ.get("NVM_BIN"):
        extra_dirs.append(os.environ["NVM_BIN"])
        
    extra_dirs.append(os.path.dirname(sys.executable))

    home = Path.home()
    extra_dirs.extend([
        str(home / ".opencode" / "bin"),
        str(home / ".local" / "bin"),
        str(home / ".npm-global" / "bin"),
        str(home / ".npm" / "bin"),
        str(home / ".pnpm-global" / "bin"),
        str(home / ".local" / "share" / "pnpm"),
        str(home / ".fnm" / "node-versions" / "v1" / "installations"),
        str(home / ".asdf" / "shims")
    ])

    if sys.platform == "win32":
        if os.environ.get("APPDATA"):
            extra_dirs.append(str(Path(os.environ["APPDATA"]) / "npm"))
        if os.environ.get("LOCALAPPDATA"):
            extra_dirs.append(str(Path(os.environ["LOCALAPPDATA"]) / "pnpm"))
        extra_dirs.append(os.environ.get("NVM_HOME"))
        extra_dirs.append(os.environ.get("NVM_SYMLINK"))
        if os.environ.get("ProgramFiles"):
            extra_dirs.append(str(Path(os.environ["ProgramFiles"]) / "nodejs"))
        if os.environ.get("ProgramFiles(x86)"):
            extra_dirs.append(str(Path(os.environ["ProgramFiles(x86)"]) / "nodejs"))
    else:
        extra_dirs.extend([
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
            "/opt/homebrew/bin",
            "/snap/bin"
        ])

    from_extras = find_executable_in_dirs(extra_dirs, names)
    if from_extras:
        return {"path": from_extras, "source": "known-locations"}

    return {"path": None, "source": "not-found"}

class ProcessManager:
    def __init__(self):
        self.process = None
        self.jail_root = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode-proxy-jail"

    async def check_health(self):
        try:
            resp = await opencode_client.client.get(f"{opencode_client.base_url}/health", headers=opencode_client.headers, timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def start_backend(self):
        if not settings.MANAGE_BACKEND:
            print("[Process] MANAGE_BACKEND is false. Skipping spawn.")
            return

        is_healthy = await self.check_health()
        if is_healthy:
            print("[Process] Backend is already running.")
            return

        info = resolve_opencode_path(settings.OPENCODE_PATH)
        exe_path = info["path"]
        if not exe_path:
            print(f"[Error] OpenCode executable not found. Configure OPENCODE_PATH.")
            return

        print(f"[Process] Found OpenCode executable at {exe_path} (source: {info['source']})")

        env = os.environ.copy()
        
        # Isolated home logic
        if settings.USE_ISOLATED_HOME and sys.platform != "win32":
            self.jail_root.mkdir(parents=True, exist_ok=True)
            env["OPENCODE_HOME"] = str(self.jail_root)
            env["XDG_CONFIG_HOME"] = str(self.jail_root / ".config")
            env["XDG_DATA_HOME"] = str(self.jail_root / ".local" / "share")
            env["XDG_STATE_HOME"] = str(self.jail_root / ".local" / "state")
            env["XDG_CACHE_HOME"] = str(self.jail_root / ".cache")

        port = settings.OPENCODE_SERVER_URL.split(":")[-1].replace("/", "")
        
        args = [exe_path, "serve", "--port", port, "--print-logs", "--log-level", "DEBUG"]
        if settings.OPENCODE_SERVER_PASSWORD:
            args.extend(["--password", settings.OPENCODE_SERVER_PASSWORD])

        print(f"[Process] Spawning: {' '.join(args)}")
        
        # Start detached
        try:
            self.process = subprocess.Popen(
                args,
                env=env,
                stdout=None,
                stderr=None,
                start_new_session=True if sys.platform != "win32" else False
            )
            
            # Wait for health check
            print("[Process] Waiting for backend to start...")
            for i in range(60):
                await asyncio.sleep(2)
                if await self.check_health():
                    print("[Process] Backend is healthy.")
                    return
                print(f"[Process] Still waiting... ({i+1}/60)")
            print("[Error] Backend failed to start within timeout.")
        except Exception as e:
            print(f"[Error] Failed to spawn backend: {e}")

    def kill_backend(self):
        if self.process:
            print("[Process] Terminating backend process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

process_manager = ProcessManager()
