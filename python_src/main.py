import json
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from .config import settings
from .process_manager import process_manager
from .opencode_client import opencode_client
from .tool_runtime import generate_tool_instructions, parse_tool_calls_from_text, strip_function_call_markup
from .stream_parser import ToolCallFilter, ToolCallStreamParser

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start OpenCode backend
    if settings.MANAGE_BACKEND:
        await process_manager.start_backend()
    yield
    # Shutdown OpenCode backend
    if settings.MANAGE_BACKEND:
        process_manager.kill_backend()

app = FastAPI(lifespan=lifespan)

# --- Auth helpers ---
def _has_valid_bearer_auth(request: Request) -> bool:
    if not settings.API_KEY or not settings.API_KEY.strip():
        return True
    auth = request.headers.get("authorization", "")
    return auth == f"Bearer {settings.API_KEY}"

def _should_allow_operational(request: Request, *, enabled: bool, require_auth: bool) -> bool:
    if not enabled:
        return False
    if not require_auth:
        return True
    return _has_valid_bearer_auth(request)

# --- Internal tool metrics ---
_internal_tool_metrics = {
    "externalBridgeRequests": 0,
    "internalAllowlistRequests": 0,
    "disabledRequests": 0,
    "discoveryFailures": 0,
    "fallbackToDisabled": 0,
}

# --- Backend tool ID cache ---
_cached_tool_ids: list | None = None
_cached_tool_ids_at: float = 0
_TOOL_IDS_CACHE_MS = 60_000

async def _get_backend_tool_ids() -> list | None:
    global _cached_tool_ids, _cached_tool_ids_at
    now_ms = time.time() * 1000
    if _cached_tool_ids is not None and (now_ms - _cached_tool_ids_at) < _TOOL_IDS_CACHE_MS:
        return _cached_tool_ids
    fixture = [s.strip() for s in settings.INTERNAL_TOOL_DISCOVERY_FIXTURE if s.strip()]
    if fixture:
        _cached_tool_ids = fixture
        _cached_tool_ids_at = now_ms
        return fixture
    try:
        data = await opencode_client.get_tool_ids()
        ids = data if isinstance(data, list) else (data.get("data", []) if isinstance(data, dict) else [])
        _cached_tool_ids = ids
        _cached_tool_ids_at = now_ms
        return ids
    except Exception:
        _internal_tool_metrics["discoveryFailures"] += 1
        return None

# --- Routes ---

@app.get("/health")
async def health():
    backend_healthy = await process_manager.check_health()
    return {"status": "ok" if backend_healthy else "degraded", "backend": backend_healthy}

@app.get("/health/details")
async def health_details(request: Request):
    if not _should_allow_operational(request, enabled=settings.HEALTH_DETAILS_ENABLED, require_auth=settings.HEALTH_DETAILS_REQUIRE_AUTH):
        status = 401 if settings.HEALTH_DETAILS_ENABLED else 404
        msg = "Unauthorized" if settings.HEALTH_DETAILS_ENABLED else "Not found"
        return JSONResponse({"error": {"message": msg}}, status_code=status)
    metrics_snapshot = dict(_internal_tool_metrics) if settings.INTERNAL_TOOL_METRICS_ENABLED else None
    allowed = [s.strip() for s in settings.INTERNAL_ALLOWED_TOOLS if s.strip()]
    fixture = [s.strip() for s in settings.INTERNAL_TOOL_DISCOVERY_FIXTURE if s.strip()]
    return {
        "status": "ok",
        "proxy": True,
        "internal_tools": {
            "config": {
                "allowed_tools": allowed,
                "metrics_enabled": settings.INTERNAL_TOOL_METRICS_ENABLED,
                "discovery_fixture": fixture,
            },
            "metrics": metrics_snapshot,
            "cache": {
                "tool_ids_cached": _cached_tool_ids is not None,
                "tool_id_count": len(_cached_tool_ids) if _cached_tool_ids else 0,
                "age_ms": int(time.time() * 1000 - _cached_tool_ids_at) if _cached_tool_ids_at else None,
            },
        },
    }

