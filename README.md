# burp

A corpus of Hungarian business-lunch menus from Kiskunfélegyháza, with a pipeline that turns scraped HTML into cleaned, lemmatized, categorized, and seasonally-analyzed dish data.

## Pipeline

1. **Scrape** — `0_code/hol_menuzzek.py` collects daily menu HTML into `1_html/`. Runs weekly via GitHub Actions.
2. **HTML → text** — `0_code/html_to_text.sh` converts to `2_txt/`.
3. **Extract menus** — `menu_extractor.py` produces `daily_menus.csv`.
4. **Clean dishes** — `clean_dishes.py` deduplicates and normalizes into `cleaned_dishes.csv`.
5. **Lemmatize** — `process_cleaned_dishes_spacy.py` (HuSpaCy) → `dishes_with_lemmas.csv`; `create_lemma_dictionary.py` → `lemma_dictionary.json`.
6. **Categorize** — `categorize_dishes.py` tags course, protein, and cooking method → `categorized_dishes.csv`.
7. **Resolve synonyms** — `resolve_synonyms.py` collapses variants using `0_code/synonym_map.json` → `dishes_resolved.csv`.
8. **Seasonal analysis** — `seasonal_analysis.py` produces monthly counts and seasonal summaries.

## Usage

```bash
make all       # run steps 2–8
make clean     # remove generated artifacts
```

Individual steps: `make text | menus | dishes | lemmas | categorize | synonyms | seasonal`.

Dependencies in `requirements.txt`.

## TL;DR

Corpus: ~39,600 menu rows, ~6,900 unique dishes after resolution, Nov 2022 → Jun 2025.

1. **Courses** — főétel 4,985 (73%) · leves 1,399 (20%) · főzelék 339 (5%) · desszert 148 (2%).
2. **Proteins** — csirke 2,086 · sertés 1,838 · vegetáriánus 697 · marha 374 · hal 238.
3. **Cooking methods** — rántott 1,143 · sült 919 · töltött 427 · párolt 413 · pörkölt 311.
4. **Top dishes overall** — roston csirkemell 748 · gyümölcsleves 696 · burgonyapüré 649 · rizibizi 647 · hasábburgonya 545.
5. **Top soups** — gyümölcsleves 696 · csontleves 484 · húsleves 428 · zöldségleves 363 · paradicsomleves 170.
6. **Top főzelék** — tökfőzelék fasírozottal 26 · burgonyafőzelék fasírttal 25 · sárgaborsó főzelék sertéspörkölttel 21 · kelkáposzta főzelék fasírozottal 21 · gyümölcsfőzelék párizsi csirkemellel 19.
7. **Winter-peaking dishes (peak Dec–Feb)** — csontleves (484, idx 0.36) · galuska (514, 0.28) · rántott sajt (533, 0.29) · káposztás tészta (122, 0.35) · túrós csusza (143, 0.33).
8. **Spring-peaking (peak Mar–May)** — gyümölcsleves (696) · burgonyapüré (649) · hasábburgonya (545) · húsleves (428) · sertéspörkölt (180).
9. **Summer-peaking (peak Jun–Aug)** — paradicsomleves (170) · zöldbableves (84) · mákos tészta (40) · töltött paprika (26) · sajtos tészta (25).
10. **Autumn-peaking (peak Sep–Nov)** — zöldségleves (363) · bolognai spagetti (327) · csirkepörkölt (97) · pecsenyeleves (82) · brassói aprópecsenye (69).

## Dish hierarchy

Three tiers based on natural breaks in the frequency distribution. Counts are total occurrences across the corpus (Nov 2022 → Jun 2025).

### Tier 1 — Staples (≥200 occurrences)

17 dishes, ~9,500 occurrences combined. The menu backbone — appear constantly across restaurants and seasons.

| # | Dish | Count |
|---|---|---:|
| 1 | gyümölcsleves | 1,662 |
| 2 | hasábburgonya | 1,148 |
| 3 | roston csirkemell | 752 |
| 4 | burgonyapüré | 716 |
| 5 | rizibizi | 707 |
| 6 | rántott sajt | 552 |
| 7 | galuska | 549 |
| 8 | csontleves | 497 |
| 9 | petrezselymes burgonya | 476 |
| 10 | húsleves | 449 |
| 11 | zöldségleves | 372 |
| 12 | rántott csirkemell | 366 |
| 13 | bolognai spagetti | 336 |
| 14 | fasírozott | 281 |
| 15 | milánói sertésborda | 240 |
| 16 | lebbencsleves | 207 |
| 17 | sertéspörkölt | 203 |

