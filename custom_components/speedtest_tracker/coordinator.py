from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SpeedtestTrackerApiAuthError,
    SpeedtestTrackerApiClient,
    SpeedtestTrackerApiConnectionError,
    SpeedtestTrackerApiError,
)
from .const import COORDINATOR_NAME

_LOGGER = logging.getLogger(__name__)


class SpeedtestTrackerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: SpeedtestTrackerApiClient, update_interval_seconds: int) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=COORDINATOR_NAME,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            latest = await self.api.async_get_latest_result()
            stats = await self.api.async_get_stats()
            alive = await self.api.async_is_alive()

            return {
                "latest": latest,
                "stats": stats,
                "alive": alive,
            }

        except SpeedtestTrackerApiAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except SpeedtestTrackerApiConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except SpeedtestTrackerApiError as err:
            raise UpdateFailed(f"API error: {err}") from err