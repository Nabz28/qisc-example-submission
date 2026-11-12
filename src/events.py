"""Event study (paper, Section 5.4): touch entries against no-touch entries into the same top-ranked trends."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
from src.backtest import Market


def events(m: Market, top: int = C.SLOTS, cost: float = C.EVENT_COST) -> pd.DataFrame:
    """One row per event with net returns r{h} from the next open, and r{h} minus the equal-weighted universe (x{h}).
    touch: first day of a signal episode; no_touch: a top-ranked stock in trend without a touch (buy now)."""
    S, Cl, O, sig, T = m.score, m.close, m.open, m.signal, len(m.dates)
    rank_ok = np.zeros_like(sig)
    for t in range(T):
        k = np.argsort(-S[t])[:top]
        rank_ok[t, k[S[t, k] > 0]] = True
    first = sig & rank_ok & ~np.vstack([np.zeros((1, sig.shape[1]), bool), sig[:-1]])
    notouch = m.trend & (S > 0) & rank_ok & ~sig
    rows = []
    for kind, mask in (("touch", first), ("no_touch", notouch)):
        ts, js = np.nonzero(mask[:-1])
        for t, j in zip(ts, js):
            e = O[t + 1, j]
            if not np.isfinite(e) or e <= 0:
                continue
            r = {"kind": kind, "t": t, "j": j, "date": m.dates[t]}
            for h in C.HORIZONS:
                x = O[t + 1 + h, j] if t + 1 + h < T else np.nan
                r[f"r{h}"] = x / e - 1 - 2 * cost if np.isfinite(x) else np.nan
            rows.append(r)
    ev = pd.DataFrame(rows)
    for h in C.HORIZONS:
        base = np.full(T, np.nan)
        for t in range(T - 1 - h):
            e, x = O[t + 1], O[t + 1 + h]
            ok = m.eligible[t] & np.isfinite(e) & np.isfinite(x) & (e > 0)
            if ok.any():
                base[t] = np.clip(x[ok] / e[ok] - 1, -0.95, 5.0).mean()    # one junk print must not move the mean
        ev[f"x{h}"] = ev[f"r{h}"] - base[ev.t.to_numpy()]
    return ev


def month_boot(df: pd.DataFrame, col: str, win: bool = False, seed: int = 7) -> list[float]:
    """95% interval of the pooled mean, resampling whole months."""
    x = df[[col, "date"]].dropna()
    if win:
        x = x.assign(**{col: (x[col] > 0).astype(float)})
    g = x.groupby(pd.to_datetime(x.date).dt.to_period("M"))[col].agg(["sum", "count"])
    if len(g) < 3:
        return [np.nan, np.nan]
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(g), np.full(len(g), 1 / len(g)), size=C.BOOT)
    v = (w @ g["sum"].to_numpy()) / (w @ g["count"].to_numpy())
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def event_table(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for kind, e in ev.groupby("kind"):
        for h in C.HORIZONS:
            x = e.dropna(subset=[f"r{h}"])
            rows.append(dict(kind=kind, h=h, n=len(x), mean=x[f"r{h}"].mean(), median=x[f"r{h}"].median(),
                             win=(x[f"r{h}"] > 0).mean(), excess=x[f"x{h}"].mean(),
                             excess_ci=month_boot(x, f"x{h}"), win_ci=month_boot(x, f"r{h}", win=True)))
    for h in C.HORIZONS:                                     # touch minus no-touch within the same month
        a, b = ev[ev.kind == "touch"], ev[ev.kind == "no_touch"]
        ma = a.groupby(pd.to_datetime(a.date).dt.to_period("M"))[f"r{h}"].mean()
        mb = b.groupby(pd.to_datetime(b.date).dt.to_period("M"))[f"r{h}"].mean()
        dm = (ma - mb).dropna()
        rng = np.random.default_rng(11)
        bs = [dm.iloc[rng.integers(0, len(dm), len(dm))].mean() for _ in range(C.BOOT)]
        rows.append(dict(kind="touch_minus_no_touch", h=h, n=len(dm), mean=dm.mean(),
                         excess_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]))
    return pd.DataFrame(rows)


def paths(m: Market, ev: pd.DataFrame, n: int = C.HOLD) -> dict[str, pd.DataFrame]:
    """Mean cumulative return from the entry open, d = 0..n sessions after the fill (Figure 5)."""
    Cl, O, T = m.close, m.open, len(m.dates)
    out = {}
    for kind in ("touch", "no_touch"):
        e = ev[ev.kind == kind]
        mat = np.full((len(e), n + 1), np.nan)
        for i, (t, j) in enumerate(zip(e.t, e.j)):
            seg = Cl[t + 1:min(T, t + 2 + n), j] / O[t + 1, j] - 1
            mat[i, :len(seg)] = seg
        out[kind] = pd.DataFrame({"mean": np.nanmean(mat, 0), "median": np.nanmedian(mat, 0),
                                  "n": np.isfinite(mat).sum(0)})
    return out
