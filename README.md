# RTLPlayground for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aalaei&repository=ha-rtlplayground)

A custom integration for switches running the RTLPlayground firmware
(ZoeRax HG0402XG V1.1 and other devices with the same JSON API).

The dashboard card is a separate component: [ha-rtlplayground-dashboard](https://github.com/aalaei/ha-rtlplayground-dashboard).
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

## Install

**Home Assistant 2026.11 and later:** HACS is built into Home Assistant as **Marketplace**
(Settings → Marketplace). Use the blue button above, or:

1. Settings → Marketplace → ⋮ → Custom repositories, and add `https://github.com/aalaei/ha-rtlplayground` as an **Integration**.
2. Install "RTLPlayground" and restart Home Assistant.
3. Settings → Devices & services → Add integration → RTLPlayground. Enter the switch address and password.

**Older versions:** use HACS (HACS → Integrations → ⋮ → Custom repositories) with the same repository.

## Develop

```
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install homeassistant pytest pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```

Tests run offline against `tests/fake_switch.py`, which serves scrubbed captures from a real
switch in `tests/fixtures/`. `scripts/live_check.py` runs a read-only check against a real switch
using `local-information/config.json` (git-ignored).
