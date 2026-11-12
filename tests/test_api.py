"""The client against the fake switch over real HTTP."""

import aiohttp
import pytest

# Talks to the fake switch on 127.0.0.1. The HA test plugin blocks sockets by default.
pytestmark = pytest.mark.enable_socket

from custom_components.rtlplayground.api import RtlPlaygroundClient
from custom_components.rtlplayground.errors import CannotConnect, InvalidAuth


async def test_login_and_read(fake_switch_server):
    switch, host = fake_switch_server
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, host, switch.password)
        data = await client.async_get_json("/information.json")
    assert data["hostname"] == "rtlplayground-test"


async def test_wrong_password_is_invalid_auth(fake_switch_server):
    switch, host = fake_switch_server
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, host, "not-the-password")
        with pytest.raises(InvalidAuth):
            await client.async_login()


async def test_expired_session_relogs_in_once(fake_switch_server):
    switch, host = fake_switch_server
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, host, switch.password)
        await client.async_get_json("/ports.json")
        switch.expire_sessions()
        data = await client.async_get_json("/ports.json")
    assert isinstance(data, list)


async def test_password_changed_on_switch_is_invalid_auth(fake_switch_server):
    switch, host = fake_switch_server
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, host, switch.password)
        await client.async_get_json("/ports.json")
        switch.password = "changed"
        switch.expire_sessions()
        with pytest.raises(InvalidAuth):
            await client.async_get_json("/ports.json")


async def test_unreachable_switch_is_cannot_connect():
    # Port 9 on localhost is closed in test environments.
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, "127.0.0.1:9", "x", timeout=2)
        with pytest.raises(CannotConnect):
            await client.async_get_json("/information.json")


async def test_set_night_sends_only_when_asked(fake_switch_server):
    switch, host = fake_switch_server
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, host, switch.password)
        await client.async_set_night(True)
        assert switch.night is True
        assert switch.night_writes == 1
        await client.async_set_night(False)
        assert switch.night is False
