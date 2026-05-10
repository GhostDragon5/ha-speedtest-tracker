from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpeedtestTrackerDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SpeedtestTrackerSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


SENSORS: tuple[SpeedtestTrackerSensorEntityDescription, ...] = (
    SpeedtestTrackerSensorEntityDescription(
        key="download",
        name="Download",
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: round(data["latest"]["download_bits"] / 1_000_000, 2)
        if data.get("latest", {}).get("download_bits") is not None else None,
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="upload",
        name="Upload",
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: round(data["latest"]["upload_bits"] / 1_000_000, 2)
        if data.get("latest", {}).get("upload_bits") is not None else None,
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="ping",
        name="Ping",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        suggested_display_precision=3,
        state_class="measurement",
        value_fn=lambda data: data.get("latest", {}).get("ping"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="packet_loss",
        name="Packet Loss",
        icon="mdi:packet",
        native_unit_of_measurement="%",
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: _nested(data.get("latest", {}), "data", "packetLoss"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="jitter",
        name="Jitter",
        icon="mdi:wifi-marker",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        suggested_display_precision=3,
        state_class="measurement",
        value_fn=lambda data: _nested(data.get("latest", {}), "data", "ping", "jitter"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="server_name",
        name="Server Name",
        icon="mdi:server-network",
        value_fn=lambda data: _nested(data.get("latest", {}), "data", "server", "name"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="isp",
        name="ISP",
        icon="mdi:domain",
        value_fn=lambda data: _nested(data.get("latest", {}), "data", "isp"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:list-status",
        value_fn=lambda data: data.get("latest", {}).get("status"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="avg_download",
        name="Avg Download",
        icon="mdi:download-multiple",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: round(_nested(data.get("stats", {}), "download", "avg_bits") / 1_000_000, 2)
        if _nested(data.get("stats", {}), "download", "avg_bits") is not None else None,
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="avg_upload",
        name="Avg Upload",
        icon="mdi:upload-multiple",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: round(_nested(data.get("stats", {}), "upload", "avg_bits") / 1_000_000, 2)
        if _nested(data.get("stats", {}), "upload", "avg_bits") is not None else None,
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="avg_ping",
        name="Avg Ping",
        icon="mdi:chart-timeline-variant",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        suggested_display_precision=2,
        state_class="measurement",
        value_fn=lambda data: _nested(data.get("stats", {}), "ping", "avg"),
    ),
    SpeedtestTrackerSensorEntityDescription(
        key="total_results",
        name="Total Results",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("stats", {}).get("total_results"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(SpeedtestTrackerSensor(coordinator, entry, description) for description in SENSORS)


class SpeedtestTrackerSensor(CoordinatorEntity, SensorEntity):
    entity_description: SpeedtestTrackerSensorEntityDescription

    def __init__(self, coordinator: SpeedtestTrackerDataUpdateCoordinator, entry: ConfigEntry, description: SpeedtestTrackerSensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "alexjustesen",
            "model": "Speedtest Tracker",
            "configuration_url": entry.data.get("base_url"),
        }

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = (self.coordinator.data or {}).get("latest", {})
        stats = (self.coordinator.data or {}).get("stats", {})
        nested = latest.get("data") or {}
        result = nested.get("result") or {}
        server = nested.get("server") or {}
        interface = nested.get("interface") or {}

        return {
            "result_id": latest.get("id"),
            "result_url": result.get("url"),
            "service": latest.get("service"),
            "healthy": latest.get("healthy"),
            "status": latest.get("status"),
            "scheduled": latest.get("scheduled"),
            "created_at": latest.get("created_at"),
            "updated_at": latest.get("updated_at"),
            "packet_loss": nested.get("packetLoss"),
            "isp": nested.get("isp"),
            "server_name": server.get("name"),
            "server_location": server.get("location"),
            "server_country": server.get("country"),
            "external_ip": interface.get("externalIp"),
            "internal_ip": interface.get("internalIp"),
            "interface_name": interface.get("name"),
            "timestamp": nested.get("timestamp"),
            "total_results": stats.get("total_results"),
        }