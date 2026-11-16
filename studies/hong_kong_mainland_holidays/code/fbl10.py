"""FBL-10 — Hong Kong sans l'acheteur continental (PREREG.md) : jours fermés et réouvertures du canal sud, contrôle sur
l'or, puis plis et admission funded. Lecture unique, décision.

Séries quotidiennes Yahoo dans ../_data/ (code/fetch.py) ; or : deep_history_utc par `a5b_expiry/code/a5b_holdout.py` ;
admission : `s2_gotobi_dose/code/s2_validation.py`. À lancer avec `python3 -I` : les CSV lus sont téléchargés.

Usage : /usr/bin/python3 -I fbl10.py                  (à ne lancer qu'une fois)
        /usr/bin/python3 -I fbl10.py --dry <dossier>   (essai à blanc : rendements synthétiques)
Sorties : ../out/fbl10.txt, ../out/fbl10.json, ../out/fbl10_jours.csv
"""
from __future__ import annotations

import site
import sys

sys.path.append(site.getusersitepackages())
sys.dont_write_bytecode = True

import io  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in ("a5b_expiry/code", "s2_gotobi_dose/code"):
    sys.path.insert(0, str(ROOT / p))
import a5b_holdout as AH  # noqa: E402
import s2_validation as V  # noqa: E402

DATA = HERE.parent / "_data"
OUT = HERE.parent / "out"
NY = "America/New_York"
LAUNCH = pd.Timestamp("2014-11-17")
SPLIT = pd.Timestamp("2020-01-01")
K0, NOTIONAL, STOP = 4.0, 3000.0, 0.02
WIN_START, WIN_END = pd.Timestamp("2014-11-17"), pd.Timestamp("2026-06-05")


def read(name: str) -> pd.DataFrame:
    d = pd.read_csv(DATA / f"{name}.csv", index_col=0, parse_dates=True)
    return d.dropna(subset=["Open", "Close"])


def calendar(hk: pd.DataFrame, ss: pd.DataFrame) -> pd.Series:
    days = hk.index[hk.index >= LAUNCH]
    closed = ~days.isin(ss.index)
    prev_closed = np.r_[False, closed[:-1]]
    kind = np.where(closed, "fermé", np.where(prev_closed, "réouverture", "ordinaire"))
    return pd.Series(kind, index=days)


def holiday(d: pd.Timestamp) -> str:
    if d.month in (1, 2):
        return "Nouvel An lunaire"
    if d.month == 5:
        return "fête du Travail"
    if d.month == 10 or (d.month == 9 and d.day >= 28):
        return "fête nationale"
    return "autres (Qingming, Bateaux-dragons, mi-automne)"


def legs(r: pd.Series, kind: pd.Series) -> dict:
    o = r[kind == "ordinaire"]
    out = {}
    for k in ("fermé", "réouverture"):
        x = r[kind == k]
        out[k] = dict(n=int(len(x)), mean=float(x.mean()), diff=float(x.mean() - o.mean()), t_hac=AH.hac_t(x - o.mean()))
    out["ordinaire"] = dict(n=int(len(o)), mean=float(o.mean()))
    return out


