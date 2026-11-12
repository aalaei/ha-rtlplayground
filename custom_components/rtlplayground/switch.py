"""Night mode switch.

Writes follow the brief's rules. Read the current state first and write only
a difference. After a write, read back and confirm it. If the switch does not
answer, the entity is unavailable, and no stale value is reported as current.

Night mode set through /night.json is live but NOT saved across reboots. Saving
it needs `night on|off` through /cmd, which is not implemented yet.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RtlPlaygroundConfigEntry
from .coordinator import RtlPlaygroundCoordinator
from .entity import RtlPlaygroundEntity
from .errors import ApiError, CannotConnect, InvalidAuth
from .parsers import parse_night

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RtlPlaygroundConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([RtlNightModeSwitch(entry.runtime_data)])


class RtlNightModeSwitch(RtlPlaygroundEntity, SwitchEntity):
    _attr_name = "Night mode"

    def __init__(self, coordinator: RtlPlaygroundCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = self._unique("night_mode")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.night

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, on: bool) -> None:
        client = self.coordinator.client
        try:
            # Read first. If the switch is already in the wanted state, do not write.
            current = parse_night(await client.async_get_json("/night.json"))
            if current != on:
                await client.async_set_night(on)
                confirmed = parse_night(await client.async_get_json("/night.json"))
                if confirmed != on:
                    raise HomeAssistantError("switch did not confirm the night mode change")
        except InvalidAuth as err:
            raise HomeAssistantError("login to the switch failed") from err
        except CannotConnect as err:
            raise HomeAssistantError(f"switch unreachable: {err}") from err
        except ApiError as err:
            raise HomeAssistantError(f"unexpected reply from switch: {err}") from err
        await self.coordinator.async_request_refresh()
