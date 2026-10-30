import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import build_record as br

STUDY = Path(__file__).resolve().parents[1]
FIXED_TS = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)


@pytest.fixture
def built(synthetic_source, tmp_path):
    data = tmp_path / "data"
    page = tmp_path / "docs" / "live" / "index.html"
    summary = br.build(synthetic_source, data, tmp_path / "summary.json", page, build_ts=FIXED_TS)
    return summary, pd.read_csv(data / "equity_daily.csv"), pd.read_csv(data / "trades.csv"), page.read_text()


def test_daily_pnl_telescopes_to_total_and_adjustment_is_removed(built):
    summary, daily, _, _ = built
    complete = daily[daily["complete"]]
    assert list(complete["date"]) == ["2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06"]
    assert complete["pnl_usd"].round(2).tolist() == [19.0, 21.0, 20.0, -50.0, -25.0]
    assert summary["pnl"]["total_usd"] == pytest.approx(-15.0)
    # the -60 reset sits on the row of the day it followed, outside P&L
    assert daily.set_index("date").loc["2026-03-04", "adjustment_usd"] == pytest.approx(-60.0)
    assert summary["pnl"]["external_adjustments_usd"] == pytest.approx(-60.0)
    # raw equity fell 10 000 -> 9 925, of which 60 is the reset: trading alone is -15
    assert summary["pnl"]["current_equity_usd"] == pytest.approx(9925.0)
    # the last row is the open, incomplete day
    assert not daily.iloc[-1]["complete"] and pd.isna(daily.iloc[-1]["pnl_usd"])


def test_drawdown_on_trading_only_curve(built):
    summary, daily, _, _ = built
    assert summary["drawdown"]["max_usd"] == pytest.approx(-75.0)
    assert summary["drawdown"]["max_pct_of_initial"] == pytest.approx(-0.75)
    assert summary["drawdown"]["peak_date"] == "2026-03-04"
    assert summary["drawdown"]["trough_date"] == "2026-03-06"
    assert daily["equity_curve"].iloc[-1] == pytest.approx(9985.0)


def test_barrier_distances_use_every_mark_in_the_window(built):
    summary, daily, _, _ = built
    b = summary["barriers"]
    # 03-05: floor 9 500 (balance 10 000 - 5 %), lowest mark in the window 9 950
    assert b["min_distance_daily_floor_usd"] == pytest.approx(450.0)
    assert b["min_distance_daily_floor_date"] == "2026-03-05"
    # Friday's window runs to Monday 00:00 and sees the Saturday mark at 9 925
    assert daily.set_index("date").loc["2026-03-06", "min_mark_equity"] == pytest.approx(9925.0)
    assert b["min_distance_static_floor_usd"] == pytest.approx(925.0)
    assert summary["daily"]["worst_day_pct_of_daily_limit"] == pytest.approx(10.0)


def test_trade_pairing_and_point_values(built):
    summary, _, trades, _ = built
    assert len(trades) == 4
    by = trades.set_index(["entry_ts", "symbol"])["pnl_usd"]
    assert by[("2026-03-02 16:05:00", "US100")] == pytest.approx(2.0)      # short, 20 pts, 0.10 lot
    assert by[("2026-03-02 17:35:00", "GER40")] == pytest.approx(5.5)      # 50 pts x 0.10 x 1.10 $/pt
    assert by[("2026-03-02 22:05:00", "US100")] == pytest.approx(-3.0)
    assert by[("2026-03-05 16:10:00", "US100")] == pytest.approx(-5.0)
    assert summary["trades"]["all"]["win_rate_pct"] == pytest.approx(50.0)
    assert summary["trades"]["by_sleeve"]["overnight"]["n"] == 2
    assert summary["trades"]["by_sleeve"]["orb"]["n"] == 2
    unmatched = summary["trades"]["unmatched_fills"]
    assert len(unmatched) == 1
    assert unmatched[0]["ts"] == "2026-03-04 16:10:00" and unmatched[0]["kind"] == "entry_without_exit"
    assert unmatched[0]["lots"] == pytest.approx(0.5)


def test_exposure_and_swaps_per_instrument(built):
    summary, _, _, _ = built
    us = summary["per_instrument"]["US100"]
    assert us["swaps_usd"] == pytest.approx(-0.5)
    assert us["max_notional_usd"] == pytest.approx(2000.0)
    # 2 of the 13 marks (8 opens + 5 closes) carry a US100 position
    assert us["marks_with_position_pct"] == pytest.approx(100 * 2 / 13, abs=0.05)
    assert summary["reconciliation"] == dict(days_logged=2, days_full=1, days_degraded=1, days_unexplained=0,
                                             max_abs_residual_usd=1.2, sum_pnl_real_full_days_usd=19.0,
                                             sum_pnl_model_full_days_usd=18.0)


def test_page_is_self_contained_and_reads_from_summary(built):
    summary, _, _, page = built
    assert "<script" not in page and "http://" not in page.replace("http://www.w3.org", "")
    assert page.count("<svg") == 3
    assert "prefers-color-scheme: dark" in page
    for needle in ("\u2212$15.00", "\u22120.75 %", "$450.00", "2026-03-10T08:00:00Z", summary["source_commit"]):
        assert needle in page
    for digest in summary["source_sha256"].values():
        assert digest in page
    assert br.FTMO_PROFILE in page


REAL_SOURCE = STUDY / "source"
REAL_SUMMARY = STUDY / "summary.json"


@pytest.mark.skipif(not (REAL_SOURCE / "snapshots.csv").exists(), reason="no committed source extracts")
def test_committed_outputs_match_committed_source(tmp_path):
    """summary.json in the repository is a pure function of source/; rebuilding must reproduce it."""
    rebuilt = br.build(REAL_SOURCE, tmp_path / "data", tmp_path / "summary.json", None, build_ts=FIXED_TS)
    committed = json.loads(REAL_SUMMARY.read_text())
    for key in ("pnl", "daily", "drawdown", "barriers", "trades", "per_instrument", "reconciliation", "period", "source_sha256"):
        assert rebuilt[key] == committed[key], key
    committed_daily = pd.read_csv(STUDY / "data" / "equity_daily.csv")
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / "data" / "equity_daily.csv"), committed_daily)


@pytest.mark.skipif(not (REAL_SOURCE / "snapshots.csv").exists(), reason="no committed source extracts")
def test_committed_files_carry_no_identifiers():
    """No account login, ticket, server, host path or key-like token in anything published."""
    files = list(REAL_SOURCE.glob("*.csv")) + list((STUDY / "data").glob("*.csv")) + [REAL_SUMMARY]
    page = STUDY.parents[1] / "docs" / "live" / "index.html"
    if page.exists():
        files.append(page)
    # 9+ digit runs outside a hex digest (the SHA-256 of the extracts are printed on purpose)
    forbidden = [re.compile(r"(?<![\da-f.])\d{9,}(?![\da-f.])"), re.compile(r"/home/|/Users/|C:\\\\"),
                 re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"), re.compile(r"(?i)login|password|token|api[_-]?key"),
                 re.compile(r"(?i)-(demo|live|server)\d*\b")]
    for f in files:
        text = f.read_text()
        for pat in forbidden:
            assert not pat.search(text), f"{f.name}: {pat.pattern} -> {pat.search(text).group(0)}"
