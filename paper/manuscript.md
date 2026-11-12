---
kicker: QISC 2027 · Preliminary Round Submission
title: Buying the Pullback in the Cleanest Trends: An EMA Band Strategy for US Equities, 2007–2026
authors: [Full Name]^1, [Full Name]^2, [Full Name]^3
affiliations: 1 [Faculty], [University], [City], Indonesia || 2 [Faculty], [University], [City], Indonesia || 3 [Faculty], [University], [City], Indonesia
meta: Team [Team Name] · Arena: United States · Benchmark: S&P 500 total return (SPY) · January 2007 to November 2026
keywords: Momentum; Short-term reversal; Exponential moving average; Transaction costs; Out-of-sample testing; Multiple testing
abstract: We study a long-only US equity strategy that holds five stocks with the cleanest trends, buys each when its price pulls back into the band between the 20-day exponential moving averages of opens and closes, and sells after 63 trading days. Under the QISC cost model, with fees, square-root market impact and every order capped at 5% of the stock's daily traded value, it earns 28.4% a year over its July 2017 to September 2026 development sample. Over January 2007 to November 2026, which adds a decade not used in development, it earns 10.9% a year against 10.8% for the S&P 500, with a lower Sharpe ratio (0.48 against 0.62) and a 64% drawdown. It loses money in the held-out decade, beats the index in the development period and in the 2025–2026 out-of-sample window, and in no period is its excess return statistically different from zero. One component survives every test: within the same month, entries on a band touch beat entries into the same trends without one by 1.2 percentage points over five days and 4.2 points over three months, including in the held-out decade. The pullback entry is a robust timing effect; the portfolio's excess return is not.
titlenote: Submitted to the Quant Investment Strategy Competition (QISC) 2027, Preliminary Round. Every number, table and figure in this paper is produced by `python run.py` in the accompanying code repository (commit `[hash]`).
footer: QISC 2027 | [Team Name] | Arena: United States
---

## Introduction

Buying a strong stock on a dip is among the most widely practised trading ideas and among the least rigorously tested. It combines two well-documented regularities. Over horizons of months, returns continue: stocks that have risen tend to keep rising (Jegadeesh and Titman, 1993; Moskowitz et al., 2012). Over days to weeks, returns partly reverse (Jegadeesh, 1990; Lehmann, 1990). An investor who selects strong trends but times the purchase to a short pullback should, in principle, earn the first premium at a better price because of the second.

We turn this idea into a fully specified, point-in-time strategy and evaluate it as an investor would have to trade it. Each day we rank US stocks by the quality of their current trend, measured as the trend's return divided by its typical pullback. Among the five top-ranked stocks, we buy one when its price dips into the band between the 20-day exponential moving average (EMA) of opens and of closes and then closes back above it, and we sell every position after 63 trading days. Trading costs follow the QISC cost model, with fees and a square-root market-impact term, and every order is capped at 5% of the stock's daily traded value. The rules were developed on data from July 2017 onward. We test them on the decade before, which played no role in their design, and correct for the number of variants we examine.

The evidence separates a robust component from a fragile one. The strategy earns 28.4% a year in its development sample but 10.9% over 2007–2026, against 10.8% for the S&P 500, with a lower Sharpe ratio and a deeper drawdown. It loses money in the held-out decade, and it beats the index in the 2025–2026 out-of-sample window only through a few extreme winners; in no period is its excess return significant. Realistic costs and the liquidity cap account for more than two points a year of the difference from a frictionless backtest. The timing rule, by contrast, holds everywhere: compared within the same month, entries on a band touch outperform entries into the same top-ranked trends without one by 1.2 percentage points over five days and 4.2 points over three months, and both effects are significant in the held-out decade.

Section 2 sets out the economic rationale and hypotheses, Section 3 the data and sample design, and Section 4 the strategy and evaluation methods. Section 5 reports the main results, Section 6 the robustness tests, Section 7 implementation and risk, and Section 8 concludes.

## Economic rationale and hypotheses

### Mechanism

We classify the edge as behavioural, with a liquidity component. Momentum is commonly attributed to investors who underreact to gradually arriving information (Jegadeesh and Titman, 2001), and the disposition effect, the tendency to sell winners too early, is one channel through which such underreaction arises (Shefrin and Statman, 1985; Frazzini, 2006). Short-term reversal, in contrast, is largely compensation for supplying liquidity to investors who need to trade (Lehmann, 1990; Nagel, 2012). A pullback within a strong trend is where the two effects meet: the trend is intact, but the price has been pushed temporarily below it by selling unrelated to the firm's prospects. The counterparty on the entry day is therefore a holder who sells into the dip, such as a trader taking profits, an investor selling a winner too early, or a trend-follower whose stop has been triggered. On the exit day, three months later, the typical counterparty is a later momentum buyer.

### Related evidence

Technical trading rules have a long and contested record. Moving-average rules appeared profitable on the Dow Jones index (Brock et al., 1992), but much of that evidence weakens once the number of rules searched is accounted for (Sullivan et al., 1999) and once transaction costs and false discoveries are controlled (Bajgrowicz and Scaillet, 2012). At the intraday horizon, none of 7,846 popular rules survives a data-snooping correction in US equities (Marshall et al., 2008). Cross-sectional moving-average signals, which compare stocks with each other rather than time a single index, have held up better (Han et al., 2013). Closest to our entry rule, algorithmically identified Fibonacci retracement zones predict price bounces, although the bounce does not by itself imply a profitable strategy (Tsinaslanidis et al., 2022). Machine-learning studies routinely use moving averages and related indicators as inputs (Patel et al., 2015; Sezer and Ozbayoglu, 2018) but rarely evaluate a complete, cost-aware portfolio. Three forces work against a strategy of this kind: momentum crashes in sharp market rebounds and broad sell-offs (Daniel and Moskowitz, 2016), published anomalies decay (McLean and Pontiff, 2016), and rules selected after inspecting a sample tend to overstate their future performance (Harvey et al., 2016).

