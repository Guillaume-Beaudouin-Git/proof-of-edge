"""Reproduce the month-end Treasury-flow study end to end from public data.

    uv run --extra studies python studies/month_end_treasury_flow/reproduce.py

Downloads the daily series from Yahoo Finance (TLT, IEF, SPY, ZN=F, ZB=F, ZF=F, 2000/2002
to 2026-07-25) and the last ~730 days of hourly ZN=F and TLT, then runs the six steps in the
order they were written. Everything lands under this folder: data/ (downloads, ignored by git)
and results/reproduction_<date>.txt (the captured output of every step).

The daily part reproduces the study's tables exactly as long as Yahoo's history is unchanged;
the hourly part (steps 2 and 3) is a rolling window and will differ from the original run.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CODE = HERE / "code"
STEPS = [
    "fetch_data.py",
    "step1_replicate_and_split.py",
    "step2_identify_session.py",
    "step3_hourly_shape.py",
    "step4_longsample_and_economics.py",
    "step5_propfirm_sim.py",
    "step6_vehicle_verdict.py",
]


def main() -> int:
    (HERE / "results").mkdir(exist_ok=True)
    out = HERE / "results" / f"reproduction_{dt.date.today():%Y-%m-%d}.txt"
    failures = 0
    with out.open("w") as log:
        for step in STEPS:
            header = f"\n{'=' * 78}\n{step}\n{'=' * 78}\n"
            print(header, end="")
            log.write(header)
            proc = subprocess.run([sys.executable, str(CODE / step)], cwd=CODE,
                                  capture_output=True, text=True)
            log.write(proc.stdout)
            print(proc.stdout, end="")
            if proc.returncode != 0:
                failures += 1
                log.write(proc.stderr)
                print(proc.stderr, end="", file=sys.stderr)
                print(f"[{step}] exit {proc.returncode}", file=sys.stderr)
    print(f"\nwritten {out} ({failures} step(s) failed)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
