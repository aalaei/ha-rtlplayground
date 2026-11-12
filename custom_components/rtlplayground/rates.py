"""Packet rates from two counter snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from .parsers import PortCounters


@dataclass(frozen=True)
class PortRates:
    """Packets per second. None means there is no usable previous sample."""

    tx_pps: float | None = None
    rx_pps: float | None = None


def compute_rates(
    previous: dict[int, tuple[float, PortCounters]],
    now: float,
    counters: dict[int, PortCounters],
) -> dict[int, PortRates]:
    """Rate per port from the last poll.

    A counter that went backwards (switch reboot, counter cleared) gives None
    for that poll instead of a negative or huge rate.
    """
    rates: dict[int, PortRates] = {}
    for port, current in counters.items():
        tx_pps: float | None = None
        rx_pps: float | None = None
        prev = previous.get(port)
        if prev is not None:
            prev_time, before = prev
            elapsed = now - prev_time
            d_tx = current.tx_good - before.tx_good
            d_rx = current.rx_good - before.rx_good
            if elapsed > 0 and d_tx >= 0 and d_rx >= 0:
                tx_pps = d_tx / elapsed
                rx_pps = d_rx / elapsed
        rates[port] = PortRates(tx_pps=tx_pps, rx_pps=rx_pps)
    return rates
