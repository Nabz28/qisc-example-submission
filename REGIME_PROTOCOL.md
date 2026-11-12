# Regime and decay protocol

Written on 12 November 2026, before any test below was run. Committed to the repository before the results, so
that the tests cannot be changed after seeing them.

**What had already been observed.** The portfolio's calendar-year returns for 2007–2026, its rolling 36-month return
above SPY (negative at every year-end from 2010 to 2017, mostly positive since 2018), and one regime filter (new
positions only while SPY is above its 200-day average), which lowered the drawdown but did not make the excess
return significant. Nothing else about market conditions has been examined.

**Question.** Does the portfolio work in some market regimes and not others, and can the regime be identified in
real time, from data available at the moment of the decision?

## Indicators

Each indicator is evaluated at every month-end *t* from data up to and including *t*, and applied to month *t* + 1.
"On" is the state in which we expect the portfolio to do well.

| | Indicator | On when |
|---|---|---|
| R1 | Market trend | SPY closes above its 200-day simple average |
| R2 | Supply of clean trends | The number of stocks passing the trend screen, averaged over the last 21 trading days, is above its median over the last 756 trading days (at least 252) |
| R3 | Small-cap leadership | The equal-weighted eligible universe has beaten SPY over the last 126 trading days |
| R4 | Strategy momentum | The portfolio has beaten SPY over the last 252 trading days |
| R5 | Edge health | The month-matched advantage of touch over no-touch entries at 21 days, averaged over event months *t* − 14 to *t* − 3 (so that every return is known at *t*), is positive |
| R6 | Combined monitor | R4 and R5 are both on |

The portfolio is the baseline (five positions, casebook costs and liquidity cap) run continuously from January 2007.
Months in which an indicator cannot yet be computed are excluded from Test 1 and treated as "on" in Test 2.

## Test 1: conditional returns

The portfolio's return minus SPY in month *t* + 1, when the indicator is on and when it is off. Reported: mean on, mean
off, the difference with a 95% interval (2,000 draws, months resampled within each group), and the share of months on;
for 2007–2014, for 2015–2026 and pooled.

**An indicator identifies the regime if** the difference is positive in both 2007–2014 and 2015–2026 and the pooled
interval excludes zero. Anything else is reported as not identified.

## Test 2: walk-forward switching rule

For each indicator, hold the portfolio in month *t* + 1 when the indicator is on and SPY when it is off. The portfolio
keeps running as a shadow book, so its positions are continuous; each switch costs 0.25% of capital. Reported: CAGR,
Sharpe ratio, worst drawdown and monthly return above SPY with a 95% interval, for 2007–2014, 2015–2026 and 2007–2026.
Every decision uses only data available at the time; no threshold is fitted. The six rules count as trials in the
deflated Sharpe ratio.

## Decay monitoring

Three monitors, plotted for 2007–2026 and evaluated as in Test 1 where they are indicators: strategy momentum (R4),
edge health (R5), and the portfolio's drawdown relative to SPY (portfolio value divided by SPY, from its running peak).

## Forward test

The rules were fixed on data up to 18 September 2026. The period from 19 September 2026 to the last available close is
reported separately, with every position opened in it, whatever the result.
