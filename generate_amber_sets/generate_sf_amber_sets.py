""" Generates slot filling data from AmbER tuples


"""
import argparse
import hashlib
import json
from os.path import join

import jsonlines
from tqdm import tqdm


def create_sf_instance(entity_name, pid_name):
    sf_input = entity_name + ' [SEP] ' + pid_name
    sf_hashlib = hashlib.md5(sf_input.encode('utf-8')).hexdigest()
    return sf_input, sf_hashlib


def generate_slot_filling_dataset(amber_set_tuples):
    amber_sets = []

    for d in tqdm(amber_set_tuples):
        name = d['name']
        amber_set = {'name': name, 'qids': {}}

        for qid, qid_dict in d['qids'].items():
            amber_set['qids'][qid] = {
                'is_topdog': qid_dict['is_topdog'],
                'pop': qid_dict['pop'],
                'wikipedia': qid_dict['wikipedia'],
                'queries': []
            }

            # Update `pid_dict` with slot filling instances
            pid_dict = qid_dict['pids']
            for pid in pid_dict:
                pid_name = pid_dict[pid]['property']
                sf_input, sf_hashlib = create_sf_instance(name, pid_name)
                pid_dict[pid]['input'] = sf_input
                pid_dict[pid]['input_id'] = sf_hashlib

                values, additional_values = [], []
                for d in pid_dict[pid]['values']:
                    values += d['aliases']
                    additional_values += d['additional_aliases']

                amber_set['qids'][qid]['queries'].append({
                    'id': pid_dict[pid]['amber_id'] + '=' + sf_hashlib,
                    'input': sf_input,
                    'output': [{
                        'answer': values + additional_values,
                        'provenance': pid_dict[pid]['provenance'],
                        'meta': {'values': values,
                                 'additional_values': additional_values}
                    }],
                    'meta': {
                        'pid': pid
                    }
                })
        amber_sets.append(amber_set)

    return amber_sets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--collection")
    args = parser.parse_args()

    input_data_file = join("amber_sets", args.collection, "amber_set_tuples.jsonl")
    output_data_file = join("amber_sets", args.collection, "sf/amber_sets.jsonl")

    amber_set_tuples = [line for line in jsonlines.open(input_data_file)]

    amber_sets = generate_slot_filling_dataset(amber_set_tuples)

    with open(output_data_file, 'w', encoding='utf-8') as f:
        for d in amber_sets:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
