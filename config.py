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
DEV_START = pd.Timestamp("2017-07-01")      # the rules were developed on data from here on
OOS_START = pd.Timestamp("2025-01-01")      # QISC out-of-sample window: the final 24 months
PERIODS = {"heldout": (SIM_START, DEV_START), "dev": (DEV_START, OOS_START), "oos": (OOS_START, None)}
DEV_WINDOW = (pd.Timestamp("2017-07-03"), pd.Timestamp("2026-09-18"))   # full development sample

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

# ---------------------------------------------------------------- the baseline portfolio (QISC constraints)
SLOTS = 10                            # casebook: at most 10% of NAV per name
LIQ_QISC = 2e6                        # casebook: position <= 5% of 60-day median traded value ($100k / 5%)
COST = 0.0010                         # per side: 5 bp fees + 5 bp slippage (casebook minimum, US)
CAPITAL = 1_000_000                   # notional, USD (casebook)

# ---------------------------------------------------------------- the concentrated variant (Table 3)
CONC_SLOTS = 5                        # five positions of 20%, $0.5M liquidity screen only
CONC_COST = 0.0005

# ---------------------------------------------------------------- statistics
BOOT = 2000                           # bootstrap draws, whole months resampled
HORIZONS = (1, 5, 10, 21, 42, 63)     # event-study horizons, sessions
WORKERS = 10                          # processes for the score computation
