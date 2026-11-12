"""Universe, price download and cleaning.

Universe: every security in the NASDAQ Trader symbol directory listed on NASDAQ, NYSE,
NYSE American or NYSE Arca, excluding ETFs, test issues, warrants, rights, units,
preferreds and notes. Prices: Yahoo Finance daily OHLCV, split- and dividend-adjusted.

Survivors only: the directory lists stocks that trade today (see the paper, Section 3.3).
"""
from __future__ import annotations

import io
import time

import numpy as np
import pandas as pd
import requests

import config as C

SYMBOL_FILES = ["https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
                "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"]
EXCLUDE = ("warrant", "right", " unit", "units", "preferred", "notes", "debenture",
           "% ", "depositary share representing", "etn", "fund", "trust preferred")
FIELDS = ("open", "high", "low", "close", "volume")
BATCH = 100


def universe() -> pd.DataFrame:
    """Today's listed common stocks, ADRs and LPs, with Yahoo Finance symbols."""
    rows = []
    for url in SYMBOL_FILES:
        txt = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
        df = pd.read_csv(io.StringIO(txt), sep="|")
        df = df[~df.iloc[:, 0].astype(str).str.startswith("File Creation Time")]
        sym = "Symbol" if "Symbol" in df.columns else "ACT Symbol"
        df = df.rename(columns={sym: "symbol", "Security Name": "name"})
        rows.append(df.loc[(df["Test Issue"] == "N") & (df["ETF"] == "N"), ["symbol", "name"]])
    u = pd.concat(rows).drop_duplicates("symbol")
    u = u[u.symbol.astype(str).str.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?")]
    name = u.name.astype(str).str.lower()
    u = u[~name.apply(lambda s: any(w in s for w in EXCLUDE))]
    u["yf"] = u.symbol.str.replace(".", "-", regex=False)
    return u.reset_index(drop=True)


SCREENER = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true"
FUND_INDUSTRIES = ("Investment Managers", "Trusts Except Educational Religious and Charitable",
                   "Finance/Investors Services", "Finance Companies", "Investment Bankers/Brokers/Service",
                   "Finance: Consumer Services")


def screener(refresh: bool = False) -> pd.DataFrame:
    """Nasdaq stock screener: country, sector and industry of every listed stock."""
    f = C.DATA / "nasdaq_screener.csv"
    if f.exists() and not refresh:
        return pd.read_csv(f, keep_default_na=False)
    r = requests.get(SCREENER, timeout=60, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    df = pd.DataFrame(r.json()["data"]["rows"])
    df.to_csv(f, index=False)
    return df.fillna("")


def excluded_tickers() -> set[str]:
    """Instrument filter: keep US companies, drop closed-end funds.
    Names missing from the screener are kept (they may have been delisted)."""
    u = pd.read_csv(C.DATA / "universe.csv")
    s = screener()
    s["yf"] = s.symbol.astype(str).str.replace("/", "-")
    u = u.merge(s[["yf", "country", "sector", "industry"]], on="yf", how="left")
    fundlike = u.name.astype(str).str.contains(r"Trust|Beneficial Interest|STRATS|Municipal|Fixed-Income", case=False, regex=True)
    finance = u.industry.isin(FUND_INDUSTRIES) | (u.sector.fillna("") == "Finance") & ~u.industry.fillna("").str.contains("Real Estate")
    foreign = u.country.fillna("").ne("") & u.country.ne("United States")
    return set(u.loc[(fundlike & finance) | foreign, "yf"])


def _fetch(batch: list[str]) -> pd.DataFrame:
    import yfinance as yf
    h = yf.download(batch, start=C.DOWNLOAD_START, auto_adjust=True, group_by="ticker",
                    threads=True, progress=False, actions=False)
    out = []
    for s in batch:
        try:
            sub = (h[s] if len(batch) > 1 else h).dropna(how="all")
        except KeyError:
            continue
        if sub.empty:
            continue
        sub = sub.rename(columns=str.lower)[list(FIELDS)].reset_index().rename(columns={"Date": "date"})
        sub["ticker"] = s
        out.append(sub)
    return pd.concat(out) if out else pd.DataFrame()


def download(refresh: bool = False) -> None:
    """data/panel.parquet: long table date, ticker, open, high, low, close, volume. Resumable."""
    panel = C.DATA / "panel.parquet"
    if panel.exists() and not refresh:
        print(f"  using cached {panel.name}")
        return
    raw = C.DATA / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    u = universe()
    u.to_csv(C.DATA / "universe.csv", index=False)
    screener(refresh=True)
    syms = sorted(u.yf) + [C.BENCHMARK]
    n = (len(syms) + BATCH - 1) // BATCH
    print(f"  {len(syms)} symbols, {n} batches")
    for k in range(n):
        f = raw / f"b{k:03d}.parquet"
        if f.exists():
            continue
        for attempt in range(3):
            try:
                _fetch(syms[k * BATCH:(k + 1) * BATCH]).to_parquet(f)
                print(f"  batch {k + 1}/{n}", flush=True)
                break
            except Exception as e:                      # rate limit or network: wait and retry
                print(f"  batch {k + 1} attempt {attempt + 1} failed: {e}", flush=True)
                time.sleep(30 * (attempt + 1))
    df = pd.concat([p for p in (pd.read_parquet(f) for f in sorted(raw.glob("b*.parquet"))) if len(p)])
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df.to_parquet(panel)
    print(f"  panel: {df.ticker.nunique()} tickers, {len(df):,} rows, {df.date.min().date()} to {df.date.max().date()}")


def sanitize(px: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Zero or negative prices -> missing; an open more than GAP_LIMIT x from its close -> missing.
    Nothing is forward-filled."""
    c = px["close"].where(px["close"] > 0)
    o = px["open"].where(px["open"] > 0)
    r = c / o
    o = o.where(r.isna() | ((r >= 1 / C.GAP_LIMIT) & (r <= C.GAP_LIMIT)))
    out = dict(px, close=c, open=o)
    for f in ("high", "low"):
        out[f] = out[f].where(out[f] > 0)
    return out


def build_wide(refresh: bool = False) -> None:
    """data/wide_<field>.parquet: date x ticker, cleaned, restricted to names that can ever pass the screen."""
    if (C.DATA / "wide_close.parquet").exists() and not refresh:
        print("  using cached wide panels")
        return
    df = pd.read_parquet(C.DATA / "panel.parquet")
    df = df[df.ticker.notna()].drop_duplicates(["date", "ticker"])
    px = {f: df.pivot(index="date", columns="ticker", values=f).sort_index().astype("float64") for f in FIELDS}
    del df
    px = sanitize(px)
    dv = (px["close"] * px["volume"]).rolling(60).median()
    ok = (dv.max() >= C.LIQ_SCREEN) & (px["close"].max() >= C.MIN_PRICE)
    ok[C.BENCHMARK] = True
    for f, v in px.items():
        v.loc[:, ok[ok].index].to_parquet(C.DATA / f"wide_{f}.parquet")
    print(f"  wide panels: {int(ok.sum()) - 1} stocks + {C.BENCHMARK}")


def load_wide(fields=("open", "close", "volume")) -> tuple[dict[str, pd.DataFrame], pd.Series]:
    px = {f: pd.read_parquet(C.DATA / f"wide_{f}.parquet") for f in fields}
    bench = px["close"][C.BENCHMARK].copy()
    for f in px:
        px[f] = px[f].drop(columns=C.BENCHMARK)
    return px, bench


def traded_value(close: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
    """60-day median traded value in USD, used by both liquidity gates."""
    return (close * vol).rolling(60).median()


def first_valid_rows(a: np.ndarray) -> np.ndarray:
    return np.argmax(np.isfinite(a), axis=0)
