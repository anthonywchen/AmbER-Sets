"""Extracts Wikidata entity information from various dumps and outputs to a
single JSON file, while filtering entities that do not match certain criteria.
The JSON file is broken down into a line for each entity
for easy reading. Each line has the following format:

entity_id: {
    "label": ``str`` Name of entity,
    "aliases": ``str`` Alternative names of entities,
    "entity_types: ``List[str]`` List of entity types,
    "wikipedia_page": ``str`` Wikipedia page of entity,
    "popularity": ``int`` Number of page views for Wikipedia page,
    "relations": ``dict`` {
        property_id1: [<list of tail entity IDs],
        property_id2: [<list of tail entity IDs],
    }
}
"""
import argparse
import bz2
import collections
import math

import tqdm
import ujson as json


def dumb_filter(line):
    """Does a simple check on a Wikidata line that is a dictionary in string format.
    The reason is that json.loads() is slow, and if we can do some filtering
    before running it, that speeds up code. Removing this function call should not
    change the output file.
    """
    return "\"enwiki\"" not in line and "\"type\":\"item\"" in line


def extract_popularities(popularity_dump):
    """Iterate through the Wikipedia popularity dump without decompressing
    it, storing each English Wikipedia page's number of page views.

    Arguments:
        popularity_dump: ``str`` A path to a .BZ2 file containing Wikipedia
        page views for a day.
    Returns:
        wiki_popularity: ``dict`` Maps from a Wikipedia page to the daily
        page view count.
    """
    wiki_popularity = {}
    with bz2.open(popularity_dump, "rt") as file:
        # Each line corresponds to the number of page views for a Wikipedia page
        for line in tqdm.tqdm(file, desc="Loading Wikipedia popularity values"):
            line = line.strip().split()
            # Skip lines w/o right len or Wikipedia pages that aren't in English
            if len(line) == 3 and line[0] == "en.z":
                # The popularity is the log of the page counts.
                wiki_popularity[line[1]] = math.log10(int(line[2]))
    print(f"Found {len(wiki_popularity)} English Wikipedia pages")
    return wiki_popularity


def extract_label(line):
    """Extracts the English label (canonical name) for an entity"""
    if 'en' in line['labels']:
        return line['labels']['en']['value']
    return None


def extract_aliases(line):
    """Extracts all English names for an entity"""
    label = extract_label(line)
    aliases = [label] if label else []
    if 'en' in line['aliases']:
        aliases += [d['value'] for d in line['aliases']['en']]
    return aliases


def extract_entity_types(line):
    """Extracts the entity type for an entity"""
    entity_types = []
    # P31 is "instance of". We define these to represent entity types.
    for entry in line['claims'].get('P31', []):
        if entry['mainsnak']['datatype'] == 'wikibase-item' and \
                'datavalue' in entry['mainsnak']:
            entity_types.append(entry['mainsnak']['datavalue']['value']['id'])
    return entity_types


def extract_wikipedia_page(line):
    """Extracts the Wikipedia page for an entity"""
    if 'sitelinks' in line and 'enwiki' in line['sitelinks']:
        return line['sitelinks']['enwiki']['title'].strip().replace(" ", "_")
    return None


def extract_relations(line):
    """Extracts all relations for each entity line where the value of the relation
    is either an entity or a quantity.
    """
    relations = collections.defaultdict(lambda: collections.defaultdict(list))

    for relation_id in line['claims']:
        # Each relation may have multiple values. Iterate through those values.
        for entry in line['claims'][relation_id]:
            if 'datavalue' in entry['mainsnak']:
                answer_type = entry['mainsnak']['datatype']

                # Check that the current answer is an entity
                if answer_type == 'wikibase-item':
                    relations[relation_id]['values'].append({
                        "type": answer_type,
                        "qid": entry['mainsnak']['datavalue']['value']['id']
                    })
                # Check that the current answer is an quantity
                elif answer_type == "quantity":
                    relations[relation_id]['values'].append({
                        "type": answer_type,
                        "amount": entry['mainsnak']["datavalue"]["value"]["amount"],
                        "unit": entry['mainsnak']["datavalue"]["value"]["unit"]
                    })
                else: # Skip answers that are strings, GPS location, etc.
                    continue

    return relations


def main():
    """For each Wikidata entity in the Wikidata dump, we extract out it's entity
    type, associated Wikipedia page (used for popularity), all aliases
    for the entity, and popularity of the entity's Wikipedia page, then write
    this information into a JSON file. We write each dictionary of entity
    information in it's own line for easy readability.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--wikidata_dump",
        help=".json.bz2 Wikidata dump for information extraction"
    )
    parser.add_argument(
        "-p",
        "--popularity_dump",
        help=".bz2 Wikipedia popularity dump"
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="Output JSON file for writing Wikidata entity information"
    )
    args = parser.parse_args()

    # Store each English Wikipedia page's number of page views
    wiki_popularity = extract_popularities(args.popularity_dump)

    # Iterate through the Wikidata dump without decompressing it
    writer = open(args.output_file, "w", encoding="utf-8")
    writer.write("{\n")
    first_line_written = False

    with bz2.open(args.wikidata_dump, "rt") as reader:
        # Each line corresponds to a dictionary about a Wikidata entity
        for line in tqdm.tqdm(reader, desc="Processing Wikidata"):
            if dumb_filter(line) or line.strip() in ["[", "]"]:
                continue

            # Remove last character (comma), then decode
            line = json.loads(line.strip()[:-1])

            # Current line is an entity
            if line["type"] == "item":
                aliases = extract_aliases(line)
                popularity = wiki_popularity.get(extract_wikipedia_page(line))

                # Skip if entity doesn't have name or English Wikipedia page views
                if aliases == [] or popularity is None:
                    continue

                info_dict = {
                    "aliases": aliases,
                    "entity_types": extract_entity_types(line),
                    "pids": extract_relations(line),
                    "popularity": popularity
                }
            # Current line is a property
            elif line["type"] == "property":
                info_dict = {"label": extract_label(line)}
            else:
                continue

            # Write extracted dictionary into a JSON format, one line at a time
            if first_line_written is True:
                writer.write(",\n")
            first_line_written = True

            writer.write(f"{json.dumps(line['id'])}: "
                         f"{json.dumps(info_dict, ensure_ascii=False)}")

    writer.write("\n}")
    writer.close()


if __name__ == "__main__":
    main()
