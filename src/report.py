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
    a, b, c, d = R["main"], R["dev_window"], R["ten_positions"], R["periods"]["history"]
    r3 = [("Trades", lambda s: s["trades"]), ("Win rate", lambda s: U(s["win"])), ("Growth per year", lambda s: P(s["cagr"])),
          ("S&P 500 growth per year", lambda s: P(s["bench_cagr"])), ("Sharpe ratio (SPY)", lambda s: f"{F(s['sharpe'])} ({F(s['bench_sharpe'])})"),
          ("Worst drawdown (SPY)", lambda s: f"{P(s['maxdd'], 0)} ({P(s['bench_dd'], 0)})"),
          ("Monthly return above SPY [95%]", lambda s: f"{P(s['excess_m'], 2)} {CI(s['excess_ci'])}"),
          ("Cumulative return (SPY)", lambda s: f"{P(s['final'] - 1, 0)} ({P(s['bench_final'] - 1, 0)})")]
    _save(pd.DataFrame([[lab, f(a), f(b), f(c), f(d)] for lab, f in r3],
                       columns=["Measure", "Portfolio, 2015-2026", "Development window, 2017-2026", "Ten positions, 2015-2026",
                                "Same rules, 2007-2014"]),
          "tableA1_samples")
    _save(pd.DataFrame([[d["label"], P(d["cagr"]), P(d["maxdd"], 0), F(d["sharpe"]), f"{P(d['excess_m'], 2)} {CI(d['excess_ci'])}"]
                        for d in R["decomposition"]],
                       columns=["Cost and liquidity assumptions", "Per year", "Worst drawdown", "Sharpe", "Monthly excess [95%]"]),
          "tableA2_costs")
    cols = {"2015-2026": R["main"], **{k: R["periods"][k] for k in ("insample", "oos", "history")}}
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
                       columns=["Measure", "2015-2026", "In-sample, 2015-2024", "QISC out-of-sample", "Before the sample, 2007-2014"]),
          "table3_performance")
    def ev_row(label, recs, h):
        ev = {(e["kind"], e["h"]): e for e in recs}
        return [label, P(ev["touch", h]["mean"]), f"{P(ev['touch', h]['excess'])} {CI(ev['touch', h]['excess_ci'], 1)}",
                P(ev["no_touch", h]["mean"]), f"{P(ev['no_touch', h]['excess'])} {CI(ev['no_touch', h]['excess_ci'], 1)}",
                f"{P(ev['touch_minus_no_touch', h]['mean'])} {CI(ev['touch_minus_no_touch', h]['excess_ci'], 1)}"]
    names = {"insample": "In-sample, 2015-2024", "oos": "QISC out-of-sample", "history": "Before the sample, 2007-2014"}
    _save(pd.DataFrame([ev_row(f"{h} days", R["events"], h) for h in (5, 21, 63)]
                       + [ev_row(f"{names[k]}, {h} days", R["events_period"][k], h) for h in (5, 63) for k in names],
                       columns=["Horizon", "Touch", "Touch above universe", "No touch", "No touch above universe", "Touch minus no touch"]),
          "table4_events")
    _save(pd.DataFrame([[s["exit"], s["trades"], U(s["win"]), P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["exits"]],
                       columns=["Exit", "Trades", "Win rate", "Per year", "Worst drawdown", "CAGR ÷ drawdown", "Sharpe"]), "tableB1_exits")
    sens = []
    for key, col in (("slots", "K"), ("hold", "H"), ("costs", "mult")):
        for s in R[key]:
            sens.append([key, s[col], s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["sharpe"]), F(s["ratio"])]
                        + [F(s["by_period"][p]) for p in ("insample", "oos", "history")])
    _save(pd.DataFrame(sens, columns=["Parameter", "Value", "Trades", "Per year", "Worst drawdown", "Sharpe", "CAGR ÷ drawdown",
                                      "In-sample", "QISC OOS", "2007-2014"]), "tableB2_sensitivity")
    _save(pd.DataFrame([[f"{s['W']} days", U(s["TOL"]), s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["touch"]]
                       + [[f"EMA span {s['span']}", "1%", s["trades"], P(s["cagr"]), P(s["maxdd"], 0), F(s["ratio"]), F(s["sharpe"])] for s in R["span"]],
                       columns=["Window / span", "Tolerance", "Trades", "Per year", "Worst drawdown", "CAGR ÷ drawdown", "Sharpe"]), "tableB3_entry")
    st = lambda lab, s: [lab, P(s["cagr"]), P(s["maxdd"], 0), F(s["sharpe"]), f"{P(s['excess_m'], 2)} {CI(s['excess_ci'], 1)}"]
    rng = lambda k, f: f"{P(min(r[f] for r in R[k]), 1 if f == 'cagr' else 0)} to {P(max(r[f] for r in R[k]), 1 if f == 'cagr' else 0)}"
    _save(pd.DataFrame([st("Baseline portfolio", R["main"]), st("Execution one day later", R["delay"]),
                        st("Without the five largest contributors", R["drop_top5"]), st("Bought without a touch", R["no_touch"]),
                        st("Pullbacks counted only once confirmed", R["strict"]),
                        st("New positions only while SPY > 200-day average", R["regime"]),
                        ["Twelve start months in 2015", rng("starts_main", "cagr"), rng("starts_main", "maxdd"), "", ""],
                        ["Twelve start months in 2007 (to 2014)", rng("starts_history", "cagr"), rng("starts_history", "maxdd"), "", ""]],
                       columns=["Test", "Per year", "Worst drawdown", "Sharpe", "Monthly excess [95%]"]), "tableB4_stress")
    # regime and decay (Section 7)
    pp = lambda x: P(x, 2)
    _save(pd.DataFrame([[r["key"], r["name"], U(r["history"]["share_on"]), f"{pp(r['history']['diff'])} {CI(r['history']['ci'])}",
                         U(r["main"]["share_on"]), f"{pp(r['main']['diff'])} {CI(r['main']['ci'])}",
                         f"{pp(r['all']['diff'])} {CI(r['all']['ci'])}", "yes" if r["identified"] else "no"]
                        for r in R["regime_test"]],
                       columns=["", "Indicator", "On, 2007-2014", "On minus off, 2007-2014", "On, 2015-2026",
                                "On minus off, 2015-2026", "On minus off, pooled", "Identified"]), "table6_regime_test")
    sw = R["regime_switch"]
    spy = sw[0]
    _save(pd.DataFrame([[r["name"] if r["key"] == "none" else f"{r['key']}: switch to SPY when off",
                         P(r["history"]["cagr"]), P(r["main"]["cagr"]), P(r["all"]["cagr"]), F(r["all"]["sharpe"]),
                         P(r["all"]["maxdd"], 0), f"{pp(r['all']['excess_m'])} {CI(r['all']['excess_ci'])}"] for r in sw]
                       + [["S&P 500 (SPY)", P(spy["history"]["bench_cagr"]), P(spy["main"]["bench_cagr"]), P(spy["all"]["bench_cagr"]),
                           F(spy["all"]["bench_sharpe"]), P(spy["all"]["bench_dd"], 0), ""]],
                       columns=["Rule", "Per year, 2007-2014", "Per year, 2015-2026", "Per year, 2007-2026", "Sharpe, 2007-2026",
                                "Worst drawdown", "Monthly excess [95%]"]), "table7_regime_switch")
    ch = R["regime_chars"]
    rows = [("Stocks passing the trend screen per day", lambda c: f"{c['trends_per_day']:.0f}"),
            ("Days with SPY above its 200-day average", lambda c: U(c["spy_above_200"])),
            ("Equal-weighted universe minus SPY, per year", lambda c: P(c["ew_minus_spy"])),
            ("Trades", lambda c: c["trades"]), ("Trades in technology", lambda c: U(c["tech"])),
            ("Trades in health care", lambda c: U(c["health"])), ("Median trade", lambda c: P(c["median_trade"])),
            ("Trades returning +50% or more", lambda c: U(c["big_share"], 1)),
            ("Touch minus no touch at 21 days, same month", lambda c: P(c["edge21"]))]
    _save(pd.DataFrame([[lab] + [f(ch[k]) for k in ("history", "insample", "oos")] for lab, f in rows],
                       columns=["Measure", "2007-2014", "2015-2024", "2025-2026"]), "table5_characteristics")
    fw = pd.read_csv(C.OUTPUT / "series" / "forward_positions.csv", parse_dates=["entry", "exit"])
    pd.DataFrame({"#": range(1, len(fw) + 1), "Stock": fw.sym, "Bought": fw.entry.dt.date, "Buy price": fw.buy.round(2),
                  "Sold": [("open" if o else str(x.date())) for o, x in zip(fw.open, fw.exit)],
                  "Price": fw.price.round(2), "Return": fw.ret.map(lambda x: P(x))}).to_csv(C.TABLES / "trades_forward.csv", index=False)
    # calendar-year returns: the portfolio from 2015, the same rules run from 2007, SPY (Appendix A)
    ser = lambda f: pd.read_csv(C.OUTPUT / "series" / f, index_col=0, parse_dates=True).iloc[:, 0]
    yr = lambda s: (s.resample("YE").last() / pd.concat([pd.Series([s.iloc[0]]), s.resample("YE").last().iloc[:-1]]).values - 1)
    cont, main_, spy_ = ser("equity_continuous.csv"), ser("equity.csv"), ser("benchmark.csv")
    ys, yc, ym = yr(spy_.reindex(cont.index).ffill()), yr(cont), yr(main_)
    _save(pd.DataFrame([[f"{d.year}{'*' if d == yc.index[-1] else ''}", P(ym.get(d)) if d in ym.index else "", P(yc[d]), P(ys[d]),
                         P(ym[d] - ys[d]) if d in ym.index else ""] for d in yc.index],
                       columns=["Year", "Portfolio, from 2015", "Same rules, from 2007", "SPY", "Portfolio minus SPY"]),
          "tableA3_years")
    # deflated Sharpe ratio over every variant reported
    eq = pd.read_csv(C.OUTPUT / "series" / "equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    r = eq.pct_change().dropna()
    trials = ([s["sharpe"] for k in ("exits", "slots", "hold", "touch", "span", "costs") for s in R[k]]
              + [R[k]["sharpe"] for k in ("delay", "drop_top5", "no_touch", "regime", "strict")]
              + [r["main"]["sharpe"] for r in R["regime_switch"] if r["key"] != "none"])
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
    comp = dict(long_only=bool((od.weight >= 0).all()), max_weight=float(od.weight.max()), leverage_max=1.0,
                avg_holding_days=float(tr.bars.mean()), execution="signal at close t, fill at open t+1",
                cost_model=f"fees {C.FEE:.2%} + max({C.IMPACT_MIN:.2%}, {C.IMPACT_K:.0%} x sqrt(order / ADV)) per side",
                avg_cost_per_side=float(pd.concat([tr.cost_in, tr.cost_out]).mean()),
                entries=len(buys), entries_within_5pct_adv=float((share <= 0.0505).mean()),
                median_order_share_of_adv=float(np.median(share)),
                note="Each order is capped at 5% of the 60-day median traded value on NAV at the time of the order.")
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
