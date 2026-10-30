"""A small SYNTHETIC source set, in the exact format ``build_record.extract`` writes.

Nothing here is account data: five trading days, two instruments, one external adjustment,
one entry whose exit is deliberately missing. Used only by the tests.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))


@pytest.fixture
def synthetic_source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    # Mon 2026-03-02 .. Fri 2026-03-06, plus the Saturday 00:00 mark and Monday 03-09 00:00.
    # 03-05 00:00: balance jumps from 10 060 to 10 000 with no trade: declared adjustment.
    snaps = [
        # date, open ts, bal_open, eq_open, close ts, bal_close, eq_close, source
        ("2026-03-02", "2026.03.02 00:00:00", 10000.00, 10000.00, "2026.03.02 22:58:00", 10000.00, 10020.00, "eod_2258"),
        ("2026-03-03", "2026.03.03 00:00:00", 10000.00, 10019.00, "2026.03.03 22:58:00", 10040.00, 10040.00, "eod_2258"),
        ("2026-03-04", "2026.03.04 00:00:00", 10040.00, 10040.00, "2026.03.04 22:54:10", 10060.00, 10060.00, "preswap_close"),
        ("2026-03-05", "2026.03.05 00:00:00", 10000.00, 10000.00, "2026.03.05 22:58:00", 9950.00, 9950.00, "eod_2258"),
        ("2026-03-06", "2026.03.06 00:00:00", 9950.00, 9950.00, "2026.03.06 22:58:00", 9950.00, 9930.00, "eod_2258"),
        ("2026-03-07", "2026.03.07 00:00:00", 9950.00, 9925.00, "", "", "", ""),
        ("2026-03-08", "2026.03.08 00:00:00", 9950.00, 9925.00, "", "", "", ""),
        ("2026-03-09", "2026.03.09 00:00:00", 9950.00, 9925.00, "", "", "", ""),
    ]
    rows = []
    for d, tso, bo, eo, tsc, bc, ec, cs in snaps:
        rows.append(dict(date=d, ts_open_paris=tso, phase="FUNDED", balance_open=bo, equity_open=eo,
                         anchor_balance=bo, daily_floor=bo - 500.0, static_floor=9000.0,
                         ts_close_paris=tsc, balance_close=bc, equity_close=ec, close_source=cs))
    pd.DataFrame(rows).to_csv(src / "snapshots.csv", index=False)

    fills = [
        # ORB round trip, Monday, short, 20 points gain on 0.10 lot = +$2
        ("2026.03.02 16:05:00", "funded_orb_entry", "US100", "SELL", 0.10, 20000.0, 20000.0, 0.0, 0),
        ("2026.03.02 22:00:00", "funded_orb_exit", "US100", "BUY", 0.10, 19980.0, 19980.0, 0.0, 0),
        # overnight GER40 long, Monday 17:35 -> Tuesday 09:00, +50 pts on 0.10 lot at 1.10 $/pt = +$5.50
        ("2026.03.02 17:35:00", "ger40_on", "GER40", "BUY", 0.10, 18000.0, 18000.0, 0.0, 0),
        ("2026.03.03 09:00:00", "ger40_off", "GER40", "SELL", 0.10, 18050.0, 18050.0, 0.0, 0),
        # overnight US100 long, Monday 22:05 -> Tuesday 15:30, -30 pts on 0.10 = -$3
        ("2026.03.02 22:05:00", "rebalance", "US100", "BUY", 0.10, 20000.0, 20000.0, 0.0, 0),
        ("2026.03.03 15:30:00", "us100_off", "US100", "SELL", 0.10, 19970.0, 19970.0, 0.0, 0),
        # ORB entry on Wednesday whose exit is NOT logged; the next ORB entry on Thursday
        ("2026.03.04 16:10:00", "funded_orb_entry", "US100", "SELL", 0.50, 20100.0, 20100.0, 0.0, 0),
        ("2026.03.05 16:10:00", "funded_orb_entry", "US100", "BUY", 0.10, 20200.0, 20200.0, 0.0, 0),
        ("2026.03.05 22:00:00", "funded_orb_exit", "US100", "SELL", 0.10, 20150.0, 20150.0, 0.0, 0),
    ]
    pd.DataFrame(fills, columns=["ts_paris", "reason", "symbol", "side", "lots", "req_price",
                                 "fill_price", "slip_bps", "latency_ms"]).to_csv(src / "fills.csv", index=False)

    pd.DataFrame([("2026-03-02", "US100", 0.10, 2000.0, -0.50), ("2026-03-02", "GER40", 0.10, 1980.0, -0.50)],
                 columns=["date_paris", "symbol", "lots_held", "notional_usd", "swap_usd"]).to_csv(src / "swaps.csv", index=False)

    pd.DataFrame([("2026.03.02 22:58:00", "close", "US100", 0.10, 1, 2000.0),
                  ("2026.03.02 22:58:00", "close", "GER40", 0.10, 1, 1980.0),
                  ("2026.03.03 00:00:00", "open", "US100", 0.10, 1, 2000.0),
                  ("2026.03.03 00:00:00", "open", "GER40", 0.10, 1, 1980.0)],
                 columns=["ts_paris", "mark", "symbol", "lots", "dir", "notional_usd"]).to_csv(src / "positions.csv", index=False)

    pv = [(d, "US100", 1.0) for d in ("2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06")]
    pv += [(d, "GER40", 1.10) for d in ("2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06")]
    pd.DataFrame(pv, columns=["date", "symbol", "usd_per_point_per_lot"]).to_csv(src / "point_values.csv", index=False)

    rec = [("2026-03-02", "full", 19.0, 18.0, 1.0, 0.0, -0.2, 0.0, 0.0, 1.2, 5.2, 0, 4),
           ("2026-03-03", "degraded", 21.0, "", "", "", "", "", "", 0.0, "", 0, 2)]
    pd.DataFrame(rec, columns=["date", "mode", "pnl_real", "pnl_model", "delta_total", "d_signal", "d_cost",
                               "d_timing", "d_micro", "residual_usd", "tol_usd", "unexplained", "n_fills"]).to_csv(src / "reconcile.csv", index=False)

    pd.DataFrame([("2026-03-05", -60.0, "synthetic: balance reset to the initial capital")],
                 columns=["date", "amount_usd", "note"]).to_csv(src / "adjustments.csv", index=False)
    return src
