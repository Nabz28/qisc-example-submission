"""The EMA band, the trend screen and the entry signal.

Equations (1)-(3) of the paper. `tests/` check the building blocks.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

import config as C


# ---------------------------------------------------------------- moving averages
def ema(x: pd.DataFrame | pd.Series, span: int):
    """E_t = a x_t + (1 - a) E_{t-1}, a = 2 / (span + 1), seeded with the first value (Eq. 1)."""
    return x.ewm(span=span, adjust=False).mean()


def band(opn: pd.DataFrame, close: pd.DataFrame, span: int = C.BAND_SPAN):
    """Upper and lower edge of the band between the EMA of opens and the EMA of closes."""
    eo, ec = ema(opn, span), ema(close, span)
    return np.maximum(eo, ec), np.minimum(eo, ec)


# ---------------------------------------------------------------- runs and pullbacks
def run_start_series(close: np.ndarray, ema_fast: np.ndarray, max_below: int = C.MAX_BELOW) -> np.ndarray:
    """First bar of the current run at every t: one past the latest block of more than
    `max_below` consecutive closes at or below the fast EMA (or a missing price)."""
    n = len(close)
    out = np.zeros(n, dtype=np.int64)
    below, last_break = 0, 0
    for i in range(n):
        if not np.isfinite(close[i]) or not np.isfinite(ema_fast[i]):
            below, last_break = 0, i
        elif close[i] > ema_fast[i]:
            below = 0
        else:
            below += 1
            if below > max_below:
                last_break = i
        out[i] = last_break + 1 if last_break + 1 < n else n - 1
    return out


def swing_points(close: np.ndarray, pct: float = C.SWING):
    """ZigZag on closes. Returns (index, kind, confirmed_at): kind +1 peak, -1 trough;
    a peak is confirmed when a close falls `pct` below it, a trough when a close rises `pct` above it."""
    c = np.asarray(close, dtype=float)
    idx, kind, conf = [], [], []
    if len(c) < 3 or not np.isfinite(c).any():
        return np.empty(0, int), np.empty(0, int), np.empty(0, int)
    start = int(np.argmax(np.isfinite(c)))
    hi_i = lo_i = start
    hi_v = lo_v = c[start]
    direction = 0
    for i in range(start + 1, len(c)):
        v = c[i]
        if not np.isfinite(v):
            continue
        if direction >= 0 and v > hi_v:
            hi_i, hi_v = i, v
        if direction <= 0 and v < lo_v:
            lo_i, lo_v = i, v
        if direction >= 0 and v <= hi_v * (1 - pct):
            idx.append(hi_i); kind.append(+1); conf.append(i)
            direction, lo_i, lo_v = -1, i, v
        elif direction <= 0 and v >= lo_v * (1 + pct):
            idx.append(lo_i); kind.append(-1); conf.append(i)
            direction, hi_i, hi_v = +1, i, v
    return np.array(idx, int), np.array(kind, int), np.array(conf, int)


# ---------------------------------------------------------------- trend scores (Eq. 2)
def _scores_block(args) -> np.ndarray:
    close, ema_f, ema_s, dvol, day_pos, strict = args
    T, N = len(day_pos), close.shape[1]
    out = np.zeros((T, N), dtype=np.float32)
    for j in range(N):
        c = close[:, j]
        if np.isfinite(c).sum() < 200:
            continue
        rs_all = run_start_series(c, ema_f[:, j])
        idx, kind, conf = swing_points(c)
        pairs = [(a, a + 1) for a in range(len(idx) - 1) if kind[a] == 1 and kind[a + 1] == -1]
        if not pairs:
            continue
        pi = np.array([idx[a] for a, _ in pairs])
        ti = np.array([idx[b] for _, b in pairs])
        known = np.array([conf[b] for _, b in pairs]) if strict else ti   # when the pullback is known
        depth = c[ti] / c[pi] - 1.0
        y = np.log(np.where(c > 0, c, np.nan))
        dy = np.diff(y, prepend=np.nan)
        for r, t in enumerate(day_pos):
            px = c[t]
            if not np.isfinite(px) or px < C.MIN_PRICE:
                continue
            if not np.isfinite(dvol[t, j]) or dvol[t, j] < C.LIQ_SCREEN:
                continue
            if px <= ema_s[t, j] or px <= ema_f[t, j]:                # above EMA20 and EMA100
                continue
            rs = rs_all[t]
            if t - rs + 1 < C.MIN_RUN_BARS:
                continue
            tot = y[t] - y[rs]
            if not np.isfinite(tot) or tot < C.MIN_RET:
                continue
            m = (known < t) & (pi >= rs)                              # pullbacks inside this run
            if m.sum() < C.MIN_CYCLES:
                continue
            seg = dy[rs + 1:t + 1]
            seg = seg[np.isfinite(seg)]
            if len(seg) < 5 or seg.max() / tot > C.MAX_DAY_SHARE or np.sort(seg)[-5:].sum() / tot > C.MAX_TOP5_SHARE:
                continue
            out[r, j] = np.expm1(tot) / abs(depth[m].mean())           # R/R: run return / |average pullback|
    return out


def trend_scores(close: pd.DataFrame, vol: pd.DataFrame, start=C.SCORE_START, strict: bool = C.STRICT_PIT,
                 workers: int = C.WORKERS) -> pd.DataFrame:
    """R/R score of every stock on every day from `start`; zero if the stock fails the screen."""
    ef, es = ema(close, C.FAST).to_numpy(), ema(close, C.SLOW).to_numpy()
    dv = (close * vol).rolling(60).median().to_numpy()
    cl = close.to_numpy(np.float64)
    day_pos = np.flatnonzero(close.index >= start)
    blocks = np.array_split(np.arange(close.shape[1]), max(1, workers * 3))
    jobs = [(cl[:, b], ef[:, b], es[:, b], dv[:, b], day_pos, strict) for b in blocks]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(_scores_block, jobs))
    return pd.DataFrame(np.hstack(parts), index=close.index[day_pos], columns=close.columns)


# ---------------------------------------------------------------- entry signal (Eq. 3)
def touch_signal(close: np.ndarray, upper: np.ndarray, win: int = C.TOUCH_WIN, tol: float = C.TOUCH_TOL) -> np.ndarray:
    """A close inside the band, or within `tol` above it, in the last `win` sessions, and today's close above the band."""
    near = pd.DataFrame(close / upper - 1).rolling(win, min_periods=1).min().to_numpy() <= tol
    return near & (close > upper)
