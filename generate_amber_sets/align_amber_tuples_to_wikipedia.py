""" Maps QIDs to Wikipedia indices in the KILT Wikipedia dump """
import argparse
import collections
import json
import sys
from os.path import isfile, join

import datasets
import jsonlines
from tqdm import tqdm

sys.path.append('evaluation')
from utils import get_tokens

wikipedia = datasets.load_dataset("kilt_wikipedia")['full']


def map_qids_to_kilt():
    """ Maps QIDs to a list of KILT Wikipedia articles.

    The KILT Wikipedia dump in `nlp` is formatted as a list, making mapping
    from QIDs to Wikipedia articles difficult. To speed this
    up, we return a dictionary mapping QIDs to the index in the KILT
    Wikipedia list. We henceforce refer to this value as `kilt_idx`.
    """
    kilt_map_file = '.cache/qids_to_wikipedia_mapping.json'

    if isfile(kilt_map_file):
        qid_to_wikipedia = json.load(open(kilt_map_file))
    else:
        qid_to_wikipedia = collections.defaultdict(list)
        for kilt_idx, wikipedia_dict in tqdm(enumerate(wikipedia)):
            qid = wikipedia_dict['wikidata_info']['wikidata_id']
            if qid:
                qid_to_wikipedia[qid].append(kilt_idx)

        with open(kilt_map_file, 'w') as f:
            f.write(json.dumps(qid_to_wikipedia))

    return qid_to_wikipedia


def map_amber_tuples_to_wikipedia_ids(amber_tuples):
    """ Add KILT Wikipedia info to AmbER tuples """
    qid_to_wikipedia = map_qids_to_kilt()

    # Add KILT mapping info to AmbER instance
    for d in tqdm(amber_tuples):
        for qid in list(d['qids'].keys()):
            d['qids'][qid]['wikipedia'] = []

            # Index KILT Wikipedia article(s) of the current QID
            kilt_idxs = qid_to_wikipedia.get(qid, [])
            for kilt_idx in kilt_idxs:
                # The ID of Wikipedia articles corresponding to the KILT indices
                wikipedia_id = wikipedia[kilt_idx]['wikipedia_id']

                d['qids'][qid]['wikipedia'].append({
                    'kilt_idx': kilt_idx,
                    'wikipedia_id': wikipedia_id,
                    'title': wikipedia[kilt_idx]['wikipedia_title'],
                })

            # If a QID doesn't have a Wikipedia article, then delete it.
            if len(d['qids'][qid]['wikipedia']) == 0:
                del d['qids'][qid]

    return amber_tuples


def answer_in_doc(answer, doc):
    answer_tokens = get_tokens(answer)
    doc_tokens = get_tokens(doc)

    # Test that answer tokens are a sublist of doc tokens
    if answer_tokens in [doc_tokens[i:len(answer_tokens) + i]
                         for i in range(len(doc_tokens))]:
        return True
    return False


def filter_unanswerables(amber_tuples):
    for d in tqdm(amber_tuples):
        for qid in d['qids']:
            for pid in list(d['qids'][qid]['pids'].keys()):
                provenance = []

                for wikipedia_dict in d['qids'][qid]['wikipedia']:
                    kilt_idx = wikipedia_dict['kilt_idx']
                    doc = ' '.join(wikipedia[kilt_idx]['text']['paragraph'])
                    doc = ' '.join(doc.split()[:350])

                    # Test if answer is in the current Wikipedia page
                    for values_dict in d['qids'][qid]['pids'][pid]['values']:
                        for answer in values_dict['aliases']:
                            if answer_in_doc(answer, doc) and wikipedia_dict not in provenance:
                                provenance.append(wikipedia_dict)

                # If the PID doesn't have a gold article, delete it.
                if len(provenance) > 0:
                    d['qids'][qid]['pids'][pid]['provenance'] = provenance
                else:
                    del d['qids'][qid]['pids'][pid]

    return amber_tuples


def filter_aliases(alias_dicts):
    """ Keep aliases that have at least 2 QIDs with PIDS
        AND the head QID has PIDs too
    """
    filtered_alias_dicts = []

    for d in alias_dicts:
        good_qid_count = 0
        head_is_good = False

        for qid_dict in d['qids'].values():
            if len(qid_dict['pids']) > 0:
                good_qid_count += 1
                if qid_dict['is_head']:
                    head_is_good = True

        if good_qid_count >= 2 and head_is_good:
            filtered_alias_dicts.append(d)

    return filtered_alias_dicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    input_data_file = join("amber_sets", args.collection, "tmp/amber_set_tuples.jsonl")
    output_data_file = join("amber_sets", args.collection, "amber_set_tuples.jsonl")

    amber_tuples = [line for line in jsonlines.open(input_data_file)]

    # Update AmbER tuples with the associated Wikipedia documents
    amber_tuples = map_amber_tuples_to_wikipedia_ids(amber_tuples)
    amber_tuples = filter_unanswerables(amber_tuples)
    amber_tuples = filter_aliases(amber_tuples)

    # Write out the AmbER tuples with associated KILT mapping
    with open(output_data_file, 'w', encoding='utf-8') as f:
        for d in amber_tuples:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
