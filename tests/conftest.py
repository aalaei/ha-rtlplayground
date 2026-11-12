"""Shared fixtures. Tests run offline against the fake switch on 127.0.0.1."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.fake_switch import FakeSwitch  # noqa: E402


@pytest.fixture
async def fake_switch_server():
    """Serve a FakeSwitch on a free localhost port. Yields (switch, host:port)."""
    from aiohttp.test_utils import TestServer

    switch = FakeSwitch()
    server = TestServer(switch.app, host="127.0.0.1")
    await server.start_server()
    try:
        yield switch, f"127.0.0.1:{server.port}"
    finally:
        await server.close()
