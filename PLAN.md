# ŠANK — plan proizvoda, softvera i sajta

Verzija 1.0, 21. septembar 2026. Autor: Đorđe Vukojević. Dokument je ulaz za Claude Code; tehničke odluke su obavezujuće osim ako se u `docs/decisions/` ne zabeleži izmena.

---

## 1. Teza

Svaki ugostiteljski objekat u Srbiji po zakonu mora da izdaje fiskalne račune kroz odobren ESIR, i skoro svaki to radi kroz softver koji je projektovan oko fiskalne kase, magacina i knjigovodstva, a ne oko dva trenutka koja se u lokalu dešavaju stotinama puta dnevno: konobar dodaje pivo na sto i gost (ili gazda) hoće da zna koliko je sto potrošio pre nego što se traži račun. Tržište je usitnjeno na desetak domaćih vendora (UniSoft, BKC Soft, Teron, Petcom, DCS, Softek, Logika, BizCore, ITSmart, 2D Soft) plus jedan uvezeni sistem (Syrve preko ITmathics-a). Cene su niske i ujednačene, funkcije su slične, a razlika u kvalitetu korisničkog iskustva na podu sale je velika i to je prostor za ulazak.

Šank je platforma koja to radi obrnuto: front-of-house prvo (brzina, sala, račun uživo, kuhinjski ekran, plaćanje na stolu), fiskalizacija kao nevidljiv sloj ispod, a analitika marže (Normativ) kao drugi proizvod koji raste iz istih podataka. Cilj za 12 meseci: odobren napredni ESIR, 150 do 350 objekata, ARR 150 do 300 hiljada evra, spremnost za Expo 2027 (15. maj do 15. avgust 2027).

## 2. Šta tržište naplaćuje i kako vendori zarađuju

Cene su po objektu mesečno, bez PDV-a, preračunato po 117,2 RSD/EUR. Podaci su sa javnih cenovnika u septembru 2026, osim gde je navedena godina.

| Vendor | Paket | EUR/mes | LPFR uključen | Model |
|---|---|---|---|---|
| BizCore | ESIR + LPFR osnova | 38 | da | modularni SaaS, bez naplate po računu i kasiru |
| BizCore | sve uključeno (online, KDS, kiosk, displej) | 124 | da | dodaci se sabiraju |
| BizCore | samo LPFR (za tuđi ESIR) | 7 | da | LPFR kao samostalna stavka |
| Syrve (ITmathics) | Basic / Professional / Enterprise | 39 / 59 / 89 | ne | po kasi; LPFR +20, konobar app +10, dostava +20 po platformi, setup 50, obuka 30/h |
| Syrve realno za restoran | Pro + LPFR + konobar + jedna dostava | 109 | da | |
| POS Sector | Basic (2023) | 22 | ne | mesečno ili godišnje (dva meseca gratis) |
| 2D Soft | Cashbox / Garson (2022) | 10 / 29 | ne | L-PFR+ 5 EUR/mes |
| DCS Cafe Soft | iznajmljivanje + održavanje | na zahtev | da | instalacija 150 EUR sa prvim mesecom |
| Petcom Bmaster, UniSoft, Softek | licenca + obavezno mesečno održavanje | na zahtev | da | podrška vezana za održavanje |

Medijana ulaznog paketa je 29 EUR, medijana punog restoranskog steka 109 EUR. Struktura prihoda vendora ima šest slojeva: mesečna licenca ili iznajmljivanje (jezgro), LPFR kao posebna stavka (5 do 20 EUR ili 800 RSD, marža na komponentu za usklađenost), dodaci (KDS, online poručivanje, kiosk, integracija dostave, 13 do 43 EUR svaki), usluge (instalacija 50 do 150 EUR, obuka 30 EUR/h), hardver (tableti, štampači, kase; komplet za e-fiskalizaciju oko 270 EUR) i obavezno održavanje. Nijedan srpski vendor ne uzima procenat od plaćanja.

