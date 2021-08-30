#!/usr/bin/python3
import argparse
import bz2
import collections
import math
import typing

import tqdm
import ujson as json


def dumb_filter(line: str) -> bool:
    """Filters a Wikidata line that is a dictionary in string format.

    Applies a simple check that tests if the currenty entity line has a English
    Wikipedia article before loading. The reason is that loading a JSON object is slow
    before running it, that speeds up code. Removing this function call should not
    change the resulting file.

    Arguments:
        line: ``str`` A line in the Wikidata dump.
    Returns:
        ``bool`` Whether the current line is for an entity with an English article
    """
    return '"enwiki"' not in line and '"type":"item"' in line


def extract_popularities(popularity_dump: str) -> typing.Dict[str, float]:
    """Extract each entity's popularity.

    Iterate through the Wikipedia popularity dump (without decompressing)
    it, storing each English Wikipedia page's (log) number of page views.

    Arguments:
        popularity_dump: ``str`` A path to a .BZ2 file containing Wikipedia
        page views for a day.
    Returns:
        wiki_popularity: ``dict`` Maps from a Wikipedia page to the monthly
        popularity.
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


def extract_label(line: dict) -> str:
    """Extracts the English label (canonical name) for an entity.
    Arguments:
        line: ``dict`` A line in the Wikidata dump.
    Returns:
        ``str`` Canonical English name for the entity.
    """
    if "en" in line["labels"]:
        return line["labels"]["en"]["value"]
    return None


def extract_aliases(line: dict) -> typing.List[str]:
    """Extracts all English names for an entity.

    Arguments:
        line: ``dict`` A line in the Wikidata dump.
    Returns:
        aliases: ``list`` All English aliases for the entity.
    """
    label = extract_label(line)
    aliases = [label] if label else []
    if "en" in line["aliases"]:
        aliases += [d["value"] for d in line["aliases"]["en"]]
    return aliases


def extract_entity_types(line: dict) -> typing.List[str]:
    """Extracts the entity type(s) for an entity.

    Arguments:
        line: ``dict`` A line in the Wikidata dump.
    Returns:
        entity_types: ``list`` A list of entity types for the entity.
            Entity types are also QIDs in Wikidata.
    """
    entity_types = []
    # P31 is "instance of". We define these to represent entity types.
    for entry in line["claims"].get("P31", []):
        if (
            entry["mainsnak"]["datatype"] == "wikibase-item"
            and "datavalue" in entry["mainsnak"]
        ):
            entity_types.append(entry["mainsnak"]["datavalue"]["value"]["id"])
    return entity_types


def extract_wikipedia_page(line: dict) -> str:
    """Extracts the Wikipedia page for an entity

    Arguments:
        line: ``dict`` A line in the Wikidata dump.
    Returns:
        ``str`` Title of the of the Wikipedia article for the entity
    """
    if "sitelinks" in line and "enwiki" in line["sitelinks"]:
        return line["sitelinks"]["enwiki"]["title"].strip().replace(" ", "_")
    return None


def extract_relations(line: dict) -> typing.Dict[str, dict]:
    """Extracts all relations for each entity line.

    Extracts all relations for the current entity where the value of the entity is
    either another entity or a quantity. This excludes relations where the value is
    something like a date (e.g. birthdate), etc.

    Arguments:
        line: ``dict`` A line in the Wikidata dump.
    Returns:
        relations: ``dict`` Maps from relation IDs (PIDs) to the value of the relation.
    """
    relations = collections.defaultdict(lambda: collections.defaultdict(list))

    for relation_id in line["claims"]:
        # Each relation may have multiple values. Iterate through those values.
        for entry in line["claims"][relation_id]:
            if "datavalue" in entry["mainsnak"]:
                answer_type = entry["mainsnak"]["datatype"]

                # Check that the current answer is an entity
                if answer_type == "wikibase-item":
                    relations[relation_id]["values"].append(
                        {
                            "type": answer_type,
                            "qid": entry["mainsnak"]["datavalue"]["value"]["id"],
                        }
                    )
                # Check that the current answer is an quantity
                elif answer_type == "quantity":
                    relations[relation_id]["values"].append(
                        {
                            "type": answer_type,
                            "amount": entry["mainsnak"]["datavalue"]["value"]["amount"],
                            "unit": entry["mainsnak"]["datavalue"]["value"]["unit"],
                        }
                    )
                else:  # Skip answers that are strings, GPS location, etc.
                    continue

    return relations


def extract_wikidata_entities(
    wikidata_dump: str, popularity_dump: str, output_file: str
) -> None:
    """Extracts Wikidata entity information from various dumps.

    For each Wikidata entity in the Wikidata dump, we extract out it's entity
    type, all aliases for the entity, Wikipedia page, and popularity of the entity's
    Wikipedia page, then write this information into a JSON file. We write each
    dictionary of entity information in it's own line for easy readability.

    Arguments:
        wikidata_dump: ``str`` Path to a BZ2 compressed JSON Wikidata dump.
        popularity_dump: ``str`` Path to a BZ2 compressed JSON Wikipedia pageview dump.
        output_file: ``str`` Path to the output BZ2 file.
    """
    # Store each English Wikipedia page's number of page views
    wiki_popularity = extract_popularities(popularity_dump)

    # Iterate through the Wikidata dump without decompressing it
    writer = open(output_file, "w", encoding="utf-8")
    writer.write("{\n")
    first_line_written = False

    with bz2.open(wikidata_dump, "rt") as reader:
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
                    "popularity": popularity,
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

            writer.write(
                f"{json.dumps(line['id'])}: "
                f"{json.dumps(info_dict, ensure_ascii=False)}"
            )

    writer.write("\n}")
    writer.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--wikidata_dump",
        help=".json.bz2 Wikidata dump for information extraction",
    )
    parser.add_argument(
        "-p", "--popularity_dump", help=".bz2 Wikipedia popularity dump"
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="Output JSON file for writing Wikidata entity information",
    )
    args = parser.parse_args()

    extract_wikidata_entities(
        args.wikidata_dump, args.popularity_dump, args.output_file
    )


if __name__ == "__main__":
    main()
