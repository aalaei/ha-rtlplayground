"""RTLPlayground switch integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RtlPlaygroundClient
from .const import CONF_HOST, CONF_PASSWORD
from .coordinator import RtlPlaygroundCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

type RtlPlaygroundConfigEntry = ConfigEntry[RtlPlaygroundCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RtlPlaygroundConfigEntry) -> bool:
    client = RtlPlaygroundClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PASSWORD],
    )
    coordinator = RtlPlaygroundCoordinator(hass, entry, client)
    # Raises ConfigEntryNotReady or ConfigEntryAuthFailed. The first read is
    # the only read before entities exist. Nothing is written here.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RtlPlaygroundConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
