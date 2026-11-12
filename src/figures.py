"""Figures 1-6 of the paper: one style, full text width (160 mm)."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config as C  # noqa: E402

SERIES, FIG = C.OUTPUT / "series", C.FIGURES
W = 6.3                                    # text width in inches (160 mm)
NAVY, GREY, LIGHT, INK, RED = "#1f3a5f", "#8c8c8c", "#d9dee6", "#222222", "#9b2335"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.edgecolor": INK, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "axes.titlelocation": "left", "axes.titleweight": "bold", "legend.frameon": False,
})
PERIODS = [("2007-01-02", "2017-07-01", "Pre-design period"), ("2017-07-01", "2025-01-01", "Design period"),
           ("2025-01-01", None, "QISC\nout-of-sample")]
pct = lambda d=0: mt.PercentFormatter(1.0, decimals=d)


def shade(ax, end, labels=True, y=0.97):
    for i, (a, b, lab) in enumerate(PERIODS):
        b = pd.Timestamp(b) if b else end
        if i != 1:
            ax.axvspan(pd.Timestamp(a), b, color=LIGHT, alpha=0.55, lw=0, zorder=0)
        if labels:
            mid = pd.Timestamp(a) + (b - pd.Timestamp(a)) / 2
            ax.text(mid, 1.015, lab.replace(chr(10), " "), transform=ax.get_xaxis_transform(), ha="center",
                    va="bottom", fontsize=7.5, color="#555555", style="italic", clip_on=False)


def fig_ema(tr, close, opn):
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 2.35), gridspec_kw={"width_ratios": [1, 1.35]})
    k = np.arange(40)
    alpha = 2 / 21
    a.bar(k, alpha * (1 - alpha) ** k, color=NAVY, width=0.75, label="EMA20 weight")
    a.step(np.r_[k, 40] - 0.5, np.r_[np.where(k < 20, 1 / 20, 0), 0], where="post", color=GREY, ls="--", lw=1,
           label="SMA20 weight")
    a.axvline(np.log(0.5) / np.log(1 - alpha), color=INK, lw=0.6, ls=":")
    a.text(np.log(0.5) / np.log(1 - alpha) + 0.8, 0.088, "half-life\n6.9 days", fontsize=7.5, va="top")
    a.set(xlabel="days ago ($k$)", ylabel="weight on the price $k$ days ago", title="(a) Weights")
    a.legend(loc="upper right")
    # (b) a real entry from the main book: a clean pullback into the band
    t = tr[(tr.ret > 0.25) & (tr.ret < 0.8)].copy()
    t["entry"] = pd.to_datetime(t.entry)
    t = t[(t.entry >= "2019-01-01") & (t.entry < "2025-01-01")]
    best, score = None, -1
    for x in t.itertuples():
        c, o = close[x.sym].dropna(), opn[x.sym].dropna()
        i = c.index.searchsorted(x.entry)
        if i < 80 or i + 30 > len(c):
            continue
        eo_, ec_ = o.ewm(span=20, adjust=False).mean(), c.ewm(span=20, adjust=False).mean()
        width = float((abs(eo_ - ec_) / ec_).iloc[i - 30:i].mean())
        dip = float((c / np.maximum(eo_, ec_) - 1).iloc[i - 6:i].min())
        sc = width - abs(dip)                                  # a visible band, a real touch
        if dip < 0.005 and sc > score:
            best, score = x, sc
    x = best
    c, o = close[x.sym].dropna(), opn[x.sym].dropna()
    eo, ec = o.ewm(span=20, adjust=False).mean(), c.ewm(span=20, adjust=False).mean()
    i = c.index.searchsorted(x.entry)
    sl = slice(i - 70, i + 25)
    cc, up, lo = c.iloc[sl], np.maximum(eo, ec).iloc[sl], np.minimum(eo, ec).iloc[sl]
    b.fill_between(cc.index, lo.reindex(cc.index), up.reindex(cc.index), color=NAVY, alpha=0.25, lw=0,
                   label="band: EMA20 of opens and closes")
    b.plot(cc.index, cc, color=INK, lw=1.1, label="close")
    b.plot(cc.index, ec.reindex(cc.index), color=NAVY, lw=0.8)
    b.plot(cc.index, eo.reindex(cc.index), color=NAVY, lw=0.8, ls="--")
    hiv = np.maximum(eo, ec)
    touch = [k for k in range(i - 6, i) if c.iloc[k] <= hiv.iloc[k] * 1.01]
    b.scatter(c.index[touch], c.iloc[touch], facecolor="white", edgecolor=INK, zorder=5, s=14, lw=0.8,
              label="close in the band (the touch)")
    b.scatter([c.index[i]], [o.iloc[o.index.searchsorted(x.entry)]], color=RED, zorder=6, s=20,
              label="buy at the next open")
    b.set(title=f"(b) An entry: {x.sym}, {pd.Timestamp(x.entry):%B %Y}", ylabel="price (USD)")
    b.xaxis.set_major_locator(matplotlib.dates.MonthLocator(interval=1))
    b.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    b.tick_params(axis="x", labelsize=7)
    b.legend(loc="upper left", fontsize=7.3)
    fig.tight_layout(w_pad=2.5)
    fig.savefig(FIG / "ema_band.png")
    plt.close(fig)


def fig_equity(eq, spy):
    sp = spy.reindex(eq.index).ffill()
    sp = sp / sp.iloc[0]
    fig, (a, b) = plt.subplots(2, 1, figsize=(W, 3.7), sharex=True, gridspec_kw={"height_ratios": [2.3, 1]})
    shade(a, eq.index[-1])
    a.plot(eq.index, eq, color=NAVY, lw=1.3, label="QISC book: EMA20 band system, 10 slots, 10 bp per side")
    a.plot(sp.index, sp, color=GREY, lw=1.0, ls="--", label="S&P 500 (SPY, total return)")
    hi_first = eq.iloc[-1] >= sp.iloc[-1]
    for s, up in ((eq, hi_first), (sp, not hi_first)):
        a.annotate(f"{s.iloc[-1]:.1f}×", (s.index[-1], s.iloc[-1]), xytext=(3, 5 if up else -5),
                   textcoords="offset points", fontsize=7.5, va="center")
    a.set_yscale("log")
    a.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:g}"))
    a.set_ylabel("growth of \\$1 (log scale)")
    a.legend(loc="upper left", bbox_to_anchor=(0, 0.88))
    a.grid(axis="y", color="#e6e6e6", lw=0.5)
    dd, sd = eq / eq.cummax() - 1, sp / sp.cummax() - 1
    shade(b, eq.index[-1], labels=False)
    b.fill_between(dd.index, dd, 0, color=NAVY, alpha=0.45, lw=0, label="system")
    b.plot(sd.index, sd, color=GREY, lw=0.8, ls="--", label="SPY")
    b.yaxis.set_major_formatter(pct())
    b.set_ylabel("drawdown")
    b.set_xlim(eq.index[0], eq.index[-1])
    fig.tight_layout(h_pad=0.4)
    fig.savefig(FIG / "equity.png")
    plt.close(fig)


def fig_paths():
    fig, ax = plt.subplots(figsize=(W, 2.3))
    for kind, col, lab, ls, lw in (("touch", NAVY, "top ten, bought on a band touch (the entry rule)", "-", 1.6),
                                   ("no_touch", GREY, "top ten, bought on a day without a touch", "--", 1.1)):
        p = pd.read_csv(SERIES / f"path_{kind}.csv", index_col=0)
        ax.plot(p.index, p["mean"], color=col, ls=ls, lw=lw, label=lab)
        ax.text(p.index[-1] + 1, p["mean"].iloc[-1], f"{p['mean'].iloc[-1]:+.1%}", fontsize=7.5, va="center")
    ax.axhline(0, color=INK, lw=0.5)
    ax.set(xlim=(0, 70), xlabel="trading days after entry", ylabel="mean return")
    ax.yaxis.set_major_formatter(pct())
    ax.legend(loc="upper left")
    fig.savefig(FIG / "path.png")
    plt.close(fig)


def fig_trades(tr):
    r = tr.ret
    fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.hist(r.clip(-1, 2), bins=np.linspace(-1, 2, 37), color=NAVY, edgecolor="white", lw=0.8)
    ax.axvline(0, color=INK, lw=0.6)
    ax.axvline(r.mean(), color=RED, lw=0.9, ls=":")
    ax.axvline(r.median(), color=GREY, lw=0.9, ls="--")
    top = ax.get_ylim()[1]
    ax.text(r.mean(), top * 0.92, f"  mean {r.mean():+.1%}", fontsize=7.5, color=RED, ha="left")
    ax.text(r.median(), top * 0.92, f"median {r.median():+.1%}  ", fontsize=7.5, color="#555555", ha="right")
    ax.xaxis.set_major_formatter(pct())
    ax.set(xlabel="return of each trade over its holding period, after costs (clipped at +200%)", ylabel="trades")
    fig.savefig(FIG / "trades_hist.png")
    plt.close(fig)


def fig_years():
    y = pd.read_csv(SERIES / "yearly.csv", index_col=0, parse_dates=True)
    fig, ax = plt.subplots(figsize=(W, 2.3))
    x = np.arange(len(y))
    ax.bar(x - 0.2, y.system, 0.4, color=NAVY, label="system")
    ax.bar(x + 0.2, y.benchmark, 0.4, color=GREY, label="SPY")
    ax.axhline(0, color=INK, lw=0.5)
    ax.set_xticks(x, [f"{d.year}{'*' if d == y.index[-1] else ''}" for d in y.index], rotation=0, fontsize=6.6)
    ax.yaxis.set_major_formatter(pct())
    ax.set_ylabel("calendar-year return")
    ax.legend(loc="upper left", ncol=2)
    fig.savefig(FIG / "years.png")
    plt.close(fig)


def fig_robust(R):
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.15), sharey=True)
    specs = [("slots", "K", "number of slots", None), ("hold", "H", "holding period (trading days)", None),
             ("costs", "cost", "cost per side", pct(2))]
    for ax, (key, col, lab, fmt) in zip(axes, specs):
        rows = R[key]
        xs = [r[col] for r in rows]
        xi = np.arange(len(xs))
        ax.plot(xi, [r["ratio"] for r in rows], color=NAVY, marker="o", ms=3.5, lw=1.2, label="full period")
        ax.plot(xi, [r["by_period"]["oos"] for r in rows], color=RED, marker="s", ms=3, lw=0.9, ls=":",
                label="QISC out-of-sample")
        ax.plot(xi, [r["by_period"]["pre"] for r in rows], color=GREY, marker="^", ms=3, lw=0.9, ls="--",
                label="pre-design")
        ax.set_xticks(xi, [f"{v:.2%}" if fmt else f"{v:g}" for v in xs], fontsize=7.3)
        ax.set_xlabel(lab)
        ax.axhline(0, color=INK, lw=0.4)
    axes[0].set_ylabel("CAGR ÷ |max drawdown|")
    axes[0].legend(loc="upper left", fontsize=7)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(FIG / "robust.png")
    plt.close(fig)


def run():
    FIG.mkdir(parents=True, exist_ok=True)
    R = json.load(open(C.OUTPUT / "results.json"))
    eq = pd.read_csv(SERIES / "equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    tr = pd.read_csv(SERIES / "trades.csv")
    bench = pd.read_csv(SERIES / "benchmark.csv", index_col=0, parse_dates=True).iloc[:, 0]
    close = pd.read_parquet(C.DATA / "wide_close.parquet")
    opn = pd.read_parquet(C.DATA / "wide_open.parquet")
    fig_ema(tr, close, opn)
    fig_equity(eq, bench)
    fig_paths()
    fig_trades(tr)
    fig_years()
    fig_robust(R)
    print(f"  6 figures -> {FIG.relative_to(C.ROOT)}")
