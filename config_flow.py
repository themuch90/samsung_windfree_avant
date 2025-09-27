
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_TOKEN
from .vendor.smartthings_pat import SmartThingsClient, SmartThingsError

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            session = async_get_clientsession(self.hass)
            client = SmartThingsClient(token, session=session)
            try:
                devices = await client.list_devices()
            except SmartThingsError:
                errors["base"] = "invalid_auth"
            else:
                title = f"SmartThings PAT ({len(devices)} devices)"
                return self.async_create_entry(title=title, data={CONF_TOKEN: token})

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