### Hypotheses

The strategy makes a selection bet and a timing bet, and we test them separately.

*H1 (selection).* Stocks ranked in the top five by trend quality earn a positive return in excess of the equal-weighted eligible universe over the following 63 trading days.

*H2 (timing).* Within the same month, entries into top-ranked stocks on a band touch earn more over the following 5, 21 and 63 trading days than entries into top-ranked stocks without a touch.

*H3 (portfolio).* A five-position portfolio that combines both rules earns a positive return in excess of the S&P 500 after costs, in the held-out decade and in the QISC out-of-sample window, not only in the development period.

## Data and sample design

### Universe and prices

The universe starts from every security in the NASDAQ Trader symbol directory (November 2026) listed on NASDAQ, NYSE, NYSE American or NYSE Arca, excluding exchange-traded funds, test issues, warrants, rights, units, preferred shares and notes. Using the country and industry fields of the Nasdaq stock screener, we keep companies located in the United States and drop closed-end funds, which leaves 4,231 names. Daily open, high, low and close prices and volume come from Yahoo Finance, adjusted for splits and dividends, from January 2005 to 11 November 2026. Of the 4,231 names, 3,793 reach a price of at least $1 and a 60-day median traded value of at least $0.5 million at some point; on an average day about 40 pass the trend screen. The benchmark is SPY with dividends reinvested. Zero and negative prices are set to missing, as is any open more than three times above or below the same day's close; no price is forward-filled. We focus on the US because the screen needs a large universe to find enough clean trends on any given day; the smaller set of liquid IDX stocks, the long-only constraint and auto-rejection limits would leave few candidates.

### Sample design

The rules were developed on data from July 2017 to September 2026. We therefore divide the sample into three periods (Table 1). The scores require 200 trading days of history, so the first decisions are made in January 2007.

| Period | Dates | Role |
|---|---|---|
| Held-out | 3 Jan 2007 to 30 Jun 2017 | Not used in any design decision; the cleanest out-of-sample test |
| Development | 1 Jul 2017 to 31 Dec 2024 | Rules, parameters and filters were chosen on data that include this period |
| QISC out-of-sample | 1 Jan 2025 to 11 Nov 2026 | The final 24 months required by the casebook; overlaps the development data up to September 2026 |

Table: Sample periods.

We report the QISC window separately throughout, as the casebook requires, but treat the held-out decade, which includes the 2008 financial crisis, as the more informative out-of-sample test.

### Survivorship bias

The symbol directory lists only stocks that trade today, so delisted companies are missing. The bias favours the strategy, because the missing stocks are disproportionately those whose trends ended badly, and it grows with distance from the present. Results for the held-out decade are therefore an upper bound, which strengthens any negative conclusion drawn from them.

## Strategy and evaluation

### The EMA band

For a price series $x_t$, the exponential moving average with span $N$ is

$$E_t = \alpha x_t + (1-\alpha)E_{t-1} = \sum_{k\ge 0}\alpha(1-\alpha)^k x_{t-k}, \qquad \alpha = \frac{2}{N+1}. $$ (eq:ema)

With $N = 20$, today's price receives 9.5% of the weight and the weight halves every 6.9 trading days, so $E_t$ approximates the average price paid by the last month's buyers. We compute the EMA on opens ($E^O_t$) and on closes ($E^C_t$) and call the space between them the band, with upper edge $U_t = \max(E^O_t, E^C_t)$ and lower edge $L_t = \min(E^O_t, E^C_t)$. A close above the band is above where recent buyers both started and ended the day (Figure 1).

![(a) The weight that the EMA20 places on the price $k$ days ago, compared with a 20-day simple moving average. (b) An entry in the portfolio: the close falls into the band, then closes back above it, and the stock is bought at the next open.](../output/figures/ema_band.png)

### Trend selection

A run starts on day $r(t)$, the first day after the latest stretch of more than ten consecutive closes below $E^C$. A stock passes the screen on day $t$ if its close is above $E^C_t$ and above the 100-day EMA of closes; the run has lasted at least 60 trading days and gained at least 5% in log terms; it contains at least two completed pullbacks of 5% or more, identified on closes with a zigzag filter; no single day contributes more than 20% of the run's log return and no five days more than 55%; and the price and liquidity floors are met. The last conditions exclude runs built on a few jumps rather than steady accumulation. Stocks that pass are ranked by

$$\text{R/R}_t = \frac{C_t / C_{r(t)} - 1}{\lvert \bar{D}_t \rvert}, $$ (eq:rr)

where $C_t$ is the close and $\bar{D}_t$ the average depth of the completed pullbacks in the current run: the number of its own typical pullbacks the stock has gained. All quantities use prices up to day $t$, with one exception: a pullback whose low lies before $t$ is counted even if the 5% rebound that confirms it occurs after $t$. Section 6.4 removes this exception.

### Entry, exit, sizing and costs

