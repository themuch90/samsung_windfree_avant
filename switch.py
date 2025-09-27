
from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SmartThingsCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartThingsCoordinator = data["coordinator"]
    entities = []
    for did in coordinator.device_ids:
        base_name = coordinator.device_labels.get(did, f"Device {did[-6:]}")
        entities.append(LightingSwitch(coordinator, did, base_name))
        entities.append(BeepSwitch(coordinator, did, base_name))
        entities.append(AutoCleanSwitch(coordinator, did, base_name))
    async_add_entities(entities)

class _BaseSTSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartThingsCoordinator, device_id: str, base_name: str):
        super().__init__(coordinator)
        self.device_id = device_id
        self.base_name = base_name

class LightingSwitch(_BaseSTSwitch):
    _attr_has_entity_name = True
    _attr_icon = "mdi:led-outline"

    def __init__(self, coordinator: SmartThingsCoordinator, device_id: str, base_name: str):
        super().__init__(coordinator, device_id, base_name)
        self._attr_unique_id = f"{DOMAIN}_{device_id}_lighting"
        self._attr_name = f"{base_name} Display"

    @property
    def is_on(self) -> bool:
        val = self.coordinator.data.get("lighting", {}).get(self.device_id)
        return val == "on"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "samsungce.airConditionerLighting", "on")
        self.coordinator.data["lighting"][self.device_id] = "on"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "samsungce.airConditionerLighting", "off")
        self.coordinator.data["lighting"][self.device_id] = "off"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

class BeepSwitch(_BaseSTSwitch):
    _attr_has_entity_name = True
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator: SmartThingsCoordinator, device_id: str, base_name: str):
        super().__init__(coordinator, device_id, base_name)
        self._attr_unique_id = f"{DOMAIN}_{device_id}_beep"
        self._attr_name = f"{base_name} Beep"

    @property
    def is_on(self) -> bool:
        val = self.coordinator.data.get("beep", {}).get(self.device_id)
        return val == "on"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "samsungce.airConditionerBeep", "setBeep", ["on"])
        self.coordinator.data["beep"][self.device_id] = "on"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "samsungce.airConditionerBeep", "setBeep", ["off"])
        self.coordinator.data["beep"][self.device_id] = "off"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

class AutoCleanSwitch(_BaseSTSwitch):
    _attr_has_entity_name = True
    _attr_icon = "mdi:spray-bottle"

    def __init__(self, coordinator: SmartThingsCoordinator, device_id: str, base_name: str):
        super().__init__(coordinator, device_id, base_name)
        self._attr_unique_id = f"{DOMAIN}_{device_id}_autoclean"
        self._attr_name = f"{base_name} Auto Cleaning"

    @property
    def is_on(self) -> bool:
        val = self.coordinator.data.get("autoclean", {}).get(self.device_id)
        return val == "on"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "custom.autoCleaningMode", "setAutoCleaningMode", ["on"])
        self.coordinator.data["autoclean"][self.device_id] = "on"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.client.command(self.device_id, "main", "custom.autoCleaningMode", "setAutoCleaningMode", ["off"])
        self.coordinator.data["autoclean"][self.device_id] = "off"
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()
