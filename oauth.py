from __future__ import annotations
import time, base64, logging
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import OAUTH_TOKEN_URL

_LOGGER = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

    @property
    def access_token(self):
        return self.entry.data.get("access_token")

    def _expires_at(self):
        return self.entry.data.get("token_expires_at", 0)

    async def async_get_valid_token(self):
        if time.time() < self._expires_at() - 60:
            return self.access_token
        return await self._async_refresh()

    async def _async_refresh(self):
        session = async_get_clientsession(self.hass)
        client_id = self.entry.data["client_id"]
        client_secret = self.entry.data["client_secret"]
        refresh_token = self.entry.data["refresh_token"]
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = await session.post(
            OAUTH_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            },
        )
        if resp.status != 200:
            text = await resp.text()
            _LOGGER.error("Refresh token fallito: %s", text)
            raise RuntimeError("token_refresh_failed")
        payload = await resp.json()
        new_data = dict(self.entry.data)
        new_data["access_token"] = payload["access_token"]
        new_data["refresh_token"] = payload["refresh_token"]
        new_data["token_expires_at"] = time.time() + payload.get("expires_in", 86400)
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        return payload["access_token"]