# Full pipeline: raw HTML → lemma dictionary
#
# Step 1 (scraping) runs via GitHub Actions on Sundays.
# Steps 2–5 are local post-processing.

.PHONY: all text menus dishes lemmas clean

all: text menus dishes lemmas

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

clean:
	rm -f dish_count.csv cleaned_dishes.csv dishes_with_lemmas.csv lemma_dictionary.csv lemma_dictionary.json
