import argparse
from collections import defaultdict
from os.path import dirname, join

import inflect
import ujson as json
import tqdm

engine = inflect.engine()
WIKIDATA_DIR = "process_wikidata_dump/processed_files"


def extract_aliases(entities, qid):
    aliases = []
    if qid in entities:
        aliases = entities[qid]['aliases']
        aliases.append(entities[qid]['label'])
    return aliases


def extract
def add_entity_types_to_values(entities):
    """Add entity types for Wikidata answers

    For the PIDs in which the value is a QID, add the entity
    type of that QID. This makes it when creating queries from templates
    since some templates require knowing what the type of the QID value is.
    """
    print("Adding entity types to values")
    for qid in tqdm.tqdm(entities):
        for pid in entities[qid].get("relations", []):
            if pid == "P31":
                continue

            for answer_dict in entities[qid]["relations"][pid]:
                if answer_dict["type"] == "wikibase-item":
                    answer_dict["entity_types"] = entities.get(answer_dict["qid"], {}).\
                        get("entity_types", [])


def add_pid_value_aliases(entities):
    """Add entity aliases for Wikidata answers

    For the PIDs in which the value is a QID, add the entity
    aliases of that QID. This makes it when using this data for extractive
    QA, so that we can compute a score over the set of aliases.
    """
    print("Adding aliases to values")

    for qid in tqdm.tqdm(entities):
        for pid in entities[qid].get("relations", []):
            for answer_dict in entities[qid]["relations"][pid]:
                if answer_dict["type"] == "wikibase-item":
                    answer_qid = answer_dict["qid"]
                    answer_dict["aliases"] = extract_aliases(entities, answer_qid)
                    answer_dict["additional_aliases"] = set()

                    # Add in aliases for the people who participated in the answer
                    # e.g. for the alias guitar, we also add in guitarist
                    if answer_qid in entities:
                        for instance in entities[answer_qid]["relations"].get("P3095", []):
                            participant_qid = instance["qid"]
                            answer_dict["additional_aliases"].update(
                                extract_aliases(entities, participant_qid)
                            )

                        for instance in entities[answer_qid]["relations"].get("P1535", []):
                            participant_qid = instance["qid"]
                            answer_dict["additional_aliases"].update(
                                extract_aliases(entities, participant_qid)
                            )

                    # answer_dict["aliases"] = answer_dict["aliases"]
                    answer_dict["additional_aliases"] = sorted(
                        answer_dict["additional_aliases"]
                    )
                elif answer_dict["type"] == "quantity":
                    amount = answer_dict["amount"]
                    assert amount[0] in ["+", "-"]
                    amount = amount[1:]
                    answer_dict["aliases"] = [amount]
                    try:
                        # TODO: Check that this doesn't always evaluate to 0
                        answer_dict["additional_aliases"] = [engine.number_to_words(amount)]
                    except:
                        answer_dict["additional_aliases"] = []


def get_most_popular_pid_values(entities, good_pids_file):
    good_pids_data = json.load(open(good_pids_file))
    good_pids = set([f for d in good_pids_data.values() for e in d.values() for f in e])

    popular_pid_values = defaultdict(lambda: defaultdict(int))

    for qid in tqdm.tqdm(entities):
        for pid in entities[qid].get("relations", []):
            if pid in good_pids:
                for answer_dict in entities[qid]["relations"][pid]:
                    if len(answer_dict["aliases"]) > 0:
                        answer = answer_dict["aliases"][-1]
                        popular_pid_values[pid][answer] += 1

    # For each PID, sort by count, then take the top 20
    for pid in popular_pid_values:
        popular_pid_values[pid] = sorted(
            popular_pid_values[pid], key=popular_pid_values[pid].get, reverse=True
        )[:20]

    output_file = join(dirname(good_pids_file), "popular_pid_values.json")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(popular_pid_values, sort_keys=True, indent=4, ensure_ascii=False)
        )


def add_pid_names(entities):
    print("Adding PID names")
    for qid in tqdm.tqdm(entities):
        if qid[0] == 'P':
            continue

        for pid in entities[qid]['relations']:
            entities[qid]["relations"][pid] = {
                "property": entities[pid]["label"],
                "values": entities[qid]["relations"][pid],
            }

        # TODO: delete this part here once fixed in extract_wikidata_entities.py
        entities[qid]['pids'] = entities[qid]['relations']
        del entities[qid]['relations']


def remove_qids(entities, good_qid_types):
    """Remove QID if WikiData type doesn't match list of accepted types"""
    print("Removing QIDs")
    for qid in tqdm.tqdm(list(entities.keys())):
        entity_types = set(entities[qid].get('entity_types', []))
        if len(entity_types.intersection(good_qid_types)) == 0:
            del entities[qid]


def load_entities(entity_file, good_pids_file):
    print("Loading entities...")
    entities = json.load(open(entity_file, encoding="utf-8"))
    good_pids = json.load(open(good_pids_file, encoding="utf-8"))

    add_entity_types_to_values(entities)
    add_pid_value_aliases(entities)
    get_most_popular_pid_values(entities, good_pids_file)
    add_pid_names(entities)
    remove_qids(entities, good_pids)
    return entities


def collect_polysemous_names(entities):
    print("Merging aliases with PIDs...")
    polysemous_names = defaultdict(dict)

    # Construct dictionary mapping names to associated entities
    for qid in tqdm.tqdm(entities):
        for name in [entities[qid]['label']] + entities[qid]['aliases']:
            polysemous_names[name][qid] = entities[qid]

    # Compute head and tail entities, and filter entities with less than 2 entities
    for name in list(polysemous_names.keys()):
        # Filter names that don't have at least two entities that share that name
        if len(polysemous_names[name]) < 2:
            del polysemous_names[name]
            continue

        pops = [polysemous_names[name][qid]["popularity"] for qid in polysemous_names[name]]
        pops = sorted(pops, reverse=True)
        head_entity_pop = pops[0]
        percent_diff = 100 * (pops[0] - pops[1]) / (0.5 * pops[0] + 0.5 * pops[1])

        # Filter if the gap in popularity between head and tail is < 10%
        if percent_diff < 10:
            del polysemous_names[name]
            continue

        for qid in polysemous_names[name]:
            if polysemous_names[name][qid]['popularity'] == head_entity_pop:
                polysemous_names[name][qid]['is_head'] = True
            else:
                polysemous_names[name][qid]['is_head'] = False

    return polysemous_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--entity_file",
        help=".JSON file containing entities, entity information, and relations"
    )
    parser.add_argument(
        "-c",
        "--collection",
        help="Collection to collect polysemous names for, AmbER-H (human) or "
             "AmbER-N (nonhuman)",
        choices=["human", "nonhuman"]
    )
    args = parser.parse_args()
    good_pids_file = join("amber_sets", args.collection, "good_pids.json")
    output_file = join("amber_sets", args.collection, "tmp/polysemous_names.jsonl")

    # Loads a dictionary that maps from QIDs to PIDs
    entities = load_entities(args.entity_file, good_pids_file)
    print(f"Found {len(entities)} entities after loading")

    # Load a list of dictionaries that maps from names to QIDs to PIDs
    polysemous_names = collect_polysemous_names(entities)
    print(f"Found {len(polysemous_names)} polysemous names")

    with open(output_file, "w", encoding="utf-8") as f:
        for name, d in tqdm.tqdm(polysemous_names.items()):
            new_d = {'name': name, 'qids': d}
            f.write(json.dumps(new_d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
