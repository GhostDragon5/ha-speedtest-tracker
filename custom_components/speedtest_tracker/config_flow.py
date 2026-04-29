from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SpeedtestTrackerApiAuthError,
    SpeedtestTrackerApiClient,
    SpeedtestTrackerApiConnectionError,
    SpeedtestTrackerApiError,
)
from .const import CONF_API_TOKEN, CONF_BASE_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN


def _normalize_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError
    return value


class SpeedtestTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                base_url = _normalize_base_url(user_input[CONF_BASE_URL])
                api = SpeedtestTrackerApiClient(
                    session=async_get_clientsession(self.hass),
                    base_url=base_url,
                    api_token=user_input[CONF_API_TOKEN],
                )
                await api.async_validate()
            except ValueError:
                errors[CONF_BASE_URL] = "invalid_url"
            except SpeedtestTrackerApiAuthError:
                errors["base"] = "invalid_auth"
            except SpeedtestTrackerApiConnectionError:
                errors["base"] = "cannot_connect"
            except SpeedtestTrackerApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(base_url.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Speedtest Tracker ({urlparse(base_url).hostname})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_URL, default="http://speedtest-tracker.local"): str,
                    vol.Required(CONF_API_TOKEN): str,
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                }
            ),
            errors=errors,
        )
