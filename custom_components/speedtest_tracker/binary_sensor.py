from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpeedtestTrackerDataUpdateCoordinator
from .api import SpeedtestTrackerApiClient


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([SpeedtestTrackerAliveBinarySensor(coordinator, api, entry)])


class SpeedtestTrackerAliveBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: SpeedtestTrackerDataUpdateCoordinator, api: SpeedtestTrackerApiClient, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_has_entity_name = True
        self._attr_name = "Alive"
        self._attr_unique_id = f"{entry.entry_id}_alive"
        self._attr_icon = "mdi:lan-connect"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "alexjustesen",
            "model": "Speedtest Tracker",
            "configuration_url": entry.data.get("base_url"),
        }

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("alive")

    @property
    def extra_state_attributes(self):
        latest = (self.coordinator.data or {}).get("latest", {})
        return {
            "base_url": self._api.base_url,
            "status": latest.get("status"),
        }