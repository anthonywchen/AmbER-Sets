#!/usr/bin/python3
import argparse
import hashlib
import json
import os
import random
import typing

import jsonlines
from tqdm import tqdm


def fill_in_template(template: str, entity_name: str) -> typing.Tuple[str, str]:
    """Fill in an QA template with an entity name.

    Arguments:
        template: ``str`` A question answering template.
        entity_name: ``str`` The name of the AmbER set to fill into the template.
    Returns:
        query: ``str`` The template with the name slotted in.
        query_hashlib: ``str`` A MD5 hash of the query.
    """
    query = template.replace("$entity", entity_name)
    assert entity_name in query
    query_hashlib = hashlib.md5(query.encode("utf-8")).hexdigest()
    return query, query_hashlib


def generate_qa_amber_sets(collection: str) -> None:
    input_data_file = os.path.join("data", collection, "amber_set_tuples.jsonl")
    templates_file = os.path.join("data", collection, "qa_templates.json")
    output_data_file = os.path.join("data", collection, "qa/amber_sets.jsonl")

    amber_set_tuples = list(jsonlines.open(input_data_file))
    templates = json.load(open(templates_file))

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

            # Update `pid_dict` with a query generated from templates
            pid_dict = qid_dict["pids"]
            for pid in pid_dict:
                value_types = []
                for v in pid_dict[pid]["values"]:
                    value_types += v.get("entity_type", [])

                # Grab all the templates that we could fill in
                # If we have specific templates matching value types, use those
                cur_templates = []
                for type in value_types:
                    cur_templates += templates[pid].get(type, [])
                # Otherwise, use the general templates for the PID
                if len(cur_templates) == 0:
                    cur_templates = templates[pid]["all"]

                # Grab a random template
                # Set seed using QID & PID so we always grab the same template
                random.seed(int(qid[1:] + pid[1:]))
                template = random.choice(cur_templates)
                query, query_hashlib = fill_in_template(template, name)
                input_id = pid_dict[pid]["amber_id"] + "=" + query_hashlib

                values, additional_values = [], []
                for d in pid_dict[pid]["values"]:
                    values += d["aliases"]
                    additional_values += d["additional_aliases"]

                amber_set["qids"][qid]["queries"].append(
                    {
                        "id": input_id,
                        "input": query,
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

    generate_qa_amber_sets(args.collection)


if __name__ == "__main__":
    main()