A top-ranked stock generates an entry signal when, within the last five trading days, it closed inside the band or less than 1% above it, and today closes above the band:

$$\min_{s \in [t-4,\,t]} \left( \frac{C_s}{U_s} - 1 \right) \le 1\% \quad \text{and} \quad C_t > U_t. $$ (eq:touch)

Decisions are made at the close of day $t$ and executed at the open of day $t+1$. Each new position receives one fifth of current equity, capped by available cash and by 5% of the stock's 60-day median traded value, measured on a notional book that starts at $1 million and compounds. Every position is sold at the open 63 trading days after entry, and a stock sold in the previous five days cannot be bought again. Each order pays fees of 0.05% and market impact of $\max\left(0.05\%,\; 1\% \times \sqrt{Q / \text{ADV}}\right)$, where $Q$ is the order's value and ADV the 60-day median traded value; an order of 1% of ADV therefore costs 0.15% in total and one of 5% about 0.27%. Uninvested cash earns nothing and the portfolio is not levered. Table 2 lists every parameter.

| Parameter | Value | Definition |
|---|---|---|
| Universe | US companies, no funds | Price at least $1; 60-day median traded value at least $0.5 million |
| Trend | EMA20 and EMA100 | Close above the 20-day and the 100-day EMA of closes |
| Run | > 10 closes; 60 days; +5% | Closes below EMA20 that end a run; minimum length and log return |
| Pullbacks | 2 of at least 5% | Zigzag reversals on closes within the current run |
| Gap filter | 20% / 55% | Maximum share of the run's log return from the best day / best five days |
| Ranking | Top 5 by R/R | Eq. (eq:rr) |
| Entry | 5 days, 1% | Window and tolerance of the band touch, Eq. (eq:touch) |
| Positions | 5 × 20% of equity | Long-only, unlevered |
| Liquidity | 5% of ADV | Maximum order size, on the compounding notional book |
| Exit | 63 trading days | Sold at the open; no other exit |
| Costs | Fees + impact | 0.05% fees; impact max(0.05%, 1% × √(Q / ADV)) per side |

Table: Parameters of the portfolio.

### Evaluation

We report the compound annual growth rate (CAGR), annualised volatility, Sharpe and Sortino ratios, maximum drawdown, the ratio of CAGR to maximum drawdown, and beta and annualised alpha from a regression of monthly returns on SPY. Sharpe ratios are computed from daily returns without subtracting a risk-free rate, for the strategy and the benchmark alike. Confidence intervals for the monthly excess return resample whole months 2,000 times. In the event study, a touch event is the first day of an entry signal for a top-ranked stock and a no-touch event is a day on which a top-ranked stock trends above the band without a recent touch, which corresponds to buying immediately. Returns run from the next open, net of 0.10% per side, and are also measured in excess of the equal-weighted eligible universe. Because no-touch events cluster in strong markets, we compare the two entries within each month and average the monthly differences. Every variant in Section 6 counts as a trial for the deflated Sharpe ratio of Bailey and López de Prado (2014).

## Results

### From the development sample to twenty years

Table 3 shows how much of the development-sample result survives a longer sample. Over July 2017 to September 2026 the strategy earns 28.4% a year against 15.0% for SPY, with the same Sharpe ratio as the index and a monthly excess return whose interval includes zero. Over 2007–2026 it earns 10.9% a year against 10.8%, with a lower Sharpe ratio and a deeper drawdown. A diversified ten-position version earns slightly more over twenty years, 11.5% a year, with a shallower drawdown.

| Measure | Portfolio, 2017–2026 | Portfolio, 2007–2026 | Ten positions, 2007–2026 |
|---|---|---|---|
| Trades | 171 | 361 | 712 |
| Win rate | 56% | 52% | 51% |
| Growth per year (SPY) | +28.4% (+15.0%) | +10.9% (+10.8%) | +11.5% (+10.8%) |
| Sharpe ratio (SPY) | 0.85 (0.85) | 0.48 (0.62) | 0.54 (0.62) |
| Worst drawdown (SPY) | −45% (−34%) | −64% (−55%) | −56% (−55%) |
| Monthly return above SPY | +1.38% | +0.33% | +0.19% |
| 95% interval | [−0.43%, +3.38%] | [−0.73%, +1.38%] | [−0.56%, +0.96%] |
| Cumulative return (SPY) | +896% (+262%) | +686% (+667%) | +766% (+667%) |

Table: The development sample, the full sample and a diversified version.
Note: The first column covers 3 July 2017 to 18 September 2026, the full development sample.

Realistic frictions matter for a concentrated strategy. Table 4 adds them one at a time. With a flat 10 basis points per side and no limit on order size, the same rules earn 13.2% a year. Square-root impact costs remove 0.7 points, and capping each order at 5% of daily traded value removes about 1.5 more, because the strongest trends are often in stocks too thin to absorb a fifth of a growing portfolio.

| Cost and liquidity assumptions | Per year | Worst drawdown | Sharpe | Monthly excess [95%] |
|---|---|---|---|---|
| Flat 10 bp per side, no liquidity cap | +13.2% | −70% | 0.52 | +0.61% [−0.60%, +1.83%] |
| Impact costs, no liquidity cap | +12.5% | −71% | 0.50 | +0.56% [−0.66%, +1.78%] |
| Flat 10 bp per side, orders capped at 5% of ADV | +11.4% | −63% | 0.49 | +0.36% [−0.70%, +1.41%] |
| Impact costs and 5% of ADV cap (the portfolio) | +10.9% | −64% | 0.48 | +0.33% [−0.73%, +1.38%] |