Referenca sa razvijenog tržišta: Toast je 2024. imao 706 miliona dolara pretplate naspram 4,1 milijarde od plaćanja, plaćanja su 85 odsto prihoda, take rate 48 baznih poena, SaaS marža 80 odsto, NRR 109 odsto, a objekat posle pet godina na platformi nosi preko 16.000 dolara ARR. U Srbiji taj model nije direktno dostupan jer kartično prihvatanje vode banke, ali IPS QR (NBS) naplaćuje trgovcu 0,3 odsto unutar banke i 0,5 odsto između banaka, višestruko manje od kartica, i to otvara partnerski put (platna institucija u IPS sistemu) koji planiramo kao opciju, ne kao osnovu.

## 3. Naš model prihoda

Tri tarife po objektu mesečno, sa dodacima, uslugama i marginom na hardver. LPFR u prvoj fazi ide preko partnera (odobren LPFR koji radi sa svakim ESIR-om, tipa 800 RSD), a sopstveni LPFR se gradi u fazi 4 da bi se ta marža uhvatila.

| Tarifa | RSD/mes | EUR | Sadržaj | Očekivan udeo |
|---|---|---|---|---|
| Start | 3.900 | 33 | 1 kasa, sala, račun uživo, napredni ESIR, mobilni pregled za vlasnika | 45% |
| Pro | 7.900 | 67 | + kuhinjski ekran, konobar aplikacija, deljenje računa, Normativ lite, SEF | 40% |
| Plus | 14.900 | 127 | + više objekata, Normativ full, integracije dostave, IPS plaćanje na stolu, API | 15% |

Dodaci: dodatna kasa 1.900 RSD, integracija dostave 2.000 RSD po platformi. Onboarding 60 do 160 EUR. Marža na hardver 0 do 120 EUR po objektu. Portal za knjigovodstvene agencije je besplatan jer je to prodajni kanal.

Rezultati Monte Carlo modela (`sank_business_model_engine.py`, 10.000 simulacija, 36 meseci, tri meseca bez naplate zbog sertifikacije i pilota):

| Scenario | Objekata @36m | ARR @36m P10/P50/P90 | LTV/CAC | P(profitabilan mesec do m24) | Najniži keš P50 / najgorih 10% |
|---|---|---|---|---|---|
| A: čist SaaS, direktna prodaja | 330 | 99 / 245 / 637 kEUR | 6,5 | 60% | −59k / −137k |
| B: + sopstveni LPFR, deo kroz agencije | 331 | 118 / 280 / 698 kEUR | 8,1 | 72% | −51k / −108k |
| C: B + agencijski kanal + IPS partner | 329 | 124 / 283 / 701 kEUR | 10,6 | 82% | −44k / −88k |

Scenario B daje ARPU od 74 EUR po objektu mesečno, churn 2,4 odsto mesečno, blendovani CAC 235 EUR, medijalni break-even u 18. mesecu. Potreban runway je 60 do 110 hiljada evra da se pokrije najgorih 10 odsto ishoda. Osetljivost pokazuje da je direktni CAC važniji od churna: pri CAC 150 EUR verovatnoća profitabilnog meseca do m24 je oko 80 odsto bez obzira na churn, pri CAC 400 EUR pada ispod 55 odsto. Zaključak za GTM: agencijski kanal i self-serve onboarding nisu opcija nego uslov.

## 4. Regulatorni okvir koji oblikuje arhitekturu

Izvori su četiri zvanična dokumenta Poreske uprave koja stoje u `docs/certification/`: Tehnički vodič (2021), Tehničko uputstvo za administrativni i tehnički pregled ESIR-a ili L-PFR-a v1.17 (avgust 2024), i dva uputstva za ručno testiranje (ESIR v1.1, L-PFR v1.0). Njihova destilacija za inženjere je `docs/certification/FISCAL-SPEC.md`, a `fiscal_reference.py` je izvršna referenca sa 22 samoprovere koje reprodukuju brojeve iz dokumenata (zaokruživanje, PDV iz bruto cene, pravila po vrsti računa, izgled isečka).

