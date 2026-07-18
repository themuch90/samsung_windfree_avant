
from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, PLATFORMS
from .coordinator import SmartThingsCoordinator
from .oauth import TokenManager
from .vendor.smartthings_client import SmartThingsClient

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    session = async_get_clientsession(hass)

    token_manager = TokenManager(hass, entry)
    # Ottiene subito un token valido (rinnovandolo se necessario) prima
    # di creare il client, così non partiamo mai con un token scaduto.
    access_token = await token_manager.async_get_valid_token()

    client = SmartThingsClient(access_token, session=session)
    coordinator = SmartThingsCoordinator(hass, client, token_manager)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "token_manager": token_manager,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data and "client" in data:
        await data["client"].close()
    return unload_ok

