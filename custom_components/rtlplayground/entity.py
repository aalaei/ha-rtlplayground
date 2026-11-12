"""Shared base for RTLPlayground entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import RtlPlaygroundCoordinator


class RtlPlaygroundEntity(CoordinatorEntity[RtlPlaygroundCoordinator]):
    """All entities hang off one device.

    Identified by (DOMAIN, MAC) only. A network-MAC connection would merge this
    device with any other integration that already reports the same MAC.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: RtlPlaygroundCoordinator) -> None:
        super().__init__(coordinator)
        info = coordinator.data.info
        self._mac = info.mac_address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._mac)},
            manufacturer=MANUFACTURER,
            model=info.hardware_version or None,
            name=info.hostname or "RTLPlayground switch",
            sw_version=info.firmware_version,
        )

    def _unique(self, key: str) -> str:
        return f"{self._mac}_{key}"