Elektronski fiskalni uređaj se sastoji od jednog PFR-a, jednog ili više ESIR-a i BE. Mi smo softverski ESIR (tableti i telefoni kroz Hub) koji preko LAN-a razgovara sa jednim L-PFR-om; fizički objekat ne sme da radi samo sa V-PFR-om. ESIR sa L-PFR-om komunicira HTTP-om (`/api/v3/status`, `pin`, `attention`, `environment-parameters`, `invoices`), a V-PFR HTTPS-om. Kada se pametna kartica izvadi, PFR staje, a vraćanje traži ponovni PIN; kada BE dostigne limit bez dokaza o iščitavanju, sledeće potpisivanje je blokirano dok L-PFR ne dobije potvrdu iz SUF-a. Zato ne postoji "fiskalizuj kasnije".

Prijavljujemo se za prenosivo odobrenje naprednog ESIR-a (deset parova vrsta/tip računa: promet, kopija, predračun, obuka, avans; prodaja i refundacija). Postupak: registracija na razvojno okruženje `tap.sandbox.suf.purs.gov.rs`, sertifikati za sandbox, razvoj, prijava za tehnički pregled sa upitnikom za samoprocenu (17 sekcija), 15 uzoraka računa i dokumentacijom na srpskom (brošura ili sajt, korisničko uputstvo, uputstvo za instalaciju, uputstvo za konfiguraciju), tehnički pregled sa statusima, pa zahtev za odobrenje od kojeg teče zakonski rok od 15 dana; rešenje nosi IB koji se štampa kao `ЕСИР број: IB/verzija` na svakom računu. Uslovi za predaju uzoraka: bar jedan račun potpisan L-PFR-om, promet-prodaja koja zatvara avans, avans-prodaja sa ESIR vremenom bar dan pre PFR vremena, račun sa GTIN-om, račun sa opcionim poljem kupca, račun sa svim načinima plaćanja, račun sa više poreskih oznaka i račun koji ponavlja test zaokruživanja. Svaka izmena koja menja funkcionalnost ili izgled računa traži novu prijavu, a Poreska uprava kontroliše da li je proizvod u objektu isti kao odobreni.

Iz ovoga slede tri arhitektonske odluke koje se ne menjaju:

1. Fiskalno jezgro (`packages/fiscal-core`) je izolovan paket bez UI-ja, sa sopstvenom verzijom, u kome žive model zahteva i odgovora, pravila po vrsti računa, zaokruživanje, obračun PDV-a iz bruto cene i renderer isečka. Sve što se često menja (sala, meni, KDS, analitika) ne dira ga.
2. ESIR se razvija i testira protiv sandbox okruženja Poreske uprave, a u produkciji razgovara sa bilo kojim odobrenim L-PFR-om preko istog HTTP API-ja. LPFR partner u fazi 1, sopstveni LPFR u fazi 4.
3. Objekat dobija lokalni čvor, „Šank Hub”: servis na računaru ili mini-PC-u u lokalu koji drži vezu sa L-PFR-om (i njegovom karticom), drajvere za štampače, lokalni keš i sinhronizaciju ka cloudu. Tableti i telefoni pričaju sa Hubom preko LAN-a, pa kasa radi kada internet padne; upozorenja L-PFR-a o limitu i PIN-u su stanja prvog reda u interfejsu.

SEF (Sistem elektronskih faktura) je obavezan za prijem i čuvanje e-faktura svima u sistemu PDV-a od 1. jula 2022, sa besplatnim API pristupom. To je izvor podataka za Normativ i ulazi u Pro tarifu.

## 5. Proizvod

### 5.1 Šank POS (sala i naplata)

Ekran sale sa stolovima u boji i tekućim iznosom po stolu, vidljiv bez otvaranja stola. Naručivanje jednim dodirom sa kategorijama, brzim artiklima i količinskom značkom. Račun uživo stalno vidljiv pored naručivanja. Prebacivanje stavki između stolova, spajanje i razdvajanje stolova, deljenje računa po stavkama ili po broju gostiju, delimična naplata. Naplata: gotovina, kartica (ručno ili preko ECR integracije), IPS QR, na račun (B2B faktura), kombinovano. Bakšiš karticom evidentiran odvojeno od pazara. Fiskalizacija u jednom dodiru, štampa fiskalnog računa sa QR kodom i nefiskalnih naloga za kuhinju i šank. Storno sa PIN-om i razlogom. Smene, PIN prijava konobara na deljenom uređaju, promet po konobaru. Sve radi offline preko Huba i sinhronizuje se kad se veza vrati.

