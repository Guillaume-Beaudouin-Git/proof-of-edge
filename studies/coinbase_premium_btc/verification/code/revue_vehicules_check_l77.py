"""Contrôle indépendant, par trade : rendement C9 au prix Kraken PF_XBTUSD vs Binance vs Coinbase (pas de série quotidienne)."""
import sys, json
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import c9lib as L
from c9lib import np, pd
DL = Path(sys.argv[2])
pn = L.build_panel(); idx = pn.idx
tr = L.run_strategy(pn, h=24)
rows = []
for p in sorted((DL/"kraken_hist").glob("trade_*.json")):
    rows += json.loads(p.read_text()).get("candles", [])
kr = pd.Series({pd.Timestamp(int(c["time"]), unit="ms"): float(c["close"]) for c in rows}).sort_index()
kr = kr[~kr.index.duplicated()].reindex(idx)
print("Kraken 1h candles:", kr.notna().sum(), kr.first_valid_index(), kr.last_valid_index())
e, x, s, w = tr["e"].values, tr["x"].values, tr["side"].values, tr["w"].values
ok = np.isfinite(kr.values[e]) & np.isfinite(kr.values[x])
def ret(p):
    pv = p.ffill().values; return s*(pv[x]/pv[e]-1)
r_kr, r_bn, r_cb = ret(kr)[ok], ret(pn.bn_btc)[ok], ret(pn.cb_btc)[ok]
n = ok.sum()
def t(a): return a.mean()/a.std(ddof=1)*np.sqrt(len(a))
print(f"n={n}  mean bps: KR {r_kr.mean()*1e4:.2f} | BN {r_bn.mean()*1e4:.2f} | CB {r_cb.mean()*1e4:.2f}")
print(f"KR-BN {(r_kr-r_bn).mean()*1e4:.2f} bps (t {t(r_kr-r_bn):.2f}) ; KR-CB {(r_kr-r_cb).mean()*1e4:.2f} (t {t(r_kr-r_cb):.2f}) ; BN-CB {(r_bn-r_cb).mean()*1e4:.2f} (t {t(r_bn-r_cb):.2f})")
d = r_bn-r_cb; beta = np.polyfit(d, r_kr-r_cb, 1)[0]; print(f"beta KR vers Binance (0=CB,1=BN): {beta:.3f}")
# pondéré par w, équivalent P&L par trade (coût taker Kraken 10.13 bps + funding ignoré)
for nm, r in (("KR", r_kr), ("BN", r_bn), ("CB", r_cb)):
    pnl = w[ok]*(r - 10.13e-4)
    print(f"{nm}: P&L net/trade moyen {pnl.mean()*1e4:.2f} bps-equity, t {t(pnl):.2f}, Sharpe par trade*sqrt(100/an) {pnl.mean()/pnl.std(ddof=1)*np.sqrt(n/ ((idx[x[ok]][-1]-idx[e[ok]][0]).days/365.25)):.2f}")
# annees
yrs = pd.DatetimeIndex(idx[e[ok]]).year
print(pd.DataFrame({"yr":yrs,"KR-BN":(r_kr-r_bn)*1e4,"KR-CB":(r_kr-r_cb)*1e4}).groupby("yr").agg(["mean","count"]).round(2))
