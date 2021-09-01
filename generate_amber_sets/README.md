# Generating AmbER Sets

AmbER sets are built by first collecting relevant Wikdata tuples (known as AmbER set tuples), then using them to construct task-specific instances.
Our AmbER set instances are aligned to the [KILT Wikipedia dump](https://github.com/facebookresearch/KILT) which we use as the knowledge source.
This pipeline requires considerable disk space and memory.

**Note**: Running the files in this directory is optional, as we provide the final output of these scripts in `data/`. 

### Download Wikidata and Wikipedia dumps
Download the following three files:
* [Wikidata dump](https://archive.org/download/wikibase-wikidatawiki-20201026/wikidata-20201026-all.json.bz2) (56GB): 
  The Wikidata dump hosted on [archive.org] from October 2020. We don't use the newest Wikidata dump because Wikidata doesn't keep old dumps so reproducibility is an issue. 
  If you'd like to use the newest dump, it is available [here](https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2).
  
* [Wikipedia dump](http://dl.fbaipublicfiles.com/KILT/kilt_knowledgesource.json) (35GB): The Wikipedia dump as provided by the KILT library from Facebook.

* [Wikipedia pageviews dump](https://dumps.wikimedia.org/other/pagecounts-ez/merged/pagecounts-2019-10-views-ge-5-totals.bz2) (500MB): 
  A file containing the number of pageviews each Wikipedia page got in the month of October 2019.
  One barrier to using a more up-to-date pageviews file is that the file format has changed in 2021, meaning that new processing code will be required.
  Also, monthly pageview files are no longer provided in this new format, only daily pageviews. 

For the subsequent commands, we will assume that these files are in the `dumps/` directory in the root of the repository.

### Generating AmbER set tuples
The first step is to collect the Wikidata tuples that become AmbER set tuples. 
For some of the following commands, you will have to provide a flag, `--collection`, which can either be `human` or `nonhuman` corresponding to the AmbER-H and Amber-N collection of AmbER sets respectively.

1. Processing the Wikidata dump and extracting entities and relevant information. This takes ~8 hours to run.

    ```bash
    python generate_amber_sets/extract_wikidata_entities.py \
        --wikidata_dump dumps/wikidata-20201026-all.json.bz2 \
        --popularity_dump dumps/pagecounts-2019-10-views-ge-5-totals.bz2 \
        --output_file dumps/wikidata_entities.json
    ```

2. Generates mapping from polysemous names to sets of corresponding entities with that name. 
These mappings for the basis for our AmbER set tuples.
Also "completes" the data by filling in additional information which is relevant to creating AmbER sets. 
The output of this file is written into `amber_sets/<collection>/tmp/polysemous_names.jsonl`.

    ```bash
    python generate_amber_sets/extract_polysemous_names.py \
        --entity_file dumps/wikidata_entities.json \
        --collection <collection>
    ```

3. Filter relations for the entities corresponding to each polysemous name if multiple entities with the same name have the relation or if the relation is not deemed "distinguishing". 
The output of this file is written into `amber_sets/<collection>/tmp/filtered_relations.jsonl`.

    ```bash
     python generate_amber_sets/filter_relations.py \
        --collection <collection>
    ```
4. Align each AmbER set tuple to its corresponding Wikipedia pages. 
These serve as "gold" documents for each AmbER set tuple when we instantiate them into queries for a task like question answering.
The output of this file is written into `amber_sets/<collection>/amber_set_tuples.jsonl`

    ```bash
    python align_tuple_to_wikipedia.py
        --wikipedia_dump dumps/kilt_knowledgesource.json
        --collection <collection> 
    ```

### Instantiating task specific instances
We use the AmbER set tuples to instantiate task-specific instances. 
To generate these instances, run the following where `task` can be `qa`, `sf`, or `fc` and `collection` can be `human` or `nonhuman`.
See the `amber_sets/` directory for more information on the structure of the output AmbER set files.
```
python generate_<task>_amber_sets.py --collection <collection>
```

_E.g.,_ to generate question answering AmbER sets for the human collection:
```
python generate_qa_amber_sets.py -c human
```
which would create the file `amber_sets/human/qa/amber_sets.jsonl`