Nije u obimu prve verzije: rezervacije, program lojalnosti, sopstvena mobilna aplikacija za goste.

### 5.2 Šank Kuhinja (KDS)

Tiketi u realnom vremenu po stanicama (roštilj, priprema, šank), tajmer po tiketu, boje po kašnjenju, zbirni prikaz po artiklu za roštilj, „gotovo” vraća status na kasu. Bez ograničenja broja ekrana po objektu. Radi u browseru na bilo kom tabletu ili TV-u sa Android boksom.

### 5.3 Šank Gost (QR meni i plaćanje na stolu)

Meni na QR kodu, višejezičan (sr, en, de, ru, tr, zh) sa alergenima, vezan za isti katalog kao kasa. U Plus tarifi: gost vidi svoj račun na telefonu, plaća IPS QR-om ili karticom, deli sa društvom, ostavlja bakšiš; kasa dobija potvrdu i fiskalizuje. Tempirano za Expo 2027.

### 5.4 Normativ (back office marže)

Automatski prijem ulaznih faktura iz SEF-a, uparivanje stavki sa namirnicama, normativi po jelu, teorijski naspram stvarnog utroška iznad dozvoljenog kala, pomeranje cena dobavljača, matrica menija, predlog cena sa ograničenjem koraka, kartica za kuhinju, nedeljni pregled i tri akcije. Lite verzija u Pro tarifi (normativi, utrošak, cene dobavljača), full u Plus (matrica menija, repricing, više objekata, agencijski portal). Referentna implementacija logike već postoji u `normativ_engine.py`.

### 5.5 Portal za knjigovođe

Jedan ekran za sve klijente: SEF sandučići, rokovi za prihvatanje faktura, stavke za potvrdu, odstupanje utroška, dnevni pazari i izveštaji spremni za knjiženje, DPU knjiga. Besplatan; agencija dovodi objekte.

### 5.6 Admin i onboarding

Self-serve registracija, unos PIB-a i poslovnog prostora, čarobnjak za uvoz menija (CSV, slika menija preko OCR-a, ručno), povezivanje L-PFR-a i BE kartice, test račun u režimu obuke, izbor hardvera, upravljanje uređajima, korisnicima, ulogama i cenovnicima, više objekata pod jednim nalogom.

## 6. Arhitektura

Monorepo (pnpm workspaces, TypeScript svuda), tri sloja: cloud, hub, klijenti.

```
sank/
  apps/
    pos/          React + Vite PWA: sala, naručivanje, naplata (tablet, telefon)
    kds/          React PWA: kuhinjski ekran
    gost/         React: QR meni i plaćanje na stolu (mobilni web)
    admin/        React: onboarding, podešavanja, Normativ, portal za knjigovođe
    web/          Astro: marketing sajt, cenovnik, demo, dokumentacija, blog
    hub/          Node servis u objektu: LPFR klijent, štampa, keš, sync (pakuje se kao jedan binarni fajl, Docker za mini-PC)
    api/          Fastify + TypeScript: REST + WebSocket, multi-tenant
  packages/
    fiscal-core/  čist TS: model računa po Tehničkom vodiču, PFR HTTP klijent, formatiranje isečka, QR
    domain/       tipovi, komande i događaji (order aggregate), validacija (zod)
    ui/           dizajn sistem (tokeni iz prototipa: Fraunces, IBM Plex, paleta papir/mastilo/paprika)
    sync/         outbox/inbox protokol klijent–hub–cloud, idempotentne komande
    sef-client/   SEF API klijent (UBL), prijem i slanje e-faktura
    printing/     ESC/POS rasteri i šabloni (fiskalni isečak, nalog za kuhinju)
    db/           Drizzle šeme i migracije (Postgres u cloudu, SQLite na hubu)
  docs/           ovaj plan, ADR-ovi, sertifikaciona dokumentacija
```

Tehnologije: React 19, Vite, TypeScript strict, Tailwind sa tokenima iz `packages/ui`, Zustand za lokalno stanje, Dexie (IndexedDB) za offline keš na klijentu, Fastify, Drizzle ORM, PostgreSQL 16 u cloudu, SQLite (better-sqlite3) na Hubu, WebSocket za realtime (Postgres LISTEN/NOTIFY u početku, Redis kad zatreba), zod za sve ulaze, Vitest i Playwright za testove, Docker za api i hub, Hetzner (EU) ili domaći provajder za hosting, Cloudflare ispred sajta.