@app.get("/metrics")
async def metrics(request: Request):
    if not _should_allow_operational(request, enabled=settings.METRICS_ENABLED, require_auth=settings.METRICS_REQUIRE_AUTH):
        status = 401 if settings.METRICS_ENABLED else 404
        msg = "Unauthorized" if settings.METRICS_ENABLED else "Not found"
        return PlainTextResponse(msg, status_code=status)
    m = _internal_tool_metrics
    lines = [
        '# HELP opencode_internal_tool_mode_requests_total Count of internal tool mode selections by mode.',
        '# TYPE opencode_internal_tool_mode_requests_total counter',
        f'opencode_internal_tool_mode_requests_total{{mode="external_bridge"}} {m["externalBridgeRequests"]}',
        f'opencode_internal_tool_mode_requests_total{{mode="internal_allowlist"}} {m["internalAllowlistRequests"]}',
        f'opencode_internal_tool_mode_requests_total{{mode="disabled"}} {m["disabledRequests"]}',
        '# HELP opencode_internal_tool_discovery_failures_total Count of backend tool discovery failures.',
        '# TYPE opencode_internal_tool_discovery_failures_total counter',
        f'opencode_internal_tool_discovery_failures_total {m["discoveryFailures"]}',
        '# HELP opencode_internal_tool_fallback_disabled_total Count of allowlist resolutions that fell back to disabled.',
        '# TYPE opencode_internal_tool_fallback_disabled_total counter',
        f'opencode_internal_tool_fallback_disabled_total {m["fallbackToDisabled"]}',
        '# HELP opencode_internal_tool_cache_ids Number of cached backend tool IDs.',
        '# TYPE opencode_internal_tool_cache_ids gauge',
        f'opencode_internal_tool_cache_ids {len(_cached_tool_ids) if _cached_tool_ids else 0}',
    ]
    return PlainTextResponse('\n'.join(lines) + '\n', media_type='text/plain; version=0.0.4')


MODEL_MAPPING = {
    "claude-3-haiku-20240307": "claude-haiku-4-5",
    "claude-3-5-haiku-20241022": "claude-haiku-4-5",
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-5",
    "claude-3-5-sonnet-20240620": "claude-sonnet-4-5",
    "claude-3-opus-20240229": "claude-opus-4-1"
}

