#!/usr/bin/python3
import argparse
import collections
import os
import typing

import inflect
import ujson as json
import tqdm

engine = inflect.engine()


def extract_aliases_for_entity(entities: dict, qid: str) -> typing.Tuple[list, list]:
    """Extracts aliases for a Wikidata entity.

    A helper function for completing the entity dictionaries. For the argument QID
    (entity), we extract the aliases as provided by Wikidata as well as extract a list
    of expanded aliases. These additional aliases are found by taking entities of
    those that "perform" or "do" the entity. For example, if the QID is
    Q6607 (guitar), the additional aliases will contain "guitarist". This was done 
    for end tasks (e.g. reading comprehension),  where for the question "What
    instrument does XXX play?" a model may answer "guitarist", which we deem correct.
    Of course, doing this makes the answer set nosier, but in our qualitative
    results, we found this not to be an issue.

    Arguments:
        entities: ``dict`` A dictionary of Wikidata entity information.
        qid: ``str`` A single entity ID.
    Returns:
        aliases: ``list`` A list of aliases for the entity provided by Wikidata.
        additional_aliases: ``list`` A list of additional aliases mined by traversing
            relations of the current entity.
    """
    aliases = []
    additional_aliases = set()
    if qid in entities:
        aliases = entities[qid]['aliases']

        # Add in aliases for the people who participate in the answer
        # e.g. for the alias guitar, we also add in guitarist
        for value in entities[qid]['pids'].get("P3095", {}).get("values", []) + \
                     entities[qid]['pids'].get("P1535", {}).get("values", []):
            pqid = value["qid"]  # pqid = participant QID
            if pqid in entities:
                additional_aliases.update(entities[pqid]['aliases'])

    return aliases, list(sorted(additional_aliases))


def extract_aliases_for_quantity(amount: str) -> typing.Tuple[list, list]:
    """Extracts aliases for a numerical value.

    A helper function for completing the entity dictionaries. For the quantity,
    we extract out the amount in numerical form (e.g. "2") as well as in textual form
    (e.g. "two") for the same reason as for extracting aliases for entities.

    Arguments:
        amount: ``str`` The quantity amount which also contains the quantity sign.
    Returns:
        aliases: ``list`` The quantity with the sign removed in a list.
        additional_aliases: ``list`` The quantity in textual form.
    """
    assert amount[0] in ["+", "-"]
    aliases = [amount[1:]]
    try:
        additional_aliases = [engine.number_to_words(amount[1:])]
    except:
        additional_aliases = []
    return aliases, additional_aliases


def extract_entity_types(entities: dict, qid: str) -> typing.List[str]:
    """Returns entity types for a specified entity.

    Arguments:
        entities: ``dict`` A dictionary of Wikidata entity information.
        qid: ``str`` A single entity ID.
    Returns:
        ``list`` A list of entity types for the entity.
    """
    return entities.get(qid, {}).get("entity_types", [])


def extract_polysemous_names(entity_file: str, collection: str) -> None:
    """Creates a mapping from polysemous to corresponding entities.

    Constructs a list of dictionaries which map from a polysemous name to Wikidata
    entities which share the name. During this process, we complete the entity
    dictionaries by adding information to the values of the relations of entities.
    We also filter entities which do not correspond to a pre-specified entity type
    for the AmbER set collection as well as compute the head entity for each
    collection of entities for a polysemous name. The resulting list of polysemous
    names are written out to a JSONLines file.

    Arguments:
        entity_file: ``str`` Path to a JSON file containing Wikidata entity info.
        collection: ``str``The collection (human/nonhuman) of AmbER sets.
    """
    entity_types_to_distinguishing_properties_file = os.path.join(
        "data", collection, "entity_types_to_distinguishing_properties.json"
    )
    output_file = os.path.join("data", collection, "tmp/polysemous_names.jsonl")

    # Loads entities, then completes the dictionary
    entities = json.load(open(entity_file))
    # Map polysemous names to entities
    polysemous_names = collections.defaultdict(dict)
    for qid in tqdm.tqdm(entities, desc="Finding polysemous names"):
        # Skip PIDs since we store QIDs and PIDs together in the entities file
        if qid[0] == 'P':
            continue

        # Map all names to the current entity and store popularity
        for name in entities[qid]['aliases']:
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
                        extract_aliases_for_quantity(value['amount'])

            # Filter out values without any aliases
            entities[qid]['pids'][pid]['values'] = [
                v for v in entities[qid]['pids'][pid]['values'] if len(v['aliases'])
            ]

    # For each polysemous name, compute the head and tail entities
    for name in polysemous_names:
        # Get all popularity of all entities which share the name
        pops = [
            polysemous_names[name][qid]["popularity"] for qid in polysemous_names[name]
        ]

        # An entity is the head if it is the most popular
        for qid in polysemous_names[name]:
            pop = polysemous_names[name][qid]['popularity']
            polysemous_names[name][qid]['is_head'] = pop == max(pops)

    # Delete entities where they have an entity type that doesn't match our collection
    acceptable_entity_types = list(json.load(open(entity_types_to_distinguishing_properties_file)))
    for qid in tqdm.tqdm(list(entities), desc="Deleting entities w/o matching types"):
        entity_types = set(entities[qid].get('entity_types', []))
        if len(entity_types.intersection(acceptable_entity_types)) == 0:
            del entities[qid]

    # Perform a round of filtering on the polysemous names and their entities
    polysemous_names_list = []
    for name in tqdm.tqdm(polysemous_names):
        # Delete entities from `polysemous_names` if they were deleted in `entities`
        for qid in list(polysemous_names[name].keys()):
            if qid not in entities:
                del polysemous_names[name][qid]
            else:
                polysemous_names[name][qid].update(entities[qid])

        # Keep names that have at least two entities that share that name
        if len(polysemous_names[name]) >= 2:
            pops = [
                polysemous_names[name][qid]["popularity"] for qid in
                polysemous_names[name]
            ]
            pops = sorted(pops, reverse=True)
            percent_diff = (pops[0]-pops[1])/(0.5*pops[0] + 0.5*pops[1])

            # Keep if the gap in popularity between head and tail is >= 10%
            if percent_diff >= .10:
                polysemous_names_list.append(
                    {'name': name, "qids": polysemous_names[name]}
                )

    with open(output_file, "w", encoding="utf-8") as f:
        for name_dict in polysemous_names_list:
            f.write(json.dumps(name_dict, ensure_ascii=False) + "\n")


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

    extract_polysemous_names(args.entity_file, args.collection)


if __name__ == "__main__":
    main()
