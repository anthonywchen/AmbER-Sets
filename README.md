# AmbER Sets

AmbER sets are stored in a JSONLines format under the following path: `amber_sets/<collection>/<task>/amber_sets.jsonl`

Here is an example AmbER set for "Abe Lincoln" from the human collection (AmbER-H) for the question answering task: `amber_sets/human/qa/amber_sets.jsonl`

<details>
<summary>Click to expand</summary>

```
{
    "name": "Abe Lincoln",
    "qids": {
        "Q91": {
            "is_head": true,
            "pop": 5.1942478558575464,
            "wikipedia": [
                {"kilt_idx": 49, "wikipedia_id": "307", "title": "Abraham Lincoln"},
                {"kilt_idx": 3767946, "wikipedia_id": "42390831", "title": "Abraham Lincoln's Life"}
            ],
            "queries": [
                {
                    "id": "6981ec17f0438a7cc94fff740cc9bb23=f12393b7ba0631871ea7126dd5127772",
                    "input": "Which battle did Abe Lincoln fight in?",
                    "output": [
                        {
                            "answer": ["American Civil War", ...],
                            "provenance": [
                                {"kilt_idx": 49, "wikipedia_id": "307", "title": "Abraham Lincoln"}
                            ],
                            "meta": {...}
                        }
                    ],
                    "meta": {...}
                }
            ]
        },
        "Q4666410": {
            "is_head": false,
            "pop": 1.7781512503836436,
            "wikipedia": [
                {"kilt_idx": 477649, "wikipedia_id": "17039796", "title": "Abe Lincoln (musician)" }
            ],
            "queries": [
                {
                    "id": "edf1ff070a3cbd5fdee738262db8e740=44a67ee4dd88179d1147102e9753a5fa",
                    "input": "What musical instrument does Abe Lincoln play?",
                    "output": [
                        {
                            "answer": ["slide trombone", "..."],
                            "provenance": [
                                {"kilt_idx": 477649, "wikipedia_id": "17039796", "title": "Abe Lincoln (musician)"}
                            ],
                            "meta": {...}
                        }
                    ],
                    "meta": {...}
                }
            ]
        }
    }
}
```

</details>

## Generating AmbER Sets
Generating AmbER sets happens in three steps:

1. Downloading and processing a large Wikidata dump
2. Extracting AmbER set tuples from this dump
3. Generating task-specific instances (e.g. QA, fact checking) from the AmbER set tuples

##### Processing Wikidata Dump

```
cd process_wikipedia_dump
./process_wikidata_dump.sh
python build_qid_popularity_dictionary.py
python map_aliases_to_qids.py
python map_pids_to_labels.py
python map_qids_to_aliases.py
python map_qids_to_pids.py
```

##### Extracting AmbER set tuples
```
python generate_amber_sets/collect_polysemous_names.py -c <collection>
python filter_uninformative_pids.py -c <collection>
python filter_multi_entity_pids -c <collection>
python align_amber_tuples_to_wikipedia.py -c <collection>
```

##### Instantiating task specific instances

```
python generate_<task>_amber_sets.py -c <collection>
```

e.g. to generate question answering AmbER sets for the human collection:
```
python generate_qa_amber_sets.py -c human
```

## Evaluating AmbER Set Predictions


## License
The AmbER data is licensed under the [Creative Commons Zero v1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/).
