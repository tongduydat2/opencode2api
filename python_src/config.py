import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = int(os.environ.get("OPENCODE_PROXY_PORT", 10000))
    API_KEY: str = ""
    OPENCODE_SERVER_URL: str = f"http://127.0.0.1:{os.environ.get('OPENCODE_SERVER_PORT', 10001)}"
    OPENCODE_SERVER_PASSWORD: str = ""
    MANAGE_BACKEND: bool = False
    OPENCODE_PATH: str = "opencode"
    BIND_HOST: str = "0.0.0.0"
    DISABLE_TOOLS: bool = True
    EXTERNAL_TOOLS_MODE: str = "proxy-bridge"
    EXTERNAL_TOOLS_CONFLICT_POLICY: str = "namespace"
    INTERNAL_WEB_FETCH_ENABLED: bool = False
    INTERNAL_ALLOWED_TOOLS: list[str] = []
    INTERNAL_TOOL_METRICS_ENABLED: bool = True
    INTERNAL_TOOL_DISCOVERY_FIXTURE: list[str] = []
    HEALTH_DETAILS_ENABLED: bool = True
    HEALTH_DETAILS_REQUIRE_AUTH: bool = True
    METRICS_ENABLED: bool = False
    METRICS_REQUIRE_AUTH: bool = True
    USE_ISOLATED_HOME: bool = False
    REQUEST_TIMEOUT_MS: int = 180000
    DEBUG: bool = False
    ZEN_API_KEY: str = ""
    PROMPT_MODE: str = "standard"
    OMIT_SYSTEM_PROMPT: bool = False
    AUTO_CLEANUP_CONVERSATIONS: bool = False
    CLEANUP_INTERVAL_MS: int = 43200000
    CLEANUP_MAX_AGE_MS: int = 86400000

    @classmethod
    def load(cls):
        config_path = Path("config.json")
        file_config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
            except Exception as e:
                print(f"[Config] Error parsing config.json: {e}")

        # ENV variables take precedence automatically in BaseSettings if prefix is set,
        # but to match JS exactly: ENV > File > Default
        
        # We manually merge them to match JS behavior precisely
        kwargs = {}
        defaults = cls().model_dump()
        
        for key in defaults.keys():
            # ENV keys map
            env_key = f"OPENCODE_PROXY_{key}" if key in ["PORT", "MANAGE_BACKEND", "REQUEST_TIMEOUT_MS", "DEBUG", "PROMPT_MODE", "OMIT_SYSTEM_PROMPT", "AUTO_CLEANUP_CONVERSATIONS", "CLEANUP_INTERVAL_MS", "CLEANUP_MAX_AGE_MS"] else (f"OPENCODE_{key}" if key not in ["PORT", "API_KEY", "BIND_HOST", "OPENCODE_SERVER_URL", "OPENCODE_SERVER_PASSWORD", "OPENCODE_PATH"] else key)
            
            # Special case mappings from JS
            if key == "PORT":
                env_val = os.environ.get("OPENCODE_PROXY_PORT") or os.environ.get("PORT")
            elif key == "OPENCODE_SERVER_URL":
                env_val = os.environ.get("OPENCODE_SERVER_URL")
            elif key == "DISABLE_TOOLS":
                env_val = os.environ.get("OPENCODE_DISABLE_TOOLS")
            elif key == "ZEN_API_KEY":
                env_val = os.environ.get("OPENCODE_ZEN_API_KEY")
            elif key == "INTERNAL_TOOL_DISCOVERY_FIXTURE":
                env_val = os.environ.get("OPENCODE_TOOL_DISCOVERY_FIXTURE")
            else:
                env_val = os.environ.get(env_key)

            # File config
            file_val = file_config.get(key)
            
            # Resolve value
            final_val = defaults[key]
            if file_val is not None:
                final_val = file_val
            if env_val is not None:
                # Type coercion
                if isinstance(defaults[key], bool):
                    if isinstance(env_val, str):
                        final_val = env_val.lower() in ["1", "true", "yes", "y", "on"]
                    else:
                        final_val = bool(env_val)
                elif isinstance(defaults[key], int):
                    final_val = int(env_val)
                elif isinstance(defaults[key], list):
                    if isinstance(env_val, str):
                        final_val = [x.strip() for x in env_val.split(",") if x.strip()]
                    elif isinstance(env_val, list):
                        final_val = env_val
                else:
                    final_val = env_val
                    
            kwargs[key] = final_val
            
        return cls(**kwargs)

settings = Settings.load()