Model podataka po objektu je event-sourced za porudžbine: svaka radnja (otvori sto, dodaj stavku, prebaci, naplati, storniraj) je događaj sa ID-jem, autorom, vremenom i uređajem; stanje stola je projekcija. Komande su idempotentne (client-generated UUID), pa se ista komanda može bezbedno ponoviti posle prekida veze. Hub je autoritet za objekat u realnom vremenu; cloud je autoritet za katalog, korisnike, izveštaje i istoriju. Konflikti se rešavaju po pravilu „hub pobeđuje za stanje stolova, cloud pobeđuje za katalog”.

Fiskalni tok: POS šalje komandu `Checkout`, Hub sastavlja zahtev preko `fiscal-core`, šalje ga L-PFR-u (`POST /api/v3/invoices` na LAN adresi, tačan ugovor se uzima iz Tehničkog vodiča i proverava u sandboxu), dobija potpisan odgovor (brojač, QR, journal), štampa isečak preko `printing`, upisuje fiskalni događaj i sinhronizuje ga u cloud. Ako L-PFR nije dostupan, naplata se ne izvršava (nema „kasnije fiskalizuj”; zakon to ne dozvoljava), a POS to jasno kaže.

Bezbednost: tenant izolacija na nivou svakog upita (tenant_id u svakoj tabeli, RLS u Postgresu), PIN i uloge (vlasnik, menadžer, konobar, kuhinja, knjigovođa), audit log nepromenljiv, TLS svuda, tajne u okruženju, dnevne enkriptovane kopije, GDPR-kompatibilno rukovanje podacima gostiju (Gost modul ne čuva identitet bez pristanka).

## 7. Model podataka (jezgro)

`tenant`, `venue`, `device`, `user`, `role`, `shift`, `floor`, `table`, `catalog_category`, `catalog_item` (naziv, cena sa PDV-om, poreska stopa, štampač/stanica, modifikatori), `price_list`, `order` (agregat po stolu ili poneti), `order_event`, `order_line`, `payment` (način, iznos, bakšiš, referenca), `fiscal_invoice` (tip računa, tip transakcije, brojač, QR, PFR odgovor, verzija fiscal-core), `kds_ticket`, `ingredient`, `recipe` (normativ), `supplier`, `sef_invoice`, `sef_invoice_line`, `stock_count`, `variance_report`, `agency`, `agency_client`.

## 8. Integracije

PFR (L-PFR i V-PFR sandbox) po Tehničkom vodiču Poreske uprave; SEF API (UBL 2.1, prijem i slanje, prihvatanje u roku); ESC/POS štampači (USB, LAN, Bluetooth); bankarski ECR protokoli za terminale (faza 3, po banci); NBS IPS QR generisanje (faza 3, uz ugovor sa bankom ili platnom institucijom); Wolt i Glovo partner API (faza 3, kao dodatak); knjigovodstveni izvoz (CSV i API za najčešće programe).

## 9. Sajt

Astro, sr-Latn primarno, en sekundarno, isti dizajn sistem kao proizvod. Stranice: početna (teza i interaktivni demo koji već postoji), Proizvod (POS, Kuhinja, Gost, Normativ), Cenovnik (tri tarife, dodaci, kalkulator „koliko plaćam sada naspram Šanka”), Za knjigovođe, Fiskalizacija (vodič: ESIR, LPFR, BE, šta treba novom lokalu; ovo je SEO stub jer konkurenti rangiraju na ovim terminima), Dokumentacija, Blog, Kontakt i zakazivanje demoa, Prijava. Lead forma piše u Postgres i šalje email; self-serve registracija vodi u admin onboarding. Analitika bez kolačića (Plausible). Brzina: Lighthouse 95+, sve slike optimizovane, bez eksternih skripti osim fontova.

## 10. Faze i radni paketi za Claude Code

Svaki paket ima jasan „gotovo je kad”. Redosled je obavezan unutar faze; faze se delimično preklapaju.

