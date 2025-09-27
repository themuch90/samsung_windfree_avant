
from typing import Any, Dict, List, Optional
import aiohttp

API = "https://api.smartthings.com/v1"

class SmartThingsError(Exception):
    pass

class SmartThingsClient:
    def __init__(self, token: str, session: Optional[aiohttp.ClientSession] = None):
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._own_session = session is None
        self._session = session or aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))

    async def close(self):
        if self._own_session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{API}{path}"
        headers = kwargs.pop("headers", {})
        merged_headers = {**self._headers, **headers}
        async with self._session.request(method, url, headers=merged_headers, **kwargs) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise SmartThingsError(f"{method} {path} -> {resp.status}: {text}")
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.text()

    async def list_devices(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/devices")
        return data.get("items", [])

    async def get_device_status(self, device_id: str):
        return await self._request("GET", f"/devices/{device_id}/status")

    async def command(self, device_id: str, component: str, capability: str, command: str, args: Optional[list]=None):
        payload = {
            "commands": [
                {
                    "component": component,
                    "capability": capability,
                    "command": command,
                    **({"arguments": args} if args else {})
                }
            ]
        }
        return await self._request("POST", f"/devices/{device_id}/commands", json=payload)
