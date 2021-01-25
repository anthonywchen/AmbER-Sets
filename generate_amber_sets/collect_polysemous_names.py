import argparse
from collections import defaultdict
from os.path import dirname, join

import inflect
import ujson as json
from tqdm import tqdm

engine = inflect.engine()
WIKIDATA_DIR = "process_wikidata_dump/processed_files"


def add_pid_value_entity_types(qid_to_pids):
    """ Add entity types for Wikidata answers

    For the PIDs in which the value is a QID, add the entity
    type of that QID. This makes it when creating queries from templates
    since some templates require knowing what the type of the QID value is.
    """
    print('Adding entity types to values')
    for qid in tqdm(qid_to_pids):
        for pid in qid_to_pids[qid]:
            if pid == 'P31':
                continue

            for answer_dict in qid_to_pids[qid][pid]:
                if answer_dict['type'] == 'entityid':
                    answer_dict['entity_types'] = [e['qid'] for e in
                                                   qid_to_pids.get(answer_dict['qid'], {}).get('P31', [])]

    return qid_to_pids


def add_pid_value_aliases(qid_to_pids, qid_to_aliases_file):
    """ Add entity alises for Wikidata answers

    For the PIDs in which the value is a QID, add the entity
    aliases of that QID. This makes it when using this data for extractive
    QA, so that we can compute a score over the set of aliases.
    """
    print('Adding aliases to values')
    qid_to_aliases = json.load(open(qid_to_aliases_file, encoding='utf-8'))

    for qid in tqdm(qid_to_pids):
        for pid in qid_to_pids[qid]:
            for answer_dict in qid_to_pids[qid][pid]:
                if answer_dict['type'] == 'entityid':
                    answer_qid = answer_dict['qid']
                    answer_dict['aliases'] = qid_to_aliases.get(answer_qid, [])

                    answer_dict['additional_aliases'] = set()

                    # Add in aliases for the people who particpate in the answer
                    # e.g. for the alias guitar, we also add in guartist
                    if answer_qid in qid_to_pids:
                        for instance in qid_to_pids[answer_qid].get('P3095', []):
                            participant_qid = instance['qid']
                            answer_dict['additional_aliases'].update(qid_to_aliases.get(participant_qid, []))

                        for instance in qid_to_pids[answer_qid].get('P1535', []):
                            participant_qid = instance['qid']
                            answer_dict['additional_aliases'].update(qid_to_aliases.get(participant_qid, []))

                    answer_dict['aliases'] = answer_dict['aliases']
                    answer_dict['additional_aliases'] = sorted(answer_dict['additional_aliases'])

                elif answer_dict['type'] == 'quantity':
                    amount = answer_dict['amount']
                    assert amount[0] in ['+', '-']
                    amount = amount[1:]
                    answer_dict['aliases'] = [amount]
                    try:
                        answer_dict['additional_aliases'] = [engine.number_to_words(amount)]
                    except:
                        answer_dict['additional_aliases'] = []

    return qid_to_pids


def get_most_popular_pid_values(qid_to_pids, good_pids_file):
    good_pids_data = json.load(open(good_pids_file))
    good_pids = set([f for d in good_pids_data.values()
                     for e in d.values() for f in e])

    popular_pid_values = defaultdict(lambda: defaultdict(int))

    for qid in tqdm(qid_to_pids):
        for pid in qid_to_pids[qid]:
            if pid in good_pids:
                for answer_dict in qid_to_pids[qid][pid]:
                    if len(answer_dict['aliases']) > 0:
                        answer = answer_dict['aliases'][-1]
                        popular_pid_values[pid][answer] += 1

    # For each PID, sort by count, then take the top 20
    for pid in popular_pid_values:
        popular_pid_values[pid] = sorted(popular_pid_values[pid],
                                         key=popular_pid_values[pid].get,
                                         reverse=True)[:20]

    output_file = join(dirname(good_pids_file), 'popular_pid_values.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(popular_pid_values, sort_keys=True,
                           indent=4, ensure_ascii=False))


