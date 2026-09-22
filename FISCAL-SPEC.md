# FISCAL-SPEC — contract for `packages/fiscal-core`

Distilled from the official Poreska uprava (PURS) documents kept in this folder. Cite them by the codes below in code comments and tests. Nothing here is invented; where a value is not printed in the documents it is marked VERIFY and must be confirmed on the sandbox before use.

| Code | Document | Use |
|---|---|---|
| TV | Tehnički vodič, jun 2021 (`Tehnickivodic.pdf`) | definitions, receipt content, invoice types, approval procedure |
| TU | Tehničko uputstvo za administrativni i tehnički pregled ESIR-a ili L-PFR-a, v1.17, 9.8.2024 (`Tehnickouputstvo-ESIRiliL-PFR.pdf`) | the certification process, ESIR self-assessment questionnaire (7.4.2), receipt layout (§16), special cases (§9), codebooks (§9.8) |
| ME | Tehničko uputstvo za ručno testiranje ESIR proizvoda, v1.1, 26.5.2022 (`RunotestiranjeESIRa.pdf`) | the manual tests PURS runs on our ESIR, 15 sample receipts, submission conditions (p.37), common mistakes |
| ML | Tehničko uputstvo za ručno testiranje L-PFR proizvoda, v1.0, 12.2.2021 (`RucnoTestiranjeLPFR-a_v10.pdf`) | PFR HTTP API behaviour, status codes, request/response JSON examples |

`fiscal_reference.py` in this folder is the executable version of this spec; its 22 self-tests reproduce numbers printed in the documents and must all pass in the TypeScript port (`packages/fiscal-core/test/reference.test.ts`).

## 1. Topology and what we are

EFU = one PFR + one or more ESIRs + BE (TV p.4). We are a software ESIR: PWAs on tablets/phones and the Hub, talking over the LAN to one L-PFR (TV p.5, figure "softverski ESIR-i preko lokalne mreže sa jednim L-PFR-om"). ESIR talks to L-PFR over HTTP and to V-PFR over HTTPS (TV p.11; TU §10 P14/P15). A physical venue must have an L-PFR; V-PFR alone is only for remote trade (TU §5 P1). The BE is a smart card in the L-PFR's reader; a receipt issued without BE is not a fiscal receipt (TV p.7).

We apply for a PRENOSIVO (transferable) approval of a NAPREDNI (advanced) ESIR, which must support all ten type/transaction pairs: Промет П/Р, Копија П/Р, Предрачун П/Р, Обука П/Р, Аванс П/Р (TU 7.2.3).

## 2. PFR HTTP API (`/api/v3`)

From ML TEST3–TEST8 and the sandbox Help pages. Base URL is the L-PFR's LAN address (Hub config) or the V-PFR URL.

| Call | Behaviour |
|---|---|
| `GET /api/v3/status` | returns status object with `gsc` list of codes; 200 even when card missing (codes 1300,1500,0210) |
| `POST /api/v3/pin` | body is the PIN; `0100` PIN OK [200]; `2100` PIN not OK [423]; `1300` card absent [200] |
| `GET /api/v3/attention` | liveness, HTTP 200 |
| `GET /api/v3/environment-parameters` | tax rates and environment; `1300` [400] without card |
| `POST /api/v3/invoices` | fiscalize; `1500` PIN required when locked; `1300` [400] without card |
| `GET /api/v3/invoices/{requestId}` | last signed invoice for an ESIR request id (ML p.13) |

Error bodies: an L-PFR may answer `text/plain` codes while the development L-PFR answers `application/json` (ML p.20). The client accepts both. Errors are prioritised lists; show the first to the operator.

Status codes seen in the documents: `0100` PIN OK, `1300` smart card not present, `1500` PIN code required, `2100` PIN not OK, `0210` appears in gsc lists (meaning VERIFY on sandbox "Status-and-Error-Codes").

Operational rules that follow (ML TEST1/TEST2): if the card is removed the PFR stops; reinserting requires the PIN again. The Hub must surface "unesite PIN" as a first-class state, not an error toast.

## 3. Invoice request

Fields as in ML TEST6 scenario 2 and TU §9 examples:

```
dateAndTimeOfIssue   ISO 8601; ONLY on Аванс-Продаја when a wire transfer was received before PFR date (TU §16 P5; ME p.30)
cashier              mandatory identification string (ME check 3); may carry code "10:JBKJS" for public-sector sellers (TU §9.8)
buyerId              "NN:value" per codebook (TU §9.8) or null
buyerCostCenterId    "NN:value" per codebook or null
invoiceType          Normal | ProForma | Copy | Training | Advance   (numeric 0/2 confirmed in TU §9.3/§9.6; 1,3,4 VERIFY)
transactionType      Sale | Refund   (numeric 0/1; refund=1 confirmed TU §9.3)
payment[]            { amount, paymentType }  — same type may repeat (TU §10 P8)
invoiceNumber        our own number or null
referentDocumentNumber   "JID-JID-N"; pre-fiscalization: "XXXXXXXX-XXXXXXXX-N"; old fiscal cash register: "XXXXXXXX-IBFM-BI" (TU §16 P6)
referentDocumentDT   PFR time of the referenced receipt
options              { omitQRCodeGen: "0"/"1", omitTextualRepresentation: "0"/"1" }
items[]              { gtin?, name, quantity (≤3 decimals), labels[], unitPrice (2 decimals, VAT-inclusive), totalAmount }
```