Table: The effect of trading costs and the liquidity cap, January 2007 to November 2026.

### The portfolio by period

Table 5 and Figure 2 report the portfolio over the full sample and in each period. In the held-out decade it loses money, −0.2% a year against +7.5% for SPY, with a drawdown of 64% from October 2007 to October 2008. In the development period it beats the index, 19.3% against 14.4%, but with a lower Sharpe ratio. In the QISC out-of-sample window it earns 28.3% a year against 16.1%, but with a Sharpe ratio of 0.73 against 0.96, a drawdown of 42% against 19%, and an excess-return interval of −3.68% to +7.36% a month. In no period is the excess return distinguishable from zero: H3 is not supported.

| Measure | Full sample | Held-out | Development | QISC out-of-sample |
|---|---|---|---|---|
| *Panel A: Return* | | | | |
| Growth per year (CAGR) | +10.9% | −0.2% | +19.3% | +28.3% |
| S&P 500 growth per year | +10.8% | +7.5% | +14.4% | +16.1% |
| Monthly return above SPY | +0.33% | −0.47% | +0.67% | +1.68% |
| 95% interval | [−0.73%, +1.38%] | [−1.54%, +0.60%] | [−1.18%, +2.62%] | [−3.68%, +7.36%] |
| Alpha per year | +3.5% | −5.1% | +7.2% | +23.7% |
| Cumulative return (SPY) | +686% (+667%) | −2% (+113%) | +274% (+174%) | +59% (+32%) |
| *Panel B: Risk* | | | | |
| Volatility per year | 33.0% | 28.0% | 34.3% | 54.5% |
| Sharpe ratio (SPY) | 0.48 (0.62) | 0.13 (0.45) | 0.68 (0.81) | 0.73 (0.96) |
| Sortino ratio | 0.65 | 0.17 | 0.97 | 1.12 |
| Worst drawdown (SPY) | −64% (−55%) | −64% (−55%) | −45% (−34%) | −42% (−19%) |
| Beta | 1.05 | 0.95 | 1.07 | 0.91 |
| Information ratio | 0.14 | −0.26 | 0.27 | 0.43 |
| *Panel C: Trades* | | | | |
| Trades | 361 | 187 | 138 | 31 |
| Win rate | 52% | 50% | 54% | 55% |
| Average win / average loss | +28.9% / −18.9% | +17.9% / −18.3% | +30.3% / −19.3% | +52.4% / −23.3% |
| Mean / median trade | +6.0% / +1.4% | −0.3% / −0.7% | +7.6% / +2.5% | +18.2% / +3.0% |

Table: Performance of the portfolio, January 2007 to November 2026.
Note: Each period is a separate portfolio that starts in cash. Intervals resample whole months. Alpha and beta are from a regression of monthly returns on SPY. Annual and cumulative returns are in Appendix A.

![Growth of $1 on a log scale (top) and drawdown from the previous peak (bottom), portfolio and SPY. Shaded regions mark the held-out decade and the QISC out-of-sample window.](../output/figures/equity.png)

The portfolio beats SPY in only eight of twenty calendar years. Its returns are concentrated in a few years and a few names: 2020 (+57.0%), 2024 (+51.5%) and 2026 to date (+195.4%), when the largest winners more than doubled or quadrupled. Trade returns are strongly skewed (Figure 3): the median trade earns 1.4% and the mean 6.0%, eleven of 361 trades more than doubled, and 36 lost at least 30%. The ten best trades account for 78% of summed trade returns.

![Return of each trade over its holding period, after costs. Returns above +200% are shown at +200%.](../output/figures/trades_hist.png)

### The timing effect

Table 6 reports the event study. Over 63 trading days, touch entries earn 5.0%, or 2.6 percentage points above the equal-weighted universe, with an interval that excludes zero; no-touch entries into the same top-ranked trends earn 4.4%, or 2.1 points above it, with an interval that just includes zero. The selection effect (H1) is therefore positive but weak, and it is concentrated in the development period: in the held-out decade neither group beats the universe.

| Horizon | Touch: return | Touch: above universe [95%] | No touch: return | No touch: above universe [95%] | Touch minus no touch, same month [95%] |
|---|---|---|---|---|---|
| *Panel A: Full sample* | | | | | |
| 5 days | +0.2% | −0.0% [−0.5%, +0.4%] | −0.1% | −0.3% [−0.6%, +0.0%] | +1.2% [+0.7%, +1.9%] |
| 21 days | +1.5% | +1.0% [−0.1%, +2.1%] | +0.7% | +0.0% [−1.1%, +1.1%] | +2.6% [+1.4%, +3.8%] |
| 63 days | +5.0% | +2.6% [+0.4%, +4.8%] | +4.4% | +2.1% [−0.2%, +4.3%] | +4.2% [+1.8%, +6.8%] |
| *Panel B: By period, 5 days* | | | | | |
| Held-out | −0.0% | −0.4% [−0.9%, +0.0%] | −0.1% | −0.3% [−0.7%, +0.1%] | +1.0% [+0.4%, +1.5%] |
| Development | +0.4% | +0.4% [−0.3%, +1.3%] | −0.2% | −0.3% [−0.9%, +0.1%] | +1.8% [+0.6%, +3.2%] |
| QISC out-of-sample | +0.2% | +0.1% [−1.5%, +1.9%] | +0.1% | −0.0% [−1.4%, +1.2%] | +0.4% [−1.8%, +2.4%] |
| *Panel C: By period, 63 days* | | | | | |
| Held-out | +2.4% | −0.2% [−2.5%, +2.0%] | +0.9% | −1.5% [−3.5%, +0.6%] | +2.8% [+0.1%, +5.4%] |
| Development | +7.3% | +5.2% [+1.9%, +8.9%] | +5.1% | +3.2% [+0.5%, +5.9%] | +5.2% [+1.6%, +9.1%] |
| QISC out-of-sample | +11.8% | +8.6% [−5.5%, +26.8%] | +19.2% | +15.8% [−0.4%, +32.6%] | +7.7% [−5.8%, +26.5%] |

