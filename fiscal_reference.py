#!/usr/bin/env python3
"""
fiscal_reference.py

Executable reference for packages/fiscal-core, distilled from the four
official documents of Poreska uprava (PURS):

  TV   Tehnički vodič (jun 2021, u primeni od 1.7.2021)
  TU   Tehničko uputstvo za administrativni i tehnički pregled ESIR-a
       ili L-PFR-a, v1.17 (9.8.2024)
  ME   Tehničko uputstvo za ručno testiranje ESIR proizvoda, v1.1 (26.5.2022)
  ML   Tehničko uputstvo za ručno testiranje L-PFR proizvoda, v1.0 (12.2.2021)

Cooperating agents:
  SchemaAgent      request/response contract of the PFR HTTP API (/api/v3)
  MoneyAgent       rounding and VAT-inclusive tax math (ME §Zaokruživanje, ML samples)
  RuleAgent        per invoice-type business rules (TV, TU §9, ME)
  ReceiptAgent     textual receipt layout checks (TU 7.4.2 §16, ME §Zabranjene)
  MatrixAgent      certification test matrix + ESIR self-assessment answers
  Orchestrator     runs self-tests against numbers printed in the documents

Money as Decimal with ROUND_HALF_UP (TypeScript port: integer para).
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple

OUT = "/mnt/user-data/outputs/sank-plan/certification"


# ============================================================ SchemaAgent
class InvoiceType(IntEnum):
    """TV §Vrste računa; numeric values seen in TU §9 examples (0=Normal,
    2=Copy) and ML TEST6 (0). Names also accepted by the sandbox
    ("invoiceType": "Normal"). Confirm 1/3/4 on the sandbox Help page."""
    Normal = 0      # Промет
    ProForma = 1    # Предрачун
    Copy = 2        # Копија
    Training = 3    # Обука
    Advance = 4     # Аванс


class TransactionType(IntEnum):
    Sale = 0        # Продаја  (TU §9.3 example: refund is 1)
    Refund = 1      # Рефундација


class PaymentType(IntEnum):
    """TU 7.4.2 §10 P7, verbatim enum. Serbian labels per TV §Način plaćanja."""
    Other = 0          # друго безготовинско плаћање
    Cash = 1           # готовина
    Card = 2           # платна картица
    Check = 3          # чек
    WireTransfer = 4   # пренос на рачун
    Voucher = 5        # ваучер
    MobileMoney = 6    # инстант плаћање (IPS)


PAYMENT_LABEL_SR = {
    PaymentType.Other: "Друго безготовинско плаћање", PaymentType.Cash: "Готовина",
    PaymentType.Card: "Платна картица", PaymentType.Check: "Чек",
    PaymentType.WireTransfer: "Пренос на рачун", PaymentType.Voucher: "Ваучер",
    PaymentType.MobileMoney: "Инстант плаћање",
}

# TU 7.4.2 §10 P7: an installation may run in "restricted" mode where Card,
# Check and MobileMoney are disabled and entered as Cash. One installation
# runs in exactly one of the two modes.
RESTRICTED_MODE_TYPES = {PaymentType.Other, PaymentType.Cash, PaymentType.WireTransfer, PaymentType.Voucher}

# Counter extension letters on the receipt (Бројач рачуна: 143271/150493ПП)
COUNTER_EXT = {
    (InvoiceType.Normal, TransactionType.Sale): "ПП", (InvoiceType.Normal, TransactionType.Refund): "ПР",
    (InvoiceType.Copy, TransactionType.Sale): "КП", (InvoiceType.Copy, TransactionType.Refund): "КР",
    (InvoiceType.ProForma, TransactionType.Sale): "РП", (InvoiceType.ProForma, TransactionType.Refund): "РР",
    (InvoiceType.Training, TransactionType.Sale): "ОП", (InvoiceType.Training, TransactionType.Refund): "ОР",
    (InvoiceType.Advance, TransactionType.Sale): "АП", (InvoiceType.Advance, TransactionType.Refund): "АР",
}
TYPE_LINE = {InvoiceType.Normal: "ПРОМЕТ", InvoiceType.Copy: "КОПИЈА", InvoiceType.ProForma: "ПРЕДРАЧУН",
             InvoiceType.Training: "ОБУКА", InvoiceType.Advance: "АВАНС"}
TX_LINE = {TransactionType.Sale: "ПРОДАЈА", TransactionType.Refund: "РЕФУНДАЦИЈА"}
NON_FISCAL = {InvoiceType.Copy, InvoiceType.ProForma, InvoiceType.Training}   # TV: "ОВО НИЈЕ ФИСКАЛНИ РАЧУН"

# Advanced ESIR must support all ten (TU 7.2.3 НАПРЕДНИ)
ADVANCED_SET = set(COUNTER_EXT.keys())

PFR_ENDPOINTS = {
    "GET  /api/v3/status": "PFR status; gsc error-code list (ML TEST3, TEST5-8)",
    "POST /api/v3/pin": "unlock smart card; 0100 Pin OK, 2100 Pin Not OK [423], 1300 card absent (ML TEST5/7/8)",
    "GET  /api/v3/attention": "availability probe, HTTP 200 (ML TEST4)",
    "GET  /api/v3/environment-parameters": "tax rates and env; 1300 [400] without card (ML TEST5)",
    "POST /api/v3/invoices": "fiscalize (ML TEST6 body); 1500 Pin Code Required if locked (ML TEST7)",
    "GET  /api/v3/invoices/{requestId}": "last signed invoice by ESIR request id (ML §Provera poslednjeg)",
}
PFR_STATUS_CODES = {"0100": "PIN OK", "0210": "returned in gsc lists alongside 1500 (see sandbox Status-and-Error-Codes)",
                    "1300": "Smart card is not present", "1500": "PIN code required", "2100": "PIN not OK (HTTP 423)"}
SANDBOX = "https://tap.sandbox.suf.purs.gov.rs/"
SANDBOX_HELP = {
    "create-invoice": "https://tap.sandbox.suf.purs.gov.rs/Help/view/1672078854/Create-Invoice/en-US",
    "error-format": "https://tap.sandbox.suf.purs.gov.rs/Help/view/1672078854/Error-Messages-Format/en-US",
    "status-codes": "https://tap.sandbox.suf.purs.gov.rs/Help/view/1672078854/Status-and-Error-Codes/en-US",
}
TECH_TEAM = "Poreska uprava, Tehnički tim, Mekenzijeva 53, 5. sprat, Beograd; budiefiskalizovan@purs.gov.rs; pon-pet 7:30-15:30"

# Buyer identification codebook (TU §9.8), value after the colon
BUYER_ID_CODES = {
    "10": "PIB (domaće pravno lice)", "11": "JMBG (preduzetnik)", "12": "PIB:JBKJS (korisnik javnih sredstava)",
    "13": "kod penzionerske kartice", "14": "PIB poljoprivrednog gazdinstva", "15": "JMBG poljoprivrednog gazdinstva",
    "16": "BPG", "20": "broj lične karte", "21": "broj izbegličke legitimacije", "22": "EBS", "23": "broj pasoša (domaće)",
    "30": "broj pasoša (strano)", "31": "diplomatska legitimacija/LK", "32": "LK MKD", "33": "LK MNE", "34": "LK ALB",
    "35": "LK BIH", "36": "LK EU/CH/NO/IS", "40": "strani poreski ID (TIN)",
}
BUYER_COST_CENTER_CODES = {"20": "SNPDV", "21": "LNPDV", "30": "PPO-PDV", "31": "ZPPO-PDV", "32": "MPPO-PDV",
                           "33": "IPPO-PDV", "50": "broj korporacijske kartice (plaćanje uvek Vaučer)",
                           "60": "period storna korporacijskih prometa, 60:ddmmgggg_ddmmgggg (samo Promet-Refundacija)"}
CASHIER_CODES = {"10": "JBKJS prodavca (korisnik javnih sredstava)"}
# Article-name prefixes with fixed meaning (TU §9.1, §9.5, §9.7, §9.8)
ARTICLE_PREFIXES = {"10: Аванс (Ђ)": "avans po 20%", "11: Аванс (Е)": "avans po 10%", "12: Аванс (Г)": "avans oslobođen",
                    "13: Аванс (А)": "avans, obveznik van PDV", "20: Једнонаменски ваучер (Ђ)": "SPV 20%",
                    "21: Једнонаменски ваучер (Е)": "SPV 10%", "22: Једнонаменски ваучер": "SPV oslobođen",
                    "00: ": "promet bez naknade (plaćanje uvek Other)"}


@dataclass
class Item:
    name: str                       # "<naziv>/<jm>"; label is appended by PFR ("Хлеб (А)")
    quantity: Decimal               # up to 3 decimals (ME §Odabir količine)
    unit_price: Decimal             # VAT-inclusive, 2 decimals
    labels: List[str]               # tax labels from PFR (e.g. ["Ђ"])
    gtin: Optional[str] = None      # mandatory support, optional on receipt (TU §10 P11)
    total_amount: Optional[Decimal] = None  # round(qty*unit_price) if None


@dataclass
class Payment:
    amount: Decimal
    payment_type: PaymentType


@dataclass
class InvoiceRequest:
    invoice_type: InvoiceType
    transaction_type: TransactionType
    payments: List[Payment]
    items: List[Item]
    cashier: str                                 # mandatory identification (ME check 3)
    buyer_id: Optional[str] = None               # "10:123456789" (TU §9.8)
    buyer_cost_center_id: Optional[str] = None   # "50:66666666"
    referent_document_number: Optional[str] = None   # "JID-JID-N" or "XXXXXXXX-XXXXXXXX-121"
    referent_document_dt: Optional[str] = None       # ISO 8601, PFR time of referenced invoice
    date_and_time_of_issue: Optional[str] = None     # ESIR time, only AP with earlier wire transfer
    invoice_number: Optional[str] = None             # ESIR's own number, may be null
    omit_qr: bool = False
    omit_textual: bool = False

    def to_json(self) -> dict:
        return {
            "dateAndTimeOfIssue": self.date_and_time_of_issue, "cashier": self.cashier,
            "buyerId": self.buyer_id, "buyerCostCenterId": self.buyer_cost_center_id,
            "invoiceType": self.invoice_type.name, "transactionType": self.transaction_type.name,
            "payment": [{"amount": float(p.amount), "paymentType": p.payment_type.name} for p in self.payments],
            "invoiceNumber": self.invoice_number,
            "referentDocumentNumber": self.referent_document_number, "referentDocumentDT": self.referent_document_dt,
            "options": {"omitQRCodeGen": "1" if self.omit_qr else "0", "omitTextualRepresentation": "1" if self.omit_textual else "0"},
            "items": [{"gtin": i.gtin, "name": i.name, "quantity": float(i.quantity), "labels": i.labels,
                       "unitPrice": float(i.unit_price), "totalAmount": float(MoneyAgent.line_total(i))} for i in self.items],
        }


RESPONSE_FIELDS = ["requestedBy", "sdcDateTime", "invoiceCounter", "invoiceCounterExtension", "invoiceNumber",
                   "taxItems", "verificationUrl", "verificationQRCode", "journal", "messages", "signedBy",
                   "encryptedInternalData", "signature", "totalCounter", "transactionTypeCounter", "totalAmount",
                   "taxGroupRevision", "businessName", "tin", "locationName", "address", "district", "mrc"]


# ============================================================ MoneyAgent
class MoneyAgent:
    Q2 = Decimal("0.01")

    @staticmethod
    def r2(x: Decimal) -> Decimal:
        """ME §Zaokruživanje: two decimals, third decimal >=5 rounds up."""
        return Decimal(x).quantize(MoneyAgent.Q2, rounding=ROUND_HALF_UP)

    @staticmethod
    def line_total(i: Item) -> Decimal:
        return i.total_amount if i.total_amount is not None else MoneyAgent.r2(i.quantity * i.unit_price)

    @staticmethod
    def tax_from_inclusive(gross: Decimal, rate_pct: Decimal) -> Decimal:
        """Prices are VAT-inclusive; tax = gross * rate / (100 + rate). Verified
        against ML sample (68.46 @9% -> 5.65) and TU §9.3 (12,000,000 @20% -> 2,000,000)."""
        return MoneyAgent.r2(gross * rate_pct / (Decimal(100) + rate_pct))

    @staticmethod
    def totals(items: List[Item], rates: Dict[str, Decimal]) -> Tuple[Decimal, Dict[str, Decimal], Decimal]:
        total = sum((MoneyAgent.line_total(i) for i in items), Decimal(0))
        by_label: Dict[str, Decimal] = {}
        for i in items:
            for lab in i.labels:
                by_label[lab] = by_label.get(lab, Decimal(0)) + MoneyAgent.line_total(i)
        tax = {lab: MoneyAgent.tax_from_inclusive(amt, rates[lab]) for lab, amt in by_label.items()}
        return total, tax, sum(tax.values(), Decimal(0))


# ============================================================ RuleAgent
class Violation(Exception):
    pass


class RuleAgent:
    BUYER_RE = re.compile(r"^(\d{2}):(.+)$")
    REF_RE = re.compile(r"^[A-Z0-9X]{8}-[A-Z0-9X]{8}-\d+$")

    def __init__(self, active_labels: Dict[str, Decimal], restricted_payments: bool = False):
        self.rates = active_labels            # only what PFR returned (TU §12 P6)
        self.restricted = restricted_payments

    def validate(self, r: InvoiceRequest) -> List[str]:
        errs: List[str] = []
        key = (r.invoice_type, r.transaction_type)
        if key not in ADVANCED_SET:
            errs.append("unknown type/transaction pair")
        if not r.items:
            errs.append("at least one item")
        if not r.cashier:
            errs.append("cashier identification is mandatory (ME check 3)")
        for i in r.items:
            if i.quantity <= 0 or i.quantity != i.quantity.quantize(Decimal("0.001")):
                errs.append(f"{i.name}: quantity must be positive with <=3 decimals")
            if i.unit_price != MoneyAgent.r2(i.unit_price):
                errs.append(f"{i.name}: unitPrice must be 2 decimals (ME rounding)")
            for lab in i.labels:
                if lab not in self.rates:
                    errs.append(f"{i.name}: tax label '{lab}' not provided by PFR (TU §12 P6)")
            if i.name.startswith("00:") and any(p.payment_type != PaymentType.Other for p in r.payments):
                errs.append("promet bez naknade (00:) requires payment Other (TU §9.7)")
            if r.invoice_type == InvoiceType.Advance and not re.match(r"^1[0-3]: Аванс", i.name):
                errs.append(f"{i.name}: advance items must be named '10..13: Аванс (label)' with qty 1 (TU §9.1)")
        # referent document rules (TV §pozivanje na broj; TU §16 P6; ME §Obavezni referentni broj)
        needs_ref = r.invoice_type == InvoiceType.Copy or r.transaction_type == TransactionType.Refund
        if needs_ref and not r.referent_document_number:
            errs.append("Copy and Refund require referentDocumentNumber")
        if r.referent_document_number and not self.REF_RE.match(r.referent_document_number):
            errs.append("referentDocumentNumber must be JID-JID-N (or XXXXXXXX-XXXXXXXX-N for pre-fiscalization)")
        if r.referent_document_number and not r.referent_document_dt and needs_ref:
            errs.append("Copy/Refund require referentDocumentDT (ME note p.21)")
        # buyer identification
        for label, val in (("buyerId", r.buyer_id), ("buyerCostCenterId", r.buyer_cost_center_id)):
            if val:
                m = self.BUYER_RE.match(val)
                book = BUYER_ID_CODES if label == "buyerId" else BUYER_COST_CENTER_CODES
                if not m or m.group(1) not in book:
                    errs.append(f"{label} '{val}' not in codebook (TU §9.8)")
        if r.buyer_cost_center_id and r.buyer_cost_center_id.startswith("50:"):
            if any(p.payment_type != PaymentType.Voucher for p in r.payments):
                errs.append("corporate card (50:) requires payment Voucher (TU §9.4)")
        if r.buyer_cost_center_id and r.buyer_cost_center_id.startswith("60:"):
            if key != (InvoiceType.Normal, TransactionType.Refund) or not re.match(r"^60:\d{8}_\d{8}$", r.buyer_cost_center_id):
                errs.append("60: period storno only on Promet-Refundacija, format 60:ddmmgggg_ddmmgggg (TU §9.4)")
        # ESIR time only on Advance Sale with earlier wire transfer (TU §16 P5, ME p.30)
        if r.date_and_time_of_issue and key != (InvoiceType.Advance, TransactionType.Sale):
            errs.append("dateAndTimeOfIssue (ESIR vreme) only on Avans-Prodaja")
        if key == (InvoiceType.Advance, TransactionType.Sale) and r.date_and_time_of_issue \
                and not any(p.payment_type == PaymentType.WireTransfer for p in r.payments):
            errs.append("ESIR vreme implies a wire-transfer payment dated before PFR time")
        # payments
        if not r.payments:
            errs.append("at least one payment line")
        for p in r.payments:
            if self.restricted and p.payment_type not in RESTRICTED_MODE_TYPES:
                errs.append(f"restricted installation: {p.payment_type.name} must be entered as Cash (TU §10 P7)")
        total, _, _ = MoneyAgent.totals(r.items, self.rates) if not errs else (Decimal(0), {}, Decimal(0))
        paid = sum((p.amount for p in r.payments), Decimal(0))
        if not errs and r.invoice_type in (InvoiceType.Normal, InvoiceType.Advance) and paid < total:
            errs.append(f"paid {paid} < total {total} (change is paid - total)")
        return errs

    @staticmethod
    def cancel_wrong_invoice(own_pib: str, wrong: InvoiceRequest, wrong_pfr_no: str, wrong_pfr_dt: str) -> InvoiceRequest:
        """TU §9.3: cancel by issuing the mirror Refund with buyerId = own PIB,
        reference to the wrong invoice, all items and prices repeated."""
        it = InvoiceType.Advance if wrong.invoice_type == InvoiceType.Advance else InvoiceType.Normal
        return InvoiceRequest(it, TransactionType.Refund, wrong.payments, wrong.items, wrong.cashier,
                              buyer_id=f"10:{own_pib}", referent_document_number=wrong_pfr_no,
                              referent_document_dt=wrong_pfr_dt)

    @staticmethod
    def close_advance_chain(cashier: str, label: str, advances_gross: List[Decimal], last_ap_no: str, last_ap_dt: str,
                            final_items: List[Item], final_payments: List[Payment]) -> Tuple[InvoiceRequest, InvoiceRequest]:
        """TU §9.1.1: before the final Promet-Prodaja, issue Avans-Refundacija
        referencing the LAST Avans-Prodaja for the whole advanced amount; the
        final PP references that AR. AR is not handed to the customer. The
        advert field on PP must carry number and date of the last AP."""
        code = {"Ђ": "10", "Е": "11", "Г": "12", "А": "13"}[label]
        total_adv = sum(advances_gross, Decimal(0))
        ar = InvoiceRequest(InvoiceType.Advance, TransactionType.Refund,
                            [Payment(total_adv, PaymentType.Cash)],
                            [Item(f"{code}: Аванс ({label})", Decimal(1), MoneyAgent.r2(total_adv), [label])],
                            cashier, referent_document_number=last_ap_no, referent_document_dt=last_ap_dt)
        pp = InvoiceRequest(InvoiceType.Normal, TransactionType.Sale, final_payments, final_items, cashier,
                            referent_document_number="<AR PFR number>", referent_document_dt="<AR PFR time>")
        return ar, pp


# ============================================================ ReceiptAgent
class ReceiptAgent:
    """Checks a rendered receipt (our own or the PFR journal) against TU 7.4.2 §16
    and ME §'ESIR ne sme da izostavi'. The renderer in fiscal-core must satisfy
    every rule here; these are also the 16 visual checks of the technical review."""
    START_F, END_F = "ФИСКАЛНИ РАЧУН", "КРАЈ ФИСКАЛНОГ РАЧУНА"
    NONF = "ОВО НИЈЕ ФИСКАЛНИ РАЧУН"
    ESIR_NO_RE = re.compile(r"^ЕСИР број:\s*(\d+)/(\d+\.\d+)\s*$", re.M)

    def check(self, text: str, r: InvoiceRequest, ib: str, version: str) -> List[str]:
        errs = []
        nonfiscal = r.invoice_type in NON_FISCAL
        first, last = text.strip().splitlines()[0], text.strip().splitlines()[-1]
        if nonfiscal:
            if self.NONF not in first or self.NONF not in last:
                errs.append("non-fiscal docs must start and end with 'ОВО НИЈЕ ФИСКАЛНИ РАЧУН' title lines")
            if text.count(self.NONF) < 3:
                errs.append("non-fiscal docs must carry the message in the body, double font (P10)")
        else:
            if self.START_F not in first or self.END_F not in last:
                errs.append("fiscal receipt must start with ФИСКАЛНИ РАЧУН and end with КРАЈ ФИСКАЛНОГ РАЧУНА (P1, P13)")
        m = self.ESIR_NO_RE.search(text)
        if not m or m.group(1) != ib or m.group(2) != version:
            errs.append(f"ЕСИР број must be exactly '{ib}/{version}' (P5, common mistake d)")
        if "Касир:" not in text:
            errs.append("cashier line missing (P3)")
        if f"{TYPE_LINE[r.invoice_type]} - {TX_LINE[r.transaction_type]}" not in text.replace("-", "-"):
            errs.append("type/transaction line missing (P7)")
        for lbl, val in (("ИД купца:", r.buyer_id), ("Опционо поље купца:", r.buyer_cost_center_id)):
            if val and lbl not in text:
                errs.append(f"{lbl} missing although sent (P4)")
            if not val and lbl in text:
                errs.append(f"{lbl} printed although not sent (common mistakes a, c)")
        if (r.invoice_type == InvoiceType.Copy or r.transaction_type == TransactionType.Refund):
            if "Реф. број:" not in text or "Реф. време:" not in text:
                errs.append("Copy/Refund must print Реф. број and Реф. време (P6)")
        if r.date_and_time_of_issue and "ЕСИР време:" not in text:
            errs.append("AP with wire transfer must print ЕСИР време (P5)")
        if not r.date_and_time_of_issue and "ЕСИР време:" in text:
            errs.append("ЕСИР време must be absent except AP wire-transfer case (ME note p.7)")
        for needle, rule in (("За уплату:", "P9 totals"), ("Ознака", "P9 tax table"), ("ПФР време:", "P11"),
                             ("ПФР број рачуна:", "P11"), ("Бројач рачуна:", "P11")):
            if needle not in text:
                errs.append(f"{needle} missing ({rule})")
        if (r.invoice_type, r.transaction_type) == (InvoiceType.Copy, TransactionType.Refund) \
                and any(p.payment_type == PaymentType.Cash for p in r.payments) and "Потпис купца" not in text:
            errs.append("Копија Рефундација with cash refund needs 'Потпис купца: ____' (common mistake f)")
        if any(p.payment_type == PaymentType.Cash for p in r.payments) and "готовина" not in text.lower():
            errs.append("payment line per method must be printed (P9)")
        return errs

    @staticmethod
    def render(r: InvoiceRequest, resp: dict, ib: str, version: str, rates: Dict[str, Decimal], advert: str = "") -> str:
        """Minimal compliant textual receipt (57-80 mm). PFR-provided header
        fields come from the response; ESIR never alters them (TU §9 P2/P3)."""
        W = 40
        nonf = r.invoice_type in NON_FISCAL
        title = ReceiptAgent.NONF if nonf else ReceiptAgent.START_F
        L = [f"{'=' * ((W - len(title) - 2) // 2)} {title} {'=' * ((W - len(title) - 2) // 2)}"]
        L += [resp["tin"].center(W), resp["businessName"].center(W), resp["locationName"].center(W),
              resp["address"].center(W), resp["district"].center(W)]
        kv = lambda k, v: f"{k}{str(v).rjust(W - len(k))}"
        L.append(kv("Касир:", r.cashier))
        if r.buyer_id: L.append(kv("ИД купца:", r.buyer_id))
        if r.buyer_cost_center_id: L.append(kv("Опционо поље купца:", r.buyer_cost_center_id))
        L.append(kv("ЕСИР број:", f"{ib}/{version}"))
        if r.date_and_time_of_issue: L.append(kv("ЕСИР време:", r.date_and_time_of_issue))
        if r.referent_document_number:
            L.append(kv("Реф. број:", r.referent_document_number))
            L.append(kv("Реф. време:", r.referent_document_dt or ""))
        tl = f"{TYPE_LINE[r.invoice_type]} - {TX_LINE[r.transaction_type]}"
        L.append(f"{'-' * ((W - len(tl) - 2) // 2)} {tl} {'-' * ((W - len(tl) - 2) // 2)}")
        L += ["Артикли", "=" * W, f"{'Назив':<12}{'Цена':>10}{'Кол.':>8}{'Укупно':>10}"]
        sign = -1 if r.transaction_type == TransactionType.Refund else 1
        total, tax, tax_sum = MoneyAgent.totals(r.items, rates)
        for i in r.items:
            L.append(f"{i.name} ({','.join(i.labels)})")
            L.append(f"{'':<12}{fmt(i.unit_price):>10}{fmt(i.quantity, 3):>8}{fmt(sign * MoneyAgent.line_total(i)):>10}")
        L += ["-" * W, kv("За уплату:", fmt(total))]
        for p in r.payments:
            L.append(kv(f"Уплаћено - {PAYMENT_LABEL_SR[p.payment_type].lower()}:", fmt(p.amount)))
        paid = sum((p.amount for p in r.payments), Decimal(0))
        L.append(kv("Повраћај:", fmt(max(paid - total, Decimal(0)))))
        L.append("=" * W)
        if nonf:
            L += [ReceiptAgent.NONF.center(W), "=" * W]     # printer: double font size here
        L.append(f"{'Ознака':<8}{'Име':<8}{'Стопа':>10}{'Порез':>14}")
        for lab, amt in tax.items():
            L.append(f"{lab:<8}{'ПДВ':<8}{fmt(rates[lab]) + '%':>10}{fmt(amt):>14}")
        L += ["-" * W, kv("Укупан износ пореза:", fmt(tax_sum)), "=" * W,
              kv("ПФР време:", resp["sdcDateTime"]), kv("ПФР број рачуна:", resp["invoiceNumber"]),
              kv("Бројач рачуна:", resp["invoiceCounter"]), "=" * W, "[QR 40-50 mm, bez logotipa]"]
        if (r.invoice_type, r.transaction_type) == (InvoiceType.Copy, TransactionType.Refund) \
                and any(p.payment_type == PaymentType.Cash for p in r.payments):
            L.append("Потпис купца: ____________________")
        end = ReceiptAgent.NONF if nonf else ReceiptAgent.END_F
        L.append(f"{'=' * ((W - len(end) - 2) // 2)} {end} {'=' * ((W - len(end) - 2) // 2)}")
        if advert:
            L.append(advert)   # smaller font; mandatory field for advanced ESIR (P14), used for AP/PP info (TU §9.1)
        return "\n".join(L)


def fmt(x: Decimal, d: int = 2) -> str:
    q = Decimal(1).scaleb(-d)
    s = f"{Decimal(x).quantize(q, rounding=ROUND_HALF_UP):,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================ MatrixAgent
class MatrixAgent:
    """Certification test matrix: every manual test case from ME/ML that concerns
    the ESIR, mapped to the automated test id fiscal-core must implement, plus
    the submission conditions of ME p.37 and the ESIR questionnaire answers."""
    CASES = [
        ("ME-forbidden-1", "No receipt without PFR data; unplug L-PFR -> issue fails", "ME p.5", "core.no_pfr_no_receipt"),
        ("ME-forbidden-2", "16 visual checks of mandatory receipt data", "ME p.6-7", "receipt.mandatory_fields_*"),
        ("ME-op-auth", "ESIR authenticates with PFR on startup", "ME p.8", "core.startup_auth"),
        ("ME-op-void", "Remove items before issuing (optional)", "ME p.9", "pos.void_line"),
        ("ME-op-discount", "Discount on item, PFR records reduced price", "ME p.9", "pos.discount_to_unit_price"),
        ("ME-op-payments", "One receipt per payment method (all 7)", "ME p.10", "core.payment_types_all"),
        ("ME-op-multipay", "Multiple methods on one receipt, one repeated", "ME p.10-11", "core.payment_split"),
        ("ME-op-gtin", "GTIN sent and visible on PU portal", "ME p.11", "core.gtin_passthrough"),
        ("ME-op-refnum", "Refund and Copy require reference number", "ME p.11-12", "rules.ref_required"),
        ("ME-op-refnum-pp", "PP closing an AR carries AR reference", "ME p.12", "rules.close_advance"),
        ("ME-op-journal", "List/search last 30 days of receipts", "ME p.13; TU §10 P16", "journal.search_30d"),
        ("ME-price-new", "Create article", "ME p.14", "catalog.create_item"),
        ("ME-price-qty", "Quantity with three decimals", "ME p.14", "core.qty_3_decimals"),
        ("ME-price-change", "Change article price (mandatory for advanced)", "ME p.15", "catalog.price_change"),
        ("ME-price-add", "Add by name or GTIN scan", "ME p.15-16", "pos.add_by_gtin"),
        ("ME-price-round", "Rounding 5.1/10.267/20.143 and 0.123x9.90, 0.123x9.95", "ME p.16", "money.rounding_examples"),
        ("ME-tax-update", "Tax rates taken from PFR/SUF, printed with labels", "ME p.17", "core.tax_rates_from_pfr"),
        ("ME-tax-show", "Show active tax rates on command", "ME p.18", "admin.show_tax_rates"),
        ("ME-tax-only-pfr", "Reject unknown tax label", "ME p.18-19", "rules.unknown_label_rejected"),
        ("ME-edelivery", "Electronic delivery of receipt (email/SMS) with hyperlink", "ME p.20", "core.electronic_receipt"),
        ("ME-samples-1..15", "15 sample receipts for advanced ESIR incl. buyer ID variants", "ME p.22-36; TU §17", "samples.generate_all"),
        ("ML-api-status", "GET /api/v3/status codes with/without card and PIN", "ML TEST3,5,7,8", "pfr_client.status_matrix"),
        ("ML-api-pin", "POST /api/v3/pin 0100/2100/1300", "ML TEST5,7,8", "pfr_client.pin"),
        ("ML-api-attention", "GET /api/v3/attention 200", "ML TEST4", "pfr_client.attention"),
        ("ML-api-invoice", "POST /api/v3/invoices body + response fields", "ML TEST6", "pfr_client.create_invoice"),
        ("ML-api-last", "GET last signed invoice by request id", "ML p.13", "pfr_client.get_last"),
        ("ML-limits", "BE limit reached: second invoice blocked until proof of audit", "ML p.5-7", "hub.audit_limit_ux"),
        ("ML-offline", "Local audit export via USB/SD when offline", "ML p.7-12", "hub.local_audit_docs"),
        ("TU-9.1", "Advance chain AP->AP->AR->PP with 10..13: Аванс items", "TU §9.1", "rules.advance_chain"),
        ("TU-9.3", "Cancel wrong invoice with own PIB as buyerId", "TU §9.3", "rules.cancel_wrong"),
        ("TU-9.4", "Corporate card 50: with Voucher; monthly storno 60:", "TU §9.4", "rules.corporate_card"),
        ("TU-9.5", "Single-purpose voucher 20..22:", "TU §9.5", "rules.spv"),
        ("TU-9.7", "Free-of-charge supply 00: with Other payment", "TU §9.7", "rules.free_supply"),
        ("TU-9.8", "Buyer ID and cost-center codebooks", "TU §9.8", "rules.codebooks"),
        ("TU-10-P7", "Restricted payment mode (Card/Check/IPS entered as Cash)", "TU §10 P7", "rules.restricted_mode"),
        ("TU-16", "Receipt layout P1-P14 incl. advert field", "TU 7.4.2 §16", "receipt.layout_*"),
    ]
    SUBMISSION = [
        "sign at least one receipt with an L-PFR (we are not remote-trade only)",
        "advanced: at least one Промет-Продаја that closes an advance",
        "advanced: at least one Аванс-Продаја with ЕСИР време at least one day before PFR time (simulated wire transfer)",
        "at least one receipt with a GTIN item (visible on PU portal, optional on paper)",
        "a Промет-Продаја with Опционо поље купца",
        "if V-PFR is supported: at least one receipt signed by V-PFR",
        "at least one receipt with all payment methods",
        "at least one receipt with multiple tax labels",
        "a receipt repeating the decimal rounding test",
        "all samples with scannable QR; all documents in Serbian",
    ]
    QUESTIONNAIRE = [  # (section, answer for Šank)
        ("1 Vrsta odobrenja", "PRENOSIVO (dobavljač isporučuje obveznicima)"),
        ("1 Klasifikacija", "3 NAPREDNI: PP, PR, KP, KR, RP, RR, OP, OR, AP, AR"),
        ("2 Dokumentacija", "brošura/sajt, korisničko uputstvo, uputstvo za instalaciju, uputstvo za konfiguraciju; sve na srpskom"),
        ("3 Tipovi ESIR-a", "P2 softver na računaru (Hub + web), P3 aplikacija za pametni uređaj (PWA)"),
        ("4 Instalacija", "P1 direktno u objektu (Hub), P2 klaud, P3 samoinstalacija"),
        ("5 PFR", "P1 L-PFR (obavezno); P3 V-PFR sa sertifikat fajlom (za online kanal, faza 3)"),
        ("6 Povezivanje", "P1 Wi-Fi (obavezno), P3 Ethernet"),
        ("7 OS", "Android, iOS (PWA), Windows, Linux (Hub)"),
        ("8 Ručno testiranje", "dostavljamo tablet + Hub mini-PC + štampač 80 mm + rolne"),
        ("9 Zabranjene funkcije", "P1, P2, P3 potvrđeno i dokumentovano (referenca na uputstvo)"),
        ("10 Operativne funkcije", "P2 auth na startu; P4 popust; P7 sve metode + restriktivni mod; P8 podeljeno plaćanje; P10 elektronski i papirni; P11 GTIN; P12/P13 referentni broj; P14 HTTP ka L-PFR; P15 HTTPS ka V-PFR; P16 e-žurnal 30 dana"),
        ("11 Cene", "P1-P6 sve obavezno: unos artikla, količina, promena cene, zaokruživanje, GTIN, uvoz/izvoz"),
        ("12 Poreske stope", "P1-P6: stope samo iz PFR-a, labela + stopa na računu, prikaz na zahtev"),
        ("13 Štampanje", "P1 do 57 mm, P2 57-80 mm, P3 A4 (PDF za e-dostavu)"),
        ("14 Štampači", "P1 eksterni ESC/POS sa QR"),
        ("15 Dostavljanje", "P1 papir, P2 elektronski (e-pošta, SMS, link)"),
        ("16 Tekstualni prikaz", "P1-P14 svi elementi; P14 reklamno polje obavezno (napredni)"),
        ("17 Primeri računa", "P1-P15 svih 15 uzoraka za napredni ESIR, sa i bez ID kupca"),
    ]

    def write(self):
        import os
        os.makedirs(OUT, exist_ok=True)
        with open(f"{OUT}/certification_matrix.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["id", "case", "source", "automated_test"]); w.writerows(self.CASES)
        with open(f"{OUT}/esir_questionnaire_answers.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["section", "answer"]); w.writerows(self.QUESTIONNAIRE)
        with open(f"{OUT}/submission_checklist.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(f"[ ] {s}" for s in self.SUBMISSION))


# ============================================================ Orchestrator / self-tests
def main():
    ok = 0
    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok += int(cond)

    print("=" * 96); print("FISCAL REFERENCE | self-tests against numbers printed in TV / TU / ME / ML"); print("=" * 96)
    M = MoneyAgent
    print("\n[MoneyAgent] rounding examples, ME §Zaokruživanje decimala")
    check("5.1 -> 5,10", M.r2(Decimal("5.1")) == Decimal("5.10"))
    check("10.267 -> 10,27", M.r2(Decimal("10.267")) == Decimal("10.27"))
    check("20.143 -> 20,14", M.r2(Decimal("20.143")) == Decimal("20.14"))
    check("0.123 x 9.90 = 1.2177 -> 1,22", M.r2(Decimal("0.123") * Decimal("9.90")) == Decimal("1.22"))
    check("0.123 x 9.95 = 1.22385 -> 1,22", M.r2(Decimal("0.123") * Decimal("9.95")) == Decimal("1.22"))
    print("\n[MoneyAgent] VAT-inclusive tax, samples from ML and TU")
    check("68.46 @ 9% -> 5,65 (ML p.23)", M.tax_from_inclusive(Decimal("68.46"), Decimal(9)) == Decimal("5.65"))
    check("21.10 @ 9% -> 1,74 (ML p.25)", M.tax_from_inclusive(Decimal("21.10"), Decimal(9)) == Decimal("1.74"))
    check("12.000.000 @ 20% -> 2.000.000 (TU §9.3)", M.tax_from_inclusive(Decimal("12000000"), Decimal(20)) == Decimal("2000000"))
    check("7.000 @ 20% -> 1.166,67 (TU §9.6)", M.tax_from_inclusive(Decimal("7000"), Decimal(20)) == Decimal("1166.67"))
    check("349.90+40.00: Ђ 58,32 + Е 3,64 = 61,96 (ME sample 1)",
          M.tax_from_inclusive(Decimal("349.90"), Decimal(20)) + M.tax_from_inclusive(Decimal("40"), Decimal(10)) == Decimal("61.96"))

    rates = {"Ђ": Decimal(20), "Е": Decimal(10), "Г": Decimal(0), "А": Decimal(0)}
    rules = RuleAgent(rates)
    print("\n[RuleAgent] business rules")
    sale = InvoiceRequest(InvoiceType.Normal, TransactionType.Sale,
                          [Payment(Decimal("200"), PaymentType.Cash), Payment(Decimal("200"), PaymentType.Card)],
                          [Item("Ceđeni sok/l", Decimal("10"), Decimal("34.99"), ["Ђ"]),
                           Item("Hleb Sava/kom", Decimal("1"), Decimal("40.00"), ["Е"], gtin="8600001234567")],
                          cashier="Tehničar", buyer_id="10:123456789", buyer_cost_center_id="20:123456789")
    check("ME sample 1 (349,90 + 40,00, cash+card) validates", rules.validate(sale) == [])
    total, tax, tsum = M.totals(sale.items, rates)
    check("za uplatu 389,90 / povraćaj 10,10 / porez 61,96",
          (total, tsum, Decimal("400") - total) == (Decimal("389.90"), Decimal("61.96"), Decimal("10.10")))
    refund_noref = InvoiceRequest(InvoiceType.Normal, TransactionType.Refund, sale.payments, sale.items, "T")
    check("refund without reference rejected", any("referentDocumentNumber" in e for e in rules.validate(refund_noref)))
    badlabel = InvoiceRequest(InvoiceType.Normal, TransactionType.Sale, [Payment(Decimal(100), PaymentType.Cash)],
                              [Item("X/kom", Decimal(1), Decimal("100.00"), ["Z"])], "T")
    check("unknown tax label rejected (ME p.18)", any("not provided by PFR" in e for e in rules.validate(badlabel)))
    corp = InvoiceRequest(InvoiceType.Normal, TransactionType.Sale, [Payment(Decimal(100), PaymentType.Cash)],
                          [Item("X/kom", Decimal(1), Decimal("100.00"), ["Ђ"])], "T", buyer_id="10:123456789",
                          buyer_cost_center_id="50:66666666")
    check("corporate card must be Voucher (TU §9.4)", any("Voucher" in e for e in rules.validate(corp)))
    free = InvoiceRequest(InvoiceType.Normal, TransactionType.Sale, [Payment(Decimal(6000), PaymentType.Cash)],
                          [Item("00: Haljina/kom", Decimal(1), Decimal("6000.00"), ["Ђ"])], "T")
    check("00: free supply must be Other (TU §9.7)", any("Other" in e for e in rules.validate(free)))
    restricted = RuleAgent(rates, restricted_payments=True)
    check("restricted mode rejects Card (TU §10 P7)", any("restricted" in e for e in restricted.validate(sale)))
    cancel = RuleAgent.cancel_wrong_invoice("111111111", sale, "Y9ANWU3Y-Y9ANWU3Y-7", "2021-08-12T10:23:11+02:00")
    check("cancel = Refund with own PIB and reference (TU §9.3)",
          cancel.buyer_id == "10:111111111" and cancel.transaction_type == TransactionType.Refund and rules.validate(cancel) == [])
    ar, pp = RuleAgent.close_advance_chain("T", "Ђ", [Decimal("10000"), Decimal("20000")], "VBGR6ZIU-VBGR6ZIU-17",
                                           "2022-03-25T10:00:00+01:00",
                                           [Item("Usluga/kom", Decimal(1), Decimal("30000.00"), ["Ђ"])],
                                           [Payment(Decimal("30000"), PaymentType.WireTransfer)])
    check("advance close: AR item '10: Аванс (Ђ)' qty 1 total 30.000 referencing last AP",
          ar.items[0].name == "10: Аванс (Ђ)" and ar.items[0].unit_price == Decimal("30000.00") and rules.validate(ar) == [])

    print("\n[ReceiptAgent] textual receipt rules, TU 7.4.2 §16 and ME checks")
    resp = dict(tin="123456789", businessName="Техничар ДОО", locationName="Продавница техничког тима",
                address="Макензијева 153", district="Врачар", sdcDateTime="06.06.2021 17:53:48",
                invoiceNumber="7AAF4DD9-E3BB350A-150493", invoiceCounter="143271/150493ПП")
    txt = ReceiptAgent.render(sale, resp, "123", "1.0", rates)
    check("rendered PP passes all layout checks", ReceiptAgent().check(txt, sale, "123", "1.0") == [])
    copy_ref = InvoiceRequest(InvoiceType.Copy, TransactionType.Refund, [Payment(Decimal("7000"), PaymentType.Cash)],
                              [Item("Color TV Sony/kom", Decimal(1), Decimal("7000.00"), ["Ђ"], gtin="987654321")], "T",
                              buyer_id="20:0023456", referent_document_number="Y9ANWU3Y-Y9ANWU3Y-26",
                              referent_document_dt="2021-09-23T08:53:15+02:00")
    resp2 = {**resp, "invoiceNumber": "Y9ANWU3Y-Y9ANWU3Y-27", "invoiceCounter": "1/27КР"}
    txt2 = ReceiptAgent.render(copy_ref, resp2, "123", "1.0", rates)
    check("КР with cash refund: non-fiscal titles + customer signature line (TU §9.6)",
          ReceiptAgent().check(txt2, copy_ref, "123", "1.0") == [] and "Потпис купца" in txt2)
    wrong = txt.replace("ЕСИР број:", "ЕСИР број:  ").replace("123/1.0", "123/1.0-beta")
    check("ESIR number with extra data is flagged (common mistake d)", any("ЕСИР број" in e for e in ReceiptAgent().check(wrong, sale, "123", "1.0")))
    print("\n--- sample rendered receipt (Копија Рефундација) ---")
    print(txt2)

    MatrixAgent().write()
    print(f"\n[MatrixAgent] wrote certification_matrix.csv ({len(MatrixAgent.CASES)} cases), esir_questionnaire_answers.csv, submission_checklist.txt")
    print(f"\n{ok} checks passed")


if __name__ == "__main__":
    main()
