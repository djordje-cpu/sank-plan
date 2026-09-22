#!/usr/bin/env python3
"""
normativ_engine.py

Reference engine behind the Normativ product screens. Simulates one demo
venue ("Restoran Primer", Vracar) for ISO week 38 of 2026 and runs the same
agent pipeline the product would run on live SEF and ESIR data:

  SupplierFeedAgent   SEF e-invoices (UBL-like) with noisy line descriptions
  MatchingAgent       entity resolution: supplier line text -> ingredient master
  SalesAgent          ESIR item sales for the week
  NormativAgent       theoretical consumption = sales x recipe norms
  InventoryAgent      actual usage = opening + purchases - closing count
  VarianceAgent       actual vs theoretical, net of allowed shrinkage (kalo)
  PriceDriftAgent     this week's paid price vs trailing four-week average
  MenuEngineeringAgent  Kasavana-Smith matrix on net-of-VAT contribution
  RepricingAgent      price that restores target food cost, rounded to 10 RSD
  ActionAgent         ranks interventions by weekly RSD impact
  PortfolioAgent      accountant's multi-client console (SEF deadlines, flags)

All data is synthetic and seeded. Menu prices include 20% VAT, so every
margin and food-cost ratio is computed on the net price.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np

RNG = np.random.default_rng(38)
VAT = 1.20
TARGET_FC = {"main": 0.33, "starter": 0.28, "dessert": 0.25}
MAX_STEP = 0.08          # guardrail: never recommend more than +8% in one step
WEEK = "Nedelja 38 · 14–20. septembar 2026"


# ------------------------------------------------------------------ master data
@dataclass
class Ingredient:
    code: str
    name: str
    unit: str
    base_price: float     # RSD per unit, trailing 4-week average
    drift: float          # this week's price change vs trailing average
    leak: float           # true excess usage this week (hidden from the engine)
    kalo: float           # allowed shrinkage tolerance
    supplier: str
    aliases: tuple


S = {
    "S1": "Šumadija Meso d.o.o.", "S2": "Mlekara Planina d.o.o.",
    "S3": "Zeleni Pijac d.o.o.", "S4": "Veleprodaja Dunav d.o.o.",
    "S5": "Pekara Varoš d.o.o.", "S6": "Destilerija Brdo d.o.o.",
    "S7": "Pivo Distribucija d.o.o.", "S8": "Podrum Morava d.o.o.",
}

ING = [
    Ingredient("karmenadl", "Svinjski karmenadl b/k", "kg", 820, .061, .09, .02, "S1",
               ("SV KARMENADL BK", "KARMENADL SVINJSKI BEZ KOSTI")),
    Ingredient("vrat", "Svinjski vrat b/k", "kg", 760, .078, .03, .02, "S1",
               ("SV VRAT BK", "SVINJSKI VRAT BEZ KOSTI")),
    Ingredient("mleveno", "Mešavina za roštilj", "kg", 830, .012, .04, .02, "S1",
               ("MESAVINA ROSTILJ JUNE SVINJA", "MLEVENO MESO ZA CEVAPE")),
    Ingredient("piletina", "Pileći file", "kg", 680, -.008, .02, .02, "S1",
               ("PILECI FILE", "FILE PILECI SVEZ")),
    Ingredient("teletina", "Teletina za čorbu", "kg", 1150, .015, .01, .02, "S1",
               ("TELETINA CORBA", "TELECE MESO ZA CORBU")),
    Ingredient("kajmak", "Kajmak mladi", "kg", 1580, .114, .21, .02, "S2",
               ("KAJMAK MLADI", "KAJMAK MLADI KANTA")),
    Ingredient("sir", "Beli sir kravlji", "kg", 690, .010, .06, .02, "S2",
               ("SIR BELI KRAVLJI", "KRAVLJI SIR MEKI")),
    Ingredient("kackavalj", "Kačkavalj", "kg", 1120, .022, .07, .02, "S2",
               ("KACKAVALJ", "KACKAVALJ KRAVLJI BLOK")),
    Ingredient("jaja", "Jaja L", "kom", 17, .000, .02, .03, "S3",
               ("JAJA L KLASA", "JAJA KONZUMNA L")),
    Ingredient("paradajz", "Paradajz", "kg", 175, -.135, .03, .05, "S3",
               ("PARADAJZ I KLASA", "PARADAJZ")),
    Ingredient("krastavac", "Krastavac", "kg", 110, -.090, .00, .05, "S3",
               ("KRASTAVAC SALATAR", "KRASTAVAC")),
    Ingredient("paprika", "Paprika babura", "kg", 160, -.040, .02, .05, "S3",
               ("PAPRIKA BABURA", "PAPRIKA")),
    Ingredient("luk", "Crni luk", "kg", 85, .005, .01, .05, "S3",
               ("LUK CRNI", "CRNI LUK MREZA")),
    Ingredient("krompir", "Krompir", "kg", 70, .020, .04, .05, "S3",
               ("KROMPIR BELI", "KROMPIR")),
    Ingredient("ulje", "Suncokretovo ulje", "l", 225, .052, .12, .03, "S4",
               ("ULJE SUNCOKRETOVO", "ULJE SUNC JESTIVO")),
    Ingredient("brasno", "Brašno T-400", "kg", 68, .000, .02, .02, "S4",
               ("BRASNO T400", "BRASNO TIP 400")),
    Ingredient("prezle", "Prezle", "kg", 175, .010, .05, .02, "S4",
               ("PREZLE", "PREZLE KRUSNE MRVICE")),
    Ingredient("orasi", "Orasi očišćeni", "kg", 1380, .018, .03, .02, "S4",
               ("ORAH JEZGRO", "ORASI OCISCENI")),
    Ingredient("lepinja", "Lepinja", "kom", 42, .000, .01, .02, "S5",
               ("LEPINJA", "LEPINJA ZA CEVAPE")),
    Ingredient("sljivovica", "Šljivovica (rinfuz)", "l", 1350, .000, .17, .01, "S6",
               ("RAKIJA SLJIVA RINFUZ", "SLJIVOVICA RINFUZ")),
    Ingredient("pivo", "Pivo točeno (keg)", "l", 205, .000, .09, .03, "S7",
               ("PIVO KEG TOCENO", "PIVO TOCENO BURE")),
    Ingredient("vino", "Vino belo (rinfuz)", "l", 480, .000, .06, .01, "S8",
               ("VINO BELO RINFUZ", "VINO STONO BELO")),
]
IDX = {i.code: i for i in ING}

MENU = {
    # item: (category, gross price RSD, units sold week 38, normativ)
    "Karađorđeva šnicla": ("main", 1390, 96, {"karmenadl": .22, "kajmak": .06, "jaja": 1,
                            "brasno": .02, "prezle": .045, "ulje": .09, "krompir": .25}),
    "Punjena pljeskavica": ("main", 1290, 74, {"mleveno": .28, "kackavalj": .04, "kajmak": .02,
                             "luk": .03, "krompir": .20, "ulje": .05}),
    "Ćevapi, 10 kom": ("main", 1190, 128, {"mleveno": .30, "lepinja": 1, "luk": .06, "kajmak": .03}),
    "Svinjski vrat": ("main", 1150, 81, {"vrat": .32, "krompir": .20, "ulje": .04, "luk": .03}),
    "Pileći file na žaru": ("main", 990, 57, {"piletina": .28, "krompir": .20, "ulje": .03,
                             "paprika": .05}),
    "Teleća čorba": ("starter", 420, 102, {"teletina": .07, "krompir": .04, "luk": .02,
                      "brasno": .01, "jaja": .2}),
    "Šopska salata": ("starter", 480, 118, {"paradajz": .15, "krastavac": .10, "paprika": .06,
                       "luk": .03, "sir": .06, "ulje": .01}),
    "Srpska salata": ("starter", 420, 61, {"paradajz": .17, "krastavac": .09, "paprika": .07,
                       "luk": .04, "ulje": .015}),
    "Pohovani kačkavalj": ("starter", 890, 39, {"kackavalj": .15, "jaja": 1, "brasno": .02,
                            "prezle": .04, "ulje": .08}),
    "Palačinke sa orasima": ("dessert", 420, 44, {"brasno": .06, "jaja": 1, "orasi": .04,
                              "ulje": .01}),
    "Šljivovica 0,05": ("bar", 280, 402, {"sljivovica": .05}),
    "Točeno pivo 0,5": ("bar", 330, 356, {"pivo": .50}),
    "Belo vino 0,2": ("bar", 390, 238, {"vino": .20}),
}


def price_now(code: str) -> float:
    i = IDX[code]
    return i.base_price * (1 + i.drift)


def fmt(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


# ------------------------------------------------------------------ agents
class SalesAgent:
    def run(self):
        return {k: v[2] for k, v in MENU.items()}


class NormativAgent:
    def run(self, sales):
        theo = {c: 0.0 for c in IDX}
        for item, qty in sales.items():
            for code, q in MENU[item][3].items():
                theo[code] += q * qty
        return theo


class InventoryAgent:
    """Opening count + SEF purchases - closing count. The leak is the ground
    truth the engine never sees directly; it only sees counts and invoices."""
    def run(self, theo):
        out = {}
        for code, t in theo.items():
            i = IDX[code]
            actual = t * (1 + i.leak + RNG.normal(0, 0.004))
            opening = t * RNG.uniform(0.35, 0.8)
            purchased = actual * RNG.uniform(0.95, 1.12)
            closing = opening + purchased - actual
            out[code] = dict(opening=opening, purchased=purchased, closing=closing,
                             actual=opening + purchased - closing)
        return out


class SupplierFeedAgent:
    NOISE = [lambda s: s, lambda s: s.replace(" ", ". ", 1),
             lambda s: s + " VAK 1/1", lambda s: s[:18]]

    def run(self, inv):
        invoices = {}
        for code, row in inv.items():
            i = IDX[code]
            desc = RNG.choice(i.aliases)
            if i.unit == "kg":
                desc = self.NOISE[int(RNG.integers(0, len(self.NOISE)))](desc)
            qty = float(round(row["purchased"])) if i.unit == "kom" else round(row["purchased"], 2)
            invoices.setdefault(i.supplier, []).append(dict(
                raw=desc, qty=qty, unit=i.unit,
                unit_price=round(price_now(code), 2), truth=code))
        invoices["S2"].append(dict(raw="SIR ZA PICU RENDANI 1KG", qty=4.0, unit="kg",
                                   unit_price=980.0, truth=None))
        invoices["S1"].append(dict(raw="MESANO MLEV. 70/30", qty=6.0, unit="kg",
                                   unit_price=955.0, truth="mleveno"))
        return invoices


class MatchingAgent:
    STOP = {"VAK", "1/1", "KG", "1KG", "BK", "B/K", "I", "KLASA"}

    def norm(self, s):
        s = s.upper().translate(str.maketrans("ČĆŠŽĐ", "CCSZD"))
        return [t for t in re.split(r"[^A-Z0-9/]+", s) if t and t not in self.STOP]

    def score(self, a, b):
        ta, tb = set(self.norm(a)), set(self.norm(b))
        jac = len(ta & tb) / max(1, len(ta | tb))
        seq = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
        pref = max((SequenceMatcher(None, x, y).ratio() for x in ta for y in tb), default=0)
        return 0.35 * jac + 0.35 * seq + 0.30 * pref

    def run(self, invoices):
        out = {}
        for sup, lines in invoices.items():
            res = []
            for ln in lines:
                cands = [(max(self.score(ln["raw"], a) for a in (*i.aliases, i.name)), i.code)
                         for i in ING if i.supplier == sup or True]
                cands.sort(reverse=True)
                conf, code = cands[0]
                gap = conf - cands[1][0]
                conf_adj = min(0.99, conf * (0.85 + min(gap, 0.3)))
                status = "Upareno" if conf_adj >= 0.72 else "Za potvrdu"
                res.append({**ln, "match": code, "match_name": IDX[code].name,
                            "confidence": round(conf_adj, 2), "status": status,
                            "correct": code == ln["truth"]})
            out[sup] = res
        return out


class VarianceAgent:
    def run(self, theo, inv):
        rows = []
        for code, t in theo.items():
            i, a = IDX[code], inv[code]["actual"]
            excess = a - t * (1 + i.kalo)
            rows.append(dict(code=code, name=i.name, unit=i.unit, theoretical=t, actual=a,
                             var_pct=(a / t - 1), over_kalo=max(0.0, excess),
                             rsd=max(0.0, excess) * price_now(code), kalo=i.kalo))
        rows.sort(key=lambda r: -r["rsd"])
        return rows


class PriceDriftAgent:
    def run(self, matched):
        rows = []
        for sup, lines in matched.items():
            for ln in lines:
                if ln["truth"] is None or not ln["correct"]:
                    continue
                i = IDX[ln["match"]]
                rows.append(dict(code=i.code, name=i.name, supplier=S[sup], unit=i.unit,
                                 avg4=i.base_price, now=price_now(i.code), drift=i.drift,
                                 weekly_rsd=ln["qty"] * (price_now(i.code) - i.base_price)))
        rows.sort(key=lambda r: -abs(r["weekly_rsd"]))
        return rows


class MenuEngineeringAgent:
    def run(self, sales):
        food = {k: v for k, v in MENU.items() if v[0] != "bar"}
        tot = sum(sales[k] for k in food)
        pop_thr = 0.70 / len(food)
        rows = []
        for item, (cat, gross, _, norm) in food.items():
            cost = sum(q * price_now(c) for c, q in norm.items())
            cost_prev = sum(q * IDX[c].base_price for c, q in norm.items())
            net = gross / VAT
            rows.append(dict(item=item, cat=cat, gross=gross, net=net, cost=cost,
                             cost_prev=cost_prev, fc=cost / net, cm=net - cost,
                             qty=sales[item], mix=sales[item] / tot))
        avg_cm = sum(r["cm"] * r["qty"] for r in rows) / tot
        for r in rows:
            hi_pop, hi_cm = r["mix"] >= pop_thr, r["cm"] >= avg_cm
            r["class"] = {(True, True): "Zvezda", (True, False): "Radni konj",
                          (False, True): "Zagonetka", (False, False): "Za preispitivanje"}[(hi_pop, hi_cm)]
        return rows, avg_cm, pop_thr


class RepricingAgent:
    def run(self, menu_rows):
        out = []
        for r in menu_rows:
            tgt = TARGET_FC[r["cat"]]
            if r["fc"] > tgt + 0.01:
                ideal = math.ceil(r["cost"] / tgt * VAT / 10) * 10
                new_gross = min(ideal, math.floor(r["gross"] * (1 + MAX_STEP) / 10) * 10)
                out.append(dict(item=r["item"], fc=r["fc"], target=tgt, gross=r["gross"],
                                ideal=ideal, capped=new_gross < ideal,
                                fc_after=r["cost"] / (new_gross / VAT),
                                new_gross=new_gross, delta=new_gross - r["gross"],
                                weekly_rsd=(new_gross - r["gross"]) / VAT * r["qty"],
                                cost_up=r["cost"] - r["cost_prev"]))
        out.sort(key=lambda r: -r["weekly_rsd"])
        return out


class ActionAgent:
    PLAYBOOK = {
        "kajmak": "Kutlača od 60 g za kajmak na Karađorđevoj i ćevapima",
        "sljivovica": "Merice 0,05 na šanku i provera evidentiranja pića",
        "karmenadl": "Porcionisanje karmenadla od 220 g na vagi pre pohovanja",
        "ulje": "Plan zamene ulja u fritezi po broju ciklusa, ne po oku",
        "pivo": "Čišćenje linija i provera pene na točenom pivu",
        "kackavalj": "Porcionisanje kačkavalja od 150 g za pohovanje",
    }

    def run(self, var_rows, reprice, drift):
        acts = []
        for r in var_rows[:6]:
            if r["code"] in self.PLAYBOOK and r["rsd"] > 0:
                acts.append(dict(kind="Utrošak", title=self.PLAYBOOK[r["code"]],
                                 why=f"{r['name']}: +{r['var_pct']*100:.0f}% iznad normativa",
                                 weekly_rsd=r["rsd"]))
        for p in reprice[:2]:
            acts.append(dict(kind="Cena", title=f"{p['item']}: {fmt(p['gross'])} → {fmt(p['new_gross'])} RSD",
                             why=f"Trošak namirnica {p['fc']*100:.1f}% uz cilj {p['target']*100:.0f}%",
                             weekly_rsd=p["weekly_rsd"]))
        top = drift[0]
        acts.append(dict(kind="Nabavka", title=f"Nova ponuda za {top['name'].lower()}",
                         why=f"{top['supplier']}: +{top['drift']*100:.1f}% u odnosu na 4 nedelje",
                         weekly_rsd=top["weekly_rsd"]))
        acts.sort(key=lambda a: -a["weekly_rsd"])
        return acts


class PortfolioAgent:
    """Accountant's console across client venues (synthetic)."""
    NAMES = ["Restoran Primer", "Bistro Lipa", "Kafana Česma", "Picerija Trg",
             "Roštilj Kod Mosta", "Konoba Obala", "Gostionica Brdo", "Hotel Sava, F&B"]

    def run(self, primer_leak_pct, primer_unmatched, primer_invoices):
        rows = []
        for k, n in enumerate(self.NAMES):
            if k == 0:
                leak, unm, inv = primer_leak_pct, primer_unmatched, primer_invoices
            else:
                leak = float(RNG.gamma(2.2, 0.0075))
                unm = int(RNG.poisson(1.2))
                inv = int(RNG.integers(6, 22))
            due = int(RNG.poisson(1.5))
            status = "Hitno" if (leak > 0.03 or due >= 3) else ("Pregled" if leak > 0.015 or unm > 1 else "U redu")
            rows.append(dict(venue=n, invoices=inv, unmatched=unm, due_soon=due,
                             leak_pct=leak, status=status))
        return rows


