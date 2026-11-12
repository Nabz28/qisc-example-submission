"""Tables, the required output files and a compliance check against the QISC constraints."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config as C
from src import data as D
from src.backtest import deflated_sharpe

P = lambda x, d=1: "" if x is None else f"{x * 100:+.{d}f}%".replace("-", "−")
U = lambda x, d=0: "" if x is None else f"{x * 100:.{d}f}%"
F = lambda x, d=2: "" if x is None else f"{x:.{d}f}".replace("-", "−")
CI = lambda c, d=2: f"[{P(c[0], d)}, {P(c[1], d)}]"


def _md(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False))


def _save(df: pd.DataFrame, name: str):
    df.to_csv(C.TABLES / f"{name}.csv", index=False)
    (C.TABLES / f"{name}.md").write_text(_md(df), encoding="utf-8")


def tables(R: dict) -> dict:
    C.TABLES.mkdir(parents=True, exist_ok=True)
    a, b, c = R["conc_dev"], R["conc_full"], R["main"]
    r3 = [("Trades", lambda s: s["trades"]), ("Win rate", lambda s: U(s["win"])), ("Growth per year", lambda s: P(s["cagr"])),
          ("S&P 500 growth per year", lambda s: P(s["bench_cagr"])), ("Sharpe ratio (SPY)", lambda s: f"{F(s['sharpe'])} ({F(s['bench_sharpe'])})"),
          ("Worst drawdown (SPY)", lambda s: f"{P(s['maxdd'], 0)} ({P(s['bench_dd'], 0)})"),
          ("Monthly return above SPY [95%]", lambda s: f"{P(s['excess_m'], 2)} {CI(s['excess_ci'])}"),
          ("Cumulative return (SPY)", lambda s: f"{P(s['final'] - 1, 0)} ({P(s['bench_final'] - 1, 0)})")]
    _save(pd.DataFrame([[lab, f(a), f(b), f(c)] for lab, f in r3],
                       columns=["Measure", "Concentrated, 2017-2026", "Concentrated, 2007-2026", "Baseline, 2007-2026"]),
          "table3_concentration")
    cols = {"Full sample": R["main"], **{k: R["periods"][k] for k in ("heldout", "dev", "oos")}}
    rows = [("Growth per year (CAGR)", lambda s: P(s["cagr"])), ("S&P 500 growth per year", lambda s: P(s["bench_cagr"])),
            ("Monthly return above SPY", lambda s: P(s["excess_m"], 2)), ("95% interval", lambda s: CI(s["excess_ci"])),
            ("Alpha per year", lambda s: P(s["alpha_ann"])), ("Cumulative return (SPY)", lambda s: f"{P(s['final'] - 1, 0)} ({P(s['bench_final'] - 1, 0)})"),
            ("Volatility per year", lambda s: U(s["vol"], 1)), ("Sharpe ratio (SPY)", lambda s: f"{F(s['sharpe'])} ({F(s['bench_sharpe'])})"),
            ("Sortino ratio", lambda s: F(s["sortino"])), ("Worst drawdown (SPY)", lambda s: f"{P(s['maxdd'], 0)} ({P(s['bench_dd'], 0)})"),
            ("CAGR ÷ max drawdown", lambda s: F(s["ratio"])), ("Beta", lambda s: F(s["beta"])), ("Information ratio", lambda s: F(s["info_ratio"])),
            ("Trades", lambda s: s["trades"]), ("Win rate", lambda s: U(s["win"])),
            ("Average win / average loss", lambda s: f"{P(s['avg_win'])} / {P(s['avg_loss'])}"),
            ("Mean / median trade", lambda s: f"{P(s['mean_trade'])} / {P(s['median_trade'])}")]
    _save(pd.DataFrame([[lab] + [f(s) for s in cols.values()] for lab, f in rows],
                       columns=["Measure", "Full sample", "Held-out", "Development", "QISC out-of-sample"]), "table4_performance")
    ev = {(e["kind"], e["h"]): e for e in R["events"]}
    _save(pd.DataFrame([[f"{h} days", P(ev["touch", h]["mean"]), f"{P(ev['touch', h]['excess'])} {CI(ev['touch', h]['excess_ci'], 1)}",
                         P(ev["no_touch", h]["mean"]), f"{P(ev['no_touch', h]['excess'])} {CI(ev['no_touch', h]['excess_ci'], 1)}",
                         f"{P(ev['touch_minus_no_touch', h]['mean'])} {CI(ev['touch_minus_no_touch', h]['excess_ci'], 1)}"]
                        for h in (5, 21, 63)],
                       columns=["Horizon", "Touch", "Touch above universe", "No touch", "No touch above universe", "Touch minus no touch"]),
          "table5_events")
    _save(pd.DataFrame([[s["exit"], s["trades"], U(s["win"]), P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["exits"]],
                       columns=["Exit", "Trades", "Win rate", "Per year", "Worst drawdown", "CAGR ÷ drawdown", "Sharpe"]), "tableB1_exits")
    sens = []
    for key, col in (("slots", "K"), ("hold", "H"), ("costs", "cost")):
        for s in R[key]:
            sens.append([key, s[col], s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["sharpe"]), F(s["ratio"])]
                        + [F(s["by_period"][p]) for p in ("heldout", "dev", "oos")])
    _save(pd.DataFrame(sens, columns=["Parameter", "Value", "Trades", "Per year", "Worst drawdown", "Sharpe", "CAGR ÷ drawdown",
                                      "Held-out", "Development", "QISC OOS"]), "tableB2_sensitivity")
    _save(pd.DataFrame([[f"{s['W']} days", U(s["TOL"]), s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["touch"]]
                       + [[f"EMA span {s['span']}", "1%", s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["span"]],
                       columns=["Window / span", "Tolerance", "Trades", "Per year", "Worst drawdown", "CAGR ÷ drawdown", "Sharpe"]), "tableB3_entry")
    st = lambda lab, s: [lab, P(s["cagr"]), P(s["maxdd"], 0), F(s["sharpe"]), f"{P(s['excess_m'], 2)} {CI(s['excess_ci'], 1)}"]
    rng = lambda k, f: f"{P(min(r[f] for r in R[k]))} to {P(max(r[f] for r in R[k]))}"
    _save(pd.DataFrame([st("Baseline portfolio", R["main"]), st("Execution one day later", R["delay"]),
                        st("Without the five largest contributors", R["drop_top5"]), st("Bought without a touch", R["no_touch"]),
                        st("Pullbacks counted only once confirmed", R["strict"]),
                        st("New positions only while SPY > 200-day average", R["regime"]),
                        ["Twelve start months, held-out decade", rng("starts_heldout", "cagr"), rng("starts_heldout", "maxdd"), "", ""],
                        ["Twelve start months, development period", rng("starts_dev", "cagr"), rng("starts_dev", "maxdd"), "", ""]],
                       columns=["Test", "Per year", "Worst drawdown", "Sharpe", "Monthly excess [95%]"]), "table6_stress")
    # deflated Sharpe ratio over every variant reported
    eq = pd.read_csv(C.OUTPUT / "series" / "equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    r = eq.pct_change().dropna()
    trials = ([s["sharpe"] for k in ("exits", "slots", "hold", "touch", "span", "costs") for s in R[k]]
              + [R[k]["sharpe"] for k in ("delay", "drop_top5", "no_touch", "regime", "strict")])
    dsr, sr0 = deflated_sharpe(R["main"]["sharpe"], trials, len(r), float(r.skew()), float(r.kurt() + 3))
    return dict(dsr=dsr, sr0=sr0, n_trials=len(trials))


def outputs() -> dict:
    """output/positions.csv (QISC format), output/trades.csv, and a compliance check."""
    od = pd.read_csv(C.OUTPUT / "series" / "orders.csv", parse_dates=["date"])
    od["weight"] = od.weight.round(4)
    od.assign(date=od.date.dt.strftime("%Y-%m-%d")).to_csv(C.OUTPUT / "positions.csv", index=False)
    tr = pd.read_csv(C.OUTPUT / "series" / "trades.csv", parse_dates=["entry", "exit"])
    tr.assign(entry=tr.entry.dt.date, exit=tr.exit.dt.date, buy=tr.buy.round(4), sell=tr.sell.round(4),
              ret=tr.ret.round(5)).to_csv(C.OUTPUT / "trades.csv", index=False)
    for name, sub in (("trades_best", tr.nlargest(10, "ret")), ("trades_worst", tr.nsmallest(10, "ret")),
                      ("trades_oos", tr[tr.entry >= C.OOS_START])):            # Appendix C of the paper
        sub = sub.reset_index(drop=True)
        pd.DataFrame({"#": range(1, len(sub) + 1), "Stock": sub.sym, "Bought": sub.entry.dt.date,
                      "Buy price": sub.buy.round(2), "Sold": sub.exit.dt.date, "Sell price": sub.sell.round(2),
                      "Return": sub.ret.map(lambda x: P(x))}).to_csv(C.TABLES / f"{name}.csv", index=False)
    # compliance with the casebook (Arena B: United States)
    px, _ = D.load_wide(("close", "volume"))
    dv = D.traded_value(px["close"], px["volume"])
    eq = pd.read_csv(C.OUTPUT / "series" / "equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    buys = od[od.weight > 0]
    nav = eq.reindex(buys.date).to_numpy() * C.CAPITAL
    adv = np.array([dv.at[d, s] for d, s in zip(buys.date, buys.ticker)])
    share = buys.weight.to_numpy() * nav / adv
    comp = dict(long_only=bool((od.weight >= 0).all()), max_weight=float(od.weight.max()),
                max_weight_ok=bool(od.weight.max() <= 0.10 + 1e-9),
                avg_holding_days=float(tr.bars.mean()), holding_ok=bool(tr.bars.mean() >= 5),
                execution="signal at close t, fill at open t+1", cost_per_side=C.COST, cost_ok=C.COST >= 0.0010,
                entries=len(buys), entries_within_5pct_adv=float((share <= 0.05).mean()),
                entries_within_5pct_adv_nav_below_2m=float((share[nav < 2e6] <= 0.05).mean()),
                note="Positions are sized on the compounding NAV of a book that starts at $1M. The 5%-of-ADV "
                     "limit binds increasingly as NAV grows; a live book would raise the liquidity floor with NAV.")
    json.dump(comp, open(C.OUTPUT / "compliance.json", "w"), indent=1)
    return comp


def run() -> None:
    R = json.load(open(C.OUTPUT / "results.json"))
    num = tables(R)
    comp = outputs()
    json.dump(num, open(C.OUTPUT / "numbers.json", "w"), indent=1)
    m = R["main"]
    print(f"  baseline portfolio: {m['cagr']:+.1%} a year (S&P 500 {m['bench_cagr']:+.1%}), Sharpe {m['sharpe']:.2f}, "
          f"worst drawdown {m['maxdd']:.0%}, deflated Sharpe {num['dsr']:.3f} over {num['n_trials']} trials")
    print(f"  compliance: max weight {comp['max_weight']:.3f}, avg holding {comp['avg_holding_days']:.0f} days, "
          f"{comp['entries_within_5pct_adv']:.0%} of entries within 5% of ADV")