PaymentType enum (TU §10 P7, verbatim): Other=0, Cash=1, Card=2, Check=3, WireTransfer=4, Voucher=5, MobileMoney=6. Serbian labels (TV p.17): готовина=Cash, инстант плаћање=MobileMoney (IPS), платна картица=Card, чек=Check, пренос на рачун=WireTransfer, ваучер=Voucher, друго безготовинско=Other. Restricted mode: an installation may disable Card, Check and MobileMoney and enter them as Cash; one installation runs in exactly one mode (TU §10 P7). This is a tenant-level setting, immutable per installation.

Item name carries the unit of measure separated by "/" ("Ceđeni Sok/l"), omitted for piece goods (TU §16 P8, ME check 10). The PFR appends the label in parentheses on the journal. Reserved name prefixes: `10..13: Аванс (label)` for advances, `20..22: Једнонаменски ваучер` for single-purpose vouchers, `00: ` for free-of-charge supply with payment Other (TU §9.1, §9.5, §9.7, §9.8).

## 4. Response

Fields (ML p.23): `requestedBy` (BE JID), `sdcDateTime`, `invoiceCounter` ("6/16NS"), `invoiceCounterExtension`, `invoiceNumber` ("JID-JID-N", unique system-wide), `taxItems[]` {categoryType,label,amount,rate,categoryName}, `verificationUrl`, `verificationQRCode` (null when omitted), `journal` (text), `messages`, `signedBy`, `encryptedInternalData`, `signature`, `totalCounter`, `transactionTypeCounter`, `totalAmount`, `taxGroupRevision`, `businessName`, `tin`, `locationName`, `address`, `district`, `mrc`.

Persist the whole response verbatim in `fiscal_invoice.pfr_response` (jsonb). The receipt is built from it; the ESIR never alters or omits PFR-provided data (TU §9 P2/P3; ME "ESIR ne sme da izostavi").

## 5. Money and tax

Prices are VAT-inclusive; tax per label = gross × rate ÷ (100 + rate). Verified: 68.46 @9% → 5.65 (ML), 12,000,000 @20% → 2,000,000 (TU §9.3), 7,000 @20% → 1,166.67 (TU §9.6), 349.90 @20% + 40.00 @10% → 61.96 (ME sample 1).

Rounding: two decimals, half-up on the third (TU §11 P4, §12 P5; ME p.16): 5.1→5.10, 10.267→10.27, 20.143→20.14, 0.123×9.90→1.22, 0.123×9.95→1.22. Quantities up to three decimals. In TypeScript use integer para and `Math.round` on the half-para boundary; port the five cases as tests.

Tax labels come only from the PFR (`environment-parameters` / response `taxItems`, `taxGroupRevision`); an unknown label must be rejected before the request is sent (TU §12 P1, P6; ME p.18). Production Serbia labels differ from the sandbox (sandbox shows "A 9%"); never hardcode.

Change = paid − total, printed as Повраћај (TU §16 P9).

## 6. Rules by invoice type

- Copy and any Refund: `referentDocumentNumber` and `referentDocumentDT` mandatory (TV p.19–20; TU §10 P12; ME p.11).
- Промет-Продаја closing an advance: references the Аванс-Рефундација (TU §10 P13, §9.1).
- Advance chain (TU §9.1.1): each Аванс-Продаја references the previous AP; before the final PP issue an Аванс-Рефундација referencing the last AP for the full advanced amount (items `10..13: Аванс`, qty 1, price editable by cashier); the final PP references the AR; the AR is not handed to the customer; the advert field on the PP must state number and date of the last AP. Advances received before e-fiscalization use `XXXXXXXX-XXXXXXXX-N` references (TU §9.1.2).
- Cancelling a wrong receipt (TU §9.3): issue the mirror Refund with `buyerId = "10:<own PIB>"`, reference to the wrong receipt, all items and prices; then issue the correct receipt. A receipt that should have carried a buyer ID can only be cancelled and reissued immediately after the sale.
- Corporate cards (TU §9.4): `buyerCostCenterId = "50:<card>"`, payment always Voucher; monthly storno via Промет-Рефундација with `"60:ddmmgggg_ddmmgggg"`.
- Single-purpose vouchers (TU §9.5): item `20..22: Једнонаменски ваучер`, qty 1.
- Cash refund on the spot: Копија-Рефундација issued right after Промет-Рефундација with a "Потпис купца: ____" line; not issued for card refunds (TU §9.6).
- Free-of-charge supply: `00:` prefix, payment Other (TU §9.7).
- Buyer identification codebook (TU §9.8): buyerId prefixes 10–16, 20–23, 30–36, 40; buyerCostCenterId prefixes 20, 21, 30–33, 50, 60; cashier prefix 10.
- ESIR time (`dateAndTimeOfIssue`) appears only on АП with an earlier wire transfer; must be absent on every other type (ME note p.7; TU §16 P5).

