from __future__ import annotations

from dataclasses import dataclass
import asyncio
import aiohttp


class SpeedtestTrackerApiError(Exception):
    pass


class SpeedtestTrackerApiAuthError(SpeedtestTrackerApiError):
    pass


class SpeedtestTrackerApiConnectionError(SpeedtestTrackerApiError):
    pass


@dataclass(slots=True)
class SpeedtestTrackerApiClient:
    session: aiohttp.ClientSession
    base_url: str
    api_token: str

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

    async def async_get_latest_result(self) -> dict:
        try:
            async with self.session.get(
                self._url("/api/v1/results/latest"),
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise SpeedtestTrackerApiAuthError("Invalid API token or missing permissions")
                if response.status == 404:
                    return {}
                if response.status >= 400:
                    raise SpeedtestTrackerApiError(await response.text())

                payload = await response.json()
                if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                    return payload["data"]
                return payload if isinstance(payload, dict) else {}
        except SpeedtestTrackerApiAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SpeedtestTrackerApiConnectionError(str(err)) from err

    async def async_get_stats(self) -> dict:
        try:
            async with self.session.get(
                self._url("/api/v1/stats"),
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise SpeedtestTrackerApiAuthError("Invalid API token or missing permissions")
                if response.status >= 400:
                    raise SpeedtestTrackerApiError(await response.text())

                payload = await response.json()
                if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                    return payload["data"]
                return payload if isinstance(payload, dict) else {}
        except SpeedtestTrackerApiAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SpeedtestTrackerApiConnectionError(str(err)) from err

    async def async_run_speedtest(self, server_id: int | None = None) -> dict:
        params = {}
        if server_id is not None:
            params["server_id"] = server_id

        try:
            async with self.session.post(
                self._url("/api/v1/speedtests/run"),
                headers=self._headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status in (401, 403):
                    raise SpeedtestTrackerApiAuthError("Invalid API token or missing permissions")
                if response.status >= 400:
                    raise SpeedtestTrackerApiError(await response.text())

                payload = await response.json()
                if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                    return payload["data"]
                return payload if isinstance(payload, dict) else {}
        except SpeedtestTrackerApiAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SpeedtestTrackerApiConnectionError(str(err)) from err

    async def async_validate(self) -> dict:
        return await self.async_get_latest_result()

    async def async_is_alive(self) -> bool:
        try:
            async with self.session.get(
                self._url("/api/v1/results/latest"),
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                return response.status not in (500, 502, 503, 504)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False