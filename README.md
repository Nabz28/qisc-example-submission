# qisc-[team-name]

Code repository for the QISC 2027 Preliminary Round submission
**"Buying the Pullback in the Cleanest Trends: A Replication and Twenty-Year Evaluation of the EMA20 Band System"**
(Team [Team Name], Arena: United States).

One command reproduces every table, figure and number in the paper, plus the files the competition requires:

```bash
pip install -r requirements.txt
python run.py
```

A first run downloads about 17 million daily prices and takes roughly 30 minutes; later runs reuse the cache in `data/` and take a few minutes.

## The strategy in one paragraph

Each day, rank US stocks by the quality of their current trend: the run's return divided by its average pullback (R/R). Take the ten highest-ranked stocks. Buy one at the next open when, within the last five sessions, its close fell into the band between the 20-day EMA of opens and the 20-day EMA of closes (or came within 1% above it), and today it closed back above the band. Hold every position for 63 trading days, then sell at the open. Ten positions of 10% of equity, long-only, 10 bp per side. The rules are those of SEE Lab (2026); the paper replicates them and tests them under the QISC constraints from January 2007 to November 2026.

## Results

| | QISC book | S&P 500 (SPY) |
|---|---|---|
| Growth per year, 2007–2026 | +12.4% | +10.8% |
| Sharpe ratio | 0.54 | 0.62 |
| Worst drawdown | −58% | −55% |
| Monthly return above SPY [95% interval] | +0.29% [−0.48%, +1.05%] | |
| Growth per year, QISC out-of-sample (2025–2026) | +10.7% | +16.1% |

The replication of the original specification (five slots, 5 bp, July 2017 to September 2026) gives 171 trades and +39.1% a year, against 170 trades and +41.9% in the original paper. The one effect that survives every test is the pullback entry: within the same month, entries on a band touch beat entries into the same trends without one by +1.1 points over five days [+0.7, +1.5] and +2.3 points over 63 days [+1.0, +3.5], including in the decade before the rules were designed. See the paper for everything else.

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
│   ├── experiments.py     the replication, the QISC book and every robustness test
│   ├── report.py          tables, positions.csv, trades.csv, compliance check
│   └── figures.py         Figures 1-6
├── tests/
│   └── test_signals.py    unit tests (pytest, or: python tests/test_signals.py)
├── paper/
│   ├── manuscript.md      the paper; rendered to output/paper.pdf by run.py
│   └── qisc_render.py     Markdown -> PDF (headless Microsoft Edge)
├── data/                  downloaded and derived data (not committed; rebuilt by run.py)
└── output/
    ├── positions.csv      REQUIRED by QISC: daily target weights
    ├── trades.csv         every trade of the QISC book
    ├── results.json       every statistic reported in the paper
    ├── numbers.json       deflated Sharpe ratio and number of trials
    ├── compliance.json    checks against the casebook constraints
    ├── tables/            Tables 3-6 and B.1-B.3 as .csv and .md, appendix trade lists
    ├── figures/           Figures 1-6 (.png, 300 dpi)
    └── paper.pdf          the rendered paper
```

## Output files

**`output/positions.csv`** follows the casebook format. One row per order: `date` is the trading day on whose close the decision is made, `ticker` is the Yahoo Finance symbol, `weight` is the target weight as a fraction of NAV. A weight of `0` closes the position. Weights dated *t* are executed at the open of *t*+1; between rows, positions are held and drift with prices.

```
date,ticker,weight
2007-01-03,XXXX,0.1
2007-04-04,XXXX,0.0
```

**`output/trades.csv`** lists every trade with entry and exit dates, the adjusted opens at which it was bought and sold, the exit reason, the holding period and the return after costs.

**`output/compliance.json`** checks the book against the Arena B constraints: long-only, at most 10% of NAV per name, average holding period of at least five days, costs of at least 10 bp per side, and the share of entries that stay within 5% of the stock's 60-day median traded value. Positions are sized on a compounding book that starts at $1 million: 97% of entries meet the 5% limit while the book is below $2 million and 90% over the whole sample, because the limit binds as the book grows (paper, Section 7).

## Data

| Source | Used for | Access |
|---|---|---|
| NASDAQ Trader symbol directory (`nasdaqlisted.txt`, `otherlisted.txt`) | The universe of listed securities | Free |
| Nasdaq stock screener | Company country and industry (US companies only, no closed-end funds) | Free |
| Yahoo Finance via `yfinance` | Daily open, high, low, close, volume, adjusted for splits and dividends; SPY | Free |

All data are public; nothing proprietary is used. The download is resumable: if Yahoo Finance rate-limits a batch, the script waits and retries, and a second run continues where the first stopped.

## Choices that matter

- **Survivors only.** The symbol directory lists stocks that trade today, so delisted companies are missing. This flatters the strategy, more so in early years (paper, Section 3.4).
- **US companies only.** The original code restricts the universe to companies located in the United States. Skipping this filter lowers the replicated return from +39.1% to +33.7% a year, because foreign listings take slots (paper, Section 5.1).
- **One use of later prices.** As in the original code, a pullback whose low lies before day *t* is counted even if the rebound that confirms it occurs after *t*. Setting `STRICT_PIT = True` in `config.py` removes this; the paper reports both (Section 6.4).
- **Costs.** 10 bp per side, the casebook minimum for the US arena: 5 bp fees and 5 bp slippage.

## Verification

`src/signals.py` is a clean re-implementation of the original rules. On the same price panel it reproduces the original code's score matrix exactly (253,161 non-zero scores, maximum difference 0). The unit tests in `tests/` check the EMA weights, the band, the zigzag and its confirmation dates, the run start, the touch signal and the simulator's holding period and costs.

## Credits

Trading rules: SEE Lab (2026), *The EMA20 band momentum system: top five trends, bought on the pullback, held for three months*. Working paper, October 2026. This repository re-implements the rules from their specification and tests them; it does not include the original code.
