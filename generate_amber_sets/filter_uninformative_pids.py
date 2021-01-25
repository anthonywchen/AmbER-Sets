""" Filters out PIDs that aren't in specified list of good PIDs.

1. Remove PIDs that aren't in a list of "good PIDs".
2. Remove QIDs that dont have any PIDs.
2. Remove aliases that don't have at least 2 QIDs after step 2.
"""
import argparse
import itertools
from os.path import join
from tqdm import tqdm
from collections import defaultdict

import jsonlines
import ujson as json


def filter_pids(input_data_file, good_pids_file):
    """ Delete all PIDs that aren't in `GOOD_PIDS_FILE` """
    good_pids_dict = json.load(open(good_pids_file))

    alias_dicts = []
    for d in tqdm(jsonlines.open(input_data_file)):
        for qid, qid_dict in d['qids'].items():
            qid_types = set([type for type in qid_dict['entity_types']
                             if type in good_pids_dict])

            # Filter inter PIDS
            inter_pids = list(itertools.chain(*[good_pids_dict[type]['inter']
                                                for type in qid_types]))
            inter_pids = [x for x in inter_pids if inter_pids.count(x) == 1]

            intra_pids = list(itertools.chain(*[good_pids_dict[type]['intra']
                                                for type in qid_types]))

            good_pids = inter_pids + intra_pids

            for pid in list(qid_dict['pids'].keys()):
                if pid not in good_pids:
                    del d['qids'][qid]['pids'][pid]

        alias_dicts.append(d)

    return alias_dicts


def filter_aliases(alias_dicts):
    """ Keep aliases that have at least 2 QIDs with unique PIDS """
    filtered_alias_dicts = []

    for d in alias_dicts:
        good_qid_count = 0
        for qid_dict in d['qids'].values():
            if len(qid_dict['pids']) > 0:
                good_qid_count += 1

        if good_qid_count >= 2:
            filtered_alias_dicts.append(d)

    return filtered_alias_dicts


def statistics(alias_dicts, output_stats_file):
    """ Writes out the number of aliases, and QIDs per alias"""
    counts = defaultdict(int)

    for d in alias_dicts:
        num_qids = len([1 for qid_dict in d['qids'].values()
                        if len(qid_dict['pids']) > 0])
        counts[num_qids] += 1

    with open(output_stats_file, 'w') as f:
        for k, v in counts.items():
            f.write("%4d aliases with %d QIDs with good PID\n" % (v, k))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    good_pids_file = join("amber_sets", args.collection, "good_pids.json")
    input_data_file = join("amber_sets", args.collection, "tmp/polysemous_names.jsonl")
    output_data_file = join("amber_sets", args.collection, "tmp/filtered_uninformative_pids.jsonl")

    alias_dicts = filter_pids(input_data_file, good_pids_file)
    alias_dicts = filter_aliases(alias_dicts)

    with open(output_data_file, 'w', encoding='utf-8') as f:
        for line in alias_dicts:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
