"""Polling coordinator. Every poll is read-only."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RtlPlaygroundClient
from .const import DOMAIN, SCAN_INTERVAL_SECONDS
from .errors import ApiError, CannotConnect, InvalidAuth
from .parsers import (
    PortCounters,
    PortInfo,
    SwitchInfo,
    parse_information,
    parse_night,
    parse_ports,
    parse_traffic,
)
from .rates import PortRates, compute_rates

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RtlPlaygroundData:
    """One complete snapshot. Built only when every read succeeded."""

    info: SwitchInfo
    ports: dict[int, PortInfo]
    counters: dict[int, PortCounters]
    rates: dict[int, PortRates]
    night: bool


class RtlPlaygroundCoordinator(DataUpdateCoordinator[RtlPlaygroundData]):
    """Reads the switch every SCAN_INTERVAL_SECONDS."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: RtlPlaygroundClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self._previous: dict[int, tuple[float, PortCounters]] = {}

    async def _async_update_data(self) -> RtlPlaygroundData:
        try:
            info = parse_information(await self.client.async_get_json("/information.json"))
            ports = parse_ports(await self.client.async_get_json("/ports.json"))
            counters = parse_traffic(await self.client.async_get_json("/traffic.json"))
            night = parse_night(await self.client.async_get_json("/night.json"))
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (CannotConnect, ApiError) as err:
            # Raising UpdateFailed makes every entity unavailable. No stale values.
            raise UpdateFailed(str(err)) from err

        now = time.monotonic()
        rates = compute_rates(self._previous, now, counters)
        self._previous = {port: (now, c) for port, c in counters.items()}
        return RtlPlaygroundData(
            info=info,
            ports=ports,
            counters=counters,
            rates=rates,
            night=night,
        )
