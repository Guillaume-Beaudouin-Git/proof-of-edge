"""§2-§4 : reconstruction indépendante de C9, concentration, jambes, fenêtres de stress, sélection d'horizon.

Usage : /usr/bin/python3 -I -B run_repro.py <out_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c9lib as L  # noqa: E402
from c9lib import np, pd  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
NT: dict[str, int] = {}


def count(fam: str, k: int = 1) -> None:
    NT[fam] = NT.get(fam, 0) + k


def periods(d: pd.Series) -> dict[str, pd.Series]:
    return {"IS": d.loc[:L.IS_END.normalize()], "HO": d.loc["2024-01-01":L.HO_END.normalize()],
            "FWD": d.loc[L.HO_END.normalize() + pd.Timedelta(days=1):], "ALL": d}


pn = L.build_panel()
first_sig = pn.z.first_valid_index().normalize()
last_day = pn.idx[-1].normalize()
print("panel", pn.idx[0], pn.idx[-1], "depeg h", int(pn.depeg.sum()), "valid primes", int(pn.prime.notna().sum()))
coverage = {"panel_start": str(pn.idx[0]), "panel_end": str(pn.idx[-1]),
            "hours": len(pn.idx), "hours_with_prime": int(pn.prime.notna().sum()),
            "depeg_hours": int(pn.depeg.sum()), "first_z": str(pn.z.first_valid_index()),
            "prime_mean_bps": float(pn.prime.mean() * 1e4), "prime_sd_bps": float(pn.prime.std() * 1e4),
            "z_gt2_h": int((pn.z > 2).sum()), "z_lt_m2_h": int((pn.z < -2).sum())}

# ---------- §2 reproduction, trois horizons, délai +1 h ----------
rows, series, trades_by = [], {}, {}
for h in (1, 4, 24):
    for delay in (0, 1):
        tr = L.run_strategy(pn, h=h, delay=delay)
        d = L.daily_pnl(pn, tr, start=first_sig, end=last_day)
        series[(h, delay)] = d
        trades_by[(h, delay)] = tr
        for name, dd in periods(d).items():
            if len(dd) < 5:
                continue
            s = L.summary(dd, ci=(delay == 0 and name in ("IS", "HO")))
            sel = tr[(tr["entry"] >= dd.index[0]) & (tr["entry"] < dd.index[-1] + pd.Timedelta(days=1))]
            s.update({"h": h, "delay": delay, "period": name, "n_trades": len(sel),
                      "gross_bps_per_trade": float(sel["ret"].mean() * 1e4) if len(sel) else np.nan,
                      "trades_per_year": len(sel) / (len(dd) / 365.0)})
            rows.append(s)
            count("S1_horizons_x_delay_x_period")
rep = pd.DataFrame(rows)
rep.to_csv(OUT / "repro_summary.csv", index=False, float_format="%.4f")
print(rep[["h", "delay", "period", "sharpe", "t_hac", "n_trades", "gross_bps_per_trade", "maxdd", "skew"]].to_string())

tr24 = trades_by[(24, 0)].copy()
d24 = series[(24, 0)]
tr24["pnl_w"] = tr24["w"] * tr24["ret"]
tr24[["signal", "entry", "exit", "side", "w", "ret", "z", "pnl_w"]].to_csv(OUT / "trades_h24.csv", index=False,
                                                                               float_format="%.6f")
d24.rename("pnl").to_csv(OUT / "daily_h24_gross.csv", float_format="%.7f")

# ---------- §3 concentration ----------
def zero_trades(tr: pd.DataFrame, drop_idx) -> pd.Series:
    return L.daily_pnl(pn, tr.drop(index=drop_idx), start=first_sig, end=last_day)


conc = []
for per, lo, hi in (("ALL", first_sig, last_day), ("IS", first_sig, L.IS_END), ("HO", pd.Timestamp("2024-01-01"), L.HO_END)):
    sub = tr24[(tr24["entry"] >= lo) & (tr24["entry"] <= hi)]
    tot = sub["pnl_w"].sum()
    order = sub["pnl_w"].sort_values(ascending=False).index
    for k in (0, 1, 3, 5, 10):
        d = zero_trades(tr24, order[:k])
        dd = d.loc[lo.normalize():hi.normalize()]
        conc.append({"period": per, "top_k_removed": k, "share_of_pnl": float(sub.loc[order[:k], "pnl_w"].sum() / tot) if k else 0.0,
                     "sharpe_without": L.sharpe(dd), "t_hac_without": L.hac_t(dd), "n_trades": len(sub)})
        count("C1_concentration")
conc = pd.DataFrame(conc)
conc.to_csv(OUT / "concentration.csv", index=False, float_format="%.4f")
print(conc.to_string())

top = tr24.sort_values("pnl_w", ascending=False).head(15).copy()
top["prime_bps_at_signal"] = pn.prime.reindex(top["signal"]).values * 1e4
top["prime_eth_bps_at_signal"] = pn.prime_eth.reindex(top["signal"]).values * 1e4
top["stress_month"] = top["entry"].dt.strftime("%Y-%m").isin(L.STRESS_MONTHS)
top[["signal", "side", "z", "w", "ret", "pnl_w", "prime_bps_at_signal", "prime_eth_bps_at_signal", "stress_month"]].to_csv(
    OUT / "top_trades_h24.csv", index=False, float_format="%.5f")
worst = tr24.sort_values("pnl_w").head(10)
worst[["signal", "side", "z", "w", "ret", "pnl_w"]].to_csv(OUT / "worst_trades_h24.csv", index=False, float_format="%.5f")

yr = d24.groupby(d24.index.year).agg(["sum", "count"])
yr["sharpe"] = d24.groupby(d24.index.year).apply(L.sharpe)
yr["share"] = yr["sum"] / d24.sum()
yr["n_trades"] = tr24.groupby(tr24["entry"].dt.year).size()
yr.to_csv(OUT / "by_year_h24.csv", float_format="%.4f")
q = d24.groupby(d24.index.to_period("Q")).sum()
q.rename("pnl").to_csv(OUT / "by_quarter_h24.csv", float_format="%.5f")
print(yr.to_string())
count("C1_by_year", len(yr))

# ---------- §3 fenêtres de stress et filtre de dépeg ----------
in_stress = tr24["entry"].dt.strftime("%Y-%m").isin(L.STRESS_MONTHS)
d_out = zero_trades(tr24, tr24.index[in_stress])
stress = {"trades_in_stress": int(in_stress.sum()), "pnl_share_in_stress": float(tr24.loc[in_stress, "pnl_w"].sum() / tr24["pnl_w"].sum()),
          "sharpe_all": L.sharpe(d24), "sharpe_excl_stress_all": L.sharpe(d_out),
          "sharpe_excl_stress_IS": L.sharpe(d_out.loc[:L.IS_END.normalize()]),
          "sharpe_excl_stress_HO": L.sharpe(d_out.loc["2024-01-01":L.HO_END.normalize()])}
count("C2_stress", 3)
tr_nf = L.run_strategy(pn, h=24, use_filter=False)
d_nf = L.daily_pnl(pn, tr_nf, start=first_sig, end=last_day)
key = lambda t: set(t["signal"])  # noqa: E731
only_nf = tr_nf[~tr_nf["signal"].isin(key(tr24))]
only_f = tr24[~tr24["signal"].isin(key(tr_nf))]
stress.update({"nofilter_sharpe_all": L.sharpe(d_nf), "nofilter_sharpe_IS": L.sharpe(d_nf.loc[:L.IS_END.normalize()]),
               "nofilter_sharpe_HO": L.sharpe(d_nf.loc["2024-01-01":L.HO_END.normalize()]),
               "trades_only_without_filter": len(only_nf), "pnl_w_only_without_filter": float((only_nf["w"] * only_nf["ret"]).sum()),
               "trades_only_with_filter": len(only_f), "pnl_w_only_with_filter": float(only_f["pnl_w"].sum()),
               "depeg_hours_by_year": {int(k): int(v) for k, v in pn.depeg.groupby(pn.idx.year).sum().items()}})
top10_sig = tr24.sort_values("pnl_w", ascending=False).head(10)["signal"]
stress["top10_trades_also_without_filter"] = int(top10_sig.isin(tr_nf["signal"]).sum())
count("C2_depeg_filter", 3)
(OUT / "stress_depeg_h24.json").write_text(json.dumps(stress, indent=1, default=str))
print(json.dumps(stress, indent=1, default=str))

# ---------- §3 deux jambes ----------
legs = []
for per, lo, hi in (("IS", first_sig, L.IS_END), ("HO", pd.Timestamp("2024-01-01"), L.HO_END),
                    ("FWD", L.HO_END + pd.Timedelta(hours=1), pn.idx[-1]), ("ALL", first_sig, pn.idx[-1])):
    for side in (1, -1):
        sub = tr24[(tr24["side"] == side) & (tr24["entry"] >= lo) & (tr24["entry"] <= hi)]
        if len(sub) < 3:
            legs.append({"period": per, "side": side, "n": len(sub), "bps_per_trade": float(sub["ret"].mean() * 1e4) if len(sub) else np.nan})
            continue
        d_leg = L.daily_pnl(pn, sub, start=max(lo.normalize(), first_sig), end=min(hi.normalize(), last_day))
        legs.append({"period": per, "side": side, "n": len(sub), "bps_per_trade": float(sub["ret"].mean() * 1e4),
                     "t_trades_hac": L.hac_t(sub["ret"]), "hit_rate": float((sub["ret"] > 0).mean()),
                     "sharpe_leg_daily": L.sharpe(d_leg)})
        count("C3_legs")
legs = pd.DataFrame(legs)
legs.to_csv(OUT / "legs_h24.csv", index=False, float_format="%.4f")
print(legs.to_string())

# ---------- §4 sélection d'horizon ----------
ho = {h: L.sharpe(periods(series[(h, 0)])["HO"]) for h in (1, 4, 24)}
is_ = {h: L.sharpe(periods(series[(h, 0)])["IS"]) for h in (1, 4, 24)}
n_ho = len(periods(series[(24, 0)])["HO"])
se_ho = float(np.sqrt((1 + ho[24] ** 2 / 2) / (n_ho / 365)))
mean3 = float(np.mean(list(ho.values())))
between = float(np.var(list(ho.values()), ddof=1))
tau2 = max(between - se_ho ** 2, 0.0)
B = se_ho ** 2 / (se_ho ** 2 + tau2) if (se_ho ** 2 + tau2) > 0 else 1.0
shrunk = mean3 + (1 - B) * (ho[24] - mean3)
# walk-forward : au 1er janvier de chaque année, choisir l'horizon au meilleur Sharpe passé (fenêtre croissante)
wf_rows, pieces = [], []
for y in range(2019, last_day.year + 1):
    past = {h: L.sharpe(series[(h, 0)].loc[:f"{y - 1}-12-31"]) for h in (1, 4, 24)}
    pick = max(past, key=past.get)
    seg = series[(pick, 0)].loc[f"{y}-01-01":f"{y}-12-31"]
    pieces.append(seg)
    wf_rows.append({"year": y, "picked_h": pick, **{f"past_sr_h{h}": v for h, v in past.items()},
                    "oos_sr_picked": L.sharpe(seg), "oos_sr_h24": L.sharpe(series[(24, 0)].loc[f"{y}-01-01":f"{y}-12-31"])})
wf = pd.DataFrame(wf_rows)
wf.to_csv(OUT / "horizon_wf.csv", index=False, float_format="%.4f")
wf_series = pd.concat(pieces)
sel = {"holdout_sr": ho, "is_sr": is_, "a_mean_of_three_holdouts": mean3, "holdout_se_h24": se_ho,
       "between_var": between, "tau2": tau2, "shrink_B": B, "b_shrunk_h24": shrunk,
       "c_wf_selected_sr_2019_end": L.sharpe(wf_series), "c_wf_selected_sr_2024_HOend": L.sharpe(wf_series.loc["2024-01-01":L.HO_END.normalize()]),
       "c_wf_selected_sr_2019_2023": L.sharpe(wf_series.loc[:"2023-12-31"]),
       "h24_fixed_sr_2019_end": L.sharpe(series[(24, 0)].loc["2019-01-01":]),
       "sidak_p_holdout_h24": None}
from scipy.stats import norm  # noqa: E402
p_one = 1 - norm.cdf(L.hac_t(periods(series[(24, 0)])["HO"]))
sel["p_one_sided_holdout_h24"] = float(p_one)
sel["sidak_p_holdout_h24"] = float(1 - (1 - p_one) ** 3)
sel["mde_sharpe_holdout"] = L.mde_sharpe(n_ho)
n_fwd = len(periods(series[(24, 0)])["FWD"])
sel["mde_sharpe_forward"] = L.mde_sharpe(max(n_fwd, 1))
sel["mde_sharpe_6m"] = L.mde_sharpe(182)
sel["mde_sharpe_3y"] = L.mde_sharpe(3 * 365)
count("S1_selection", 4)
(OUT / "horizon_selection.json").write_text(json.dumps(sel, indent=1, default=str))
print(json.dumps(sel, indent=1, default=str))
print(wf.to_string())

# ---------- WF 5 plis expansifs (lecture RESEARCH_PASS, sans paramètre estimé) ----------
folds = []
for y in (2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026):
    dd = d24.loc[f"{y}-01-01":f"{y}-12-31"]
    folds.append({"fold_year": y, "sharpe": L.sharpe(dd), "pnl": float(dd.sum())})
pd.DataFrame(folds).to_csv(OUT / "folds_h24.csv", index=False, float_format="%.4f")

(OUT / "coverage.json").write_text(json.dumps(coverage, indent=1))
(OUT / "_nt_repro.json").write_text(json.dumps(NT, indent=1))
