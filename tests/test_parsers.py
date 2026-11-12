"""Parsers against the documented firmware formats (see tests/fixtures/README.md)."""

import pytest

from custom_components.rtlplayground.errors import ApiError
from custom_components.rtlplayground.parsers import (
    parse_hex,
    parse_information,
    parse_night,
    parse_ports,
    parse_traffic,
)
from tests.fake_switch import load


def test_parse_hex_accepts_firmware_strings():
    assert parse_hex("0x6ce") == 0x6CE
    assert parse_hex("0x0") == 0
    assert parse_hex(7) == 7


@pytest.mark.parametrize("bad", ["6ce", "0xzz", None, True, 1.5])
def test_parse_hex_rejects_wrong_shape(bad):
    with pytest.raises(ApiError):
        parse_hex(bad)


def test_information_fields():
    info = parse_information(load("information.json"))
    assert info.mac_address == "02:00:00:00:00:01"
    assert info.hostname == "rtlplayground-test"
    assert info.firmware_version == "v0.1.0-eff1c55-dirty"
    assert info.uptime_seconds == 0x4D6
    assert info.chip_temperature == 75.0


def test_information_missing_field_is_api_error():
    data = load("information.json")
    del data["mac_address"]
    with pytest.raises(ApiError):
        parse_information(data)


def test_information_temperature_absent_is_none():
    data = load("information.json")
    del data["chip_temp"]
    assert parse_information(data).chip_temperature is None


def test_ports_mark_sfp_cages():
    ports = parse_ports(load("ports.json"))
    assert sorted(ports) == [1, 2, 3, 4, 5, 6]
    assert ports[1].is_sfp is False
    assert ports[5].is_sfp is True
    assert ports[5].enabled is False


def test_traffic_link_states_and_counters():
    counters = parse_traffic(load("traffic.json"))
    assert counters[1].link_up is True
    assert counters[1].speed == "1000M"
    assert counters[1].tx_good == 0x83F9
    assert counters[3].link_up is False
    assert counters[3].speed is None
    assert counters[4].speed == "2.5G"
    assert counters[4].macs_learned == 0x10
    assert counters[5].link_up is False


def test_traffic_non_list_is_api_error():
    with pytest.raises(ApiError):
        parse_traffic({"port": 1})


def test_night_requires_boolean():
    assert parse_night({"night": True}) is True
    with pytest.raises(ApiError):
        parse_night({"night": "on"})
