from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([SpeedtestTrackerRunButton(coordinator, api, entry)])


class SpeedtestTrackerRunButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_has_entity_name = True
        self._attr_name = "Run Speedtest"
        self._attr_unique_id = f"{entry.entry_id}_run_speedtest"
        self._attr_icon = "mdi:speedometer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "alexjustesen",
            "model": "Speedtest Tracker",
            "configuration_url": entry.data.get("base_url"),
        }

    async def async_press(self) -> None:
        await self._api.async_run_speedtest()
        await self.coordinator.async_request_refresh()