Table: Event study: entries into top-five stocks with and without a band touch.
Note: 2,151 touch and 15,092 no-touch events. Returns run from the next open, net of 0.10% per side. "Above universe" subtracts the equal-weighted return of all eligible stocks over the same days. The last column is the mean over months of the within-month difference between touch and no-touch returns.

The timing effect (H2) is robust. Within the same month, touch entries beat no-touch entries by 1.2 percentage points over five days, 2.6 over 21 days and 4.2 over 63 days, with every interval excluding zero. The effect is significant in the held-out decade, +1.0 points over five days and +2.8 over 63 days, and has the same sign in the out-of-sample window, where less than two years of events leave the intervals wide. In pooled averages (Figure 4) the gap is smaller, 0.6 points at 63 days, because no-touch entries cluster in strong markets.

![Mean cumulative return from the entry open for top-five stocks bought on a band touch and without one, pooled over all events.](../output/figures/path.png)

## Robustness

### Exit rules

A time-based exit is often defended on three grounds: momentum returns accrue slowly, a few large winners carry the strategy, and price-based exits cannot distinguish a pullback from the end of a trend. Table B.1 compares eight alternatives on the same entries. Exits on closes below the band are clearly worse, consistent with that argument. An exit on a heavy-volume down day, however, raises the CAGR from 10.9% to 14.8% and the ratio of CAGR to drawdown from 0.17 to 0.28, and a 25% stop-loss also improves on the time exit. The evidence on stop-losses in long-only portfolios is mixed: they can reduce risk but often at a cost in return (Lei and Li, 2009; Kaminski and Lo, 2014). We do not adopt either alternative, because both were selected after seeing the results and would require their own out-of-sample test.

### Position count, holding period and costs

Figure 5 and Table B.2 vary one parameter at a time. With three positions the portfolio loses 91% at its worst; with five, 64%. Additional positions mainly reduce the drawdown, to 48% with twenty, while the CAGR stays between 9% and 12% for any count from five to twenty. A 42-day holding period earns more than 63 days (12.5% a year), and longer periods earn less. Costs matter moderately: the portfolio trades about 7.3 times its capital a year, counting purchases and sales, at an average of 0.17% per side, so doubling the cost model lowers the CAGR to 10.2% and five times the cost model to 8.1%.

![CAGR divided by the absolute maximum drawdown as one parameter of the portfolio varies, for the full sample, the held-out decade and the QISC out-of-sample window.](../output/figures/robust.png)

### Entry parameters

Table B.3 varies the touch window, the tolerance above the band and the EMA span, with the trend screen unchanged. The baseline setting is not the best cell: requiring a close strictly inside the band raises the CAGR to 18.9%, and the strict touch is the best tolerance for every window. The pattern is not monotonic, however: a 1% tolerance is worse than both 0% and 2% in every window, and the other cells range from 5.0% to 14.7%. A five-position portfolio is path-dependent, since one missed entry changes every later one, so we read the grid as noise around a positive effect rather than evidence for a better parameter, and we do not switch to the strict touch after seeing it. Spans from 10 to 40 days give CAGRs between 7.7% and 13.4%.

### Stress tests

Table 7 reports the stress tests described in the casebook and four further checks. Delaying every trade by one day lowers the return to 10.3% a year. Removing the five largest contributors (AXTI, SNDK, NUTX, APPS and CELH) lowers it to 5.9% and turns the monthly excess return negative. Buying the same stocks without waiting for a touch earns 9.8% over the full sample and loses 12.3% a year in the out-of-sample window, against a gain of 28.3% for the portfolio: the timing rule is what separates the two. Counting pullbacks only once confirmed lowers the return to 9.8%. Starting the portfolio in different months moves the held-out CAGR between −3.3% and +4.9% and the development CAGR between 12.2% and 22.3%.

| Test | Per year | Worst drawdown | Sharpe | Monthly excess [95%] |
|---|---|---|---|---|
| Portfolio | +10.9% | −64% | 0.48 | +0.33% [−0.7%, +1.4%] |
| Execution one day later | +10.3% | −63% | 0.46 | +0.29% [−0.8%, +1.4%] |
| Without the five largest contributors | +5.9% | −64% | 0.34 | −0.16% [−1.1%, +0.8%] |
| Bought without a touch | +9.8% | −69% | 0.44 | +0.22% [−0.8%, +1.2%] |
| Pullbacks counted only once confirmed | +9.8% | −64% | 0.45 | +0.26% [−0.8%, +1.3%] |
| New positions only while SPY is above its 200-day average | +12.0% | −45% | 0.54 | +0.26% [−0.6%, +1.2%] |
| Twelve start months, held-out decade | −3.3% to +4.9% | −49% to −69% | | |
| Twelve start months, development period | +12.2% to +22.3% | −44% to −58% | | |

