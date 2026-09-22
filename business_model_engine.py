#!/usr/bin/env python3
"""
sank_business_model_engine.py

Cooperating agents:
  CompetitorAgent   sourced Serbian ESIR/POS price list -> normalized EUR/venue/month
  RevenueStackAgent decomposes how incumbents earn (rental, maintenance, LPFR,
                    add-ons, services, hardware) and how Toast earns (fintech)
  PricingAgent      proposes Šank tiers and positions them vs incumbents
  CohortAgent       36-month Monte Carlo: acquisition via agencies + direct,
                    tier mix, churn, ARPU expansion, services, hardware margin
  CostAgent         build (Claude Code assisted), certification, support, hosting
  ScenarioAgent     A pure SaaS | B SaaS + own LPFR | C B + accountant channel
                    + pay-at-table IPS partner share (speculative, low weight)
  SensitivityAgent  churn x CAC grid -> P(break-even by month 24)
  Orchestrator      report + CSV + PNG

All money in EUR (EUR/RSD 117.2). Priors are deliberately wide.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RNG = np.random.default_rng(210926)
N = 10_000
EUR_RSD = 117.2
MONTHS = 36
OUT = "/mnt/user-data/outputs"


def T(n, a, m, b):
    return RNG.triangular(a, m, b, n)


def rsd(x):  # RSD/month -> EUR/month
    return x / EUR_RSD


# ------------------------------------------------------------ competitors
@dataclass
class Offer:
    vendor: str
    plan: str
    eur_month: float          # per venue, typical single-till restaurant
    includes_lpfr: bool
    model: str
    source: str
    note: str = ""


class CompetitorAgent:
    OFFERS = [
        Offer("BizCore", "ESIR+LPFR osnova", rsd(4500), True, "modular SaaS, no VAT",
              "bizcore.rs/cenovnik", "no per-receipt/per-cashier fees"),
        Offer("BizCore", "sve uključeno", rsd(14500), True, "modular SaaS",
              "bizcore.rs/cenovnik", "+online 5000, KDS 1500, kiosk 2500, display 1000"),
        Offer("BizCore", "LPFR samo", rsd(800), True, "LPFR passthrough",
              "bizcore.rs/cenovnik", "works with any approved ESIR"),
        Offer("Syrve (ITmathics)", "Basic", 39, False, "per-till SaaS",
              "syrve.rs", "+LPFR 20, waiter app 10, delivery 20/35, setup 50, training 30/h"),
        Offer("Syrve (ITmathics)", "Professional", 59, False, "per-till SaaS", "syrve.rs"),
        Offer("Syrve (ITmathics)", "Enterprise", 89, False, "per-till SaaS", "syrve.rs"),
        Offer("Syrve (ITmathics)", "Pro restoran realno", 59 + 20 + 10 + 20, True,
              "per-till SaaS + add-ons", "syrve.rs", "Pro + LPFR + waiter + 1 delivery"),
        Offer("POS Sector", "Basic", 22, False, "SaaS monthly/annual", "possector.rs (2023)",
              "annual = 2 months free"),
        Offer("2D Soft", "Cashbox", 10, False, "SaaS", "b92.net (2022)"),
        Offer("2D Soft", "Garson", 29, False, "SaaS", "b92.net (2022)", "L-PFR+ 5 EUR/mo"),
        Offer("DCS Cafe Soft", "iznajmljivanje", np.nan, True, "rental + maintenance",
              "dcsoft.rs", "setup 150 EUR incl. first month"),
        Offer("Petcom Bmaster", "obavezno održavanje", np.nan, True, "license + mandatory maintenance",
              "petcom.rs", "price on request"),
        Offer("UniSoft", "POS kafići", np.nan, True, "license + maintenance", "unisoft.co.rs",
              "price on request, 30-day demo"),
    ]

    def table(self):
        df = pd.DataFrame([o.__dict__ for o in self.OFFERS])
        return df

    def stats(self):
        df = self.table().dropna(subset=["eur_month"])
        base = df[df.plan.str.contains("osnova|Basic|Cashbox|Garson", regex=True)]
        full = df[df.plan.str.contains("sve|Enterprise|realno", regex=True)]
        return dict(entry_median=base.eur_month.median(), entry_min=base.eur_month.min(),
                    entry_max=base.eur_month.max(), full_median=full.eur_month.median(),
                    full_max=full.eur_month.max())


class RevenueStackAgent:
    """Where incumbents' euros come from (structural, from price lists)."""
    SERBIA = {
        "mesečna licenca / iznajmljivanje": "core, 10-90 EUR/venue/month",
        "LPFR kao posebna stavka": "5-20 EUR/mo or 800 RSD; margin on a compliance component",
        "dodaci (KDS, online, kiosk, dostava)": "+13-43 EUR each; Syrve 20-35 EUR per delivery platform",
        "usluge (instalacija, obuka)": "50-150 EUR setup; 30 EUR/h training",
        "hardver (tableti, štampači, kase)": "resale margin; e-fiscalization kit ~270 EUR",
        "obavezno održavanje": "Petcom/Softek: support tied to maintenance fee",
        "procenat od plaćanja": "absent in Serbia",
    }
    TOAST = {
        "subscription_2024_musd": 706, "payments_2024_musd": 4100,
        "payments_take_rate_bps": 48, "fintech_net_take_rate_bps": 58,
        "saas_gross_margin": 0.80, "saas_nrr": 1.09, "locations": 164_000,
        "arr_5yr_location_usd": 16_000,
    }


