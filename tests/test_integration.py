"""Config flow, entities and night mode, run through Home Assistant against the fake switch."""

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rtlplayground.const import CONF_HOST, CONF_PASSWORD, DOMAIN

pytestmark = [pytest.mark.enable_socket, pytest.mark.usefixtures("enable_custom_integrations")]

MAC = "02:00:00:00:00:01"


def _entity_id(hass, platform: str, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{MAC}_{key}")
    assert entity_id is not None, f"no {platform} entity for {key}"
    return entity_id


async def _setup(hass, host: str, password: str) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        data={CONF_HOST: host, CONF_PASSWORD: password},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_rejects_wrong_password_then_accepts(hass, fake_switch_server):
    switch, host = fake_switch_server
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    bad = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {CONF_HOST: host, CONF_PASSWORD: "wrong"}
    )
    assert bad["type"] == "form"
    assert bad["errors"] == {"base": "invalid_auth"}

    good = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {CONF_HOST: host, CONF_PASSWORD: switch.password}
    )
    assert good["type"] == "create_entry"
    assert good["data"][CONF_HOST] == host


async def test_setup_creates_read_only_entities_and_writes_nothing(hass, fake_switch_server):
    switch, host = fake_switch_server
    await _setup(hass, host, switch.password)

    assert hass.states.get(_entity_id(hass, "sensor", "ports_up")).state == "3"
    assert hass.states.get(_entity_id(hass, "sensor", "chip_temperature")).state == "75.0"
    assert hass.states.get(_entity_id(hass, "binary_sensor", "port1_link")).state == STATE_ON
    assert hass.states.get(_entity_id(hass, "binary_sensor", "port3_link")).state == STATE_OFF
    assert hass.states.get(_entity_id(hass, "sensor", "port1_tx_packets")).state == str(0x83F9)
    assert hass.states.get(_entity_id(hass, "sensor", "port1_link_speed")).state == "1000M"
    assert switch.night_writes == 0


async def test_night_mode_switch_writes_only_a_difference(hass, fake_switch_server):
    switch, host = fake_switch_server
    await _setup(hass, host, switch.password)
    night = _entity_id(hass, "switch", "night_mode")
    assert hass.states.get(night).state == STATE_OFF

    await hass.services.async_call(SWITCH_DOMAIN, "turn_on", {"entity_id": night}, blocking=True)
    assert switch.night is True
    assert switch.night_writes == 1
    assert hass.states.get(night).state == STATE_ON

    # Already on: no further write.
    await hass.services.async_call(SWITCH_DOMAIN, "turn_on", {"entity_id": night}, blocking=True)
    assert switch.night_writes == 1


async def test_switch_going_unreachable_marks_entities_unavailable(hass, fake_switch_server):
    switch, host = fake_switch_server
    entry = await _setup(hass, host, switch.password)
    coordinator = entry.runtime_data
    assert hass.states.get(_entity_id(hass, "sensor", "ports_up")).state == "3"

    # Point the client at a closed port to simulate the switch going away.
    coordinator.client._base = "http://127.0.0.1:9"
    coordinator.client._token = None
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(_entity_id(hass, "sensor", "ports_up")).state == STATE_UNAVAILABLE
    assert hass.states.get(_entity_id(hass, "switch", "night_mode")).state == STATE_UNAVAILABLE


async def test_changed_password_starts_reauth(hass, fake_switch_server):
    switch, host = fake_switch_server
    entry = await _setup(hass, host, switch.password)

    switch.password = "changed-on-switch"
    switch.expire_sessions()
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(f["context"]["source"] == "reauth" for f in flows)
    assert hass.states.get(_entity_id(hass, "sensor", "ports_up")).state == STATE_UNAVAILABLE