Table: Stress tests, January 2007 to November 2026.
Note: The market filter is exploratory: it was specified after the 2008 drawdown had been observed and is counted as a trial in Section 6.5.

The market filter is the most tempting fix. Opening positions only while SPY is above its 200-day average, which held on 79% of days, cuts the worst drawdown from 64% to 45% and raises the Sharpe ratio to 0.54, still below SPY's, without creating a significant excess return.

### Multiple testing

Section 6 reports 45 variants, counting the baseline each time it appears. If none had any true edge, the expected maximum annualised Sharpe ratio across 45 trials with the observed dispersion would be 0.20. The deflated Sharpe ratio of the portfolio, the probability that its true Sharpe ratio exceeds that benchmark after allowing for skewness and fat tails, is 0.896, below the conventional 0.95.

## Implementation and risk

**Capacity.** The median order is 1.1% of the stock's 60-day median traded value, and 21% of orders are cut back by the 5% cap. At entry, the median stock bought trades $23.4 million a day and the 5th percentile $1.0 million, where the cap limits a position to about $50,000. The cap binds more as the notional book compounds; a larger book would face a smaller effective universe and higher impact costs.

**Execution.** All trades are market-on-open orders placed after the previous close, so the strategy needs one decision a day. Because every trade happens at the open, returns combine overnight and intraday components, which respond differently to news (Bahcivan, 2025). Average costs are 0.17% per side, most of it market impact in the smaller names.

**Risk.** Beta is 1.05 and volatility 33%, about 1.7 times that of SPY. Investors should expect a drawdown of 50% to 70% and about one trade in ten to lose 30% or more. Losses cluster in market sell-offs and abrupt reversals, the momentum-crash pattern of Daniel and Moskowitz (2016): the worst calendar years are 2008 (−54.7%), 2018, 2022 and 2025, and 2025 is also the worst year relative to the index, 34 points behind it. Volatility scaling, which helps conventional momentum portfolios (Barroso and Santa-Clara, 2015), is a natural next test.

**Kill criteria.** We would stop trading if the drawdown exceeded 70%, beyond any backtest path, or if the month-matched advantage of touch over no-touch entries turned negative over a trailing 24-month window.

## Conclusion

This strategy earns 28.4% a year in the sample on which it was developed. Over twenty years, with realistic costs and a liquidity cap, it earns 10.9% a year against 10.8% for the S&P 500, with more risk and no significant excess return; it loses money in the held-out decade and beats the index after 2017 through a handful of extreme winners. Its design choices, the five-position portfolio and the time-only exit among them, do not carry over to the held-out decade.

The pullback entry does. Waiting for a stock in a strong trend to dip into its 20-day EMA band and close back above it improves the entry by about one percentage point over the following week and four points over three months, relative to buying a comparable stock in the same month without the pullback, before as well as after the development period. We therefore recommend the band touch as an entry filter to combine with other selection rules, rather than the portfolio in its current form, and would test every further refinement, including the exits and market filter in Section 6, on data not used to choose it.

## Statement of Originality and AI Disclosure

We declare that this paper and the accompanying code are the original work of Team [Team Name], that all sources are cited, and that the submission has not been submitted to any other competition. Generative AI was used to assist with programming the data pipeline and with formatting tables and figures. The strategy, the analysis and the written paper are the team's own work, and the team takes full responsibility for the content.

## Code and data availability

The repository `qisc-[team-name]` reproduces every table and figure with one command, `python run.py`. It downloads the symbol directory, the Nasdaq screener and the prices, computes the point-in-time scores, runs every test, and writes the tables, the figures, the trade list and `output/positions.csv` in the format required by the competition. All data are publicly available; a full run takes about 30 minutes, most of it the price download.

## References