### Faza 0: temelj (nedelje 1 do 3)
- P0.1 Monorepo, TypeScript strict, lint, format, CI (GitHub Actions: typecheck, test, build). Gotovo: `pnpm -r build` prolazi.
- P0.2 `packages/ui` sa tokenima i komponentama iz prototipa (dugme, čip, kartica, tabela, stepper, tab). Gotovo: Storybook sa svim komponentama u svetloj i tamnoj temi.
- P0.3 `packages/domain`: komande, događaji, order aggregate, projekcije, zod šeme, 100% testirano. Gotovo: property testovi za idempotentnost i redosled događaja.
- P0.4 `packages/db`: šeme i migracije za sve entitete iz §7, seed sa „Restoran Primer”. Gotovo: migracije prolaze na čistoj bazi, seed vraća radnu salu.
- P0.5 Prototip `sank-website/index.html` prebačen u `apps/web` kao demo komponenta.

### Faza 1: kasa koja radi (nedelje 3 do 10)
- P1.1 `apps/api`: auth (tenant, PIN, uloge), katalog, sala, order komande i događaji, WebSocket. Gotovo: Postman kolekcija, integracioni testovi.
- P1.2 `apps/pos`: sala, naručivanje, račun uživo, prebacivanje i deljenje, naplata (bez fiskalizacije). Gotovo: Playwright scenario „dva piva, ćevapi, podeli na tri, naplati”.
- P1.3 `apps/hub`: lokalni servis, SQLite keš, sync protokol sa cloudom, otkrivanje na LAN-u. Gotovo: kasa radi 30 minuta bez interneta i sinhronizuje se bez gubitka događaja.
- P1.4 `packages/fiscal-core`: port `fiscal_reference.py` u TypeScript (isti nazivi agenata: schema, money, rules, receipt), PFR klijent za `/api/v3`, svih deset vrsta računa, specijalni slučajevi iz TU §9 (lanac avansa, poništavanje sa sopstvenim PIB-om, korporacijske kartice, jednonamenski vaučeri, promet bez naknade, šifarnici), restriktivni mod plaćanja, renderer isečka po TU §16. Gotovo: 22 referentna testa zelena, svih 36 slučajeva iz `certification_matrix.csv` ima test, zeleno protiv sandbox V-PFR-a i razvojnog L-PFR-a.
- P1.5 `packages/printing`: ESC/POS, šabloni fiskalnog isečka i naloga za kuhinju. Gotovo: štampa na dva najčešća štampača (Epson TM-T20 klasa, kineski 80mm).
- P1.6 Naplata sa fiskalizacijom kroz Hub i partner L-PFR. Gotovo: pravi fiskalni račun u test režimu, QR prolazi proveru na portalu Poreske uprave.

### Faza 2: sertifikacija, kuhinja, pilot, sajt (nedelje 10 do 16)
- P2.1 Sertifikacija: registracija na sandbox (uraditi odmah u fazi 0), 15 uzoraka računa po TU §17 generisanih iz fiscal-core, dokumentacija na srpskom (brošura/sajt, korisničko uputstvo, uputstvo za instalaciju, uputstvo za konfiguraciju), popunjen upitnik (`esir_questionnaire_answers.csv`), uslovi iz `submission_checklist.txt` ispunjeni. Gotovo: prijava za tehnički pregled podneta, verzija fiscal-core zamrznuta i tagovana; posle statusa „Tehnički deo odobren” podnet zahtev za odobrenje.
- P2.2 `apps/kds`. Gotovo: tiket od kase do „gotovo” ispod 300 ms na LAN-u.
- P2.3 `apps/admin`: onboarding, meni uvoz, uređaji, korisnici, izveštaji dana i smene. Gotovo: novi objekat od registracije do prvog računa u obuci za 20 minuta bez pomoći.
- P2.4 `apps/web` uživo sa cenovnikom, demoom, vodičem o fiskalizaciji i lead formom.
- P2.5 Pilot u 3 do 5 objekata u Beogradu (jedan kafić, dva restorana, jedan roštilj) sa partner L-PFR-om. Gotovo: 30 dana rada, izmerena brzina naručivanja i broj intervencija podrške.

