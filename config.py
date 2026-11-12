"""Every parameter of the study, in one place.

Changing a value here and running `python run.py` re-runs the whole study with it.
The defaults reproduce the paper.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"                  # downloaded and derived data (not committed; rebuilt by run.py)
OUTPUT = ROOT / "output"              # everything the paper uses
FIGURES = OUTPUT / "figures"
TABLES = OUTPUT / "tables"

# ---------------------------------------------------------------- data
DOWNLOAD_START = "2005-01-01"         # first price; scores need ~200 days of history
SCORE_START = pd.Timestamp("2006-07-01")
SIM_START = pd.Timestamp("2007-01-02")
BENCHMARK = "SPY"
GAP_LIMIT = 3.0                       # an open more than 3x away from its own close is a data error

# ---------------------------------------------------------------- sample periods (Table 1)
MAIN_START = pd.Timestamp("2015-01-01")     # main sample: the casebook's backtest period, 2015 to today
OOS_START = pd.Timestamp("2025-01-01")      # QISC out-of-sample window: the final 24 months
DEV_START = pd.Timestamp("2017-07-01")      # the rules were developed on data from here ...
DEV_WINDOW = (pd.Timestamp("2017-07-03"), pd.Timestamp("2026-09-18"))   # ... to here
FORWARD_START = pd.Timestamp("2026-09-19")  # forward test: every close after the rules were fixed
PERIODS = {"insample": (MAIN_START, OOS_START), "oos": (OOS_START, None),
           "history": (SIM_START, MAIN_START)}   # history: 2007-2014, before the sample, never used in development

# ---------------------------------------------------------------- trend screen
FAST, SLOW = 20, 100                  # EMA spans: the run and the regime
MAX_BELOW = 10                        # more consecutive closes under the fast EMA end a run
MIN_RUN_BARS = 60
MIN_RET = 0.05                        # minimum log return of the run
SWING = 0.05                          # zigzag reversal that defines a pullback
MIN_CYCLES = 2                        # completed pullbacks required
MAX_DAY_SHARE = 0.20                  # best day's share of the run's log return
MAX_TOP5_SHARE = 0.55                 # best five days' share
MIN_PRICE = 1.0
LIQ_SCREEN = 5e5                      # 60-day median traded value, USD
STRICT_PIT = False                    # True: count a pullback only once its trough is confirmed (see README)

# ---------------------------------------------------------------- entry and exit
BAND_SPAN = 20                        # EMA of opens and of closes that define the band
TOUCH_WIN = 5                         # the touch must occur within this many sessions
TOUCH_TOL = 0.01                      # a close up to 1% above the band counts as a touch
HOLD = 63                             # sell at the open after this many sessions
COOLDOWN = 5                          # a stock sold cannot be bought again within this many sessions

# ---------------------------------------------------------------- the baseline portfolio (QISC rules)
SLOTS = 5                             # five positions of 20% of equity (no per-name limit in the casebook)
LIQ_QISC = 0.0                        # no fixed liquidity floor beyond the screen's $0.5M ...
MAX_ADV_FRAC = 0.05                   # ... but each order <= 5% of the 60-day median traded value, on NAV
CAPITAL = 1_000_000                   # notional, USD (casebook)
FEE = 0.0005                          # fees per side, US arena
IMPACT_K, IMPACT_MIN = 0.01, 0.0005   # impact per side = max(0.05%, 1% x sqrt(order / ADV))
EVENT_COST = FEE + IMPACT_MIN         # flat cost per side for the signal-level event study

# ---------------------------------------------------------------- statistics
BOOT = 2000                           # bootstrap draws, whole months resampled
HORIZONS = (1, 5, 10, 21, 42, 63)     # event-study horizons, sessions
WORKERS = 10                          # processes for the score computation
