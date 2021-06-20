# Generating AmbER Sets

AmbER sets are built by first collecting relevant Wikdata tuples (known as AmbER tuples), then using them to construct task-specific instances.
Our AmbER set instances are aligned to the [KILT Wikipedia snapshot](https://github.com/facebookresearch/KILT) which we use as the knowledge source.

### Generating AmbER set tuples
The first step is to collect the Wikidata tuples in used as AmbER tuples. 
For the following commands which you will run in order, you will have to provide a flag, `-c`, which can either be `human` or `nonhuman`.

1. `python generate_amber_sets/collect_polysemous_names.py -c <collection>`: Merges files from `process_wikidata_dump/processed_files` into one large file which maps from an alias to all associated entities and their respective relations. 

2. `python generate_amber_sets/filter_uninformative_pids.py -c <collection>`: Filters relations by removing PIDs which aren't in `amber_sets/<collection>/good_pids.json`

3. `python generate_amber_sets/filter_multi_entity_pids -c <collection>`: Filters relations by removing PIDs which are shared by multiple entities which share an alias.

4. `python generate_amber_sets/align_to_wikipedia.py -c <collection>`: Aligns Wikidata entities to Wikipedia page in KILT.

The final AmbER set tuples file is `amber_sets/<collection>/amber_set_tuples.jsonl`.

### Instantiating task specific instances
We use AmbER tuples to instantiate task-specific instances. 
To generate these instances, run the following where `task` can be `qa`, `sf`, or `fc` and `collection` can be `human` or `nonhuman.

```
python generate_<task>_amber_sets.py -c <collection>
```

_e.g.,_ to generate question answering AmbER sets for the human collection:
```
python generate_qa_amber_sets.py -c human
```