def add_pid_names(qid_to_pids, pid_to_label_file):
    print('Adding PID names')
    pid_to_label = json.load(open(pid_to_label_file, encoding='utf-8'))

    for qid in tqdm(qid_to_pids):
        for pid in qid_to_pids[qid]:
            qid_to_pids[qid][pid] = {
                'property': pid_to_label[pid],
                'values': qid_to_pids[qid][pid],
            }

    return qid_to_pids


def remove_qids(qid_to_pids, good_pids_file):
    """ Remove QID if WikiData type doesn't match list of accepted types """
    print('Removing QIDs')

    # Get set of good QID types to filter down the QIDs to save storage/memory
    good_qid_types = json.load(open(good_pids_file, encoding='utf-8'))

    for qid in tqdm(list(qid_to_pids.keys())):
        pids_dict = qid_to_pids[qid]

        # Only keep QIDs where its type matches a list of accepted types
        qid_types = set([e['qid'] for e in pids_dict.get('P31', {}).get('values', [])])
        if len(qid_types.intersection(good_qid_types)) == 0:
            del qid_to_pids[qid]

    return qid_to_pids


def load_qid_to_pids(qid_to_pids_file, qid_to_aliases_file,
                     pid_to_label_file, good_pids_file):
    print('Loading QID to PID mappings...')
    qid_to_pids = json.load(open(qid_to_pids_file, encoding='utf-8'))

    qid_to_pids = add_pid_value_entity_types(qid_to_pids)
    qid_to_pids = add_pid_value_aliases(qid_to_pids, qid_to_aliases_file)
    get_most_popular_pid_values(qid_to_pids, good_pids_file)
    qid_to_pids = add_pid_names(qid_to_pids, pid_to_label_file)
    qid_to_pids = remove_qids(qid_to_pids, good_pids_file)

    return qid_to_pids


def merge_aliases_and_pids(alias_to_qids_file, qid_to_pids):
    print('Merging aliases with PIDs...')
    alias_dicts = []
    for alias, qids in tqdm(json.load(open(alias_to_qids_file, encoding='utf-8')).items()):
        alias_dict = {
            'name': alias,
            'qids': {
                e['qid']: {
                    'pids': qid_to_pids[e['qid']],
                    'pop': e['pop'],
                    'is_topdog': e['is_topdog'],
                    'entity_types': [e['qid'] for e in
                                     qid_to_pids[e['qid']]['P31']['values']]
                } for e in qids if e['qid'] in qid_to_pids
            },
        }

        # Append alias dictionary if this alias has more than 1 QID
        if len(alias_dict['qids']) > 1:
            # And if the gap in popularity between topdog and underdog is > 10%
            pops = [alias_dict['qids'][qid]['pop'] for qid in alias_dict['qids']]
            pops = sorted(pops, reverse=True)
            percent_diff = 100 * (pops[0] - pops[1]) / (0.5 * pops[0] + 0.5 * pops[1])
            if percent_diff >= 10:
                alias_dicts.append(alias_dict)

    return alias_dicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    alias_to_qids_file = join(WIKIDATA_DIR, "alias_to_qids.json")
    qid_to_aliases_file = join(WIKIDATA_DIR, "qid_to_aliases.json")
    qid_to_pids_file = join(WIKIDATA_DIR, "qid_to_pids.json")
    pid_to_label_file = join(WIKIDATA_DIR, "pid_to_label.json")
    good_pids_file = join("amber_sets", args.collection, "good_pids.json")

    output_file = join("amber_sets", args.collection, "tmp/polysemous_names.jsonl")

    # Loads a dictionary that maps from QIDs to PIDs
    qid_to_pids = load_qid_to_pids(qid_to_pids_file, qid_to_aliases_file,
                                   pid_to_label_file, good_pids_file)

    # Load a list of dictionaries that maps from aliases to QIDs to PIDs
    alias_dicts = merge_aliases_and_pids(alias_to_qids_file, qid_to_pids)

    with open(output_file, 'w', encoding='utf-8') as f:
        for d in tqdm(alias_dicts):
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
