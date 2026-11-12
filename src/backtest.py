"""The portfolio simulator and its statistics.

Rules (paper, Section 4.3): decide on the close of day t, fill at the open of t+1; each new
position gets equity / slots (capped by cash); sell at the open after HOLD sessions or when an
optional exit fires; a stock sold cannot be bought again for COOLDOWN sessions; costs are
charged on both sides; cash earns nothing; nothing is forward-filled.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config as C


@dataclass
class Market:
    """Everything the simulator reads, as date x stock arrays over the simulation dates."""
    dates: pd.DatetimeIndex
    cols: pd.Index
    close: np.ndarray
    open: np.ndarray
    vol: np.ndarray
    upper: np.ndarray          # band edges
    lower: np.ndarray
    vol_med: np.ndarray        # 50-day median volume, lagged one day (heavy-volume exit)
    prev_close: np.ndarray
    score: np.ndarray          # R/R, 0 = not eligible
    signal: np.ndarray         # band touch, Eq. (3)
    trend: np.ndarray          # close above the band (for "buy without a touch")
    eligible: np.ndarray       # event-study universe: price >= $1 and >= $0.5M a day
    extra: dict = field(default_factory=dict)

    def with_(self, **kw) -> "Market":
        d = dict(self.__dict__)
        d.update(kw)
        return Market(**d)


def simulate(m: Market, slots: int = C.SLOTS, cost: float = C.COST, hold: int = C.HOLD, touch: bool = True,
             band_k: int = 0, vol_k: float = 0.0, stop: float = 0.0, start=None, end=None):
    """One long-only book. Optional exits (decided on a close, executed at the next open):
    band_k  > 0: band_k consecutive closes below the lower band edge;
    vol_k   > 0: a down close on volume >= vol_k x its 50-day median;
    stop    > 0: close at least `stop` below the entry price.
    Returns (equity curve, trades, orders) where orders are the target weights for positions.csv."""
    d = m.dates
    i0 = 0 if start is None else int(np.searchsorted(d, start))
    i1 = len(d) if end is None else int(np.searchsorted(d, end))
    Cl, O, V, LO, VM, PC = m.close, m.open, m.vol, m.lower, m.vol_med, m.prev_close
    S, G, TR = m.score, m.signal, m.trend
    cash, pos, trades, orders, cool = 1.0, [], [], [], {}
    eq = np.empty(i1 - i0)
    for t in range(i0, i1):
        # exits at today's open
        keep = []
        for p in pos:
            j = p["j"]
            why = "clock" if t - p["t"] >= hold else p.get("flag")
            if why and np.isfinite(O[t, j]):
                px = O[t, j]
                cash += p["alloc"] + p["sh"] * (px - p["px"]) - p["alloc"] * cost
                trades.append(dict(sym=m.cols[j], entry=d[p["t"]], exit=d[t], why=why, bars=t - p["t"],
                                   buy=p["px"], sell=px, ret=px / p["px"] - 1 - 2 * cost))
                orders.append(dict(date=d[t - 1], ticker=m.cols[j], weight=0.0))
                cool[j] = t
            else:
                keep.append(p)
        pos = keep
        # entries decided on yesterday's close, filled at today's open
        if t > i0 and len(pos) < slots:
            s = S[t - 1]
            held = {p["j"] for p in pos}
            for j in np.argsort(-s)[:slots]:
                if len(pos) >= slots:
                    break
                if s[j] <= 0 or j in held or t - cool.get(j, -999) < C.COOLDOWN:
                    continue
                if (touch and not G[t - 1, j]) or (not touch and not TR[t - 1, j]):
                    continue
                if not np.isfinite(O[t, j]) or O[t, j] <= 0:
                    continue
                mtm = cash + sum(p["alloc"] + p["sh"] * (p["last"] - p["px"]) for p in pos)
                alloc = min(mtm / slots, cash)
                if alloc <= 0:
                    break
                cash -= alloc * (1 + cost)
                pos.append(dict(j=j, t=t, px=O[t, j], sh=alloc / O[t, j], alloc=alloc, last=O[t, j], below=0))
                orders.append(dict(date=d[t - 1], ticker=m.cols[j], weight=alloc / mtm))
                held.add(j)
        # mark to market at the close; flag price-based exits for tomorrow's open
        val = cash
        for p in pos:
            j, c = p["j"], Cl[t, p["j"]]
            if np.isfinite(c):
                p["last"] = c
                if t > p["t"]:
                    p["below"] = p["below"] + 1 if c < LO[t, j] else 0
                    if band_k and p["below"] >= band_k:
                        p.setdefault("flag", "band")
                    if vol_k and c < PC[t, j] and np.isfinite(VM[t, j]) and V[t, j] >= vol_k * VM[t, j] > 0:
                        p.setdefault("flag", "volume")
                    if stop and c / p["px"] - 1 <= -stop:
                        p.setdefault("flag", "stop")
            val += p["alloc"] + p["sh"] * (p["last"] - p["px"])
        eq[t - i0] = val
    return pd.Series(eq, d[i0:i1]), pd.DataFrame(trades), pd.DataFrame(orders)


# ---------------------------------------------------------------- statistics
def month_excess(eq: pd.Series, bench: pd.Series) -> pd.Series:
    mr = eq.resample("ME").last().pct_change().dropna()
    br = bench.reindex(eq.index).ffill().resample("ME").last().pct_change().dropna()
    return (mr - br.reindex(mr.index)).dropna()


def stats(eq: pd.Series, tr: pd.DataFrame, bench: pd.Series, slots: int = C.SLOTS) -> dict:
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    ruined = bool((eq <= 0).any())
    cagr = np.nan if ruined else eq.iloc[-1] ** (1 / yrs) - 1
    dd = eq / eq.cummax() - 1
    ex = month_excess(eq, bench)
    rng = np.random.default_rng(3)
    boot = [ex.iloc[rng.integers(0, len(ex), len(ex))].mean() for _ in range(C.BOOT)] if len(ex) > 3 else [np.nan]
    r = eq.pct_change().dropna()
    b = bench.reindex(eq.index).ffill()
    br = b.pct_change().dropna()
    mr = eq.resample("ME").last().pct_change().dropna()
    mb = b.resample("ME").last().pct_change().dropna().reindex(mr.index)
    beta = float(np.cov(mr, mb)[0, 1] / np.var(mb, ddof=1)) if len(mr) > 3 else np.nan
    bn = b / b.iloc[0]
    tret = tr.ret if len(tr) else pd.Series(dtype=float)
    w, l = tret[tret > 0], tret[tret <= 0]
    trough = dd.idxmin()
    return dict(
        trades=len(tr), win=float((tret > 0).mean()) if len(tr) else np.nan,
        avg_win=float(w.mean()), avg_loss=float(l.mean()), payoff=float(w.mean() / abs(l.mean())) if len(l) else np.nan,
        mean_trade=float(tret.mean()) if len(tr) else np.nan, median_trade=float(tret.median()) if len(tr) else np.nan,
        cagr=float(cagr), maxdd=float(dd.min()), ratio=float(cagr / abs(dd.min())) if not ruined else np.nan,
        vol=float(r.std() * np.sqrt(252)), sharpe=float(r.mean() / r.std() * np.sqrt(252)),
        sortino=float(r.mean() / r[r < 0].std() * np.sqrt(252)),
        beta=beta, alpha_ann=float((1 + mr.mean() - beta * mb.mean()) ** 12 - 1),
        info_ratio=float(ex.mean() / ex.std() * np.sqrt(12)),
        excess_m=float(ex.mean()), excess_ci=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        final=float(eq.iloc[-1]), years=yrs, turnover=float(len(tr) * 2 / slots / yrs) if len(tr) else np.nan,
        dd_peak=str(eq[:trough].idxmax().date()), dd_trough=str(trough.date()),
        big=int((tret >= 1).sum()), bad=int((tret <= -0.3).sum()),
        bench_cagr=float(bn.iloc[-1] ** (1 / yrs) - 1), bench_dd=float((bn / bn.cummax() - 1).min()),
        bench_sharpe=float(br.mean() / br.std() * np.sqrt(252)), bench_final=float(bn.iloc[-1]),
        ruined=ruined)


def deflated_sharpe(sr_ann: float, trial_srs: list[float], n_obs: int, skew: float, kurt: float) -> tuple[float, float]:
    """Bailey and López de Prado (2014): P[true SR > expected max SR of the trials], daily units inside."""
    from scipy.stats import norm
    sr = sr_ann / np.sqrt(252)
    tr = np.array([t for t in trial_srs if t is not None and np.isfinite(t)]) / np.sqrt(252)
    n, g = len(tr), 0.5772156649
    sr0 = np.sqrt(tr.var(ddof=1)) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e)))
    z = (sr - sr0) * np.sqrt(n_obs - 1) / np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return float(norm.cdf(z)), float(sr0 * np.sqrt(252))