REF: Bahcivan, H., 2025. Day and night expected returns under overnight information shocks: new tug-of-war pattern. *Finance Research Letters* 86, 108591.
REF: Bailey, D.H., López de Prado, M., 2014. The deflated Sharpe ratio: correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management* 40 (5), 94–107.
REF: Bajgrowicz, P., Scaillet, O., 2012. Technical trading revisited: false discoveries, persistence tests, and transaction costs. *Journal of Financial Economics* 106 (3), 473–491.
REF: Barroso, P., Santa-Clara, P., 2015. Momentum has its moments. *Journal of Financial Economics* 116 (1), 111–120.
REF: Brock, W., Lakonishok, J., LeBaron, B., 1992. Simple technical trading rules and the stochastic properties of stock returns. *Journal of Finance* 47 (5), 1731–1764.
REF: Daniel, K., Moskowitz, T.J., 2016. Momentum crashes. *Journal of Financial Economics* 122 (2), 221–247.
REF: Frazzini, A., 2006. The disposition effect and underreaction to news. *Journal of Finance* 61 (4), 2017–2046.
REF: Han, Y., Yang, K., Zhou, G., 2013. A new anomaly: the cross-sectional profitability of technical analysis. *Journal of Financial and Quantitative Analysis* 48 (5), 1433–1461.
REF: Harvey, C.R., Liu, Y., Zhu, H., 2016. … and the cross-section of expected returns. *Review of Financial Studies* 29 (1), 5–68.
REF: Jegadeesh, N., 1990. Evidence of predictable behavior of security returns. *Journal of Finance* 45 (3), 881–898.
REF: Jegadeesh, N., Titman, S., 1993. Returns to buying winners and selling losers: implications for stock market efficiency. *Journal of Finance* 48 (1), 65–91.
REF: Jegadeesh, N., Titman, S., 2001. Profitability of momentum strategies: an evaluation of alternative explanations. *Journal of Finance* 56 (2), 699–720.
REF: Kaminski, K.M., Lo, A.W., 2014. When do stop-loss rules stop losses? *Journal of Financial Markets* 18, 234–254.
REF: Lehmann, B.N., 1990. Fads, martingales, and market efficiency. *Quarterly Journal of Economics* 105 (1), 1–28.
REF: Lei, A.Y.T., Li, H., 2009. The value of stop loss strategies. *Financial Services Review* 18 (1), 23–51.
REF: Marshall, B.R., Cahan, R.H., Cahan, J.M., 2008. Does intraday technical analysis in the U.S. equity market have value? *Journal of Empirical Finance* 15, 199–210.
REF: McLean, R.D., Pontiff, J., 2016. Does academic research destroy stock return predictability? *Journal of Finance* 71 (1), 5–32.
REF: Moskowitz, T.J., Ooi, Y.H., Pedersen, L.H., 2012. Time series momentum. *Journal of Financial Economics* 104 (2), 228–250.
REF: Nagel, S., 2012. Evaporating liquidity. *Review of Financial Studies* 25 (7), 2005–2039.
REF: Patel, J., Shah, S., Thakkar, P., Kotecha, K., 2015. Predicting stock and stock price index movement using trend deterministic data preparation and machine learning techniques. *Expert Systems with Applications* 42, 259–268.
REF: Sezer, O.B., Ozbayoglu, A.M., 2018. Algorithmic financial trading with deep convolutional neural networks: time series to image conversion approach. *Applied Soft Computing* 70, 525–538.
REF: Shefrin, H., Statman, M., 1985. The disposition to sell winners too early and ride losers too long: theory and evidence. *Journal of Finance* 40 (3), 777–790.
REF: Sullivan, R., Timmermann, A., White, H., 1999. Data-snooping, technical trading rule performance, and the bootstrap. *Journal of Finance* 54 (5), 1647–1691.
REF: Tsinaslanidis, P., Guijarro, F., Voukelatos, N., 2022. Automatic identification and evaluation of Fibonacci retracements: empirical evidence from three equity markets. *Expert Systems with Applications* 187, 115893.

## Appendix A. Annual and cumulative returns

Table A.1 lists calendar-year returns. Figure A.1 shows the cumulative return of the portfolio and SPY over the full sample, together with the portfolio's value relative to SPY. Figure A.2 repeats the comparison for each period, with each portfolio starting in cash.

| Year | Portfolio | SPY | Difference |
|---|---|---|---|
| 2007 | +8.8% | +5.3% | +3.4% |
| 2008 | −54.7% | −36.8% | −17.9% |
| 2009 | +32.7% | +26.4% | +6.4% |
| 2010 | +4.7% | +15.1% | −10.3% |
| 2011 | −7.5% | +1.9% | −9.4% |
| 2012 | +4.7% | +16.0% | −11.3% |
| 2013 | +22.4% | +32.3% | −9.9% |
| 2014 | +13.0% | +13.5% | −0.4% |
| 2015 | −11.0% | +1.2% | −12.2% |
| 2016 | +5.0% | +12.0% | −7.0% |
| 2017 | +39.9% | +21.7% | +18.1% |
| 2018 | −18.0% | −4.6% | −13.4% |
| 2019 | +12.3% | +31.2% | −18.9% |
| 2020 | +57.0% | +18.3% | +38.6% |
| 2021 | +9.4% | +28.7% | −19.4% |
| 2022 | −17.4% | −18.2% | +0.7% |
| 2023 | +34.3% | +26.2% | +8.1% |
| 2024 | +51.5% | +24.9% | +26.6% |
| 2025 | −16.4% | +17.7% | −34.1% |
| 2026* | +195.4% | +11.7% | +183.7% |

Table: Calendar-year returns of the portfolio.
Note: The portfolio runs continuously from January 2007 and beats SPY in eight of twenty years. * 2026 to 11 November.

