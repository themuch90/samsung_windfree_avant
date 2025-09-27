
from __future__ import annotations
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SmartThingsCoordinator

API_TO_HA_MODES = {
    "off" : "off", # Not supported from API, but is used to chenge the "switch" state
    "auto": "auto",
    "cool": "cool",
    "heat": "heat",
    "dry": "dry",
    "fan": "fan_only",
}
SUPPORTED_HA_MODES = list(API_TO_HA_MODES.values())
HA_TO_API_MODES = {v: k for k, v in API_TO_HA_MODES.items()}
  
API_TO_HA_FAN_MODES = {
    "auto": "auto",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "turbo": "Turbo",
}
SUPPORTED_FAN_MODES = list(API_TO_HA_FAN_MODES.values())
HA_TO_API_FAN_MODES= {v: k for k, v in API_TO_HA_FAN_MODES.items()}

API_TO_HA_SWING_MODES = {
    "fixed": "off",
    "vertical": "vertical",
    "horizontal": "horizontal",
    "all": "both",
}
SUPPORTED_SWING_MODES = list(API_TO_HA_SWING_MODES.values())
HA_TO_API_SWING_MODES= {v: k for k, v in API_TO_HA_SWING_MODES.items()}

PRESET_MODES = ["None","Good Sleep","Quiet","WindFree","WindFree & GoodSleep","Rapid"]
API_TO_HA_PRESET = {
    "off": "None",
    "sleep": "Good Sleep",
    "quiet": "Quiet",
    "windFree": "WindFree",
    "windFreeSleep": "WindFree & GoodSleep",
    "speed": "Rapid",
}
PRESET_MODES = list(API_TO_HA_PRESET.values())
HA_TO_API_PRESET = {v: k for k, v in API_TO_HA_PRESET.items()}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartThingsCoordinator = data["coordinator"]
    entities = [SmartThingsClimate(coordinator, did) for did in coordinator.device_ids]
    async_add_entities(entities)

class SmartThingsClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:air-conditioner"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator: SmartThingsCoordinator, device_id: str):
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}"
        base_name = coordinator.device_labels.get(device_id, "WindFree")
        self._attr_name = f"{base_name}"
        self._attr_hvac_modes = SUPPORTED_HA_MODES
        self._attr_fan_modes = SUPPORTED_FAN_MODES
        self._attr_swing_modes = SUPPORTED_SWING_MODES
        self._attr_preset_modes = PRESET_MODES

    # ---- state ----
    @property
    def current_temperature(self):
        return self.coordinator.data.get("temps", {}).get(self.device_id)
    
    @property
    def current_humidity(self):
        return self.coordinator.data.get("humidity", {}).get(self.device_id)
    
    @property
    def target_temperature(self):
        return self.coordinator.data.get("cool_sp", {}).get(self.device_id)

    @property
    def hvac_mode(self):
        if self.is_on is False:
            return HVACMode.OFF
        st = self.coordinator.data.get("mode", {}).get(self.device_id)
        return HVACMode(API_TO_HA_MODES.get(st, "auto"))

    @property
    def is_on(self):
        sw = self.coordinator.data.get("switch", {}).get(self.device_id)
        return sw == "on"

    @property
    def fan_mode(self):
        api_val = self.coordinator.data.get("fan", {}).get(self.device_id, "off")
        return API_TO_HA_FAN_MODES.get(api_val)

    @property
    def swing_mode(self):
        api_val = self.coordinator.data.get("swing", {}).get(self.device_id, "off")
        return API_TO_HA_SWING_MODES.get(api_val)

    @property
    def preset_mode(self):
        api_val = self.coordinator.data.get("opt_mode", {}).get(self.device_id, "None")
        return API_TO_HA_PRESET.get(api_val)

    # ---- commands ----
    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.command(self.device_id, "main", "switch", "off")
            self.coordinator.data["switch"][self.device_id] = "off"
        else:
            if not self.is_on:
                await self.coordinator.client.command(self.device_id, "main", "switch", "on")
                self.coordinator.data["switch"][self.device_id] = "on"
            st_mode = HA_TO_API_MODES[hvac_mode]
            await self.coordinator.client.command(self.device_id, "main", "airConditionerMode", "setAirConditionerMode", [st_mode])
            self.coordinator.data["mode"][self.device_id] = st_mode
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            t = int(temp)
            await self.coordinator.client.command(self.device_id, "main", "thermostatCoolingSetpoint", "setCoolingSetpoint", [t])
            self.coordinator.data["cool_sp"][self.device_id] = t
            self.coordinator.async_set_updated_data(self.coordinator.data)
            #await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str):
        api_val = HA_TO_API_FAN_MODES.get(fan_mode, "auto")
        await self.coordinator.client.command(self.device_id, "main", "airConditionerFanMode", "setFanMode", [api_val])
        self.coordinator.data["fan"][self.device_id] = api_val
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_set_swing_mode(self, swing_mode: str):
        api_val = HA_TO_API_SWING_MODES.get(swing_mode, "fixed")
        await self.coordinator.client.command(self.device_id, "main", "fanOscillationMode", "setFanOscillationMode", [api_val])
        self.coordinator.data["swing"][self.device_id] = api_val
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str):
        api_val = HA_TO_API_PRESET.get(preset_mode, "off")
        await self.coordinator.client.command(self.device_id, "main", "custom.airConditionerOptionalMode", "setAcOptionalMode", [api_val])
        self.coordinator.data["opt_mode"][self.device_id] = api_val
        self.coordinator.async_set_updated_data(self.coordinator.data)
        #await self.coordinator.async_request_refresh()