# ------------------------------------------------------------ our pricing
TIERS = {
    # name: (RSD/month, share of new customers, includes)
    "Start": (3900, 0.45, "1 kasa, sala, račun uživo, ESIR, mobilni pregled"),
    "Pro": (7900, 0.40, "+ KDS, konobar app, deljenje, Normativ lite, SEF"),
    "Plus": (14900, 0.15, "+ više objekata, Normativ full, dostave, IPS na stolu, API"),
}
ADDONS_EUR = dict(extra_till=rsd(1900), delivery=rsd(2000))
SETUP_EUR = (60, 110, 160)
HW_MARGIN_EUR = (0, 45, 120)          # margin on tablets/printers per new venue
OWN_LPFR_EUR = rsd(800)               # captured only in scenarios B/C


class PricingAgent:
    def arpu_draw(self, n):
        tier = RNG.choice(list(TIERS), size=n, p=[v[1] for v in TIERS.values()])
        base = np.array([rsd(TIERS[t][0]) for t in tier])
        extra_tills = RNG.poisson(np.where(tier == "Start", 0.1, np.where(tier == "Pro", 0.5, 1.4)))
        deliveries = RNG.binomial(1, np.where(tier == "Start", 0.15, 0.45))
        arpu = base + extra_tills * ADDONS_EUR["extra_till"] + deliveries * ADDONS_EUR["delivery"]
        return arpu, tier

    def position(self, comp_stats):
        rows = []
        for name, (p, share, inc) in TIERS.items():
            e = rsd(p)
            rows.append(dict(tier=name, rsd=p, eur=e, share=share,
                             vs_entry_median=e / comp_stats["entry_median"] - 1,
                             vs_full_median=e / comp_stats["full_median"] - 1, includes=inc))
        return pd.DataFrame(rows)


# ------------------------------------------------------------ cohorts & costs
class CostAgent:
    """Monthly fixed costs, EUR. Build is founder + Claude Code + 1 contractor."""
    def draw(self, n):
        return dict(
            dev_month=T(n, 1500, 3500, 7000),          # contractor + tools; founder unpaid
            cert_once=T(n, 2000, 5000, 12000),          # ESIR approval, legal, test devices
            hosting_per_venue=T(n, 0.6, 1.2, 2.5),
            support_per_venue=T(n, 2.5, 4.5, 8.0),      # 1 support FTE per ~150-250 venues
            gm_saas=0.85,
            cac_direct=T(n, 120, 260, 500),
            cac_agency=T(n, 30, 70, 140),
        )


class CohortAgent:
    def run(self, n, scenario: str, pricing: PricingAgent, cost: CostAgent):
        c = cost.draw(n)
        agency_share = {"A": 0.15, "B": 0.25, "C": 0.55}[scenario]
        own_lpfr = scenario in ("B", "C")
        ips_share = scenario == "C"
        # acquisition ramp: new venues per month grows with the channel
        ramp0 = T(n, 1.5, 3, 6)         # month-1 new venues
        growth = T(n, 0.03, 0.06, 0.10)  # monthly growth of acquisition rate
        churn = T(n, 0.012, 0.022, 0.040)
        arpu, tier = pricing.arpu_draw(n)
        arpu = arpu + (OWN_LPFR_EUR if own_lpfr else 0)
        # IPS pay-at-table partner share: 0.10-0.20% of the card+IPS GPV of the venue, on ~30% adoption
        gpv = T(n, 15000, 28000, 60000) * T(n, 0.35, 0.50, 0.65)   # monthly non-cash revenue per venue
        ips_rev = (gpv * T(n, 0.0005, 0.0012, 0.0020) * T(n, 0.10, 0.30, 0.50)) if ips_share else np.zeros(n)
        ips_rev *= RNG.binomial(1, 0.35, n)   # 35% chance a partner deal exists at all

        venues = np.zeros(n)
        cash = -c["cert_once"].copy()
        cum = np.zeros((MONTHS, n))
        mrr_path = np.zeros((MONTHS, n))
        venues_path = np.zeros((MONTHS, n))
        be_month = np.full(n, np.nan)
        for m in range(MONTHS):
            new = ramp0 * (1 + growth) ** m
            if m < 3:  # certification + pilot period: no paid customers
                new = new * 0.25
            venues = venues * (1 - churn) + new
            mrr = venues * (arpu + ips_rev)
            gross = mrr * c["gm_saas"] + new * (T(n, *SETUP_EUR) + T(n, *HW_MARGIN_EUR))
            cac = new * (agency_share * c["cac_agency"] + (1 - agency_share) * c["cac_direct"])
            opex = c["dev_month"] + venues * (c["hosting_per_venue"] + c["support_per_venue"])
            cash = cash + gross - cac - opex
            cum[m] = cash
            mrr_path[m] = mrr
            venues_path[m] = venues
            hit = (np.isnan(be_month)) & (gross - cac - opex > 0) & (m >= 6)
            be_month[hit] = m + 1
        ltv = arpu * c["gm_saas"] * (1 - (1 - churn) ** 60) / churn
        blended_cac = agency_share * c["cac_agency"] + (1 - agency_share) * c["cac_direct"]
        return dict(cum=cum, mrr=mrr_path, venues=venues_path, be=be_month,
                    ltv_cac=ltv / blended_cac, arpu=arpu, churn=churn, cac=blended_cac,
                    trough=cum.min(0), arr36=mrr_path[-1] * 12, venues36=venues_path[-1])


