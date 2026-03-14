# Full pipeline: raw HTML → lemma dictionary
#
# Step 1 (scraping) runs via GitHub Actions on Sundays.
# Steps 2–5 are local post-processing.

.PHONY: all text menus dishes lemmas categorize synonyms seasonal clean

all: text menus dishes lemmas categorize synonyms seasonal

# 2. Convert HTML to plain text
text:
	bash 0_code/html_to_text.sh

# 3. Extract structured menu data from HTML
menus:
	python3 menu_extractor.py

# 4. Clean and deduplicate dish names
#    Requires dish_count.csv (generated from daily_menus.csv):
#      cut -d, -f3 daily_menus.csv | sort | uniq -c | sort -rn > dish_count.csv
dishes: dish_count.csv
	python3 clean_dishes.py

dish_count.csv: daily_menus.csv
	python3 -c "\
	import pandas as pd; \
	df = pd.read_csv('daily_menus.csv'); \
	counts = df['dish_name'].value_counts().reset_index(); \
	counts.columns = ['dish_name', 'count']; \
	counts.to_csv('dish_count.csv', index=False)"

# 5. Lemmatize with spaCy / HuSpaCy
lemmas:
	python3 0_code/process_cleaned_dishes_spacy.py --csv cleaned_dishes.csv --output dishes_with_lemmas.csv
	python3 0_code/create_lemma_dictionary.py --input dishes_with_lemmas.csv --output-json lemma_dictionary.json

# 6. Categorize dishes by course, protein, cooking method
categorize:
	python3 0_code/categorize_dishes.py --input dishes_with_lemmas.csv --output categorized_dishes.csv --stats category_stats.json

# 7. Resolve synonyms and variants
synonyms:
	python3 0_code/resolve_synonyms.py --input categorized_dishes.csv --synonym-map 0_code/synonym_map.json --output dishes_resolved.csv --groups synonym_groups.csv

# 8. Seasonal/temporal analysis
seasonal:
	python3 0_code/seasonal_analysis.py --menus daily_menus.csv --dishes dishes_resolved.csv --output-monthly dish_monthly_counts.csv --output-summary dish_seasonal_summary.csv --output-json seasonal_dishes.json --min-count 10

clean:
	rm -f dish_count.csv cleaned_dishes.csv dishes_with_lemmas.csv lemma_dictionary.csv lemma_dictionary.json
	rm -f categorized_dishes.csv category_stats.json dishes_resolved.csv synonym_groups.csv
	rm -f dish_monthly_counts.csv dish_seasonal_summary.csv seasonal_dishes.json
