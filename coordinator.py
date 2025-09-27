
from __future__ import annotations
import logging, re, random
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import UPDATE_INTERVAL
from .vendor.smartthings_pat import SmartThingsClient, SmartThingsError

_LOGGER = logging.getLogger(__name__)

class SmartThingsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: SmartThingsClient):
        jitter = random.randint(0, 5)
        super().__init__(
            hass,
            logger=_LOGGER,
            name="SmartThings PAT",
            update_interval=timedelta(seconds=UPDATE_INTERVAL + jitter),
        )
        self.client = client
        self.device_ids = []
        self.device_labels = {}

    async def _async_update_data(self):
        try:
            if not self.device_ids:
                devs = await self.client.list_devices()
                self.device_ids = [d["deviceId"] for d in devs if "deviceId" in d]
                self.device_labels = {
                    d["deviceId"]: (d.get("label") or d.get("name") or d["deviceId"])
                    for d in devs if "deviceId" in d
                }

            data = {
                "switch": {},
                "mode": {},
                "cool_sp": {},
                "fan": {},
                "swing": {},
                "opt_mode": {},
                "temps": {},
                "humidity": {},
                "lighting": {},
                "beep": {},
                "autoclean": {},
            }
            for did in self.device_ids:
                try:
                    full = await self.client.get_device_status(did)
                except SmartThingsError as e:
                    if "-> 429" in str(e):
                        m = re.search(r"retry in (\d+) millis", str(e))
                        wait_s = int(int(m.group(1))/1000) if m else 60
                        new_iv = max(wait_s, 60)
                        self.update_interval = timedelta(seconds=new_iv)
                        raise UpdateFailed(f"Rate limited by SmartThings; backing off {new_iv}s") from e
                    raise UpdateFailed(str(e)) from e

                comp = full.get("components", {}).get("main", {})
                def g(cap, prop):
                    return comp.get(cap, {}).get(prop, {}).get("value")

                data["switch"][did] = g("switch", "switch")
                data["mode"][did] = g("airConditionerMode", "airConditionerMode")
                data["cool_sp"][did] = g("thermostatCoolingSetpoint", "coolingSetpoint")
                data["fan"][did] = g("airConditionerFanMode", "fanMode")
                data["swing"][did] = g("fanOscillationMode", "fanOscillationMode")
                data["opt_mode"][did] = g("custom.airConditionerOptionalMode", "acOptionalMode") or "none"
                data["temps"][did] = g("temperatureMeasurement", "temperature")
                data["humidity"][did] = g("relativeHumidityMeasurement", "humidity")
                data["lighting"][did] = g("samsungce.airConditionerLighting", "lighting")
                data["beep"][did] = g("samsungce.airConditionerBeep", "beep")
                data["autoclean"][did] = g("custom.autoCleaningMode", "autoCleaningMode")

            return data
        except Exception as err:
            raise UpdateFailed(str(err)) from err
