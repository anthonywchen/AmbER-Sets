#!/usr/bin/python3
import argparse
import hashlib
import json
import os
import typing

import jsonlines
from tqdm import tqdm


def create_sf_instance(entity_name: str, property_label: str) -> typing.Tuple[str, str]:
    """Creates a slot filling instance by combining a name and a relation.

    Arguments:
        entity_name: ``str`` The name of the AmbER set to fill into the template.
        property_label: ``str`` The property name of the AmbER set tuple.
    Returns:
        query: ``str`` The template with the name slotted in.
        query_hashlib: ``str`` A MD5 hash of the query.
    """
    sf_input = entity_name + " [SEP] " + property_label
    sf_hashlib = hashlib.md5(sf_input.encode("utf-8")).hexdigest()
    return sf_input, sf_hashlib


def generate_sf_amber_sets(collection: str) -> None:
    """Generates slot filling instances from all AmbER set tuples.

    Arguments:
        collection: ``str``The collection (human/nonhuman) of AmbER sets.
    """
    input_data_file = os.path.join("data", collection, "amber_set_tuples.jsonl")
    output_data_file = os.path.join("data", collection, "sf/amber_sets.jsonl")
    amber_set_tuples = list(jsonlines.open(input_data_file))

    amber_sets = []

    for d in tqdm(amber_set_tuples):
        name = d["name"]
        amber_set = {"name": name, "qids": {}}

        for qid, qid_dict in d["qids"].items():
            amber_set["qids"][qid] = {
                "is_head": qid_dict["is_head"],
                "popularity": qid_dict["popularity"],
                "wikipedia": qid_dict["wikipedia"],
                "queries": [],
            }

            # Update `pid_dict` with slot filling instances
            pid_dict = qid_dict["pids"]
            for pid in pid_dict:
                pid_name = pid_dict[pid]["property"]
                sf_input, sf_hashlib = create_sf_instance(name, pid_name)
                pid_dict[pid]["input"] = sf_input
                pid_dict[pid]["input_id"] = sf_hashlib

                values, additional_values = [], []
                for d in pid_dict[pid]["values"]:
                    values += d["aliases"]
                    additional_values += d["additional_aliases"]

                amber_set["qids"][qid]["queries"].append(
                    {
                        "id": pid_dict[pid]["amber_id"] + "=" + sf_hashlib,
                        "input": sf_input,
                        "output": {
                            "answer": values + additional_values,
                            "provenance": pid_dict[pid]["provenance"],
                            "meta": {
                                "values": values,
                                "additional_values": additional_values,
                            },
                        },
                        "meta": {"pid": pid},
                    }
                )
        amber_sets.append(amber_set)

    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in amber_sets:
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

    generate_sf_amber_sets(args.collection)


if __name__ == "__main__":
    main()
