"""Rates come from two snapshots. A counter that went backwards gives no rate."""

from custom_components.rtlplayground.parsers import PortCounters
from custom_components.rtlplayground.rates import compute_rates


def _c(port, tx, rx):
    return PortCounters(
        port=port, link_up=True, speed="1000M", tx_good=tx, tx_bad=0,
        rx_good=rx, rx_bad=0, macs_learned=1,
    )


def test_first_poll_has_no_rate():
    rates = compute_rates({}, 100.0, {1: _c(1, 10, 20)})
    assert rates[1].tx_pps is None
    assert rates[1].rx_pps is None


def test_rate_from_delta_over_elapsed_time():
    before = {1: (100.0, _c(1, 10, 20))}
    rates = compute_rates(before, 130.0, {1: _c(1, 70, 50)})
    assert rates[1].tx_pps == 2.0
    assert rates[1].rx_pps == 1.0


def test_counter_reset_gives_no_rate():
    before = {1: (100.0, _c(1, 500, 500))}
    rates = compute_rates(before, 130.0, {1: _c(1, 3, 4)})
    assert rates[1].tx_pps is None
    assert rates[1].rx_pps is None


def test_zero_elapsed_gives_no_rate():
    before = {1: (100.0, _c(1, 10, 10))}
    rates = compute_rates(before, 100.0, {1: _c(1, 20, 20)})
    assert rates[1].tx_pps is None
