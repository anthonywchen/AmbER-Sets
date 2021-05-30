""" Writes PIDs that are unique to a QID in a set of QIDs (maps to an alias)

Given a mapping from an alias (i.e. a string) to QIDs and PIDs for each QID, we
aim to find the PIDs that are unique to a QID in a set of QIDs.

For example, given the alias "Michael Jordan" and associated QIDs {Q41421,
Q3308007, Q3308285}, a unique PID would be P185 (doctoral students) because
it is a property of Q3308285 (Michael I Jordan, the professor).
"""
import argparse
import json
from collections import defaultdict
from hashlib import md5
from os.path import join

import jsonlines


def get_unique_pids(alias_dicts):
    for d in alias_dicts:
        for qid in d['qids']:
            # Iterate through PIDs, deleting them if its not unique for alias.
            for pid in list(d['qids'][qid]['pids'].keys()):
                pid_is_unique = True

                for other_qid in d['qids']:
                    if other_qid == qid:
                        continue

                    # If the current PID is found in other QID, then delete it
                    if pid in d['qids'][other_qid]['pids']:
                        del d['qids'][other_qid]['pids'][pid]
                        pid_is_unique = False

                # If the current PID isn't unique, then delete it from QID
                if not pid_is_unique:
                    del d['qids'][qid]['pids'][pid]

    return alias_dicts


def filter_aliases(alias_dicts):
    """ Keep aliases that have at least 2 QIDs with PIDS AND the HEAD QID
    has PIDs """
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


def add_amber_ids(alias_dicts):
    """ For each (alias, QID, PID), we add a unique AmbER ID """
    for d in alias_dicts:
        name = d['name']
        for qid in d['qids']:
            for pid in d['qids'][qid]['pids']:
                hash_input = repr([name, qid, pid]).encode()
                d['qids'][qid]['pids'][pid]['amber_id'] = md5(hash_input).hexdigest()

    return alias_dicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    input_data_file = join("amber_sets", args.collection, "tmp/filtered_uninformative_pids.jsonl")
    output_data_file = join("amber_sets", args.collection, "tmp/amber_set_tuples.jsonl")

    alias_dicts = [line for line in jsonlines.open(input_data_file)]
    alias_dicts = get_unique_pids(alias_dicts)
    alias_dicts = filter_aliases(alias_dicts)
    alias_dicts = add_amber_ids(alias_dicts)

    # Sort list of alias dictionaries by the alias
    alias_dicts = sorted(alias_dicts, key=lambda k: k['name'])

    with open(output_data_file, 'w', encoding='utf-8') as f:
        for d in alias_dicts:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
