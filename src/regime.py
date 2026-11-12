"""Regime and decay analysis (paper, Section 7). The tests follow REGIME_PROTOCOL.md, written before they were run."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
from src import data as D
from src.backtest import Market, stats

NAMES = {"R1": "Market trend: SPY above its 200-day average",
         "R2": "Supply of clean trends above its 3-year median",
         "R3": "Small-cap leadership: equal-weighted universe beat SPY over 6 months",
         "R4": "Strategy momentum: portfolio beat SPY over 12 months",
         "R5": "Edge health: touch advantage positive over the past year",
         "R6": "Combined monitor: R4 and R5 both on"}
SAMPLES = {"history": (pd.Timestamp("2007-01-01"), C.MAIN_START), "main": (C.MAIN_START, None),
           "all": (pd.Timestamp("2007-01-01"), None)}


def universe_index(m: Market) -> pd.Series:
    """Equal-weighted daily close-to-close return of the eligible universe (eligible on the previous day)."""
    cl = m.close
    r = cl[1:] / cl[:-1] - 1
    ok = m.eligible[:-1] & np.isfinite(r)
    r = np.where(ok, np.clip(np.nan_to_num(r), -0.5, 1.0), 0.0)
    ew = r.sum(1) / np.maximum(ok.sum(1), 1)
    return pd.Series(np.r_[1.0, np.cumprod(1 + ew)], m.dates)


def edge_by_month(ev: pd.DataFrame, h: int = 21) -> pd.Series:
    """Month-matched touch minus no-touch return at horizon h, by event month."""
    g = ev.dropna(subset=[f"r{h}"]).assign(month=lambda x: pd.to_datetime(x.date).dt.to_period("M"))
    a = g[g.kind == "touch"].groupby("month")[f"r{h}"].mean()
    b = g[g.kind == "no_touch"].groupby("month")[f"r{h}"].mean()
    return (a - b).dropna()


def indicators(m: Market, bench: pd.Series, eq: pd.Series, ev: pd.DataFrame) -> pd.DataFrame:
    """Indicator states at each month-end (True = on, NaN = not yet computable), from data up to that month-end."""
    d = m.dates
    spy = bench.reindex(d).ffill()
    n = pd.Series((m.score > 0).sum(1), d, dtype=float).rolling(21).mean()
    ew = universe_index(m)
    eqd = eq.reindex(d).ffill()
    daily = pd.DataFrame({
        "R1": (spy > spy.rolling(200).mean()).where(spy.rolling(200).mean().notna()),
        "R2": (n > n.rolling(756, min_periods=252).median()).where(n.rolling(756, min_periods=252).median().notna()),
        "R3": ((ew / ew.shift(126)) > (spy / spy.shift(126))).where(ew.shift(126).notna()),
        "R4": ((eqd / eqd.shift(252)) > (spy / spy.shift(252))).where(eqd.shift(252).notna()),
    }).astype(float)
    out = daily.resample("ME").last()
    out.index = out.index.to_period("M")
    em = edge_by_month(ev)
    r5 = {}
    for p in out.index:
        w = em[(em.index >= p - 14) & (em.index <= p - 3)]
        r5[p] = float(w.mean() > 0) if len(w) >= 6 else np.nan
    out["R5"] = pd.Series(r5)
    out["R6"] = (out.R4.astype(float) * out.R5).where(out.R4.notna() & out.R5.notna())
    out["supply"] = n.resample("ME").last().to_numpy()
    out["edge12"] = [em[(em.index >= p - 14) & (em.index <= p - 3)].mean() for p in out.index]
    return out


def monthly(eq: pd.Series, bench: pd.Series) -> pd.DataFrame:
    s = eq.resample("ME").last()
    b = bench.reindex(eq.index).ffill().resample("ME").last()
    out = pd.DataFrame({"strat": s.pct_change(), "spy": b.pct_change()})
    out.index = out.index.to_period("M")
    return out.dropna()


def _boot_diff(on: np.ndarray, off: np.ndarray, seed: int = 5) -> list[float]:
    if len(on) < 3 or len(off) < 3:
        return [np.nan, np.nan]
    rng = np.random.default_rng(seed)
    v = [on[rng.integers(0, len(on), len(on))].mean() - off[rng.integers(0, len(off), len(off))].mean()
         for _ in range(C.BOOT)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def conditional(ind: pd.DataFrame, mr: pd.DataFrame) -> list[dict]:
    """Test 1: next-month return above SPY with the indicator on and off."""
    ex = (mr.strat - mr.spy)
    nxt = ex.reindex(ind.index + 1).to_numpy()
    rows = []
    for k in NAMES:
        st = ind[k].to_numpy(dtype=float)
        row = dict(key=k, name=NAMES[k])
        for tag, (a, b) in SAMPLES.items():
            pa, pb = pd.Period(a, "M"), (pd.Period(b, "M") if b is not None else None)
            mask = np.array([(p + 1 >= pa) and (pb is None or p + 1 < pb) for p in ind.index])
            ok = mask & np.isfinite(st) & np.isfinite(nxt)
            on, off = nxt[ok & (st == 1)], nxt[ok & (st == 0)]
            row[tag] = dict(on=float(on.mean()) if len(on) else np.nan, off=float(off.mean()) if len(off) else np.nan,
                            diff=float(on.mean() - off.mean()) if len(on) and len(off) else np.nan,
                            ci=_boot_diff(on, off), share_on=float(len(on) / max(ok.sum(), 1)), months=int(ok.sum()))
        h, mn, al = row["history"]["diff"], row["main"]["diff"], row["all"]["ci"]
        row["identified"] = bool(h > 0 and mn > 0 and al[0] > 0)
        rows.append(row)
    return rows


def switch_series(eq: pd.Series, bench: pd.Series, state: pd.Series, fee: float = 0.0025) -> pd.Series:
    """Test 2: hold the portfolio (a shadow book) in a month when the previous month-end state is on, SPY otherwise."""
    rs = eq.pct_change().fillna(0.0)
    rb = bench.reindex(eq.index).ffill().pct_change().fillna(0.0)
    per = eq.index.to_period("M")
    st = state.astype(float).fillna(1.0)
    s_prev = pd.Series(st.reindex(per - 1).to_numpy(), eq.index).fillna(1.0)
    r = np.where(s_prev == 1.0, rs, rb)
    first = np.r_[True, per[1:] != per[:-1]]
    sw = first & (s_prev.diff().fillna(0).to_numpy() != 0)
    r = r - np.where(sw, fee, 0.0)
    return pd.Series(np.cumprod(1 + r), eq.index)


def slice_stats(eq: pd.Series, bench: pd.Series, a, b=None) -> dict:
    s = eq[(eq.index >= a) & ((eq.index < b) if b is not None else True)]
    s = s / s.iloc[0]
    out = stats(s, pd.DataFrame(columns=["ret"]), bench)
    return {k: out[k] for k in ("cagr", "maxdd", "sharpe", "excess_m", "excess_ci", "bench_cagr", "bench_sharpe",
                                "bench_dd", "final", "bench_final", "vol")}


def switching(eq: pd.Series, bench: pd.Series, ind: pd.DataFrame) -> list[dict]:
    rows = [dict(key="none", name="Portfolio, always invested",
                 **{t: slice_stats(eq, bench, a, b) for t, (a, b) in SAMPLES.items()})]
    for k in NAMES:
        sw = switch_series(eq, bench, ind[k])
        rows.append(dict(key=k, name=NAMES[k], share_on=float(ind[k].fillna(1).mean()),
                         **{t: slice_stats(sw, bench, a, b) for t, (a, b) in SAMPLES.items()}))
    return rows


def relative_drawdown(eq: pd.Series, bench: pd.Series) -> pd.Series:
    rel = eq / bench.reindex(eq.index).ffill()
    return rel / rel.cummax() - 1


def characteristics(m: Market, bench: pd.Series, trades: pd.DataFrame, ev: pd.DataFrame, ind: pd.DataFrame) -> dict:
    """What the market looked like in each period: supply of trends, breadth, sector mix of trades, the edge."""
    s = D.screener()
    sector = dict(zip(s.symbol.astype(str).str.replace("/", "-"), s.sector.replace("", "Unknown")))
    tr = trades.assign(entry=pd.to_datetime(trades.entry), sector=trades.sym.map(sector).fillna("Unknown"))
    spy = bench.reindex(m.dates).ffill()
    ew = universe_index(m)
    n = pd.Series((m.score > 0).sum(1), m.dates)
    em = edge_by_month(ev)
    above = (spy > spy.rolling(200).mean())
    out = {}
    for tag, (a, b) in (("history", SAMPLES["history"]), ("insample", (C.MAIN_START, C.OOS_START)), ("oos", (C.OOS_START, None))):
        sel = (m.dates >= a) & ((m.dates < b) if b is not None else True)
        d = m.dates[sel]
        yrs = (d[-1] - d[0]).days / 365.25
        t = tr[(tr.entry >= a) & ((tr.entry < b) if b is not None else True)]
        e = em[(em.index >= pd.Period(a, "M")) & ((em.index < pd.Period(b, "M")) if b is not None else True)]
        shares = t.sector.value_counts(normalize=True)
        out[tag] = dict(
            trends_per_day=float(n[sel].mean()),
            ew_minus_spy=float((ew[d[-1]] / ew[d[0]]) ** (1 / yrs) - (spy[d[-1]] / spy[d[0]]) ** (1 / yrs)),
            spy_above_200=float(above[sel].mean()),
            trades=int(len(t)), tech=float(shares.get("Technology", 0.0)), health=float(shares.get("Health Care", 0.0)),
            median_trade=float(t.ret.median()), big_share=float((t.ret >= 0.5).mean()),
            edge21=float(e.mean()), sectors={k: float(v) for k, v in shares.head(6).items()})
    return out
