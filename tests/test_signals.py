"""Unit tests for the building blocks of the strategy.  Run with:  python -m pytest -q"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import signals as SG  # noqa: E402
from src.backtest import Market, simulate  # noqa: E402


def test_ema_weights_and_half_life():
    x = pd.Series([0.0] * 50 + [1.0])
    e = SG.ema(x, 20)
    assert abs(e.iloc[-1] - 2 / 21) < 1e-12                     # today's weight is 2 / (N + 1)
    half_life = np.log(0.5) / np.log(1 - 2 / 21)
    assert 6.8 < half_life < 7.0                                   # "the weight halves every 6.9 days"


def test_band_edges():
    o = pd.DataFrame({"a": [10.0, 11, 12]})
    c = pd.DataFrame({"a": [11.0, 12, 11]})
    up, lo = SG.band(o, c, span=20)
    assert (up >= lo).all().all()


def test_zigzag_finds_peak_and_trough_with_confirmation():
    c = np.array([100, 104, 110, 108, 103, 101, 104, 107, 112.0])
    idx, kind, conf = SG.swing_points(c, 0.05)
    assert list(kind) == [-1, 1, -1]                               # the first leg up confirms the starting low
    assert idx[1] == 2 and conf[1] == 4                            # peak at 110, confirmed when 103 <= 110 * 0.95
    assert idx[2] == 5 and conf[2] == 7                            # trough at 101, confirmed when 107 >= 101 * 1.05


def test_run_start_ends_after_long_stretch_below():
    c = np.array([1.0] * 5 + [0.5] * 12 + [2.0] * 5)
    e = np.full_like(c, 0.9)
    rs = SG.run_start_series(c, e, max_below=10)
    assert rs[-1] == 17                                            # one past the last of the 12 closes below


def test_touch_signal():
    up = np.full((6, 1), 100.0)
    close = np.array([[105], [100.5], [99], [102], [103], [104.0]])
    sig = SG.touch_signal(close, up, win=5, tol=0.01)
    assert not sig[0, 0]                                           # 5% above the band: no touch yet
    assert sig[1, 0]                                               # within 1% above the band and above it: a touch
    assert not sig[2, 0]                                           # closes below the band: wait
    assert sig[3, 0]                                               # back above the band after the touch


def _toy_market(T=200, N=3, adv=1e9):
    d = pd.bdate_range("2020-01-01", periods=T)
    px = np.cumprod(1 + np.full((T, N), 0.001), axis=0) * 10
    one = np.ones((T, N), bool)
    return Market(dates=d, cols=pd.Index([f"S{j}" for j in range(N)]), close=px, open=px, vol=np.full((T, N), 1e6),
                  upper=px * 0.99, lower=px * 0.98, vol_med=np.full((T, N), 1e6), prev_close=np.roll(px, 1, 0),
                  score=np.ones((T, N)), signal=one, trend=one, eligible=one,
                  extra=dict(traded_value=np.full((T, N), adv)))


def test_simulator_holds_63_days_and_charges_costs():
    m = _toy_market()
    eq, tr, od = simulate(m, slots=3, cost=0.001, hold=63)
    assert (tr.bars == 63).all()
    assert np.allclose(tr.ret, tr.sell * 0.999 / (tr.buy * 1.001) - 1)
    assert od.weight.max() <= 1 / 3 + 1e-9                        # equity / slots per position
    assert eq.iloc[-1] > 1.0                                       # rising prices, small costs


def test_order_capped_at_5pct_of_adv_and_impact_cost():
    m = _toy_market(adv=1e6)                                       # $1M a day: a $1M book may buy $50k per name
    eq, tr, od = simulate(m, slots=3, hold=63, capital=1e6)
    assert od[od.weight > 0].weight.max() <= 0.05 / eq.min() + 1e-9          # $50k on a NAV just below $1M
    assert (tr.adv_share <= 0.05 + 1e-9).all()
    assert np.allclose(tr.cost_in.iloc[0], 0.0005 + max(0.0005, 0.01 * np.sqrt(tr.adv_share.iloc[0])))


def test_regime_switch_uses_last_month_end_state_and_charges_switches():
    from src.regime import switch_series
    d = pd.bdate_range("2020-01-01", "2020-04-30")
    eq = pd.Series(np.cumprod(np.full(len(d), 1.01)), d)            # the strategy gains 1% a day
    spy = pd.Series(1.0, d)                                         # SPY is flat
    state = pd.Series([1.0, 0.0, 1.0, 1.0], pd.period_range("2020-01", periods=4, freq="M"))
    sw = switch_series(eq, spy, state, fee=0.01)
    feb, mar = sw[d.month == 2], sw[d.month == 3]
    assert np.allclose(feb.iloc[1:] / feb.shift(1).iloc[1:], 1.01)     # January's state (on) is applied in February
    assert np.allclose(mar.iloc[1:] / mar.shift(1).iloc[1:], 1.0)      # February's state (off) is applied in March
    first_mar = sw.index.get_loc(mar.index[0])
    assert np.isclose(sw.iloc[first_mar] / sw.iloc[first_mar - 1], 1.0 - 0.01)   # one switch charged on its first day


if __name__ == "__main__":                       # also runs without pytest:  python tests/test_signals.py
    tests = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for f in tests:
        f()
        print("ok ", f.__name__)
    print(f"{len(tests)} passed")
