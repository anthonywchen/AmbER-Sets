# AmbER Sets

AmbER sets are stored in a JSONLines format under the following path: `amber_sets/<collection>/<task>/amber_sets.jsonl`

## Generating AmbER Sets
Here are details if you are interested in reproducing the AmbER sets from scratch.
Generating AmbER sets happens in three steps:

1. Downloading and processing a large Wikidata dump
2. Extracting AmbER set tuples from this dump
3. Generating task-specific instances (e.g. QA, fact checking) from the AmbER set tuples

Follow the instructions in `process_wikidata_dump/` followed by `generate_amber_sets/`.


## Evaluating AmbER Set Predictions

## License
The AmbER data is licensed under the [Creative Commons Zero v1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/).
