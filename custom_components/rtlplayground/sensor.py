"""Sensors: switch-level values and per-port counters and rates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RtlPlaygroundConfigEntry
from .coordinator import RtlPlaygroundCoordinator, RtlPlaygroundData
from .entity import RtlPlaygroundEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RtlSwitchSensorDescription(SensorEntityDescription):
    value_fn: Callable[[RtlPlaygroundData], Any]


@dataclass(frozen=True, kw_only=True)
class RtlPortSensorDescription(SensorEntityDescription):
    value_fn: Callable[[RtlPlaygroundData, int], Any]


SWITCH_SENSORS: tuple[RtlSwitchSensorDescription, ...] = (
    RtlSwitchSensorDescription(
        key="firmware_version",
        name="Firmware version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.firmware_version,
    ),
    RtlSwitchSensorDescription(
        key="uptime",
        name="Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.uptime_seconds,
    ),
    RtlSwitchSensorDescription(
        key="chip_temperature",
        name="Chip temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.info.chip_temperature,
    ),
    RtlSwitchSensorDescription(
        key="ports_up",
        name="Ports up",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(1 for c in d.counters.values() if c.link_up),
    ),
    RtlSwitchSensorDescription(
        key="ip_address",
        name="IP address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.ip_address,
    ),
    RtlSwitchSensorDescription(
        key="hostname",
        name="Hostname",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.hostname or None,
    ),
    RtlSwitchSensorDescription(
        key="mac_address",
        name="MAC address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.mac_address,
    ),
)

PORT_SENSORS: tuple[RtlPortSensorDescription, ...] = (
    RtlPortSensorDescription(
        key="link_speed",
        name="Link speed",
        value_fn=lambda d, p: d.counters[p].speed,
    ),
    RtlPortSensorDescription(
        key="tx_packets",
        name="TX packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="packets",
        value_fn=lambda d, p: d.counters[p].tx_good,
    ),
    RtlPortSensorDescription(
        key="rx_packets",
        name="RX packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="packets",
        value_fn=lambda d, p: d.counters[p].rx_good,
    ),
    RtlPortSensorDescription(
        key="tx_bad_packets",
        name="TX bad packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="packets",
        value_fn=lambda d, p: d.counters[p].tx_bad,
    ),
    RtlPortSensorDescription(
        key="rx_bad_packets",
        name="RX bad packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="packets",
        value_fn=lambda d, p: d.counters[p].rx_bad,
    ),
    RtlPortSensorDescription(
        key="tx_rate",
        name="TX rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="packets/s",
        value_fn=lambda d, p: _round(d.rates[p].tx_pps) if p in d.rates else None,
    ),
    RtlPortSensorDescription(
        key="rx_rate",
        name="RX rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="packets/s",
        value_fn=lambda d, p: _round(d.rates[p].rx_pps) if p in d.rates else None,
    ),
    RtlPortSensorDescription(
        key="macs_learned",
        name="MAC addresses learned",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d, p: d.counters[p].macs_learned,
    ),
)


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RtlPlaygroundConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        RtlSwitchSensor(coordinator, description) for description in SWITCH_SENSORS
    ]
    for port in sorted(coordinator.data.counters):
        entities.extend(
            RtlPortSensor(coordinator, description, port) for description in PORT_SENSORS
        )
    async_add_entities(entities)


class RtlSwitchSensor(RtlPlaygroundEntity, SensorEntity):
    entity_description: RtlSwitchSensorDescription

    def __init__(
        self,
        coordinator: RtlPlaygroundCoordinator,
        description: RtlSwitchSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = self._unique(description.key)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)


class RtlPortSensor(RtlPlaygroundEntity, SensorEntity):
    entity_description: RtlPortSensorDescription

    def __init__(
        self,
        coordinator: RtlPlaygroundCoordinator,
        description: RtlPortSensorDescription,
        port: int,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._port = port
        self._attr_unique_id = self._unique(f"port{port}_{description.key}")
        self._attr_name = f"Port {port} {description.name.lower()}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if self._port not in data.counters:
            return None
        return self.entity_description.value_fn(data, self._port)
