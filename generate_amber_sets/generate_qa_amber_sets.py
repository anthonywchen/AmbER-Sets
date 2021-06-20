""" Generates question answering data from AmbER tuples with query templates


"""
import argparse
import hashlib
import json
import random
from os.path import join

import jsonlines
from tqdm import tqdm

random.seed(0)


def fill_in_template(template, entity_name):
    """Fill in template with an entity name.
    Also returns the hashlib of the query as a query ID.
    """
    query = template.replace("$entity", entity_name)
    assert entity_name in query
    query_hashlib = hashlib.md5(query.encode("utf-8")).hexdigest()
    return query, query_hashlib


def generate_queries(amber_set_tuples, templates):
    amber_sets = []

    for d in tqdm(amber_set_tuples):
        name = d["name"]
        amber_set = {"name": name, "qids": {}}

        for qid, qid_dict in d["qids"].items():
            amber_set["qids"][qid] = {
                "is_head": qid_dict["is_head"],
                "pop": qid_dict["pop"],
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
                        "output": [
                            {
                                "answer": values + additional_values,
                                "provenance": pid_dict[pid]["provenance"],
                                "meta": {
                                    "values": values,
                                    "additional_values": additional_values,
                                },
                            }
                        ],
                        "meta": {"pid": pid},
                    }
                )
        amber_sets.append(amber_set)

    return amber_sets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    input_data_file = join("amber_sets", args.collection, "amber_set_tuples.jsonl")
    templates_file = join("amber_sets", args.collection, "qa_templates.json")
    output_data_file = join("amber_sets", args.collection, "qa/amber_sets.jsonl")

    amber_set_tuples = [line for line in jsonlines.open(input_data_file)]
    templates = json.load(open(templates_file))

    amber_sets = generate_queries(amber_set_tuples, templates)

    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in amber_sets:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
