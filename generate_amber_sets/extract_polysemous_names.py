import argparse
import collections
import os

import inflect
import ujson as json
import tqdm

engine = inflect.engine()


def extract_aliases_for_entity(entities, qid):
    """Extracts aliases for a Wikidata entity"""
    aliases = []
    additional_aliases = set()
    if qid in entities:
        aliases = set(entities[qid]['aliases'])

        # Add in aliases for the people who participated in the answer
        # e.g. for the alias guitar, we also add in guitarist
        for value in entities[qid]['pids'].get("P3095", {}).get("values", []) + \
                     entities[qid]['pids'].get("P1535", {}).get("values", []):
            pqid = value["qid"]  # pqid = participant QID
            if pqid in entities:
                additional_aliases.update([entities[pqid]['label']] + entities[pqid]['aliases'])

        # Ensures label is always first element in aliases
        aliases = [entities[qid]['label']] + sorted(aliases)
    return aliases, list(sorted(additional_aliases))


def extract_aliases_for_quantity(entities, amount):
    """Extracts aliases for a numerical value"""
    assert amount[0] in ["+", "-"]
    aliases = [amount[1:]]
    try:
        additional_aliases = [engine.number_to_words(amount[1:])]
    except:
        additional_aliases = []
    return aliases, additional_aliases


def extract_entity_types(entities, qid):
    """Returns entity types for a specified entity"""
    return entities.get(qid, {}).get("entity_types", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e", "--entity_file",
        help=".JSON file containing entities, entity information, and relations"
    )
    parser.add_argument(
        "-c", "--collection",
        help="Collection to collect polysemous names for, AmbER-H (human) or "
             "AmbER-N (nonhuman)",
        choices=["human", "nonhuman"]
    )
    args = parser.parse_args()
    good_pids_file = os.path.join("amber_sets", args.collection, "good_pids.json")
    output_file = os.path.join("amber_sets", args.collection, "tmp/polysemous_names.jsonl")

    # Loads entities, then completes the dictionary
    entities = json.load(open(args.entity_file))
    # Map polysemous names to entities
    polysemous_names = collections.defaultdict(dict)
    for qid in tqdm.tqdm(entities, desc="Completing entity dictionary"):
        # Skip PIDs since we store QIDs and PIDs together in the entities file
        if qid[0] == 'P':
            continue

        # Map all names to the current entity and store popularity
        for name in [entities[qid]['label']] + entities[qid]['aliases']:
            polysemous_names[name][qid] = {'popularity': entities[qid]['popularity']}

        # Iterate through all relations for the current entity
        for pid in list(entities[qid]['pids'].keys()):
            # Add the name of the property into the relations
            entities[qid]['pids'][pid]['property'] = entities[pid]['label']

            # Iterate through all possible values for the current relation
            for value in entities[qid]['pids'][pid]['values']:
                # If the current value is a Wikidata entity
                if value['type'] == "wikibase-item":
                    value['aliases'], value['additional_aliases'] = \
                        extract_aliases_for_entity(entities, value['qid'])
                    value['entity_types'] = extract_entity_types(entities, value['qid'])
                # If the current value is some numerical quantity
                elif value['type'] == 'quantity':
                    value['aliases'], value['additional_aliases'] = \
                        extract_aliases_for_quantity(entities, value['amount'])

    # For each polysemous name, compute the head and tail entities
    for name in polysemous_names:
        # Get all popularity of all entities which share the name
        pops = [polysemous_names[name][qid]["popularity"] for qid in
                polysemous_names[name]]

        # An entity is the head if it is the most popular
        for qid in polysemous_names[name]:
            pop = polysemous_names[name][qid]['popularity']
            polysemous_names[name][qid]['is_head'] = pop == max(pops)

    # Delete entities where they have an entity type that doesn't match our collection
    good_pids = json.load(open(good_pids_file))
    for qid in tqdm.tqdm(list(entities.keys()), desc="Deleting entities without matching entity types"):
        entity_types = set(entities[qid].get('entity_types', []))
        if len(entity_types.intersection(good_pids)) == 0:
            del entities[qid]

    # Filter names with < 2 entities
    polysemous_names_list = []
    for name in tqdm.tqdm(polysemous_names):
        # Update the QIDs with the entire dictionary if the entity wasn't deleted
        for qid in list(polysemous_names[name].keys()):
            if qid not in entities:
                del polysemous_names[name][qid]
            else:
                polysemous_names[name][qid].update(entities[qid])

        # Keep names that have at least two entities that share that name
        if len(polysemous_names[name]) >= 2:
            pops = [polysemous_names[name][qid]["popularity"] for qid in
                    polysemous_names[name]]
            pops = sorted(pops, reverse=True)
            percent_diff = 100 * (pops[0] - pops[1]) / (0.5 * pops[0] + 0.5 * pops[1])

            # Keep if the gap in popularity between head and tail is >= 10%
            if percent_diff >= 10:
                polysemous_names_list.append({'name': name, "qids": polysemous_names[name]})

    with open(output_file, "w", encoding="utf-8") as f:
        for name_dict in polysemous_names_list:
            f.write(json.dumps(name_dict, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
