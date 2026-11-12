"""Every experiment in the paper. Writes output/results.json and the series behind the figures."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

import config as C
from src import data as D
from src import signals as SG
from src import events as EV
from src.backtest import Market, simulate, stats


# ---------------------------------------------------------------- inputs
def scores(strict: bool = False) -> pd.DataFrame:
    """Point-in-time R/R scores, cached in data/."""
    f = C.DATA / f"scores{'_strict' if strict else ''}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    px, _ = D.load_wide(("close", "volume"))
    t0 = time.time()
    sc = SG.trend_scores(px["close"], px["volume"], strict=strict)
    sc.to_parquet(f)
    print(f"  scores{' (strict)' if strict else ''}: {sc.shape}, {time.time() - t0:.0f}s")
    return sc


def market(span: int = C.BAND_SPAN, strict: bool = False, liq: float = C.LIQ_QISC) -> tuple[Market, pd.Series]:
    """The simulation inputs. liq = C.LIQ_QISC for the QISC book, 0 for the original specification."""
    px, bench = D.load_wide(("open", "close", "volume"))
    close, opn, vol = px["close"], px["open"], px["volume"]
    sc = scores(strict).reindex(columns=close.columns, fill_value=0.0)
    out = [c for c in D.excluded_tickers() if c in sc.columns]          # US companies only, no funds
    sc[out] = 0.0
    d = sc.index[sc.index >= C.SIM_START]
    upper, lower = SG.band(opn, close, span)
    dv = D.traded_value(close, vol)
    A = lambda f: f.loc[d].to_numpy(np.float64)
    C_, U = A(close), A(upper)
    m = Market(dates=d, cols=close.columns, close=C_, open=A(opn), vol=A(vol), upper=U, lower=A(lower),
               vol_med=A(vol.rolling(50, min_periods=40).median().shift(1)), prev_close=A(close.shift(1)),
               score=sc.loc[d].where(dv.loc[d] >= liq, 0.0).to_numpy(np.float64),
               signal=SG.touch_signal(C_, U), trend=C_ > U,
               eligible=A(((close >= C.MIN_PRICE) & (dv >= C.LIQ_SCREEN)).astype(float)) > 0,
               extra=dict(traded_value=A(dv)))
    return m, bench


# ---------------------------------------------------------------- helpers
def book(m, bench, start=None, end=None, slots=C.SLOTS, **kw):
    eq, tr, od = simulate(m, slots=slots, start=start, end=end, **kw)
    return eq, tr, od, stats(eq, tr, bench, slots)


def by_period(m, bench, **kw):
    return {k: book(m, bench, a, b, **kw)[3] for k, (a, b) in C.PERIODS.items()}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return o


# ---------------------------------------------------------------- the battery
def run_all() -> dict:
    t0 = time.time()
    log = lambda *a: print(f"  [{time.time() - t0:4.0f}s]", *a, flush=True)
    out = C.OUTPUT / "series"
    out.mkdir(parents=True, exist_ok=True)
    m, bench = market()
    bench.to_csv(out / "benchmark.csv")
    R = {"meta": dict(start=str(m.dates[0].date()), end=str(m.dates[-1].date()), stocks=int(m.score.shape[1]),
                      scored_per_day=float((m.score > 0).sum(1).mean()))}

    # 1. replication: original rules (5 slots, $0.5M, 5 bp), original window and full sample
    mo, _ = market(liq=0.0)
    eq, tr, _, R["replication"] = book(mo, bench, *C.SEE_WINDOW, slots=C.SEE_SLOTS, cost=C.SEE_COST)
    tr.to_csv(out / "trades_replication.csv", index=False)
    R["original_full"] = book(mo, bench, slots=C.SEE_SLOTS, cost=C.SEE_COST)[3]
    del mo
    log("replication", f"{R['replication']['cagr']:+.1%}", R["replication"]["trades"], "trades")

    # 2. the QISC book
    eq, tr, od, R["main"] = book(m, bench)
    eq.to_csv(out / "equity.csv")
    tr.to_csv(out / "trades.csv", index=False)
    od.to_csv(out / "orders.csv", index=False)
    R["periods"] = by_period(m, bench)
    sp = bench.reindex(eq.index).ffill()
    ye, ys = eq.resample("YE").last(), sp.resample("YE").last()
    ye = ye / pd.concat([pd.Series([eq.iloc[0]]), ye.iloc[:-1]]).values - 1
    ys = ys / pd.concat([pd.Series([sp.iloc[0]]), ys.iloc[:-1]]).values - 1
    pd.DataFrame({"system": ye, "benchmark": ys}).to_csv(out / "yearly.csv")
    log("QISC book", f"{R['main']['cagr']:+.1%}")

    # 3. event study
    ev = EV.events(m)
    R["events"] = EV.event_table(ev).to_dict("records")
    R["events_period"] = {}
    for k, (a, b) in C.PERIODS.items():
        e = ev[(ev.date >= a) & ((ev.date < b) if b is not None else True)]
        R["events_period"][k] = EV.event_table(e).to_dict("records")
    for k, p in EV.paths(m, ev).items():
        p.to_csv(out / f"path_{k}.csv")
    R["events_n"] = ev.kind.value_counts().to_dict()
    log("event study", R["events_n"])

    # 4-9. one change at a time
    grid = [("clock", {}), ("band1", dict(band_k=1)), ("band3", dict(band_k=3)), ("band5", dict(band_k=5)),
            ("vol3", dict(vol_k=3.0)), ("vol5", dict(vol_k=5.0)), ("band3+vol3", dict(band_k=3, vol_k=3.0)),
            ("stop25", dict(stop=0.25)), ("stop40", dict(stop=0.40))]
    R["exits"] = [dict(book(m, bench, **kw)[3], exit=name) for name, kw in grid]
    R["slots"] = [dict(book(m, bench, slots=k)[3], K=k, by_period={p: v["ratio"] for p, v in by_period(m, bench, slots=k).items()})
                  for k in (3, 5, 8, 10, 12, 15, 20)]
    R["hold"] = [dict(book(m, bench, hold=h)[3], H=h, by_period={p: v["ratio"] for p, v in by_period(m, bench, hold=h).items()})
                 for h in (21, 42, 63, 84, 126)]
    R["costs"] = [dict(book(m, bench, cost=c)[3], cost=c, by_period={p: v["ratio"] for p, v in by_period(m, bench, cost=c).items()})
                  for c in (0.0005, 0.0010, 0.0020, 0.0030, 0.0050)]
    log("exits, slots, holding period, costs")
    R["touch"] = []
    for w in (3, 5, 10):
        for tol in (0.0, 0.01, 0.02):
            R["touch"].append(dict(book(m.with_(signal=SG.touch_signal(m.close, m.upper, w, tol)), bench)[3], W=w, TOL=tol))
    R["span"] = []
    for span in (10, 15, 20, 30, 40):
        m2, _ = market(span)
        R["span"].append(dict(book(m2, bench)[3], span=span))
        del m2
    log("entry parameters")

    # 10-15. stress tests
    shift = lambda a: np.vstack([np.zeros((1, a.shape[1]), a.dtype), a[:-1]])
    md = m.with_(score=shift(m.score), signal=shift(m.signal))
    R["delay"], R["delay_period"] = book(md, bench)[3], by_period(md, bench)
    del md
    top5 = tr.groupby("sym").ret.sum().sort_values(ascending=False).head(5).index.tolist()
    S = m.score.copy()
    S[:, [list(m.cols).index(s) for s in top5]] = 0.0
    R["drop_top5"] = dict(book(m.with_(score=S), bench)[3], names=top5)
    R["no_touch"], R["no_touch_period"] = book(m, bench, touch=False)[3], by_period(m, bench, touch=False)
    ms, _ = market(strict=True)
    R["strict"], R["strict_period"] = book(ms, bench)[3], by_period(ms, bench)
    del ms
    sma = bench.rolling(200).mean()
    on = (bench > sma).reindex(m.dates).fillna(False).to_numpy()
    mr = m.with_(score=np.where(on[:, None], m.score, 0.0))
    R["regime"], R["regime_period"], R["regime_share_on"] = book(mr, bench)[3], by_period(mr, bench), float(on.mean())
    del mr
    for tag, first, end in (("pre", "2007-01-01", C.DESIGN_START), ("design", "2017-07-01", C.OOS_START)):
        R[f"starts_{tag}"] = []
        for k in range(12):
            a = pd.Timestamp(first) + pd.DateOffset(months=k)
            s = book(m, bench, a, end)[3]
            R[f"starts_{tag}"].append(dict(start=str(a.date()), cagr=s["cagr"], maxdd=s["maxdd"], ratio=s["ratio"]))
    log("stress tests")
    json.dump(clean(R), open(C.OUTPUT / "results.json", "w"), indent=1)
    return R