### Faza 3: monetizacija i kanal (meseci 5 do 8)
- P3.1 `packages/sef-client` i Normativ lite (uparivanje, normativi, utrošak, cene dobavljača), portal za knjigovođe. Gotovo: dve agencije sa po pet klijenata.
- P3.2 Konobar mobilna aplikacija (PWA na telefonu), bakšiš tok, ECR integracija za bar jednu banku.
- P3.3 Šank Gost: QR meni višejezičan, plaćanje na stolu preko IPS QR-a. Gotovo: ugovor sa bankom ili platnom institucijom za IPS, prvi objekat naplaćuje na stolu.
- P3.4 Integracije Wolt i Glovo, naplata dodataka, samostalna promena tarife.

### Faza 4: skala (meseci 9 do 12)
- P4.1 Sopstveni L-PFR (odobrenje kao poseban element), zamena partnera gde se isplati.
- P4.2 Više objekata, centralni katalog, Normativ full, javni API.
- P4.3 Spremnost za Expo 2027: meni na šest jezika, sezonsko osoblje sa PIN-om za dan, izveštaji po smeni.

## 11. Izlazak na tržište

Kanal jedan su knjigovodstvene agencije: one već sede u SEF sandučićima svojih klijenata i imaju uticaj na izbor kase; portal je besplatan, a agencija dobija 10 odsto prve godine pretplate za svaki dovedeni objekat. Kanal dva je self-serve sajt sa SEO sadržajem o fiskalizaciji (na to konkurenti dobijaju promet) i besplatnim probnim periodom od 30 dana (standard na tržištu). Kanal tri je direktna prodaja u Beogradu za restorane sa kuhinjom (Pro tarifa) i lance (Plus), gde se kasa nudi kao zamena za postojeću uz besplatan prenos menija.

Poruka: „Pivo jednim dodirom. Sto vidiš na prvi pogled. Fiskalizacija se ne vidi.” Cena Start tarife je namerno 15 odsto iznad medijane ulaznih paketa i 69 odsto ispod punog steka konkurenata, jer prodajemo brzinu, ne najnižu cenu. Pro je glavni proizvod. Plus postoji da ne izgubimo lance i hotele.

## 12. Rizici i šta prvo proveriti

1. Sandbox pristup: registracija na `tap.sandbox.suf.purs.gov.rs` je prvi zadatak faze 0 jer PURS ručno pregleda registraciju pre slanja sertifikata; numeričke vrednosti InvoiceType 1/3/4 i značenje koda 0210 proveriti na sandbox Help stranama (označeno VERIFY u FISCAL-SPEC).
2. Uslovi partner L-PFR-a (cena, SLA, ko drži BE karticu). Kandidati: BizCore LPFR (800 RSD, radi sa svakim ESIR-om), Master LPFR, myLPFR.
3. Rok odobrenja u praksi (15 dana je zakonski rok od podnošenja posle provere; realno računati 6 do 10 nedelja sa ispravkama).
4. Hardver: koje tablete i štampače standardizovati; kupiti tri kompleta za razvoj.
5. Bakšiš karticom: 20 odsto porez i tretman kroz kasu; proizvod mora korektno da evidentira, ne da savetuje.
6. Offline pravila: limit BE bez dokaza o iščitavanju kontroliše SUF; Hub mora da prikaže upozorenje L-PFR-a i da vodi operatera kroz lokalno iščitavanje na USB kada interneta nema danima (ML §Lokalno iščitavanje).
7. Konkurencija na cenu: BizCore je 38 EUR sa LPFR-om; naša odbrana je proizvod, ne cena.
8. Glovo je u avgustu 2026. napustio BiH i pod znakom je pitanja regionalno; integracije dostave držati kao dodatak koji se lako gasi.

## 13. Metrike

Vreme od dodira do stavke na računu ispod 1 s; od naplate do štampe fiskalnog računa ispod 3 s; 99,9 odsto uspešnih fiskalizacija; onboarding bez pomoći ispod 20 minuta; mesečni churn ispod 2,5 odsto; NRR iznad 105 odsto kroz dodatke; direktni CAC ispod 200 EUR; udeo objekata dovedenih preko agencija iznad 40 odsto do kraja prve godine.