### Tier 2 — Regulars (50–199 occurrences)

42 dishes, ~3,644 occurrences. Familiar dishes that rotate in and out of weekly menus.

**Profile:** main courses (1,919) and soups (1,561) are roughly balanced — soups carry more weight here than in Tier 1. Pork (458) edges out beef (365); chicken drops to fifth (123), and vegetarian dishes (840) — főzelék, rakott, pasta — take a much larger share. The dominant cooking methods shift away from frying: *pörkölt* (457) leads, followed by *sült* (241), *töltött* (178), and *rakott* (151). Characteristic dish types: stews (gulyás-, csirke-, sertéspörkölt), layered casseroles (rakott karfiol, székelykáposzta), thicker soups (tarhonya-, frankfurti, brokkoli krém), and a handful of comfort-food desserts (máglyarakás).

| # | Dish | Count | | # | Dish | Count |
|---|---|---:|---|---|---|---:|
| 1 | gyros tál | 186 | | 11 | frankfurti leves | 115 |
| 2 | paradicsomleves | 175 | | 12 | székelykáposzta | 112 |
| 3 | túrós csusza | 159 | | 13 | zöldborsóleves | 106 |
| 4 | tojásleves | 134 | | 14 | savanyúság | 104 |
| 5 | bacon/sajt/csibe burger | 130 | | 15 | brokkoli krémleves | 98 |
| 6 | gulyásleves | 123 | | 16 | lasagne | 94 |
| 7 | káposztás tészta | 123 | | 17 | máglyarakás | 93 |
| 8 | csirkepörkölt | 123 | | 18 | rakott karfiol | 92 |
| 9 | tarhonyaleves | 120 | | 19 | zöldbableves | 89 |
| 10 | orjaleves | 116 | | 20 | pecsenyeleves | 82 |

### Tier 3 — Occasional (10–49 occurrences)

214 dishes, ~4,204 occurrences. Variety items that keep menus from feeling repetitive.

**Profile:** mains (2,193) and soups (1,674) again split most of the weight, but főzelék (181) finally appears as a real category — almost absent in Tier 1. Protein distribution flattens: vegetarian 456, chicken 387, pork 368, beef 297 — no single protein dominates. Methods diversify further: *pörkölt* (405) and *rakott* (260) lead, joined by *párizsi*-style (92), *főtt* (boiled, 38), and *bécsi* (Wiener-style, 23) — techniques rare in higher tiers. Characteristic dish types: regional and old-style stews (hentes/sertés/borsos tokány, hamis gulyás, korhelyleves), heritage dishes (erdélyi rakott káposzta, krumplis tészta, szilvás gombóc), and lighter brothy soups (lencse-, csirkeaprólék, húsgombóc). This is where the menus pick up character and local variation.

| # | Dish | Count | | # | Dish | Count |
|---|---|---:|---|---|---|---:|
| 1 | pirított tésztaleves | 49 | | 11 | mákos tészta | 42 |
| 2 | rakott burgonya | 48 | | 12 | erdélyi rakott káposzta | 42 |
| 3 | húsgombóc leves | 48 | | 13 | szilvás gombóc | 41 |
| 4 | hentes tokány, tészta | 47 | | 14 | sárgaborsó krémleves | 41 |
| 5 | lencseleves | 47 | | 15 | tejszínes-gombás csirkemell tésztával | 40 |
| 6 | legényfogó leves | 47 | | 16 | csirkeaprólék leves | 39 |
| 7 | rakott kelkáposzta | 46 | | 17 | krumplis tészta | 39 |
| 8 | sertés tokány galuskával | 45 | | 18 | sajttal-sonkával töltött szelet | 39 |
| 9 | korhelyleves | 44 | | 19 | borsos tokány tészta | 38 |
| 10 | hamis gulyásleves | 43 | | 20 | (continues — 214 total) |  |

### Below tier

3,956 long-tail dishes appearing 1–9 times each (~7,659 occurrences). Daily specials, one-offs, and seasonal experiments — not part of the hierarchy.