![Cumulative return of the portfolio and SPY, January 2007 to November 2026 (top), and the portfolio's value relative to SPY (bottom). Shaded regions mark the held-out decade and the QISC out-of-sample window.](../output/figures/cumulative.png)

![Cumulative return of the portfolio and SPY in each period: (a) held-out decade, (b) development period, (c) QISC out-of-sample window. Each portfolio starts in cash on the first day of its period, as in Table 5.](../output/figures/cumulative_periods.png)

## Appendix B. Robustness tables

| Exit rule (entries unchanged) | Trades | Win rate | Per year | Worst drawdown | CAGR ÷ drawdown | Sharpe |
|---|---|---|---|---|---|---|
| Hold 63 days (baseline) | 361 | 52% | +10.9% | −64% | 0.17 | 0.48 |
| Close below the band | 1,517 | 31% | +2.9% | −64% | 0.04 | 0.24 |
| Three closes below the band | 1,006 | 35% | +8.2% | −73% | 0.11 | 0.42 |
| Five closes below the band | 784 | 36% | +9.7% | −64% | 0.15 | 0.47 |
| Heavy-volume down day (≥ 3×) | 526 | 52% | +14.8% | −52% | 0.28 | 0.61 |
| Heavy-volume down day (≥ 5×) | 414 | 52% | +7.7% | −58% | 0.13 | 0.39 |
| Three closes below the band or volume ≥ 3× | 1,110 | 38% | +10.1% | −66% | 0.15 | 0.49 |
| Stop at −25% | 407 | 50% | +12.7% | −56% | 0.23 | 0.55 |
| Stop at −40% | 376 | 51% | +10.7% | −61% | 0.17 | 0.48 |

Table: Exit rules, January 2007 to November 2026.
Note: Exits other than the clock are decided on a close and executed at the next open; every position is sold after 63 days at the latest. Heavy-volume down day: a lower close on volume of at least the stated multiple of its 50-day median.

| Variant | Trades | Per year | Worst drawdown | Sharpe | CAGR ÷ drawdown: full | Held-out | Development | QISC OOS |
|---|---|---|---|---|---|---|---|---|
| *Panel A: Number of positions* | | | | | | | | |
| 3 | 213 | +7.4% | −91% | 0.38 | 0.08 | −0.19 | 0.63 | 0.72 |
| 5 (baseline) | 361 | +10.9% | −64% | 0.48 | 0.17 | −0.00 | 0.43 | 0.68 |
| 8 | 577 | +11.1% | −59% | 0.51 | 0.19 | 0.11 | 0.25 | 0.76 |
| 10 | 712 | +11.5% | −56% | 0.54 | 0.20 | 0.15 | 0.29 | 0.17 |
| 12 | 847 | +9.8% | −52% | 0.49 | 0.19 | 0.13 | 0.30 | 0.39 |
| 15 | 1,048 | +9.1% | −53% | 0.46 | 0.17 | 0.06 | 0.30 | 0.45 |
| 20 | 1,362 | +10.2% | −48% | 0.52 | 0.21 | 0.19 | 0.22 | 0.95 |
| *Panel B: Holding period (trading days)* | | | | | | | | |
| 21 | 885 | +9.7% | −49% | 0.48 | 0.20 | 0.05 | 0.40 | 0.37 |
| 42 | 513 | +12.5% | −52% | 0.55 | 0.24 | 0.19 | 0.30 | 0.39 |
| 63 (baseline) | 361 | +10.9% | −64% | 0.48 | 0.17 | −0.00 | 0.43 | 0.68 |
| 84 | 276 | +8.7% | −70% | 0.41 | 0.12 | −0.04 | 0.38 | 0.93 |
| 126 | 189 | +5.6% | −70% | 0.33 | 0.08 | 0.02 | 0.22 | 0.10 |
| *Panel C: Cost model multiple* | | | | | | | | |
| 0.5× | 361 | +11.3% | −63% | 0.49 | 0.18 | 0.00 | 0.44 | 0.69 |
| 1× (baseline) | 361 | +10.9% | −64% | 0.48 | 0.17 | −0.00 | 0.43 | 0.68 |
| 2× | 361 | +10.2% | −64% | 0.46 | 0.16 | −0.02 | 0.40 | 0.65 |
| 3× | 361 | +9.5% | −64% | 0.44 | 0.15 | −0.03 | 0.38 | 0.63 |
| 5× | 361 | +8.1% | −64% | 0.40 | 0.13 | −0.05 | 0.33 | 0.58 |

Table: Position count, holding period and costs.
Note: Each row changes one parameter of the baseline. Panel C scales both fees and market impact. The last three columns are separate portfolios per period.

| Touch window or EMA span | Tolerance | Trades | Per year | Worst drawdown | CAGR ÷ drawdown | Sharpe |
|---|---|---|---|---|---|---|
| *Panel A: Touch window* | | | | | | |
| 3 days | 0% | 330 | +11.4% | −54% | 0.21 | 0.50 |
| 3 days | 1% | 354 | +6.4% | −63% | 0.10 | 0.35 |
| 3 days | 2% | 365 | +7.5% | −70% | 0.11 | 0.39 |
| 5 days | 0% | 347 | +18.9% | −45% | 0.42 | 0.75 |
| 5 days (baseline) | 1% | 361 | +10.9% | −64% | 0.17 | 0.48 |
| 5 days | 2% | 369 | +14.7% | −57% | 0.26 | 0.59 |
| 10 days | 0% | 360 | +12.7% | −54% | 0.23 | 0.55 |
| 10 days | 1% | 369 | +5.0% | −66% | 0.08 | 0.31 |
| 10 days | 2% | 372 | +7.2% | −76% | 0.10 | 0.38 |
| *Panel B: EMA span of the band* | | | | | | |
| 10 days | 1% | 373 | +8.0% | −59% | 0.14 | 0.40 |
| 15 days | 1% | 370 | +7.7% | −70% | 0.11 | 0.39 |
| 20 days (baseline) | 1% | 361 | +10.9% | −64% | 0.17 | 0.48 |
| 30 days | 1% | 331 | +13.4% | −47% | 0.29 | 0.58 |
| 40 days | 1% | 294 | +11.8% | −46% | 0.26 | 0.54 |

Table: Entry parameters.
Note: Panel B keeps the five-day window. The trend screen is unchanged throughout.

## Appendix C. Trades

The full list of 361 trades is in `output/trades.csv`. Prices are split- and dividend-adjusted opens; returns are after fees and market impact.

{{trades:../output/tables/trades_best.csv | The ten best trades.}}

{{trades:../output/tables/trades_worst.csv | The ten worst trades.}}

{{trades:../output/tables/trades_oos.csv | Every trade entered in the QISC out-of-sample window, January 2025 to November 2026.}}
