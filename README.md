# RTLPlayground for Home Assistant

A custom integration for switches running the [RTLPlayground](https://github.com/aalaei) firmware
(ZoeRax HG0402XG V1.1 and other devices with the same JSON API).

The dashboard card is a separate HACS component: [ha-rtlplayground-dashboard](https://github.com/aalaei/ha-rtlplayground-dashboard).

## What it does

- Config flow with host and password. Reauth when the password changes. A MAC check stops a
  different switch from being added to an existing entry.
- Polls every 30 s. Read-only, except when you change night mode. Nothing is written on startup.
- Switch sensors: firmware version, uptime, chip temperature, ports up, IP, hostname, MAC.
- Per port (physical 1–6): link (binary sensor), link speed, TX and RX packets, bad packets,
  TX and RX rate from counter deltas, MAC addresses learned.
- Night mode switch. It reads the state first and writes only a difference, then reads back to confirm.
  It is live but **not saved across reboots**. Saving needs `night on|off` through `/cmd`, which
  is not implemented yet.
- If the switch is unreachable, all its entities go unavailable. No stale value is reported.

Not built yet: per-port enable/disable of the switch.

PoE is not part of this integration. The PoE data comes from the ESPHome PoE device that is
already in Home Assistant, and the dashboard reads it.

## Install (HACS)

1. HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/aalaei/ha-rtlplayground`, category **Integration**.
2. Install "RTLPlayground" and restart Home Assistant.
3. Settings → Devices & services → Add integration → RTLPlayground. Enter the switch address and password.

## Develop

```
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install homeassistant pytest pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```

Tests run offline against `tests/fake_switch.py`, which serves scrubbed captures from a real
switch in `tests/fixtures/`. `scripts/live_check.py` runs a read-only check against a real switch
using `local-information/config.json` (git-ignored).
