"""Reproduce every result of the paper with one command.

    python run.py              # download (or reuse) data, compute, write output/, render the paper
    python run.py --refresh    # force a fresh download of prices and the symbol lists
    python run.py --no-paper   # skip rendering output/paper.pdf

Steps: data -> scores -> experiments -> tables and required files -> figures -> paper.
Every step caches its result in data/ or output/, so a second run is fast.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

import config as C


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-download prices, symbol directory and screener")
    ap.add_argument("--no-paper", action="store_true", help="do not render output/paper.pdf")
    a = ap.parse_args()

    from src import data, experiments, figures, report
    C.DATA.mkdir(parents=True, exist_ok=True)
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    step = lambda n, s: print(f"\n[{n}/6] {s}  ({time.time() - t0:.0f}s)", flush=True)

    step(1, "data: symbol directory, screener, prices")
    data.download(refresh=a.refresh)
    data.screener(refresh=False)
    data.build_wide(refresh=a.refresh)
    step(2, "point-in-time trend scores")
    experiments.scores(strict=False)
    experiments.scores(strict=True)
    step(3, "portfolio, forward test, cost decomposition, event study, regime tests and robustness tests")
    experiments.run_all()
    step(4, "tables, positions.csv, trades.csv, compliance check")
    report.run()
    step(5, "figures")
    figures.run()
    if not a.no_paper:
        step(6, "paper")
        r = subprocess.run([sys.executable, str(C.ROOT / "paper" / "qisc_render.py"), str(C.ROOT / "paper" / "manuscript.md"),
                            str(C.OUTPUT / "paper.pdf")], capture_output=True, text=True)
        print("  " + (r.stdout.strip() or r.stderr.strip()[-400:]))
    print(f"\ndone in {time.time() - t0:.0f}s -> {C.OUTPUT.relative_to(C.ROOT)}/")


if __name__ == "__main__":
    main()
