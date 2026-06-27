# burp

A corpus of Hungarian business-lunch menus from Kiskunfélegyháza, with a pipeline that turns scraped HTML into cleaned, lemmatized, categorized, and seasonally-analyzed dish data.

**[→ Explore the interactive visualization](https://soobrosa.info/burp/)** — a monochrome, searchable dashboard of the corpus (`index.html`).

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

Corpus: ~51,200 menu rows, ~5,050 unique dishes after resolution, Nov 2022 → Apr 2026.

1. **Courses** (unique dishes) — főétel 5,994 (72%) · leves 1,688 (20%) · főzelék 388 (5%) · desszert 188 (2%).
2. **Proteins** (unique dishes) — csirke 2,536 · sertés 2,218 · vegetáriánus 833 · marha 463 · hal 306.
3. **Cooking methods** (unique dishes) — rántott 1,400 · sült 1,109 · párolt 503 · töltött 491 · pörkölt 357.
4. **Top dishes overall** (resolved occurrences) — gyümölcsleves 2,268 · hasábburgonya 1,232 · roston csirkemell 995 · rizibizi 938 · burgonyapüré 886.
5. **Top soups** — gyümölcsleves 2,268 · csontleves 642 · húsleves 593 · zöldségleves 467 · lebbencsleves 269.
6. **Top főzelék** — gyümölcsfőzelék párizsi csirkemellel 24 · meggyfőzelék párizsi csirkével 21 · burgonyafőzelék vagdalttal 20 · sárgaborsó főzelék borsos tokánnyal 19 · meggyfőzelék párizsi csirkemellel 18.
7. **Winter-peaking dishes (peak Dec–Feb)** — rántott sertésszelet (75, idx 0.76) · töltött káposzta (65, 0.61) · paprikás krumpli (66, 0.53) · tarhonyás hús (64, 0.49) · paradicsomos húsgombóc (88, 0.43).
8. **Spring-peaking (peak Mar–May)** — sertés tokány galuskával (62, 0.58) · carbonara spagetti (60, 0.55) · magyaros burgonyaleves (63, 0.46) · rakott kelkáposzta (53, 0.41) · szilvás gombóc (51, 0.40).
9. **Summer-peaking (peak Jun–Aug)** — fahéjas szilvaleves (60, 0.42) · mákos tészta (51, 0.35) · zöldborsóleves (131, 0.25) · hentes tokány (56, 0.24) · lasagne (114, 0.21).
10. **Autumn-peaking (peak Sep–Nov)** — krumplis tészta (54, 0.72) · hamis gulyásleves (51, 0.64) · korhelyleves (50, 0.58) · rakott zöldbab (69, 0.51) · brassói aprópecsenye (80, 0.40).

> Seasonal lists rank by seasonality index (peak-month concentration) among dishes with ≥50 occurrences, so they surface genuinely seasonal items rather than year-round staples. Top-soup and top-főzelék lists skip a few entries the categorizer mislabels by course (e.g. *galuska* tagged as a soup) — see [Data notes](#data-notes).

## Dish hierarchy

Three tiers based on natural breaks in the frequency distribution. Counts are total occurrences across the corpus (Nov 2022 → Apr 2026).

### Tier 1 — Staples (≥200 occurrences)

20 dishes, ~12,750 occurrences combined. The menu backbone — appear constantly across restaurants and seasons. Mains (7,695) lead soups (4,452); chicken (5,071) edges pork (3,629) and vegetarian (3,189); frying dominates (*rántott* 5,900).

| # | Dish | Count |
|---|---|---:|
| 1 | gyümölcsleves | 2,268 |
| 2 | hasábburgonya | 1,232 |
| 3 | roston csirkemell | 995 |
| 4 | rizibizi | 938 |
| 5 | burgonyapüré | 886 |
| 6 | galuska | 674 |
| 7 | csontleves | 642 |
| 8 | rántott csirkemell | 632 |
| 9 | rántott sajt | 630 |
| 10 | húsleves | 593 |
| 11 | petrezselymes burgonya | 583 |
| 12 | zöldségleves | 467 |
| 13 | bolognai spagetti | 386 |
| 14 | fasírozott | 352 |
| 15 | milánói sertésborda | 290 |
| 16 | lebbencsleves | 269 |
| 17 | sertéspörkölt | 252 |
| 18 | gyros tál | 238 |
| 19 | paradicsomleves | 213 |
| 20 | túrós csusza | 211 |

### Tier 2 — Regulars (50–199 occurrences)

53 dishes, ~4,663 occurrences. Familiar dishes that rotate in and out of weekly menus.

**Profile:** main courses (2,351) and soups (2,044) are roughly balanced — soups carry more weight here than in Tier 1. Vegetarian dishes (826) — főzelék, rakott, pasta — take the largest protein share, ahead of beef (494), pork (393) and chicken (213). The dominant cooking methods shift away from frying: *rakott* (366) leads, followed by *pörkölt* (300), *sült* (226), and *töltött* (129). Characteristic dish types: stews (gulyás-, csirke-, sertéspörkölt), layered casseroles (rakott karfiol, székelykáposzta), thicker soups (tarhonya-, frankfurti, brokkoli krém), and a handful of comfort-food desserts (máglyarakás).

| # | Dish | Count | | # | Dish | Count |
|---|---|---:|---|---|---|---:|
| 1 | tojásleves | 172 | | 11 | zöldborsóleves | 136 |
| 2 | bacon, sajt vagy csibe burger | 169 | | 12 | brokkoli krémleves | 125 |
| 3 | csirkepörkölt | 162 | | 13 | máglyarakás | 123 |
| 4 | orjaleves | 155 | | 14 | lasagne | 121 |
| 5 | tarhonyaleves | 154 | | 15 | rakott karfiol | 120 |
| 6 | káposztás tészta | 153 | | 16 | zöldbableves | 108 |
| 7 | gulyásleves | 150 | | 17 | pecsenyeleves | 92 |
| 8 | székelykáposzta | 140 | | 18 | paradicsomos húsgombóc | 92 |
| 9 | frankfurti leves | 140 | | 19 | brassói aprópecsenye | 89 |
| 10 | savanyúság | 138 | | 20 | májgombócleves | 79 |

### Tier 3 — Occasional (10–49 occurrences)

248 dishes, ~4,798 occurrences. Variety items that keep menus from feeling repetitive.

**Profile:** mains (2,563) and soups (1,749) again split most of the weight, but főzelék (287) appears as a real category — almost absent in Tier 1. Protein distribution flattens: vegetarian 537, chicken 509, pork 452, beef 313 — no single protein dominates. Methods diversify further: *pörkölt* (510) leads, joined by *rakott* (148) and *párizsi*-style (148) — techniques rare in higher tiers. Characteristic dish types: regional and old-style stews (hentes/sertés/borsos/csikós tokány, hamis gulyás, korhelyleves), heritage dishes (erdélyi rakott káposzta, krumplis tészta, szilvás gombóc), and lighter brothy soups (lencse-, csirkeaprólék, húsgombóc). This is where the menus pick up character and local variation.

| # | Dish | Count | | # | Dish | Count |
|---|---|---:|---|---|---|---:|
| 1 | sárgaborsó krémleves | 49 | | 11 | zellerkrémleves | 41 |
| 2 | sonkás kocka | 46 | | 12 | tejszínes-gombás csirkemell tésztával | 41 |
| 3 | borsos tokány tésztával | 46 | | 13 | burgonyaleves | 41 |
| 4 | brassói | 45 | | 14 | grízgombóc leves | 41 |
| 5 | zúzapörkölt tésztával | 44 | | 15 | csülökpörkölt tarhonyával | 40 |
| 6 | sárgaborsóleves | 44 | | 16 | lencsegulyás | 40 |
| 7 | sertéskaraj vadasan, tészta | 43 | | 17 | túrós palacsinta | 39 |
| 8 | rizsfelfújt | 42 | | 18 | gombaleves | 39 |
| 9 | tárkonyos raguleves | 42 | | 19 | nyírségi gombócleves | 38 |
| 10 | csikós tokány, tészta | 42 | | 20 | (continues — 248 total) |  |

### Below tier

4,726 long-tail dishes appearing 1–9 times each (~9,277 occurrences). Daily specials, one-offs, and seasonal experiments — not part of the hierarchy.

### Data notes

- **Coverage.** The scraper (GitHub Actions, weekly) collects HTML into `1_html/`; the analysis pipeline (steps 2–8) is run by hand. This refresh reprocessed the full corpus through **2026-04-05** — the previous README froze at June 2025 because the pipeline hadn't been re-run, even though scraping continued.
- **Menu boilerplate.** The newer site layout interleaves price lines, section headers (`Levesek:`, `Főételek:`), greetings, and season's-greetings into the menu blocks. `menu_extractor.py` captured these as dish rows, and previously they survived into the results (~40 raw strings, ~1,600 occurrences — `Kínálatunkat itt találja` alone appeared 606×). `clean_dishes.py`'s `is_noise_line()` now filters them (price tokens, trailing-colon labels, greeting/announcement and section-header phrases), so they no longer reach the dish data.
- **Casing.** Some canonical names retain their original capitalization where synonym/lemma resolution didn't map them to a lowercase form (curated synonyms in `synonym_map.json` are lowercase; auto-grouped and unmatched dishes keep their cleaned, sentence-cased form). Display names above are lowercased for consistency; this introduces no count collisions (verified) and is cosmetic — it does not affect any count.