class SensitivityAgent:
    def grid(self, pricing, cost):
        churns = [0.015, 0.022, 0.030, 0.040]
        cacs = [80, 150, 250, 400]
        rows = []
        for ch in churns:
            for ca in cacs:
                n = 3000
                c = cost.draw(n)
                c["cac_direct"] = np.full(n, ca); c["cac_agency"] = np.full(n, ca * 0.35)
                arpu, _ = pricing.arpu_draw(n); arpu += OWN_LPFR_EUR
                venues = np.zeros(n); profit_hit = np.zeros(n, bool)
                ramp0 = T(n, 1.5, 3, 6); growth = T(n, 0.03, 0.06, 0.10)
                for m in range(24):
                    new = ramp0 * (1 + growth) ** m * (0.25 if m < 3 else 1)
                    venues = venues * (1 - ch) + new
                    gross = venues * arpu * 0.85 + new * 110
                    opex = c["dev_month"] + venues * (c["hosting_per_venue"] + c["support_per_venue"])
                    cac = new * (0.35 * c["cac_agency"] + 0.65 * c["cac_direct"])
                    if m >= 6:
                        profit_hit |= (gross - cac - opex > 0)
                rows.append(dict(churn=ch, cac=ca, p_be24=profit_hit.mean()))
        return pd.DataFrame(rows).pivot(index="churn", columns="cac", values="p_be24")


# ------------------------------------------------------------ orchestrator
def q(x, p): return float(np.percentile(x, p))


