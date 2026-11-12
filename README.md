# qisc-tester

Code repository for the QISC 2027 Preliminary Round submission
**"Buying the Pullback in the Cleanest Trends: An EMA Band Strategy for the Current US Equity Regime"**
(Team Tester, Arena: United States).

One command reproduces every table, figure and number in the paper, plus the files the competition requires:

```bash
pip install -r requirements.txt
python run.py
```

A first run downloads about 17 million daily prices and takes roughly 30 minutes; later runs reuse the cache in `data/` and take about 12 minutes.

## The strategy

Each day, rank US stocks by the quality of their current trend: the run's return divided by its average pullback (R/R). Among the five highest-ranked stocks, buy one at the next open when, within the last five sessions, its close fell into the band between the 20-day EMA of opens and the 20-day EMA of closes (or came within 1% above it), and today it closed back above the band. Hold every position for 63 trading days, then sell at the open. Five positions of 20% of equity, long-only and unlevered. Every order is capped at 5% of the stock's 60-day median traded value and pays the casebook cost model: 0.05% fees plus market impact of max(0.05%, 1% × √(order ÷ ADV)) per side.

## Results

Main sample: January 2015 to 11 November 2026, the casebook's backtest period.

| | Portfolio | S&P 500 (SPY) |
|---|---|---|
| Growth per year, 2015–2026 | +22.1% | +13.5% |
| Growth of $1 | $10.6 | $4.5 |
| Sharpe ratio | 0.75 | 0.81 |
| Worst drawdown | −43% | −34% |
| Monthly return above SPY [95% interval] | +0.97% [−0.50%, +2.54%] | |
| Growth per year, QISC out-of-sample (2025–2026) | +28.3% | +16.1% |
| 2026 to date | +196.4% | +11.7% |
| Forward test, 19 Sep to 11 Nov 2026 (after the rules were fixed) | −7.9% | −0.7% |
| Growth per year, same rules before the sample (2007–2014) | −1.1% | +7.0% |

The strategy works in the current regime but not before it, and its excess return is not statistically significant. The deflated Sharpe ratio across the 51 variants reported is 0.96. The forward test is short; one in five 38-day windows since 2015 was as bad. The pre-registered regime tests (`REGIME_PROTOCOL.md`, paper Section 7) find that market trend, the supply of clean trends and small-cap leadership point the right way in both decades but are not significant on their own, and that switching out after poor performance destroys value. The effect that survives every test is the pullback entry: within the same month, entries on a band touch beat entries into the same trends without one by +1.6 points over five days [+0.7, +2.6] and +5.1 points over 63 days [+1.7, +8.9].

## Repository layout

```
qisc-tester/
├── README.md
├── requirements.txt
├── REGIME_PROTOCOL.md     the regime and decay tests, written and committed before they were run
├── config.py              every parameter of the study, in one place
├── run.py                 single entry point: data -> scores -> tests -> tables -> figures -> paper
├── src/
│   ├── data.py            symbol directory, Nasdaq screener, Yahoo Finance prices, cleaning
│   ├── signals.py         EMA band, trend runs, zigzag pullbacks, R/R score, band-touch signal
│   ├── backtest.py        portfolio simulator, performance statistics, deflated Sharpe ratio
│   ├── events.py          event study: touch versus no-touch entries
│   ├── regime.py          regime indicators, walk-forward switching rules, decay monitors
│   ├── experiments.py     the portfolio, the forward test, the cost decomposition, the regime tests and every robustness test
│   ├── report.py          tables, positions.csv, trades.csv, compliance check
│   └── figures.py         the paper's figures
├── tests/
│   └── test_signals.py    unit tests (pytest, or: python tests/test_signals.py)
├── paper/
│   ├── manuscript.md      the paper; rendered to output/paper.pdf by run.py
│   └── qisc_render.py     Markdown -> PDF (headless Microsoft Edge)
├── data/                  downloaded and derived data (not committed; rebuilt by run.py)
└── output/
    ├── positions.csv      REQUIRED by QISC: daily target weights
    ├── trades.csv         every trade of the baseline portfolio
    ├── results.json       every statistic reported in the paper
    ├── numbers.json       deflated Sharpe ratio and number of trials
    ├── compliance.json    checks against the casebook constraints
    ├── tables/            Tables 3-7, A.1-A.3 and B.1-B.4 as .csv and .md, appendix trade lists
    ├── figures/           figures, including cumulative returns versus SPY (.png, 300 dpi)
    └── paper.pdf          the rendered paper
```

## Output files

**`output/positions.csv`** follows the casebook format. One row per order: `date` is the trading day on whose close the decision is made, `ticker` is the Yahoo Finance symbol, `weight` is the target weight as a fraction of NAV. A weight of `0` closes the position. Weights dated *t* are executed at the open of *t*+1; between rows, positions are held and drift with prices.

```
date,ticker,weight
2015-01-02,PANW,0.2
2015-01-05,LUV,0.2
```

**`output/trades.csv`** lists every trade with entry and exit dates, the adjusted opens at which it was bought and sold, the exit reason, the holding period and the return after costs.

**`output/compliance.json`** checks the portfolio against the casebook rules: long-only, no leverage, execution at the next open, the cost model and the average cost actually paid (0.18% per side), and the share of orders within 5% of the stock's 60-day median traded value, measured on NAV at the time of the order (all of them, up to rounding of the weights). The median order is 1.8% of that traded value.

## Data

| Source | Used for | Access |
|---|---|---|
| NASDAQ Trader symbol directory (`nasdaqlisted.txt`, `otherlisted.txt`) | The universe of listed securities | Free |
| Nasdaq stock screener | Company country and industry (US companies only, no closed-end funds) | Free |
| Yahoo Finance via `yfinance` | Daily open, high, low, close, volume, adjusted for splits and dividends; SPY | Free |

All data are public. The download is resumable: if Yahoo Finance rate-limits a batch, the script waits and retries, and a second run continues where the first stopped.

## Choices that matter

- **Sample design.** The main sample is 2015–2026. The rules were developed on data from July 2017 to 18 September 2026, so the QISC out-of-sample window overlaps the development data; the clean evidence is the forward test after 18 September 2026 and the same rules over 2007–2014 (paper, Section 3.2).
- **Regime tests.** `REGIME_PROTOCOL.md` was committed before the tests in `src/regime.py` were run; the paper reports every indicator and rule it lists.
- **Survivors only.** The symbol directory lists stocks that trade today, so delisted companies are missing. This flatters the strategy, more so in early years (paper, Section 3.3).
- **US companies only.** In a concentrated portfolio this filter matters, because foreign listings and closed-end funds would otherwise take scarce positions (paper, Section 3.1).
- **One use of later prices.** A pullback whose low lies before day *t* is counted even if the rebound that confirms it occurs after *t*. Setting `STRICT_PIT = True` in `config.py` removes this; the paper reports both (Section 6.4).
- **Costs and liquidity.** The casebook cost model with square-root market impact, and orders capped at 5% of ADV on a book that starts at $1 million and compounds. Both lower the return of a concentrated strategy; the paper reports the effect of each (Table A.2) and of two to five times the costs (Table B.2).

## Tests

`tests/test_signals.py` checks the EMA weights and half-life, the band, the zigzag and its confirmation dates, the run start, the touch signal, and the simulator's holding period, costs, position sizes and the liquidity cap, and the timing of the regime switching rule.
