# Fixtures

These are scrubbed captures from the real switch (firmware `v0.1.0-eff1c55-dirty`).
They were made with `local-information/scrub.py`, which replaces the IP, MAC and
hostname with documentation values (`192.0.2.0/24`, `02:00:00:00:00:xx`,
`rtlplayground-test`). No other values were changed.

- `information.json`, `ports.json`, `traffic.json`, `night.json`: read endpoints.
  Night mode was ON when captured.
- The raw captures and the switch address stay in `local-information/`, which is git-ignored.
