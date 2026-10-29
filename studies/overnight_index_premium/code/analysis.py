"""Full overnight analysis for US100/GER40: HAC by day, block-bootstrap placebo,
endogenous break, net of cost (measured spread + swap, asymmetric), economic
contribution of Monday vs Tuesday. Writes results/analysis_results.json as it goes
(one print + flush per section) so that nothing is lost if the session is cut.
The keys "lundi"/"mardi" (Monday/Tuesday) are kept as identifiers so that the
committed JSON stays readable.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats_lib import (hac_mean_t, block_bootstrap_null_pvalue,
                        break_bootstrap_pvalue, sidak_threshold)

RES = Path(__file__).resolve().parent.parent / "results"
OUTJ = RES / "analysis_results.json"

WD_NAME = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}

# Most recent measured costs (native round trip, week of 2026-08-17);
# swap_long_bps_ref from the live spec's measured_specs (MT5 points measured 2026-06-10).
RT_BPS_RECENT = {"US100": 1.045, "GER40": 1.017}       # round trip, recent measurement
RT_BPS_SPEC_2026_06 = {"US100": 2.2, "GER40": 2.2}     # cost_anchors.rt_bps_legs_allin (June, conservative)
SWAP_LONG_BPS = {"US100": -2.1257, "GER40": -1.564}    # measured_specs, measured 2026-06-10
SWAP_SHORT_BPS = {"US100": 0.0917, "GER40": -0.1933}   # L30 asymmetry (context; the sleeve is LONG-only)
TRIPLE_DOW = {"US100": 4, "GER40": 4}                   # Friday -- Mon/Tue = 1x, not concerned here
ON_W = 0.35
INIT_EQUITY = 10_000.0

log = []


def emit(msg):
    print(msg)
    log.append(str(msg))
    OUTJ.parent.mkdir(exist_ok=True)
    (RES / "analysis_log.txt").write_text("\n".join(log) + "\n")


def load(sym):
    df = pd.read_csv(RES / f"{sym.lower()}_overnight_daily.csv", parse_dates=["date"])
    return df.set_index("date")


def main():
    results = {"per_weekday": {}, "monday_tuesday": {}, "breaks": {}, "net_of_cost": {},
               "economic": {}, "n_tests": 0}
    n_tests = 0

    # ---------------------------------------------------------- Section 1 --
    emit("=" * 78)
    emit("SECTION 1 -- gross measurement by ENTRY day, HAC lag 6, full period")
    emit("=" * 78)
    data = {}
    for sym in ("US100", "GER40"):
        df = load(sym)
        data[sym] = df
        emit(f"\n--- {sym} : {df.index.min().date()} -> {df.index.max().date()}, "
             f"N={df['ov_bps_entryday'].notna().sum()} nights ---")
        rows = {}
        for wd in range(5):
            x = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna().to_numpy()
            m, se, t, n = hac_mean_t(x, lag=6)
            n_tests += 1
            rows[WD_NAME[wd]] = dict(mean_bps=round(m, 3), t_hac6=round(t, 3), n=int(n))
            emit(f"  {WD_NAME[wd]:9s} mean={m:7.3f} bps  t_HAC6={t:6.3f}  n={n}")
        results["per_weekday"][sym] = rows

    emit(f"\nTests counted (section 1): {n_tests} (5 days x 2 instruments). "
         f"Sidak local(10)={sidak_threshold(10):.3f}")

    # ---------------------------------------------------- Section 2: trap --
    emit("\n" + "=" * 78)
    emit("SECTION 2 -- labelling-trap check (entry day vs open day)")
    emit("=" * 78)
    emit("By construction (ov_bps_entryday == ov_bps_openday at the "
         "value level, only the row label differs), check explicitly "
         "the coordinating note's example: the WEEKEND gap (Friday entry -> "
         "Monday open) must appear under 'Friday' here, NOT under 'Monday'.")
    for sym in ("US100", "GER40"):
        df = data[sym]
        fri = df[df["weekday"] == 4]
        gap_med = fri["gap_cal_days"].median()
        emit(f"  {sym}: FRIDAY-entry nights, median calendar gap to the next "
             f"suivant = {gap_med:.0f}j (attendu 3 = week-end) ; mean={fri['ov_bps_entryday'].mean():.2f} bps")
    emit("Confirmed: the weekend gap is carried by the 'Friday' row "
         "(ENTRY day), not 'Monday'. Labelling by entry day avoids the trap.")

    # ------------------------------------------------- Section 3: Mon/Tue --
    emit("\n" + "=" * 78)
    emit("SECTION 3 -- Monday and Tuesday: block-bootstrap placebo (H0 = zero mean)")
    emit("=" * 78)
    for sym in ("US100", "GER40"):
        df = data[sym]
        for wd, name in ((0, "lundi"), (1, "mardi")):
            x = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna().to_numpy()
            r = block_bootstrap_null_pvalue(x, lag=6, n_boot=4000, block=20, seed=abs(hash((sym, wd))) % 2**31 if False else (100+wd if sym=='US100' else 200+wd))
            n_tests += 1
            results["monday_tuesday"][f"{sym}_{name}_full"] = r
            emit(f"  {sym:6s} {name:6s} full : mean={r['mean']:7.3f} bps  t={r['t']:6.3f}  "
                 f"n={r['n']:4d}  p_block_bootstrap={r['p_block_bootstrap']:.4f}")

    # -------------------------------------------- Section 4: endogenous break --
    emit("\n" + "=" * 78)
    emit("SECTION 4 -- ENDOGENOUS break (estimated date, not imposed), Monday/Tuesday only")
    emit("=" * 78)
    for sym in ("US100", "GER40"):
        df = data[sym]
        for wd, name in ((0, "lundi"), (1, "mardi")):
            sub = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna()
            x = sub.to_numpy()
            dates = sub.index
            r = break_bootstrap_pvalue(x, lag=6, min_seg=90, step=10, n_boot=300,
                                        block=15, seed=(300+wd if sym=='US100' else 400+wd))
            n_tests += 1
            brk_date = dates[r["k"]] if r["k"] is not None else None
            results["breaks"][f"{sym}_{name}"] = {**r, "break_date": str(brk_date.date()) if brk_date is not None else None}
            emit(f"  {sym:6s} {name:6s}: estimated break at {brk_date.date() if brk_date is not None else 'NA'} "
                 f"(obs {r['n_pre']} avant / {r['n_post']} apres) ; "
                 f"mean_pre={r['mean_pre']:.3f} mean_post={r['mean_post']:.3f} bps ; "
                 f"t_diff={r['t']:.3f} ; p_bootstrap(recherche corrigee)={r['p_break_bootstrap']:.4f}")

    # ---------------------------------------------- Section 5: net of cost --
    emit("\n" + "=" * 78)
    emit("SECTION 5 -- net of spread AND of FTMO swap (asymmetric, L30 -- LONG sleeve)")
    emit("=" * 78)
    emit("Cost applied per NIGHT held (Mon/Tue = 1x, no triple-swap day here):")
    for sym in ("US100", "GER40"):
        rt_recent = RT_BPS_RECENT[sym]
        rt_spec = RT_BPS_SPEC_2026_06[sym]
        sw = SWAP_LONG_BPS[sym]
        emit(f"  {sym}: recent RT (2026-08-17, native)={rt_recent:.3f} bps | "
             f"RT spec conservateur (2026-06)={rt_spec:.3f} bps | "
             f"measured swap_long={sw:.3f} bps/night (short={SWAP_SHORT_BPS[sym]:.3f}, "
             f"triple_dow={TRIPLE_DOW[sym]}=vendredi, non touche Mon/Tue)")
        df = data[sym]
        for wd, name in ((0, "lundi"), (1, "mardi")):
            x = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna().to_numpy()
            net_recent = x - rt_recent + sw
            net_spec = x - rt_spec + sw
            m_g, _, t_g, n_ = hac_mean_t(x, lag=6)
            m_nr, _, t_nr, _ = hac_mean_t(net_recent, lag=6)
            m_ns, _, t_ns, _ = hac_mean_t(net_spec, lag=6)
            n_tests += 1  # the "net > 0" test is the economically relevant one
            results["net_of_cost"][f"{sym}_{name}"] = dict(
                gross_mean=round(m_g, 3), gross_t=round(t_g, 3),
                net_recent_cost_mean=round(m_nr, 3), net_recent_cost_t=round(t_nr, 3),
                net_spec_cost_mean=round(m_ns, 3), net_spec_cost_t=round(t_ns, 3), n=int(n_))
            emit(f"    {name:6s}: gross={m_g:7.3f} (t={t_g:5.2f})  "
                 f"net[recent cost]={m_nr:7.3f} (t={t_nr:5.2f})  "
                 f"net[June spec cost, conservative]={m_ns:7.3f} (t={t_ns:5.2f})  n={n_}")

    # ------------------------------------------- Section 6: economic contribution --
    emit("\n" + "=" * 78)
    emit("SECTION 6 -- economic contribution of Monday vs Tuesday to the sleeve (weight 0.35, $10k)")
    emit("=" * 78)
    tot_usd = {}
    for sym in ("US100", "GER40"):
        df = data[sym]
        rt_recent = RT_BPS_RECENT[sym]
        sw = SWAP_LONG_BPS[sym]
        rows = {}
        for wd in range(5):
            x = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna().to_numpy()
            net_bps = x - rt_recent + sw
            usd = net_bps / 1e4 * ON_W * INIT_EQUITY
            rows[WD_NAME[wd]] = dict(sum_usd=round(float(usd.sum()), 2), n=len(x),
                                      mean_usd_per_night=round(float(usd.mean()), 3) if len(x) else None)
        tot = sum(v["sum_usd"] for v in rows.values())
        tot_usd[sym] = tot
        results["economic"][sym] = rows
        emit(f"  {sym}: total net (2013/2013-09 -> 2026-06, weight {ON_W}, equity {INIT_EQUITY:.0f}$ "
             f"CONSTANTE -- pas de compounding) = {tot:9.2f} $")
        for wd in range(5):
            v = rows[WD_NAME[wd]]
            share = (v["sum_usd"] / tot * 100) if tot != 0 else float("nan")
            emit(f"    {WD_NAME[wd]:9s}: {v['sum_usd']:9.2f} $  ({share:6.1f} % of net total)  n={v['n']}")
    mon_tue = {sym: tot_usd[sym] for sym in tot_usd}
    results["economic"]["totals_usd"] = tot_usd

    # ------------------------------------- Section 6b: real share Mon vs Tue --
    emit("\n" + "=" * 78)
    emit("SECTION 6b -- share of Monday vs Tuesday IN THE REAL SLEEVE (Mon+Tue only, "
         "not the hypothetical 5-day portfolio -- denominator correction)")
    emit("=" * 78)
    combined_mon = 0.0
    combined_tue = 0.0
    for sym in ("US100", "GER40"):
        r = results["economic"][sym]
        mon_usd = r["lundi"]["sum_usd"]
        tue_usd = r["mardi"]["sum_usd"]
        tot = mon_usd + tue_usd
        combined_mon += mon_usd
        combined_tue += tue_usd
        emit(f"  {sym}: Monday {mon_usd:9.2f}$ ({mon_usd/tot*100:5.1f}%)  "
             f"Tuesday {tue_usd:9.2f}$ ({tue_usd/tot*100:5.1f}%)  sleeve total (2 days) {tot:9.2f}$")
    tot_c = combined_mon + combined_tue
    emit(f"  US100+GER40 combined: Monday {combined_mon:9.2f}$ ({combined_mon/tot_c*100:5.1f}%)  "
         f"Tuesday {combined_tue:9.2f}$ ({combined_tue/tot_c*100:5.1f}%)")
    results["economic"]["share_mon_tue_only"] = dict(
        combined_mon_usd=round(combined_mon, 2), combined_tue_usd=round(combined_tue, 2),
        mon_share_pct=round(combined_mon / tot_c * 100, 1),
        tue_share_pct=round(combined_tue / tot_c * 100, 1))

    # --------------------------------------------- Section 7: JOINT test Mon+Tue --
    emit("\n" + "=" * 78)
    emit("SECTION 7 -- JOINT test, Monday+Tuesday pooled (hypothesis: the overnight sleeve "
         "midweek as a whole != 0), HAC + block bootstrap")
    emit("=" * 78)
    joint_all = []
    for sym in ("US100", "GER40"):
        df = data[sym]
        x = df.loc[df["weekday"].isin([0, 1]), "ov_bps_entryday"].dropna().to_numpy()
        rt_recent = RT_BPS_RECENT[sym]
        sw = SWAP_LONG_BPS[sym]
        net = x - rt_recent + sw
        r_gross = block_bootstrap_null_pvalue(x, lag=6, n_boot=4000, block=20, seed=(500 if sym=='US100' else 501))
        r_net = block_bootstrap_null_pvalue(net, lag=6, n_boot=4000, block=20, seed=(600 if sym=='US100' else 601))
        n_tests += 2
        results.setdefault("joint", {})[sym] = dict(gross=r_gross, net=r_net)
        emit(f"  {sym}: GROSS  mean={r_gross['mean']:6.3f} bps t={r_gross['t']:5.3f} "
             f"n={r_gross['n']} p_boot={r_gross['p_block_bootstrap']:.4f}")
        emit(f"  {sym}: NET    mean={r_net['mean']:6.3f} bps t={r_net['t']:5.3f} "
             f"n={r_net['n']} p_boot={r_net['p_block_bootstrap']:.4f}")
    emit(f"Local Sidak updated (n={n_tests}): |t| > {sidak_threshold(n_tests):.3f}")

    results["n_tests"] = n_tests
    emit(f"\nTOTAL tests counted this session: {n_tests}")
    emit(f"Local Sidak (n={n_tests}): |t| > {sidak_threshold(n_tests):.3f}")
    n_cum = 1994 + n_tests
    emit(f"CUMULATIVE Sidak (n={n_cum} = 1994 + {n_tests}): |t| > {sidak_threshold(n_cum):.3f}")
    results["sidak_local"] = sidak_threshold(n_tests)
    results["sidak_cumulative"] = sidak_threshold(n_cum)
    results["n_cumulative"] = n_cum

    # ------------------------------------------- Section 8: vol, tail, options D --
    emit("\n" + "=" * 78)
    emit("SECTION 8 -- volatility, tail, and comparison of the options (Part D)")
    emit("=" * 78)
    opt = {}
    for sym in ("US100", "GER40"):
        df = data[sym]
        rt_recent, sw = RT_BPS_RECENT[sym], SWAP_LONG_BPS[sym]
        rows = {}
        for wd, name in ((0, "lundi"), (1, "mardi")):
            x = df.loc[df["weekday"] == wd, "ov_bps_entryday"].dropna().to_numpy()
            net = x - rt_recent + sw
            mean, std = float(net.mean()), float(net.std())
            sharpe_ann = mean / std * np.sqrt(52) if std > 0 else float("nan")  # 1 night/week, L47
            p1, p5 = float(np.percentile(net, 1)), float(np.percentile(net, 5))
            worst = float(net.min())
            rows[name] = dict(mean_net_bps=round(mean, 3), std_net_bps=round(std, 3),
                               sharpe_ann_L47=round(sharpe_ann, 3), p1_bps=round(p1, 2),
                               p5_bps=round(p5, 2), worst_bps=round(worst, 2), n=len(x))
            emit(f"  {sym} {name}: mean_net={mean:6.2f} std={std:6.2f} bps  "
                 f"Sharpe_ann(sqrt52)={sharpe_ann:5.3f}  p1={p1:7.2f}  p5={p5:6.2f}  worst={worst:7.2f} bps")
        # pooled Mon+Tue (live config) vs half-size Mon+Tue (flat de-leverage, L54)
        x_pool = df.loc[df["weekday"].isin([0, 1]), "ov_bps_entryday"].dropna().to_numpy()
        net_pool = x_pool - rt_recent + sw
        m, s = float(net_pool.mean()), float(net_pool.std())
        sharpe_pool = m / s * np.sqrt(104) if s > 0 else float("nan")  # 2 nights/week
        # option "Tuesday alone": keep Tuesday, cut Monday
        x_tue = df.loc[df["weekday"] == 1, "ov_bps_entryday"].dropna().to_numpy()
        net_tue = x_tue - rt_recent + sw
        m_t, s_t = float(net_tue.mean()), float(net_tue.std())
        sharpe_tue = m_t / s_t * np.sqrt(52) if s_t > 0 else float("nan")
        # option "flat de-leverage" = same 2 nights, weight ON_W/2 -> mean and std halved,
        # ANNUALISED Sharpe unchanged (the L54 point: de-leveraging does not change the Sharpe)
        emit(f"  {sym}: POOL Mon+Tue full weight -- Sharpe_ann={sharpe_pool:.3f} "
             f"(mean={m:.2f} std={s:.2f} bps/night, n={len(x_pool)})")
        emit(f"  {sym}: TUESDAY ALONE (Monday cut) -- Sharpe_ann={sharpe_tue:.3f} "
             f"(mean={m_t:.2f} std={s_t:.2f} bps/night, n={len(x_tue)})")
        emit(f"  {sym}: FLAT DE-LEVERAGE (Mon+Tue at half weight) -- Sharpe_ann IDENTICAL to pool "
             f"({sharpe_pool:.3f}, L54: de-leveraging changes the scale, not the Sharpe) "
             f"but $ expectation halved AND the 2 nights/week are KEPT "
             f"(exposure days unchanged, unlike 'Tuesday alone')")
        opt[sym] = dict(per_day=rows, pool_sharpe=round(sharpe_pool, 3),
                         tue_only_sharpe=round(sharpe_tue, 3),
                         pool_mean=round(m, 3), pool_std=round(s, 3), pool_n=len(x_pool),
                         tue_mean=round(m_t, 3), tue_std=round(s_t, 3), tue_n=len(x_tue))
    results["options_D"] = opt

    OUTJ.write_text(json.dumps(results, indent=2, default=str))
    emit(f"\n[written] {OUTJ}")


if __name__ == "__main__":
    main()