def main():
    pd.set_option("display.width", 170); pd.set_option("display.max_colwidth", 60)
    comp = CompetitorAgent(); cs = comp.stats()
    print("=" * 100); print("ŠANK BUSINESS MODEL ENGINE | sims", N, "| horizon", MONTHS, "m | EUR/RSD", EUR_RSD); print("=" * 100)
    print("\n[CompetitorAgent] Serbian ESIR/POS price list, EUR per venue per month\n")
    t = comp.table().copy(); t["eur_month"] = t["eur_month"].map(lambda v: "na zahtev" if np.isnan(v) else f"{v:.0f}")
    print(t[["vendor", "plan", "eur_month", "includes_lpfr", "model", "note"]].to_string(index=False))
    print(f"\n  entry tier: median EUR {cs['entry_median']:.0f}  (min {cs['entry_min']:.0f}, max {cs['entry_max']:.0f})")
    print(f"  full-stack restaurant: median EUR {cs['full_median']:.0f}, max {cs['full_max']:.0f}")

    print("\n[RevenueStackAgent] how incumbents earn")
    for k, v in RevenueStackAgent.SERBIA.items():
        print(f"  {k:<40} {v}")
    tst = RevenueStackAgent.TOAST
    print(f"\n  Toast reference: payments {tst['payments_2024_musd']/(tst['payments_2024_musd']+tst['subscription_2024_musd']):.0%} of revenue, "
          f"take rate {tst['payments_take_rate_bps']} bps, SaaS GM {tst['saas_gross_margin']:.0%}, NRR {tst['saas_nrr']:.0%}, "
          f"5-yr location ARR ${tst['arr_5yr_location_usd']:,}")

    pricing = PricingAgent(); cost = CostAgent()
    pos = pricing.position(cs)
    print("\n[PricingAgent] proposed Šank tiers\n")
    pp = pos.copy(); pp["eur"] = pp.eur.map("{:.0f}".format)
    for col in ["share", "vs_entry_median", "vs_full_median"]: pp[col] = pp[col].map("{:+.0%}".format if "vs" in col else "{:.0%}".format)
    print(pp.to_string(index=False))

    results = {}
    print("\n[CohortAgent + ScenarioAgent] 36-month Monte Carlo\n")
    print(f"  {'scenario':<34} {'venues@36':>10} {'ARR@36 P10/P50/P90 (kEUR)':>28} {'LTV/CAC':>8} {'P(BE<=24m)':>11} {'trough P50':>11} {'trough worst10%':>15}")
    labels = {"A": "A pure SaaS, direct sales", "B": "B + own LPFR, some agencies", "C": "C + agency channel + IPS share"}
    for s in ("A", "B", "C"):
        r = CohortAgent().run(N, s, pricing, cost); results[s] = r
        pbe = np.mean(np.nan_to_num(r["be"], nan=99) <= 24)
        print(f"  {labels[s]:<34} {np.median(r['venues36']):>10.0f} "
              f"{q(r['arr36'],10)/1e3:>8.0f}/{q(r['arr36'],50)/1e3:.0f}/{q(r['arr36'],90)/1e3:.0f}"
              f"{'':>6} {np.median(r['ltv_cac']):>8.1f} {pbe:>11.0%} {q(r['trough'],50)/1e3:>10.0f}k {q(r['trough'],10)/1e3:>14.0f}k")
    r = results["B"]
    print(f"\n  scenario B detail: ARPU median EUR {np.median(r['arpu']):.0f}/venue/month, churn median {np.median(r['churn']):.1%}/mo, "
          f"blended CAC EUR {np.median(r['cac']):.0f}, break-even month median {np.nanmedian(r['be']):.0f}")
    print(f"  cumulative cash at 36m: P10 {q(r['cum'][-1],10)/1e3:.0f}k, P50 {q(r['cum'][-1],50)/1e3:.0f}k, P90 {q(r['cum'][-1],90)/1e3:.0f}k EUR")

    sens = SensitivityAgent().grid(pricing, cost)
    print("\n[SensitivityAgent] P(profitable month by m24) — rows churn/mo, cols direct CAC EUR\n")
    print(sens.map("{:.0%}".format).to_string())

    # artefacts
    comp.table().to_csv(f"{OUT}/sank_competitor_pricing.csv", index=False)
    pos.to_csv(f"{OUT}/sank_pricing_tiers.csv", index=False)
    fig, ax = plt.subplots(2, 2, figsize=(14, 10))
    df = comp.table().dropna(subset=["eur_month"]).sort_values("eur_month")
    ax[0, 0].barh(df.vendor + " · " + df.plan, df.eur_month, color="#8E8A80")
    for name, (p, _, _) in TIERS.items():
        ax[0, 0].axvline(rsd(p), color="#A33A1F", ls="--"); ax[0, 0].text(rsd(p) + 1, 0.2, f"Šank {name}", color="#A33A1F", fontsize=8, rotation=90)
    ax[0, 0].set_title("Konkurenti: EUR / objekat / mesec (Šank tarife isprekidano)"); ax[0, 0].tick_params(labelsize=8)
    m = np.arange(1, MONTHS + 1)
    for s, col in zip("ABC", ["#8E8A80", "#A33A1F", "#2C6446"]):
        c = results[s]["cum"] / 1e3
        ax[0, 1].plot(m, np.median(c, 1), color=col, label=labels[s])
        ax[0, 1].fill_between(m, np.percentile(c, 25, 1), np.percentile(c, 75, 1), color=col, alpha=.15)
    ax[0, 1].axhline(0, color="k", lw=.8); ax[0, 1].set_title("Kumulativni keš, kEUR (medijana, IQR)"); ax[0, 1].legend(fontsize=8)
    ax[1, 0].hist(results["B"]["arr36"] / 1e3, bins=60, color="#A33A1F", alpha=.8)
    ax[1, 0].set_title("Scenario B: ARR posle 36 meseci, kEUR")
    im = ax[1, 1].imshow(sens.values, cmap="RdYlGn", vmin=0, vmax=1)
    ax[1, 1].set_xticks(range(len(sens.columns)), [f"CAC {c}" for c in sens.columns]); ax[1, 1].set_yticks(range(len(sens.index)), [f"churn {c:.1%}" for c in sens.index])
    for i in range(sens.shape[0]):
        for j in range(sens.shape[1]): ax[1, 1].text(j, i, f"{sens.values[i, j]:.0%}", ha="center", va="center", fontsize=9)
    ax[1, 1].set_title("P(profitabilan mesec do m24)")
    fig.tight_layout(); fig.savefig(f"{OUT}/sank_business_model.png", dpi=150)
    print("\nartefacts: sank_competitor_pricing.csv, sank_pricing_tiers.csv, sank_business_model.png")


if __name__ == "__main__":
    main()
