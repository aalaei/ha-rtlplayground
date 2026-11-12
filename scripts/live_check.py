"""Read-only check of the integration's client and parsers against a real switch.

Reads local-information/config.json (host, password). Sends only GET requests
and the login POST. It never calls night.json?set=... or any /cmd.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from custom_components.rtlplayground.api import RtlPlaygroundClient  # noqa: E402
from custom_components.rtlplayground.parsers import (  # noqa: E402
    parse_information,
    parse_night,
    parse_ports,
    parse_traffic,
)
from custom_components.rtlplayground.rates import compute_rates  # noqa: E402

CONFIG = Path(__file__).resolve().parent.parent / "local-information" / "config.json"


async def main() -> None:
    cfg = json.loads(CONFIG.read_text())
    async with aiohttp.ClientSession() as session:
        client = RtlPlaygroundClient(session, cfg["host"], cfg["password"])
        await client.async_login()
        print("login: ok")
        info = parse_information(await client.async_get_json("/information.json"))
        ports = parse_ports(await client.async_get_json("/ports.json"))
        t1 = time.monotonic()
        c1 = parse_traffic(await client.async_get_json("/traffic.json"))
        night = parse_night(await client.async_get_json("/night.json"))
        print(f"info: {info.hostname} fw={info.firmware_version} uptime={info.uptime_seconds}s "
              f"temp={info.chip_temperature}C")
        print(f"night: {night}")
        print(f"ports: {sorted(ports)} sfp={[p for p, v in ports.items() if v.is_sfp]}")
        for port, c in sorted(c1.items()):
            print(f"  port {port}: link={'up' if c.link_up else 'down'} speed={c.speed} "
                  f"tx={c.tx_good} rx={c.rx_good} macs={c.macs_learned}")
        await asyncio.sleep(5)
        c2 = parse_traffic(await client.async_get_json("/traffic.json"))
        rates = compute_rates({p: (t1, v) for p, v in c1.items()}, time.monotonic(), c2)
        for port, r in sorted(rates.items()):
            print(f"  port {port} rate: tx={r.tx_pps} rx={r.rx_pps} pkt/s")


asyncio.run(main())
