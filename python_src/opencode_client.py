import json
import base64
import httpx
from typing import AsyncGenerator
from .config import settings

class OpenCodeClient:
    def __init__(self):
        self.base_url = settings.OPENCODE_SERVER_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {}
        if settings.OPENCODE_SERVER_PASSWORD:
            token = base64.b64encode(f"opencode:{settings.OPENCODE_SERVER_PASSWORD}".encode()).decode()
            self.headers["Authorization"] = f"Basic {token}"

    async def get_providers(self):
        resp = await self.client.get(f"{self.base_url}/config/providers", headers=self.headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[Error] {e.response.text}")
            raise
        return resp.json()

    async def get_tool_ids(self):
        resp = await self.client.get(f"{self.base_url}/experimental/tool/ids", headers=self.headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[Error] {e.response.text}")
            raise
        return resp.json()

    async def create_session(self):
        resp = await self.client.post(f"{self.base_url}/session", headers=self.headers, json={})
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[Error] {e.response.text}")
            raise
        return resp.json()

    async def delete_session(self, session_id: str):
        resp = await self.client.delete(f"{self.base_url}/session/{session_id}", headers=self.headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[Error] {e.response.text}")
            raise
        return resp.json()

    async def prompt(self, session_id: str, prompt_params: dict):
        body = prompt_params.get("body", prompt_params)
        resp = await self.client.post(
            f"{self.base_url}/session/{session_id}/message", 
            headers=self.headers, 
            json=body
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[Error] {e.response.text}")
            raise
        return resp.json()

    async def subscribe_events(self) -> AsyncGenerator[dict, None]:
        async with self.client.stream("GET", f"{self.base_url}/event", headers=self.headers, timeout=None) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

opencode_client = OpenCodeClient()
