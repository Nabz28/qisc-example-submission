# qisc-[team-name]

Code repository for the QISC 2027 Preliminary Round submission
**"Buying the Pullback in the Cleanest Trends: An EMA Band Strategy for US Equities, 2007–2026"**
(Team [Team Name], Arena: United States).

One command reproduces every table, figure and number in the paper, plus the files the competition requires:

```bash
pip install -r requirements.txt
python run.py
```

A first run downloads about 17 million daily prices and takes roughly 30 minutes; later runs reuse the cache in `data/` and take about 12 minutes.

## The strategy

Each day, rank US stocks by the quality of their current trend: the run's return divided by its average pullback (R/R). Among the ten highest-ranked stocks, buy one at the next open when, within the last five sessions, its close fell into the band between the 20-day EMA of opens and the 20-day EMA of closes (or came within 1% above it), and today it closed back above the band. Hold every position for 63 trading days, then sell at the open. Ten positions of 10% of equity, long-only, 10 bp per side.

## Results

| | Baseline portfolio | S&P 500 (SPY) |
|---|---|---|
| Growth per year, 2007–2026 | +12.4% | +10.8% |
| Sharpe ratio | 0.54 | 0.62 |
| Worst drawdown | −58% | −55% |
| Monthly return above SPY [95% interval] | +0.29% [−0.48%, +1.05%] | |
| Growth per year, held-out decade (2007–2017) | +6.3% | +7.5% |
| Growth per year, QISC out-of-sample (2025–2026) | +10.7% | +16.1% |

A concentrated five-position variant earns +39.1% a year over its July 2017 to September 2026 development sample, but +13.6% over 2007–2026. The effect that survives every test is the pullback entry: within the same month, entries on a band touch beat entries into the same trends without one by +1.1 points over five days [+0.7, +1.5] and +2.3 points over 63 days [+1.0, +3.5], including in the held-out decade.

## Repository layout

```
qisc-[team-name]/
├── README.md
├── requirements.txt
├── config.py              every parameter of the study, in one place
├── run.py                 single entry point: data -> scores -> tests -> tables -> figures -> paper
├── src/
│   ├── data.py            symbol directory, Nasdaq screener, Yahoo Finance prices, cleaning
│   ├── signals.py         EMA band, trend runs, zigzag pullbacks, R/R score, band-touch signal
│   ├── backtest.py        portfolio simulator, performance statistics, deflated Sharpe ratio
│   ├── events.py          event study: touch versus no-touch entries
│   ├── experiments.py     the concentrated variant, the baseline portfolio and every robustness test
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
    ├── tables/            Tables 3-6 and B.1-B.3 as .csv and .md, appendix trade lists
    ├── figures/           figures, including cumulative returns versus SPY (.png, 300 dpi)
    └── paper.pdf          the rendered paper
```

## Output files

**`output/positions.csv`** follows the casebook format. One row per order: `date` is the trading day on whose close the decision is made, `ticker` is the Yahoo Finance symbol, `weight` is the target weight as a fraction of NAV. A weight of `0` closes the position. Weights dated *t* are executed at the open of *t*+1; between rows, positions are held and drift with prices.

```
date,ticker,weight
2007-01-03,ALB,0.1
2007-04-04,ALB,0.0
```

**`output/trades.csv`** lists every trade with entry and exit dates, the adjusted opens at which it was bought and sold, the exit reason, the holding period and the return after costs.

**`output/compliance.json`** checks the portfolio against the Arena B constraints: long-only, at most 10% of NAV per name, average holding period of at least five days, costs of at least 10 bp per side, and the share of entries that stay within 5% of the stock's 60-day median traded value. Positions are sized on a compounding book that starts at $1 million: 97% of entries meet the 5% limit while the book is below $2 million and 90% over the whole sample, because the limit binds as the book grows (paper, Section 7).

## Data

| Source | Used for | Access |
|---|---|---|
| NASDAQ Trader symbol directory (`nasdaqlisted.txt`, `otherlisted.txt`) | The universe of listed securities | Free |
| Nasdaq stock screener | Company country and industry (US companies only, no closed-end funds) | Free |
| Yahoo Finance via `yfinance` | Daily open, high, low, close, volume, adjusted for splits and dividends; SPY | Free |

All data are public. The download is resumable: if Yahoo Finance rate-limits a batch, the script waits and retries, and a second run continues where the first stopped.

## Choices that matter

- **Sample design.** The rules were developed on data from July 2017 onward; 2007–2017 is held out. The QISC out-of-sample window (2025–2026) overlaps the development data (paper, Section 3.2).
- **Survivors only.** The symbol directory lists stocks that trade today, so delisted companies are missing. This flatters the strategy, more so in early years (paper, Section 3.3).
- **US companies only.** In a concentrated portfolio this filter matters: without it, the five-position variant earns +33.7% instead of +39.1% a year over its development sample, because foreign listings take scarce positions (paper, Section 5.1).
- **One use of later prices.** A pullback whose low lies before day *t* is counted even if the rebound that confirms it occurs after *t*. Setting `STRICT_PIT = True` in `config.py` removes this; the paper reports both (Section 6.4).
- **Costs.** 10 bp per side, the casebook minimum for the US arena: 5 bp fees and 5 bp slippage.

## Tests

`tests/test_signals.py` checks the EMA weights and half-life, the band, the zigzag and its confirmation dates, the run start, the touch signal, and the simulator's holding period, costs and position sizes.
