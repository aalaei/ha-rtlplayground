"""Binary sensors: link up or down per physical port."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RtlPlaygroundConfigEntry
from .coordinator import RtlPlaygroundCoordinator
from .entity import RtlPlaygroundEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RtlPlaygroundConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        RtlPortLinkSensor(coordinator, port) for port in sorted(coordinator.data.counters)
    )


class RtlPortLinkSensor(RtlPlaygroundEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: RtlPlaygroundCoordinator, port: int) -> None:
        super().__init__(coordinator)
        self._port = port
        self._attr_unique_id = self._unique(f"port{port}_link")
        self._attr_name = f"Port {port} link"

    @property
    def is_on(self) -> bool | None:
        counters = self.coordinator.data.counters.get(self._port)
        return None if counters is None else counters.link_up
