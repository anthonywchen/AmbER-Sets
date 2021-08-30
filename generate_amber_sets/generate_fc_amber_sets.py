#!/usr/bin/python3
import argparse
import hashlib
import json
import os
import random
import typing
from collections import defaultdict

import jsonlines
from tqdm import tqdm

random.seed(0)


def fill_template(template: str, entity: str, object: str) -> typing.Tuple[str, str]:
    """Fill in an FC template with an entity name and the value.

    Arguments:
        template: ``str`` A fact checking template.
        entity: ``str`` The name of the AmbER set to fill into the template.
        object: ``str`` The value of the AmbER set tuple.
    Returns:
        query: ``str`` The template with the name and object slotted in.
        query_hashlib: ``str`` A MD5 hash of the query.
    """
    query = template.replace("$entity", entity).replace("$object", object)
    assert entity in query and object in query
    query_hashlib = hashlib.md5(query.encode("utf-8")).hexdigest()
    return query, query_hashlib


def generate_true_instance(
    template: str,
    entity_name: str,
    pid_dict: typing.Dict[str, dict]
) -> typing.Tuple[str, str]:
    """Creates a true fact checking query.

    Creates a true fact checking query by taking the entity name of an AmbER set and
    the value of an AmbER set tuple and filling in an fact checking template. We
    check that the value we use to generate the query was found in the gold document.

    Arguments:
        template: ``str`` A fact checking template.
        entity_name: ``str`` The name of the AmbER set to fill into the template.
        pid_dict: ``dict`` A relation dictionary of a AmbER set tuple.
    Returns:
        query: ``str`` A true fact checking query.
        query_hashlib: ``str`` A MD5 hash of the query.
    """
    for value in pid_dict['values']:
        if value['found_in_passage']:
            answer = value["aliases"][0]
            query, query_hashlib = fill_template(template, entity_name, answer)
            break
    return query, query_hashlib


def generate_false_instance(
    template: str,
    entity_name: str,
    pid_dict: typing.Dict[str, dict],
    other_answers: typing.List[str]
) -> typing.Tuple[str, str]:
    """Creates a false fact checking query.

    Creates a false fact checking query by taking the entity name of an AmbER set and
    a false value. For example, for the entity Michael Jordan and the relation sport,
    a false value might be soccer. We then use these to fill in a fact checking
    template.

    Arguments:
        template: ``str`` A fact checking template.
        entity_name: ``str`` The name of the AmbER set to fill into the template.
        pid_dict: ``dict`` A relation dictionary of a AmbER set tuple.
        other_answers: ``list`` A list of values that have appeared for the relation.
    Returns:
        query: ``str`` A false fact checking query.
        query_hashlib: ``str`` A MD5 hash of the query.
    """
    answers = [value['aliases'][0] for value in pid_dict["values"]]
    for wrong_answer in other_answers:
        if wrong_answer not in answers:
            query, query_hashlib = fill_template(template, entity_name, wrong_answer)
            return query, query_hashlib


def generate_fc_amber_sets(collection: str) -> None:
    input_data_file = os.path.join("data", collection, "amber_set_tuples.jsonl")
    templates_file = os.path.join("data", collection, "fc_templates.json")
    output_data_file = os.path.join("data", collection, "fc/amber_sets.jsonl")

    amber_set_tuples = list(jsonlines.open(input_data_file))
    templates = json.load(open(templates_file))

    # Get the most popular values for each PID
    popular_pid_values = defaultdict(lambda: defaultdict(int))
    for d in tqdm(amber_set_tuples):
        for qid in d['qids']:
            for pid in d['qids'][qid]['pids']:
                for value in d['qids'][qid]['pids'][pid]['values']:
                    answer = value["aliases"][0]
                    popular_pid_values[pid][answer] += 1

    # For each PID, keep all values sorted by popularity
    for pid in popular_pid_values:
        popular_pid_values[pid] = sorted(
            popular_pid_values[pid], key=popular_pid_values[pid].get, reverse=True
        )

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

            pid_dict = qid_dict["pids"]
            # Update `pid_dict` with a query generated from templates
            for pid in list(pid_dict.keys()):
                # Grab a random template.
                # Set seed using QID & PID so we always grab the same template
                random.seed(int(qid[1:] + pid[1:]))
                template = random.choice(templates[pid])

                # Generate queries
                true_query, true_query_id = generate_true_instance(
                    template, name, pid_dict[pid]
                )

                false_query, false_query_id = generate_false_instance(
                    template, name, pid_dict[pid], popular_pid_values[pid]
                )

                # Get aliases
                values = []
                additional_values = []
                for d in pid_dict[pid]["values"]:
                    values += d["aliases"]
                    additional_values += d["additional_aliases"]

                # Append true fact
                amber_set["qids"][qid]["queries"].append(
                    {
                        "id": pid_dict[pid]["amber_id"] + "=" + true_query_id,
                        "input": true_query,
                        "output": {
                                "answer": "SUPPORTS",
                                "provenance": pid_dict[pid]["provenance"],
                                "meta": {
                                    "values": values,
                                    "additional_values": additional_values,
                                },
                        },
                        "meta": {"pid": pid},
                    }
                )

                # Append false fact
                amber_set["qids"][qid]["queries"].append(
                    {
                        "id": pid_dict[pid]["amber_id"] + "=" + false_query_id,
                        "input": false_query,
                        "output": {
                            "answer": "REFUTES",
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

    generate_fc_amber_sets(args.collection)


if __name__ == "__main__":
    main()