## 7. Receipt (textual representation), TU 7.4.2 §16

Order and mandatory elements: title line `=== ФИСКАЛНИ РАЧУН ===` (P1); PFR header PIB, обвезник, место продаје, адреса, град (P2); Касир (P3); ИД купца and Опционо поље купца only when sent (P4; common mistakes a–c); `ЕСИР број: IB/version` exactly, e.g. `123/1.0`, nothing appended (P5; mistake d); `ЕСИР време` only on АП wire case (P5); Реф. број and Реф. време on Copy/Refund and PP closing AR (P6); type line `--- ПРОМЕТ - ПРОДАЈА ---` (P7); Артикли table with name/unit, unit price, quantity, line total, negative totals on refunds (P8); За уплату, one `Уплаћено - <method>` per payment, Повраћај, tax table by label with rate and amount, Укупан износ пореза (P9); for Копија/Предрачун/Обука the message `ОВО НИЈЕ ФИСКАЛНИ РАЧУН` in the body at least double the font size, and the title lines at top and bottom replaced by it (P10; TV p.17); ПФР време, ПФР број рачуна, Бројач рачуна (P11); QR square 40–50 mm, no logo, or a verification hyperlink for electronic delivery (P12; TV p.19); `=== КРАЈ ФИСКАЛНОГ РАЧУНА ===` (P13); advert field below the end line in a smaller font, mandatory for advanced ESIR (P14; TV p.20).

Samples submitted must be scannable (mistake h). Data on the receipt must match the PURS administration portal.

## 8. Operational obligations of the ESIR (TU 7.4.2)

Mandatory: authenticate with PFR on startup (§10 P2); software product must expose manufacturer, serial number, software version (§10 P6); all payment methods plus restricted mode (§10 P7); connect to peripherals without disturbing the PFR (§10 P9); issue receipts electronically and printed (§10 P10); GTIN support (§10 P11); reference numbers (§10 P12/P13); HTTP to L-PFR, HTTPS to V-PFR (§10 P14/P15); electronic journal with search for the last 30 days (§10 P16); create item, choose quantity, change price (advanced), rounding, select by name or GTIN scan, import/export item list (§11); tax rates only from PFR, printed with label and rate, shown on demand (§12); Wi-Fi connection to PFR (§6 P1).

Forbidden (§9): issuing anything without PFR data; omitting or changing PFR data or header data.

Optional but implemented: discounts (§10 P4), removing lines before issue (§10 P3), split payments (§10 P8).

## 9. Certification process (TU §7, §7.9, §8)

1. Register on the developer environment `https://tap.sandbox.suf.purs.gov.rs/` (company data, contact); confirm by email; PURS reviews; certificates for the sandbox arrive by email (TU 7.1.1–7.1.4). A test BE is provided for sandbox use only (TV p.7).
2. Develop against sandbox V-PFR and the development L-PFR.
3. Submit the application for technical review with the self-assessment questionnaire (17 sections, answers proposed in `esir_questionnaire_answers.csv`), the 15 sample receipts (advanced classification, TU §17) and documentation in Serbian: brochure/website, user manual, installation manual, configuration manual (TU 7.4.2 §2; ME p.3–4). Status flow: Priprema tehničkog dela → Tehnički deo dostavljen → Tehnički pregled → Tehnički deo odobren, or Potrebne tehničke izmene (TU 7.3, 7.4).
4. Submission conditions (ME p.37): at least one receipt signed by an L-PFR; a PP closing an advance; an АП with ЕСИР време at least one day before PFR time; a receipt with a GTIN item; a PP with Опционо поље купца; a V-PFR-signed receipt if V-PFR is supported; a receipt with all payment methods; one with multiple tax labels; the rounding test receipt.
5. After "Tehnički deo odobren" submit the request for approval; the legal 15-day deadline starts then; the rešenje carries the IB and the report (TU §7). The IB/version becomes the `ЕСИР број` on every receipt.
6. Any change that alters functionality or receipt appearance requires a new application with samples (TU 7.9). PURS inspects venues to check the deployed product matches the approved one and can revoke approval (TU 7.10). Therefore `fiscal-core` is versioned separately, and the receipt renderer lives inside it.

Technical team: Mekenzijeva 53, Beograd; budiefiskalizovan@purs.gov.rs; Mon–Fri 7:30–15:30 (TU §8).

## 10. L-PFR partner interface requirements we depend on

Proof-of-audit limits: once the BE reaches its limit without proof of audit from SUF, the next signing is blocked until the L-PFR uploads and receives the proof (ML p.5–7); with no internet the venue exports audit packages to USB/SD and uploads them through the PURS portal (ML p.7–12). The Hub must show the L-PFR's limit warnings and never queue receipts for later. The L-PFR must keep issuing while a local audit runs (ML p.13).

## 11. Test plan mapping

`certification_matrix.csv` maps 36 document test cases to automated test ids. Each id must exist in `packages/fiscal-core` or the relevant app before P2.1 is considered done.