@app.get("/v1/models")
async def list_models():
    try:
        providers_response = await opencode_client.get_providers()
        models = []
        # The HTTP response has {"providers": [...]}
        for p in providers_response.get("providers", []):
            models_dict = p.get("models", {})
            for m_id, m_data in models_dict.items():
                models.append({
                    "id": f"{p['id']}/{m_id}",
                    "object": "model",
                    "created": 1709772800,
                    "owned_by": p["id"]
                })
        return {"object": "list", "data": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/messages")
async def create_message(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Claude format to OpenCode promptParams mapping
    model_id = data.get("model", "")
    provider_id = "opencode"
    
    # Apply standard model mapping if found
    if model_id in MODEL_MAPPING:
        model_id = MODEL_MAPPING[model_id]
        
    if "/" in model_id:
        provider_id, model_id = model_id.split("/", 1)
        
    messages = data.get("messages", [])
    system = data.get("system", "")
    
    # Tool handling
    tools = data.get("tools", [])
    if tools and not settings.DISABLE_TOOLS:
        tool_instructions = generate_tool_instructions(tools)
        system = f"{system}\n\n{tool_instructions}" if system else tool_instructions

    # Track tool mode metrics
    if tools and not settings.DISABLE_TOOLS:
        _internal_tool_metrics["externalBridgeRequests"] += 1
    elif settings.INTERNAL_ALLOWED_TOOLS:
        _internal_tool_metrics["internalAllowlistRequests"] += 1
    else:
        _internal_tool_metrics["disabledRequests"] += 1

    # Build OpenCode session body
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        
        content_text = ""
        if isinstance(content, str):
            content_text = content
        elif isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    content_text += block.get("text", "")
                elif block.get("type") == "tool_result":
                    content_text += f"Tool execution result for '{block.get('tool_use_id')}':\n{block.get('content', '')}"

        if not content_text:
            continue
            
        if role == "tool" or content_text.startswith("ASSISTANT: ") or content_text.startswith("TOOL_RESULT: ") or role == "user":
            text = content_text
        else:
            text = f"{str(role).upper()}: {content_text}"

        parts.append({"type": "text", "text": text})

    prompt_params = {
        "body": {
            "model": {"providerID": provider_id, "modelID": model_id},
            "system": system,
            "parts": parts
        }
    }

    try:
        session_info = await opencode_client.create_session()
        session_id = session_info["id"]
        prompt_params["path"] = {"id": session_id}
        
        is_stream = data.get("stream", False)
        
        async def delayed_prompt():
            try:
                await asyncio.sleep(0.5)
                await opencode_client.prompt(session_id, prompt_params)
            except Exception:
                pass
        
        if not is_stream:
            # Subscribe to events first, then trigger prompt
            loop = asyncio.get_event_loop()
            prompt_task = loop.create_task(delayed_prompt())
            try:
                response = await handle_non_streaming(session_id, data, tools)
                # DO NOT await prompt_task as it might raise 500 when we delete session
                return response
            finally:
                try:
                    await opencode_client.delete_session(session_id)
                except Exception:
                    pass
        else:
            async def streaming_generator():
                loop = asyncio.get_event_loop()
                prompt_task = loop.create_task(delayed_prompt())
                try:
                    async for chunk in handle_streaming(session_id, data, tools):
                        yield chunk
                finally:
                    try:
                        await opencode_client.delete_session(session_id)
                    except Exception:
                        pass
            return EventSourceResponse(streaming_generator())
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_non_streaming(session_id: str, request_data: dict, tools: list):
    content = ""
    reasoning = ""
    part_types = {}
    
    async for event in opencode_client.subscribe_events():
        event_type = event.get("type")
        props = event.get("properties", {})
        
        if event_type == "message.part.updated" and props.get("part", {}).get("sessionID") == session_id:
            part = props["part"]
            part_id = part.get("id")
            part_type = part.get("type")
            if part_id and part_type:
                part_types[part_id] = part_type
                
        elif event_type == "message.part.delta" and props.get("sessionID") == session_id:
            part_id = props.get("partID")
            delta = props.get("delta", "")
            part_type = part_types.get(part_id, "text")
            
            if part_type == "reasoning":
                reasoning += delta
            else:
                content += delta
                
        elif event_type == "message.updated" and props.get("info", {}).get("sessionID") == session_id:
            finish_reason = props.get("info", {}).get("finish")
            if finish_reason:
                print(f"[Finish] Breaking loop, reason: {finish_reason}")
                break
                
    # Parse tools if any
    tool_uses = []
    if tools and not settings.DISABLE_TOOLS:
        tool_uses = parse_tool_calls_from_text(content)
        content = strip_function_call_markup(content)

    resp = {
        "id": f"msg_{session_id}",
        "type": "message",
        "role": "assistant",
        "model": request_data.get("model", ""),
        "stop_reason": "tool_use" if tool_uses else "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "content": []
    }
    
    if content:
        resp["content"].append({"type": "text", "text": content})
        
    for tu in tool_uses:
        resp["content"].append(tu)
        
    return JSONResponse(resp)

async def handle_streaming(session_id: str, request_data: dict, tools: list):
    try:
        # Initial message_start
        yield {
            "event": "message_start",
            "data": json.dumps({
                "type": "message_start",
                "message": {
                    "id": f"msg_{session_id}",
                    "type": "message",
                    "role": "assistant",
                    "model": request_data.get("model", ""),
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0}
                }
            })
        }
        
        # content_block_start
        yield {
            "event": "content_block_start",
            "data": json.dumps({
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""}
            })
        }

        tool_parser = ToolCallStreamParser()
        tool_filter = ToolCallFilter(disable_tools=settings.DISABLE_TOOLS)
        tool_uses = []
        part_types = {}

        async for event in opencode_client.subscribe_events():
            event_type = event.get("type")
            props = event.get("properties", {})
            
            if event_type == "message.part.updated" and props.get("part", {}).get("sessionID") == session_id:
                part = props["part"]
                part_id = part.get("id")
                part_type = part.get("type")
                if part_id and part_type:
                    part_types[part_id] = part_type
                    
            elif event_type == "message.part.delta" and props.get("sessionID") == session_id:
                part_id = props.get("partID")
                delta = props.get("delta", "")
                part_type = part_types.get(part_id, "text")
                
                if part_type == "text" and delta:
                    # Filter markup before yielding text to user
                    filtered_delta = tool_filter.filter_chunk(delta)
                    
                    if filtered_delta:
                        yield {
                            "event": "content_block_delta",
                            "data": json.dumps({
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": filtered_delta}
                            })
                        }
                        
                    # Parse tool calls from the raw delta
                    if tools and not settings.DISABLE_TOOLS:
                        new_tools = tool_parser.parse_chunk(delta)
                        for t in new_tools:
                            tool_uses.append(t)
                            
            elif event_type == "message.updated" and props.get("info", {}).get("sessionID") == session_id:
                if props["info"].get("finish") == "stop":
                    break

        yield {
            "event": "content_block_stop",
            "data": json.dumps({"type": "content_block_stop", "index": 0})
        }
        
        # If tools were parsed, yield them as well
        for idx, tu in enumerate(tool_uses, start=1):
            yield {
                "event": "content_block_start",
                "data": json.dumps({
                    "type": "content_block_start",
                    "index": idx,
                    "content_block": {"type": "tool_use", "id": tu["id"], "name": tu["name"], "input": {}}
                })
            }
            # We yield the entire input as a single delta for simplicity
            yield {
                "event": "content_block_delta",
                "data": json.dumps({
                    "type": "content_block_delta",
                    "index": idx,
                    "delta": {"type": "input_json_delta", "partial_json": json.dumps(tu["input"])}
                })
            }
            yield {
                "event": "content_block_stop",
                "data": json.dumps({"type": "content_block_stop", "index": idx})
            }

        # message_delta
        yield {
            "event": "message_delta",
            "data": json.dumps({
                "type": "message_delta",
                "delta": {"stop_reason": "tool_use" if tool_uses else "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 0}
            })
        }
        
        yield {
            "event": "message_stop",
            "data": json.dumps({"type": "message_stop"})
        }
    except Exception as e:
        print(f"[Streaming Error] {e}")
