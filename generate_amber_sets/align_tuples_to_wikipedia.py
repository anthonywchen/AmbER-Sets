""" Maps QIDs to Wikipedia indices in the KILT Wikipedia dump """
import argparse
import collections
import hashlib
import itertools
import json
import os
import string
import re

import jsonlines
import tqdm


def normalize_answer(s):
    """Lower text and remove punctuation, articles and extra whitespace."""
    def remove_articles(text):
        regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
        return re.sub(regex, " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        # Replace dash with a space
        text = text.replace("-", " ")
        # Replace other punctuation with empty string
        for punc in string.punctuation:
            text = text.replace(punc, "")
        return text

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s):
    if not s:
        return []
    return normalize_answer(s).split()


def answer_in_doc(answer, doc):
    answer_tokens = get_tokens(answer)
    doc_tokens = get_tokens(doc)

    # Test that answer tokens are a sublist of doc tokens
    if answer_tokens in [
        doc_tokens[i:len(answer_tokens)+i] for i in range(len(doc_tokens))
    ]:
        return True
    return False


def create_amber_id(name, qid, pid):
    """For each (name, QID, PID), we compute a unique AmbER set tuple ID"""
    hash_input = repr([name, qid, pid]).encode()
    md5 = hashlib.md5(hash_input).hexdigest()
    return md5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--wikipedia_dump",
        help=".json KILT Wikipedia dump for aligning entities to Wikipedia articles"
    )
    parser.add_argument(
        "-c", "--collection",
        help="Collection to collect polysemous names for, AmbER-H (human) or "
             "AmbER-N (nonhuman)",
        choices=["human", "nonhuman"]
    )
    args = parser.parse_args()

    input_data_file = os.path.join(
        "amber_sets", args.collection, "tmp/filtered_relations.jsonl"
    )
    output_data_file = os.path.join(
        "amber_sets", args.collection, "amber_set_tuples.jsonl"
    )

    polysemous_names = list(jsonlines.open(input_data_file))

    # Keep track of all entities that are in our polysemous names set
    qids = set(itertools.chain(*[d['qids'].keys() for d in polysemous_names]))

    # Store a mapping of QIDs that are in our set to associated Wikipedia dictionary
    qid_to_wikipedia = collections.defaultdict(list)
    with open(args.wikipedia_dump) as reader:
        for line in tqdm.tqdm(reader, desc="Loading Wikipedia articles"):
            line = json.loads(line)
            if 'wikidata_info' in line:
                qid = line['wikidata_info']['wikidata_id']
                if qid in qids:
                    qid_to_wikipedia[qid].append(line)

    # Add Wikipedia information to each entity in the tuples and filter
    # unanswerable relations
    for d in tqdm.tqdm(polysemous_names, desc="Aligning entities to Wikipedia articles"):
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

                # All possible answers to the current tuple
                pid_answers = list(itertools.chain(*[
                    value_dict['aliases']
                    for value_dict in d['qids'][qid]['pids'][pid]['values']
                ]))

                # Iterate through each Wikipedia article, and check that the value of
                # the current relation has value aliases in the Wikipedia article. If
                # so, we treat this as the "gold" document
                for article in articles:
                    doc = " ".join(article["text"])
                    doc = " ".join(doc.split()[:350])

                    # Check if any of the answers is in the document
                    for answer in pid_answers:
                        # If so, we treat the current document as a gold document
                        if answer_in_doc(answer, doc):
                            d['qids'][qid]['pids'][pid]['provenance'].append({
                                'wikipedia_id': article['wikipedia_id'],
                                'title': article['wikipedia_title']
                            })
                            break

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
                d['qids'][qid]['pids'][pid]['amber_id'] = create_amber_id(d['name'], qid, pid)

    # Sort list of alias dictionaries by the alias
    filtered_names = sorted(filtered_names, key=lambda k: k["name"])

    # Write out the AmbER tuples with associated KILT mapping
    with open(output_data_file, "w", encoding="utf-8") as f:
        for d in filtered_names:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
