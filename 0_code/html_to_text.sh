#!/usr/bin/env bash

rm 2_txt/dump.txt

for file in 1_html/*.html; do
    cat ${file} | python3 0_code/html_to_text.py >> 2_txt/dump.txt
done

cat 2_txt/dump.txt | sort | uniq -c | sort > 2_txt/group_by.txt