def main(out: Path, dry: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    lines = ["ESSAI À BLANC (rendements synthétiques)"] if dry else []
    hk, ss, tr = read("HSI"), read("000001_SS"), read("2800_HK")
    if dry:
        rng = np.random.default_rng(3)
        hk = hk.assign(Close=hk["Open"] * np.exp(rng.normal(0.0, 0.012, len(hk))))
        tr = tr.assign(Close=tr["Open"] * np.exp(rng.normal(0.0, 0.012, len(tr))))
    kind = calendar(hk, ss)
    r = ((hk["Close"] / hk["Open"] - 1) * 1e4).reindex(kind.index)
    L = legs(r, kind)
    k1 = L["fermé"]["diff"] <= -10.0
    k2 = L["réouverture"]["diff"] >= 15.0
    per = {}
    for nm, sel in (("2015-2019", kind.index < SPLIT), ("2020-2026", kind.index >= SPLIT)):
        per[nm] = legs(r[sel], kind[sel])
    k3 = (per["2020-2026"]["fermé"]["diff"] < per["2015-2019"]["fermé"]["diff"]
          and per["2020-2026"]["réouverture"]["diff"] > per["2015-2019"]["réouverture"]["diff"])
    gold = AH.load("XAUUSD", dry, 21)
    t0 = AH.local_times(kind.index - pd.Timedelta(days=1), "20:00", NY)
    t1 = AH.local_times(kind.index, "03:00", NY)
    g = pd.Series((AH.px_at(gold, t1) / AH.px_at(gold, t0) - 1) * 1e4, index=kind.index)
    g_closed, g_ord = g[kind == "fermé"].dropna(), g[kind == "ordinaire"].dropna()
    k4 = float(g_closed.mean() - g_ord.mean()) <= 0
    res: dict = dict(K0=K0, counts=kind.value_counts().to_dict(), legs=L, periods=per, K1=bool(k1), K2=bool(k2),
                     K3=bool(k3), gold=dict(n_closed=int(len(g_closed)), closed=float(g_closed.mean()), ordinary=float(g_ord.mean()),
                                            diff=float(g_closed.mean() - g_ord.mean())), K4=bool(k4))
    alive = k1 and k2 and k3 and k4
    if alive:
        ev = kind[kind != "ordinaire"]
        h = hk.reindex(ev.index)
        short = ev == "fermé"
        pnl = np.where(short, -r.reindex(ev.index), r.reindex(ev.index))
        stopped = np.where(short, h["High"] >= h["Open"] * (1 + STOP), h["Low"] <= h["Open"] * (1 - STOP))
        pnl = pd.Series(np.where(stopped, -STOP * 1e4, pnl) - K0, index=ev.index)
        folds = []
        for c in np.array_split(np.arange(len(pnl)), 5):
            y = pnl.iloc[c]
            folds.append(dict(debut=str(y.index.min().date()), fin=str(y.index.max().date()), n=int(len(y)), net=float(y.mean())))
        e1 = sum(f["net"] > 0 for f in folds) >= 4
        sleeve = pnl * NOTIONAL / 1e4
        book = pd.read_csv(io.StringIO(V.A.git_show(V.A.BR_COMMIT, V.A.BR_CSV)), index_col=0, parse_dates=True)
        idx = book.index.union(sleeve.index)
        idx = idx[(idx >= WIN_START) & (idx <= WIN_END)]
        book = book.reindex(idx).fillna(0.0)
        adm = V.admission(book["Livre complet"] - book["ORB seul"], sleeve.reindex(idx).fillna(0.0), "3 000 $")
        res.update(trade=dict(n=int(len(pnl)), net=float(pnl.mean()), stops=float(stopped.mean())), folds=folds, E1=bool(e1),
                   admission=adm, E4=adm["verdict"] == "ADMIS")
        launch = bool(e1 and adm["verdict"] == "ADMIS")
    else:
        launch = False
    mech = L["fermé"]["diff"] >= 0 or L["réouverture"]["diff"] <= 0
    res["decision"] = "LANCER (sous réserve de la fourchette HK50.cash)" if launch else "ARCHIVER"
    res["nature"] = None if launch else ("mécanique" if mech else "de puissance")

    # rapporté, sans décider
    hol = {}
    for k in ("fermé", "réouverture"):
        x = r[kind == k]
        hol[k] = {nm: dict(n=int(len(v)), diff=float(v.mean() - L["ordinaire"]["mean"]))
                  for nm, v in x.groupby([holiday(d) for d in x.index])}
    yrs = {}
    for k in ("fermé", "réouverture"):
        x = r[kind == k] - L["ordinaire"]["mean"]
        yrs[k] = {str(y): float(v.mean()) for y, v in x.groupby(x.index.year)}
    rt = ((tr["Close"] / tr["Open"] - 1) * 1e4).reindex(kind.index)
    res["reported"] = dict(by_holiday=hol, by_year=yrs, tracker_2800=legs(rt, kind))

    fmt = lambda x: f"{x['diff']:+.2f} bps (n {x['n']}, t {x['t_hac']:+.2f})"  # noqa: E731
    lines += [f"Calendrier (Yahoo, depuis 2014-11-17) : {res['counts']}",
              f"^HSI ouverture → clôture, écart aux jours ordinaires (moyenne ordinaire {L['ordinaire']['mean']:+.2f}) :",
              f"  K1 jours fermés {fmt(L['fermé'])} → {k1} (seuil ≤ −10)",
              f"  K2 réouvertures {fmt(L['réouverture'])} → {k2} (seuil ≥ +15)",
              "  K3 dose : " + " ; ".join(f"{nm} fermés {v['fermé']['diff']:+.2f}, réouvertures {v['réouverture']['diff']:+.2f}"
                                          for nm, v in per.items()) + f" → {k3}",
              f"  K4 or, séance asiatique : jours fermés {res['gold']['closed']:+.2f} contre ordinaires {res['gold']['ordinary']:+.2f} "
              f"(écart {res['gold']['diff']:+.2f}, n {res['gold']['n_closed']}) → {k4}"]
    if alive:
        lines += [f"  trade : n {res['trade']['n']}, net {res['trade']['net']:+.2f} bps, stops {res['trade']['stops']:.0%}",
                  "  E1 plis : " + " ; ".join(f"{f['debut'][:7]}→{f['fin'][:7]} {f['net']:+.1f}" for f in folds) + f" → {e1}",
                  "  E4 :"] + ["  " + s for s in V.fmt_adm(adm)]
    lines += [f"→ FBL-10 : {res['decision']}" + (f" (mort {res['nature']})" if res["nature"] else ""),
              "Rapporté :"]
    for k, v in hol.items():
        lines.append(f"  {k} par fête : " + " ; ".join(f"{nm} {x['diff']:+.1f} (n {x['n']})" for nm, x in v.items()))
    for k, v in yrs.items():
        lines.append(f"  {k} par année : " + " ".join(f"{y}:{m:+.0f}" for y, m in v.items()))
    t8 = res["reported"]["tracker_2800"]
    lines.append(f"  2800.HK (ouvertures figées à 15,6 %) : fermés {t8['fermé']['diff']:+.2f}, réouvertures {t8['réouverture']['diff']:+.2f}")
    pd.DataFrame({"kind": kind, "r_hsi": r, "gold_asia": g}).to_csv(out / "fbl10_jours.csv")
    (out / "fbl10.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    (out / "fbl10.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dry":
        main(Path(sys.argv[2]), dry=True)
    else:
        main(OUT, dry=False)
