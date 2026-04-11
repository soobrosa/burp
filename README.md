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
