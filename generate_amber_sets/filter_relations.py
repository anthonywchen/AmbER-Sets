""" Filters relations.

1. Remove PIDs that aren't in a list of "good PIDs" or that are shared across entities.
2. Remove aliases that don't have at least 2 entities with relations or head entity
doesn't have relations.
"""
import argparse
import collections
import itertools
import json
import os

import jsonlines
import tqdm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    input_data_file = os.path.join("amber_sets", args.collection, "tmp/polysemous_names.jsonl")
    good_pids_file = os.path.join("amber_sets", args.collection, "good_pids.json")
    output_data_file = os.path.join("amber_sets", args.collection, "tmp/filtered_relations.jsonl")
    polysemous_names = list(jsonlines.open(input_data_file))
    good_pids = json.load(open(good_pids_file))

    # Iterate through all polysemous names and their entities
    for d in tqdm.tqdm(polysemous_names, desc="Filtering relations"):
        # Keep a count for how many times each PID occurs for this name
        pid_counts = collections.defaultdict(int)
        for qid in d['qids']:
            for pid in d['qids'][qid]['pids']:
                pid_counts[pid] += 1

        for qid in d['qids']:
            entity_types = d['qids'][qid]['entity_types']

            # Stores the pre-specified relations that are informative for an entity type
            informative_pids = list(itertools.chain(*[good_pids[et]['inter'] + good_pids[et]['intra']
                                                      for et in entity_types if et in good_pids]))

            # Remove relations that aren't informative or are shared across entities
            for pid in list(d['qids'][qid]['pids'].keys()):
                if pid not in informative_pids or pid_counts[pid] > 1:
                    del d['qids'][qid]['pids'][pid]

    # Filter names where multiple entities or head entity doesn't have relations
    filtered_names = []
    for d in polysemous_names:
        entities_with_relations = 0
        head_has_relations = False
        for qid in d['qids']:
            if len(d['qids'][qid]['pids']) > 0:
                entities_with_relations += 1
                if d['qids'][qid]['is_head']:
                    head_has_relations = True

        if entities_with_relations >= 2 and head_has_relations:
            filtered_names.append(d)

    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in filtered_names:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
