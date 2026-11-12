"""Turn the firmware's JSON pages into typed values.

The firmware writes counters and most numbers as hex strings with a `0x`
prefix. Every parser raises ApiError when a field is missing or has the wrong
shape, so the coordinator can mark entities unavailable instead of guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .errors import ApiError

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def parse_hex(value: Any) -> int:
    """Parse a firmware hex string such as "0x6ce" into an int."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ApiError(f"expected hex string, got {value!r}")
    if isinstance(value, int):
        return value
    if not value.lower().startswith("0x"):
        raise ApiError(f"hex value without 0x prefix: {value!r}")
    try:
        return int(value, 16)
    except ValueError as err:
        raise ApiError(f"bad hex value {value!r}") from err


def _require_list(data: Any, what: str) -> list[Any]:
    if not isinstance(data, list):
        raise ApiError(f"{what}: expected a list")
    return data


def _require_dict(data: Any, what: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ApiError(f"{what}: expected an object")
    return data


@dataclass(frozen=True)
class SwitchInfo:
    """Values from information.json."""

    mac_address: str
    hostname: str
    ip_address: str
    firmware_version: str
    hardware_version: str
    uptime_seconds: int
    chip_temperature: float | None


def parse_information(data: Any) -> SwitchInfo:
    obj = _require_dict(data, "information.json")
    try:
        temp_text = obj.get("chip_temp")
        temp: float | None = None
        if isinstance(temp_text, str):
            match = _NUMBER.search(temp_text)
            if match:
                temp = float(match.group(0))
        return SwitchInfo(
            mac_address=str(obj["mac_address"]).lower(),
            hostname=str(obj.get("hostname", "")),
            ip_address=str(obj["ip_address"]),
            firmware_version=str(obj["sw_ver"]),
            hardware_version=str(obj.get("hw_ver", "")),
            uptime_seconds=parse_hex(obj["uptime"]),
            chip_temperature=temp,
        )
    except KeyError as err:
        raise ApiError(f"information.json: missing {err}") from err


@dataclass(frozen=True)
class PortInfo:
    """One entry of ports.json. Port numbers are physical."""

    port: int
    is_sfp: bool
    enabled: bool


def parse_ports(data: Any) -> dict[int, PortInfo]:
    result: dict[int, PortInfo] = {}
    for item in _require_list(data, "ports.json"):
        obj = _require_dict(item, "ports.json entry")
        try:
            port = int(obj["port"])
            result[port] = PortInfo(
                port=port,
                is_sfp=bool(obj["isSFP"]),
                enabled=bool(obj["enabled"]),
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ApiError(f"ports.json: bad entry {obj!r}") from err
    return result


@dataclass(frozen=True)
class PortCounters:
    """One entry of traffic.json. Counters are cumulative since boot."""

    port: int
    link_up: bool
    speed: str | None
    tx_good: int
    tx_bad: int
    rx_good: int
    rx_bad: int
    macs_learned: int


def parse_traffic(data: Any) -> dict[int, PortCounters]:
    result: dict[int, PortCounters] = {}
    for item in _require_list(data, "traffic.json"):
        obj = _require_dict(item, "traffic.json entry")
        try:
            port = int(obj["port"])
            link = str(obj["link"])
            link_up = link.upper() != "DOWN"
            result[port] = PortCounters(
                port=port,
                link_up=link_up,
                speed=link if link_up else None,
                tx_good=parse_hex(obj["txG"]),
                tx_bad=parse_hex(obj["txB"]),
                rx_good=parse_hex(obj["rxG"]),
                rx_bad=parse_hex(obj["rxB"]),
                macs_learned=parse_hex(obj["macs"]),
            )
        except KeyError as err:
            raise ApiError(f"traffic.json: missing {err}") from err
        except (TypeError, ValueError) as err:
            raise ApiError(f"traffic.json: bad entry {obj!r}") from err
    return result


def parse_night(data: Any) -> bool:
    obj = _require_dict(data, "night.json")
    if not isinstance(obj.get("night"), bool):
        raise ApiError("night.json: 'night' is not a boolean")
    return obj["night"]
