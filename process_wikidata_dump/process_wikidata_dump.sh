#!/bin/bash

wget https://archive.org/download/wikibase-wikidatawiki-20201026/wikidata-20201026-all.json.bz2
# Uncomment below and comment above for faster downloading
#axel -n 10 -a https://archive.org/download/wikibase-wikidatawiki-20201026/wikidata-20201026-all.json.bz2

# Run background processes to extract out information from Wikidata dump without decompressing the bz2 file.
process_wikidata_command="bzcat wikidata-20201026-all.json.bz2 | grep '^{' | sed 's/,$//'"
eval $process_wikidata_command | parallel --pipe "jq '. as \$g | .sitelinks | .[] | [.site, .title, \$g.id] | @tsv' -cr" | tr ' ' '_' | awk '$1 == "enwiki"' > wiki_to_qid.tsv &
eval $process_wikidata_command | parallel --pipe "jq '. as \$g | .labels[] | [.language, .value, \$g.id] | @tsv' -cr" | awk '$1 == "en"' > labels.tsv &
eval $process_wikidata_command | parallel --pipe "jq '. as \$g | .aliases[][] | [.language, .value, \$g.id] | @tsv' -cr" | awk '$1 == "en"' > aliases.tsv &
eval $process_wikidata_command | parallel --pipe "jq '. as \$g | .claims[][] | [\$g.id, .mainsnak.property, .mainsnak.datavalue|tostring] | @tsv' -cr" > pids.tsv &

wait # Wait for background processes to finish before continuing
cat aliases.tsv labels.tsv > cands.tsv

# Download page counts and process
wget https://dumps.wikimedia.org/other/pagecounts-ez/merged/pagecounts-2019-10-views-ge-5-totals.bz2
bzcat pagecounts-2019-10-views-ge-5-totals.bz2 | awk '$1 ~ /\.z/' | sed 's/.z/wiki/' | tr ' ' '\t' > pagecounts.tsv
LANG=en_EN join -t $'\t' <(cat wiki_to_qid.tsv | sed 's/\t/#/' | LANG=en_EN sort -t$'\t' -k1) <(cat pagecounts.tsv | sed 's/\t/#/' | LANG=en_EN sort -t$'\t' -k1) > qids_with_pagecounts.tsv