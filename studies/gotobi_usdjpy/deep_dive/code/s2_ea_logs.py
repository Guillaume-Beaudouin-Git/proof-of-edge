"""S2 — donnée neuve : les événements gotobi des journaux de l'EA FTMO (bid/ask réels, 2026-08 → 10).

Pré-enregistrement : ../PREREG_DEEP.md §4 (commité avant le lancement). Lecture descriptive : ~12
événements, dont 4 dans D. Une seule alarme, qui ne peut que bloquer (critère L5) :
  - coût réalisé médian (fourchette aux 4 minutes + 1,0 bp de commission) > 2,5 bps ;
  - ou une des 4 minutes absente pour plus de 2 événements.
Horloge : ts_server = UTC + 3 h sur toute la fenêtre (heure d'été US), vérifié dans le script.

Usage : /usr/bin/python3 s2_ea_logs.py
Sorties : ../out/s2_ea_logs.txt, ../out/s2_ea_logs.json, ../out/s2_ea_events.csv
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "code"))
import s2_holdout as H  # noqa: E402

OUT = HERE.parent / "out"
LOGS = sorted(glob.glob(os.environ.get("RESEARCH_DATA_ROOT", "data") + "/raw/ftmo_ea_spread_logs/spread_log_2026*.csv"))
COMMISSION_EVENT = 1.0
ALARM_COST = 2.5
D_CATS = ("D25", "DME")


def load() -> pd.DataFrame:
    d = pd.concat([pd.read_csv(f) for f in LOGS])
    d = d[d["symbol"] == "USDJPY"].copy()
    srv = pd.to_datetime(d["ts_server"], format="%Y.%m.%d %H:%M:%S")
    par = pd.to_datetime(d["ts_paris"], format="%Y.%m.%d %H:%M:%S")
    assert ((srv - par) == pd.Timedelta(hours=1)).all(), "serveur ≠ Paris + 1 h : horloge à revoir"
    assert srv.max() < pd.Timestamp("2026-11-01"), "fenêtre hors heure d'été US"
    d.index = (srv - pd.Timedelta(hours=3)).dt.floor("min")
    d = d[~d.index.duplicated()].sort_index()
    d["mid"] = (d["bid"] + d["ask"]) / 2
    return d[["bid", "ask", "mid", "spread_bps"]]


def snap(d: pd.DataFrame, t: pd.Timestamp):
    return d.loc[t] if t in d.index else None


def event(d: pd.DataFrame, day: pd.Timestamp) -> dict | None:
    ts = [day - pd.Timedelta(hours=1), day + pd.Timedelta(minutes=54), day + pd.Timedelta(minutes=56),
          day + pd.Timedelta(minutes=120)]
    s = [snap(d, t) for t in ts]
    r: dict = dict(day=day, missing=sum(x is None for x in s))
    if r["missing"]:
        return r
    a0, a1, b0, b1 = s
    r["A_exec"] = (a1["bid"] / a0["ask"] - 1) * 1e4
    r["B_exec"] = (1 - b1["ask"] / b0["bid"]) * 1e4
    r["A_mid"] = (a1["mid"] / a0["mid"] - 1) * 1e4
    r["B_mid"] = -(b1["mid"] / b0["mid"] - 1) * 1e4
    r["A_bid"] = (a1["bid"] / a0["bid"] - 1) * 1e4
    r["B_bid"] = -(b1["bid"] / b0["bid"] - 1) * 1e4
    # stop de 25 bps sur les instantanés de minute (approximation : pas de chemin intra-minute)
    lvl_a = a0["ask"] * (1 - H.STOP_BPS / 1e4)
    path_a = d.loc[ts[0] + pd.Timedelta(minutes=1): ts[1] - pd.Timedelta(minutes=1), "bid"]
    hit_a = path_a[path_a <= lvl_a]
    r["stopA"] = len(hit_a) > 0
    r["A_exec_s"] = (min(hit_a.iloc[0], lvl_a) / a0["ask"] - 1) * 1e4 if r["stopA"] else r["A_exec"]
    lvl_b = b0["bid"] * (1 + H.STOP_BPS / 1e4)
    path_b = d.loc[ts[2] + pd.Timedelta(minutes=1): ts[3] - pd.Timedelta(minutes=1), "ask"]
    hit_b = path_b[path_b >= lvl_b]
    r["stopB"] = len(hit_b) > 0
    r["B_exec_s"] = (1 - max(hit_b.iloc[0], lvl_b) / b0["bid"]) * 1e4 if r["stopB"] else r["B_exec"]
    r["exec"] = r["A_exec_s"] + r["B_exec_s"]
    r["net"] = r["exec"] - COMMISSION_EVENT
    r["mid"] = r["A_mid"] + r["B_mid"]
    r["bid"] = r["A_bid"] + r["B_bid"]
    r["spread_cost"] = r["mid"] - (r["A_exec"] + r["B_exec"])
    r["cost"] = r["spread_cost"] + COMMISSION_EVENT
    r["spreads_4min"] = [float(x["spread_bps"]) for x in s]
    r["px"] = float(a0["mid"])
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = load()
    cal = pd.bdate_range("2026-08-01", "2026-10-31")
    cat = H.categories(cal)
    first, last = d.index.min(), d.index.max()
    cat = cat[(cat.index - pd.Timedelta(hours=1) >= first) & (cat.index + pd.Timedelta(minutes=120) <= last)]
    rows = [event(d, x) for x in cat.index]
    ev = pd.DataFrame(rows).set_index("day")
    ev["cat"] = cat
    ev.drop(columns=["spreads_4min"], errors="ignore").to_csv(OUT / "s2_ea_events.csv")
    n_missing = int((ev["missing"] > 0).sum())
    full = ev[ev["missing"] == 0]
    med_cost = float(full["cost"].median())
    alarm = med_cost > ALARM_COST or n_missing > 2
    L = [f"Journaux EA USDJPY : {first} → {last} UTC ({len(d)} minutes) ; horloge serveur = UTC + 3 h vérifiée",
         f"Événements gotobi dans la fenêtre : {len(ev)} (D : {int(ev['cat'].isin(D_CATS).sum())}) ; "
         f"avec une des 4 minutes absente : {n_missing}",
         "",
         "Par événement (bps) — exécutable = achat à l'ask / vente au bid, stop 25 bps sur instantanés de minute",
         f"  {'jour':10s} {'cat':6s} {'A exéc':>7s} {'B exéc':>7s} {'total':>7s} {'net':>7s} | {'mid':>7s} {'bid':>7s} "
         f"{'coût':>5s} | fourchettes 23:00/00:54/00:56/02:00   USDJPY"]
    for x, r in ev.iterrows():
        if r["missing"]:
            L.append(f"  {x.date()} {r['cat']:6s} minute(s) absente(s) : {int(r['missing'])}")
            continue
        sp = "/".join(f"{v:.2f}" for v in r["spreads_4min"])
        L.append(f"  {x.date()} {r['cat']:6s} {r['A_exec_s']:+7.2f} {r['B_exec_s']:+7.2f} {r['exec']:+7.2f} {r['net']:+7.2f} | "
                 f"{r['mid']:+7.2f} {r['bid']:+7.2f} {r['cost']:5.2f} | {sp}  {r['px']:.2f}"
                 + ("  [stop A]" if r["stopA"] else "") + ("  [stop B]" if r["stopB"] else ""))
    res: dict = dict(window=[str(first), str(last)], n_events=len(ev), n_missing=n_missing, median_cost=med_cost,
                     alarm=bool(alarm))
    L.append("")
    for lab, sub in (("D (25 + fin de mois)", full[full["cat"].isin(D_CATS)]), ("AUTRES", full[~full["cat"].isin(D_CATS)]),
                     ("tous", full)):
        s = dict(n=len(sub), A=float(sub["A_exec_s"].mean()), B=float(sub["B_exec_s"].mean()), exec=float(sub["exec"].mean()),
                 net=float(sub["net"].mean()), mid=float(sub["mid"].mean()), bid=float(sub["bid"].mean()),
                 cost=float(sub["cost"].mean()))
        res[lab] = s
        L.append(f"  {lab:22s} n {s['n']:2d} : exécutable {s['exec']:+6.2f} (A {s['A']:+6.2f}, B {s['B']:+6.2f}) ; "
                 f"net {s['net']:+6.2f} ; brut mid {s['mid']:+6.2f}, brut bid {s['bid']:+6.2f} ; coût moyen {s['cost']:.2f}")
    shift = float((full["bid"] - full["mid"]).mean())
    res["bid_minus_mid"] = shift
    res["px_last"] = float(d["mid"].iloc[-1])
    L += ["",
          f"Convention : brut au bid − brut au mid = {shift:+.2f} bp par événement (la série historique est en bid)",
          f"Coût réalisé par événement (fourchette aux 4 minutes + 1,0 bp de commission) : médiane {med_cost:.2f}, "
          f"moyenne {full['cost'].mean():.2f}, max {full['cost'].max():.2f}",
          f"USDJPY au dernier relevé : {d['mid'].iloc[-1]:.3f} ; moyenne de la fenêtre {d['mid'].mean():.2f}",
          f"Alarme L5 (coût médian > {ALARM_COST} ou > 2 événements incomplets) : {'OUI → ne pas lancer' if alarm else 'NON'}"]
    (OUT / "s2_ea_logs.json").write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False))
    (OUT / "s2_ea_logs.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