# ------------------------------------------------------------------ orchestrator
def main():
    sales = SalesAgent().run()
    revenue_gross = sum(MENU[k][1] * q for k, q in sales.items())
    revenue_net = revenue_gross / VAT
    theo = NormativAgent().run(sales)
    inv = InventoryAgent().run(theo)
    invoices = SupplierFeedAgent().run(inv)
    matched = MatchingAgent().run(invoices)
    var_rows = VarianceAgent().run(theo, inv)
    drift = PriceDriftAgent().run(matched)
    menu_rows, avg_cm, pop_thr = MenuEngineeringAgent().run(sales)
    reprice = RepricingAgent().run(menu_rows)
    actions = ActionAgent().run(var_rows, reprice, drift)

    cost_theo = sum(theo[c] * price_now(c) for c in theo)
    cost_actual = sum(inv[c]["actual"] * price_now(c) for c in theo)
    leak_rsd = sum(r["rsd"] for r in var_rows)
    lines = [ln for ls in matched.values() for ln in ls]
    n_unmatched = sum(ln["status"] != "Upareno" for ln in lines)
    accuracy = np.mean([ln["correct"] for ln in lines if ln["truth"] is not None])
    portfolio = PortfolioAgent().run(leak_rsd / revenue_net, n_unmatched, len(matched))
    impact = sum(a["weekly_rsd"] for a in actions)

    # eight-week cost-per-portion history for the flagship item, from price paths
    hero = "Karađorđeva šnicla"
    norm = MENU[hero][3]
    history = []
    for w in range(31, 39):
        t = (w - 31) / 7
        c = sum(q * IDX[k].base_price * (1 + IDX[k].drift * (t ** 1.6) - IDX[k].drift * 0.25 * (1 - t))
                * (1 + RNG.normal(0, 0.004)) for k, q in norm.items())
        history.append(dict(week=w, cost=c))
    hero_lines = [dict(code=k, name=IDX[k].name, unit=IDX[k].unit, qty=q, price=price_now(k),
                       line=q * price_now(k),
                       actual_qty=q * inv[k]["actual"] / theo[k]) for k, q in norm.items()]

    out = dict(
        week=WEEK, venue="Restoran Primer · Vračar",
        kpi=dict(revenue_net=revenue_net, revenue_gross=revenue_gross,
                 fc_theo=cost_theo / revenue_net, fc_actual=cost_actual / revenue_net,
                 leak_rsd=leak_rsd, leak_pct=leak_rsd / revenue_net,
                 leak_month_eur=leak_rsd * 52 / 12 / 117.2,
                 purchases_rsd=sum(ln["qty"] * ln["unit_price"] for ln in lines),
                 invoices=len(matched), lines=len(lines), unmatched=n_unmatched,
                 match_accuracy=float(accuracy), actions_weekly_rsd=impact),
        variance=var_rows, drift=drift, menu=menu_rows, avg_cm=avg_cm, pop_thr=pop_thr,
        reprice=reprice, actions=actions,
        invoices={S[k]: v for k, v in matched.items()},
        portfolio=portfolio,
        hero=dict(item=hero, gross=MENU[hero][1], lines=hero_lines, history=history,
                  sold=sales[hero]),
    )
    with open("/mnt/user-data/outputs/normativ_demo_week38.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)

    k = out["kpi"]
    print("=" * 92)
    print(f"NORMATIV ENGINE | {out['venue']} | {WEEK}")
    print("=" * 92)
    print(f"net revenue            {fmt(k['revenue_net'])} RSD  (gross {fmt(k['revenue_gross'])})")
    print(f"food+bev cost, theo    {k['fc_theo']*100:.1f}%")
    print(f"food+bev cost, actual  {k['fc_actual']*100:.1f}%")
    print(f"leak beyond kalo       {fmt(k['leak_rsd'])} RSD = {k['leak_pct']*100:.2f}% of net revenue"
          f"  (~EUR {k['leak_month_eur']:.0f}/month)")
    print(f"SEF: {k['invoices']} invoices, {k['lines']} lines, {k['unmatched']} need review, "
          f"auto-match accuracy {k['match_accuracy']*100:.0f}%")
    print("\n[VarianceAgent] top leaks")
    for r in var_rows[:7]:
        print(f"  {r['name']:<26} theo {r['theoretical']:7.2f} {r['unit']:<3} actual {r['actual']:7.2f}"
              f"  {r['var_pct']*100:+5.1f}%  kalo {r['kalo']*100:.0f}%  {fmt(r['rsd']):>7} RSD")
    print("\n[PriceDriftAgent]")
    for d in drift[:6]:
        print(f"  {d['name']:<26} {d['avg4']:7.0f} -> {d['now']:7.0f}  {d['drift']*100:+5.1f}%  "
              f"{fmt(d['weekly_rsd']):>7} RSD/wk  {d['supplier']}")
    print("\n[MenuEngineeringAgent] avg CM", fmt(avg_cm), "RSD, popularity threshold",
          f"{pop_thr*100:.1f}%")
    for r in sorted(menu_rows, key=lambda r: -r["cm"] * r["qty"]):
        print(f"  {r['item']:<24} mix {r['mix']*100:5.1f}%  CM {fmt(r['cm']):>5}  FC {r['fc']*100:4.1f}%"
              f"  {r['class']}")
    print("\n[RepricingAgent]")
    for p in reprice:
        print(f"  {p['item']:<24} {fmt(p['gross'])} -> {fmt(p['new_gross'])}  +{fmt(p['weekly_rsd'])} RSD/wk")
    print("\n[ActionAgent] ranked interventions")
    for a in actions:
        print(f"  {fmt(a['weekly_rsd']):>7} RSD/wk  [{a['kind']}] {a['title']}")
    print(f"  total {fmt(impact)} RSD/week")
    print("\n[MatchingAgent] lines needing review")
    for ln in lines:
        if ln["status"] != "Upareno" or not ln["correct"]:
            print(f"  {ln['raw']:<28} -> {ln['match_name']:<24} conf {ln['confidence']:.2f}  {ln['status']}")
    print("\n[PortfolioAgent]")
    for p in portfolio:
        print(f"  {p['venue']:<20} inv {p['invoices']:>3}  unmatched {p['unmatched']}  due {p['due_soon']}"
              f"  leak {p['leak_pct']*100:4.1f}%  {p['status']}")


if __name__ == "__main__":
    main()
