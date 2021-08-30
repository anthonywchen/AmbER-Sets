#!/usr/bin/python3
import argparse
import collections
import hashlib
import itertools
import json
import os

import jsonlines
import tqdm

from evaluation.utils import get_tokens


def answer_in_doc(answer: str, doc: str) -> bool:
    """Checks if an answer is in a document.

    This function uses the `get_tokens()` function which is dervied from the SQuAD
    evaluation script.

    Arguments:
        answer: ``str`` Answer.
        doc: ``str`` Document.
    Returns:
        ``bool`` Whether the answer tokens are a subset of the token documents.
    """
    answer_tokens = get_tokens(answer)
    doc_tokens = get_tokens(doc)

    # Test that answer tokens are a sublist of doc tokens
    if answer_tokens in [
        doc_tokens[i:len(answer_tokens)+i] for i in range(len(doc_tokens))
    ]:
        return True
    return False


def create_amber_id(name: str, qid: str, pid: str) -> str:
    """For each (name, QID, PID) tuple, we compute a unique AmbER ID.

    Arguments:
        name: ``str`` The polysemous name for the AmbER set.
        qid: ``str`` The ID of an entity.
        pid: ``str`` The ID of a property.
    Returns:
        md5: ``str`` A MD5 has of the concatenation of the name, QID, and PID,
            which we use as the ID of the AmbER set tuple.
    """
    hash_input = repr([name, qid, pid]).encode()
    md5 = hashlib.md5(hash_input).hexdigest()
    return md5


def align_tuples_to_wikipedia(wikipedia_dump: str, collection: str) -> None:
    """Aligns each tuple in the list of polysemous names to a Wikipedia article.

    For each tuple in a set corresponding to a polysemous name, we align the tuple
    to the corresponding Wikipedia article in a KILT Wikipedia dump. As part of this
    alignment, we check that the value of the tuple appears in the text (first 350
    tokens) of the document, so that when we create task-specific instances,
    the instance is solvable. We filter tuples that aren't able to be aligned to an
    article. The remaining tuples after this filtering are the AmbER sets tuples,
    are written out to a JSONLines file and are used to instantiate task-specific
    queries.

    Arguments:
        wikipedia_dump: ``str`` Path to a JSON KILT Wikipedia dump.
        collection: ``str`` The collection (human/nonhuman) of AmbER sets.
    """
    input_data_file = os.path.join("data", collection, "tmp/filtered_relations.jsonl")
    output_data_file = os.path.join("data", collection, "amber_set_tuples.jsonl")
    polysemous_names = list(jsonlines.open(input_data_file))

    # Keep track of all entities that are in our polysemous names set
    qids = set(itertools.chain(*[d['qids'].keys() for d in polysemous_names]))

    # Store a mapping of QIDs that are in our set to associated Wikipedia dictionary
    qid_to_wikipedia = collections.defaultdict(list)
    with open(wikipedia_dump) as reader:
        for line in tqdm.tqdm(reader, desc="Loading Wikipedia articles"):
            line = json.loads(line)
            if 'wikidata_info' in line:
                qid = line['wikidata_info']['wikidata_id']
                if qid in qids:
                    qid_to_wikipedia[qid].append(line)

    # Add Wikipedia information to each entity in the tuples and filter
    # unanswerable relations
    for d in tqdm.tqdm(polysemous_names, desc="Aligning entities to Wikipedia"):
        for qid in list(d['qids']):
            # Grabs all Wikipedia articles for the current QID
            d['qids'][qid]['wikipedia'] = []
            articles = qid_to_wikipedia.get(qid, [])

            for article in articles:
                d['qids'][qid]['wikipedia'].append({
                    'wikipedia_id': article['wikipedia_id'],
                    'title': article['wikipedia_title']
                })

            # Filter unanswerable relations
            for pid in list(d['qids'][qid]['pids']):
                # The provenance of each relation is documents that correspond to the
                # current entity that also contain aliases of the current relation
                d['qids'][qid]['pids'][pid]['provenance'] = []

                # Iterate through each Wikipedia article, and check that the value of
                # the current relation has value aliases in the Wikipedia article. If
                # so, we treat the article as a "gold" document and mark
                # that this value appeared in a gold document
                for value in d['qids'][qid]['pids'][pid]["values"]:
                    found_in_passage = False
                    for answer in value["aliases"]:
                        for article in articles:
                            doc = " ".join(article["text"])
                            doc = " ".join(doc.split()[:350])
                            if answer_in_doc(answer, doc):
                                provenance_dict = {
                                    'wikipedia_id': article['wikipedia_id'],
                                    'title': article['wikipedia_title']
                                }
                                if provenance_dict not in \
                                        d['qids'][qid]['pids'][pid]['provenance']:
                                    d['qids'][qid]['pids'][pid]['provenance'].append(
                                        provenance_dict
                                    )
                                found_in_passage = True
                    value['found_in_passage'] = found_in_passage

                # Delete relation if no article had an answer in the document
                if len(d['qids'][qid]['pids'][pid]['provenance']) == 0:
                    del d['qids'][qid]['pids'][pid]

            # If the current QID doesn't have any Wikipedia articles, delete it
            if d['qids'][qid]['wikipedia'] == []:
                del d['qids'][qid]

    # Filter names with < 2 entities with relations or no head entity with relations
    filtered_names = []
    for d in polysemous_names:
        entities_with_relations = 0
        head_has_relations = False
        for qid in d['qids']:
            if len(d['qids'][qid]['pids']) > 0:
                entities_with_relations += 1
                if d['qids'][qid]['is_head']:
                    head_has_relations = True

        if entities_with_relations >= 2 and head_has_relations:
            filtered_names.append(d)

    # Add AmbER set tuple IDs
    for d in filtered_names:
        for qid in d['qids']:
            for pid in d['qids'][qid]['pids']:
                d['qids'][qid]['pids'][pid]['amber_id'] = \
                    create_amber_id(d['name'], qid, pid)

    # Sort list of AmbER set tuples by the name
    filtered_names = sorted(filtered_names, key=lambda k: k["name"])

    # Write out the AmbER tuples with associated KILT mapping
    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in filtered_names:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--wikipedia_dump",
        help=".json KILT Wikipedia dump for aligning entities to Wikipedia articles"
    )
    parser.add_argument(
        "-c", "--collection",
        help="Collection to collect polysemous names for, AmbER-H (human) or "
             "AmbER-N (nonhuman)",
        choices=["human", "nonhuman"]
    )
    args = parser.parse_args()

    align_tuples_to_wikipedia(args.wikipedia_dump, args.collection)


if __name__ == "__main__":
    main()
