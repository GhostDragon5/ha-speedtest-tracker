from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SpeedtestTrackerApiClient
from .const import CONF_API_TOKEN, CONF_BASE_URL, CONF_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import SpeedtestTrackerDataUpdateCoordinator

SERVICE_RUN_SPEEDTEST = "run_speedtest"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = SpeedtestTrackerApiClient(
        session=session,
        base_url=entry.data[CONF_BASE_URL],
        api_token=entry.data[CONF_API_TOKEN],
    )

    coordinator = SpeedtestTrackerDataUpdateCoordinator(
        hass,
        api,
        update_interval_seconds=entry.data.get(CONF_SCAN_INTERVAL, 3600),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    if not hass.services.has_service(DOMAIN, SERVICE_RUN_SPEEDTEST):
        async def handle_run_speedtest(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            server_id = call.data.get("server_id")

            target_entry = None
            if entry_id:
                target_entry = hass.data[DOMAIN].get(entry_id)
            elif hass.data[DOMAIN]:
                target_entry = next(iter(hass.data[DOMAIN].values()))

            if target_entry is None:
                return

            await target_entry["api"].async_run_speedtest(server_id=server_id)
            await target_entry["coordinator"].async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_RUN_SPEEDTEST,
            handle_run_speedtest,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): str,
                    vol.Optional("server_id"): int,
                }
            ),
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_RUN_SPEEDTEST):
            hass.services.async_remove(DOMAIN, SERVICE_RUN_SPEEDTEST)
    return unload_ok