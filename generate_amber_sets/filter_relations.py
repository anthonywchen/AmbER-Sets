#!/usr/bin/python3
import argparse
import collections
import itertools
import json
import os

import jsonlines
import tqdm


def filter_relations(collection: str) -> None:
    """Filters relations from entities group by polysemous names.

    For each entity in a set corresponding to a polysemous name, we filter relations
    if the relation ID (PID) is NOT in a list of distinguishing PIDs for the
    entities' entity type or if the relation is share by multiple entiites in the set.
    The list of polysemous names with entities with filtered relations is written out
    into a JSONLines file.

    Arguments:
        collection: ``str``The collection (human/nonhuman) of AmbER sets.
    """
    input_data_file = os.path.join("data", collection, "tmp/polysemous_names.jsonl")
    entity_types_to_distinguishing_properties_file = \
        os.path.join("data", collection, "entity_types_to_distinguishing_properties.json")
    output_data_file = os.path.join("data", collection, "tmp/filtered_relations.jsonl")
    polysemous_names = list(jsonlines.open(input_data_file))
    entity_types_to_distinguishing_properties = json.load(open(
        entity_types_to_distinguishing_properties_file
    ))

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
            distinguishing_properties = list(itertools.chain(*[
                entity_types_to_distinguishing_properties[et]
                for et in entity_types
                if et in entity_types_to_distinguishing_properties
            ]))

            # Remove relations that aren't informative or are shared across entities or
            # don't have any values
            for pid in list(d['qids'][qid]['pids'].keys()):
                if pid not in distinguishing_properties or pid_counts[pid] > 1 or \
                        len(d['qids'][qid]['pids'][pid]['values']) == 0:
                    del d['qids'][qid]['pids'][pid]

    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in polysemous_names:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--collection",
        help="Collection to collect polysemous names for, AmbER-H (human) or "
             "AmbER-N (nonhuman)",
        choices=["human", "nonhuman"]
    )
    args = parser.parse_args()

    filter_relations(args.collection)


if __name__ == "__main__":
    main()
