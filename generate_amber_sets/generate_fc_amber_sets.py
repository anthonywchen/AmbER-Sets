""" Generates fact checking data from AmbER tuples with declarative templates


"""
import argparse
import hashlib
import json
import random
from os.path import join

import datasets
import jsonlines
from tqdm import tqdm

from align_amber_tuples_to_wikipedia import answer_in_doc

random.seed(0)
wikipedia = datasets.load_dataset("kilt_wikipedia")['full']


def fill_template(template, entity, object):
    """ Fill in template with an entity name.
    Also returns the hashlib of the query as a query ID.
    """
    query = template.replace('$entity', entity).replace('$object', object)
    assert entity in query and object in query
    query_hashlib = hashlib.md5(query.encode('utf-8')).hexdigest()
    return query, query_hashlib


def generate_true_instance(template, entity_name, pid_dict):
    for value in pid_dict['values']:
        for answer in value['aliases']:
            for wikipedia_dict in pid_dict['provenance']:
                kilt_idx = wikipedia_dict['kilt_idx']
                doc = ' '.join(wikipedia[kilt_idx]['text']['paragraph'])
                doc = ' '.join(doc.split()[:350])

                # Test if answer is in the current Wikipedia page
                if answer_in_doc(answer, doc):
                    answer = value['aliases'][-1]
                    query, query_hashlib = fill_template(template, entity_name, answer)
                    return query, query_hashlib


def generate_false_instance(template, entity_name, pid_dict, other_answers):
    answers = []
    for value in pid_dict['values']:
        if len(value['aliases']):
            answers.append(value['aliases'][-1])

    for wrong_answer in other_answers:
        if wrong_answer not in answers:
            query, query_hashlib = fill_template(template, entity_name, wrong_answer)
            return query, query_hashlib


def generate_queries(amber_set_tuples, popular_pid_values, templates):
    amber_sets = []

    for d in tqdm(amber_set_tuples):
        name = d['name']
        amber_set = {'name': name, 'qids': {}}

        for qid, qid_dict in d['qids'].items():
            amber_set['qids'][qid] = {
                'is_head': qid_dict['is_head'],
                'pop': qid_dict['pop'],
                'wikipedia': qid_dict['wikipedia'],
                'queries': []
            }

            pid_dict = qid_dict['pids']
            # Update `pid_dict` with a query generated from templates
            for pid in list(pid_dict.keys()):
                # Grab a random template.
                # Set seed using QID & PID so we always grab the same template
                random.seed(int(qid[1:] + pid[1:]))
                template = random.choice(templates[pid])

                # Generate queries
                true_query, true_query_id = \
                    generate_true_instance(template, name, pid_dict[pid])

                false_query, false_query_id = \
                    generate_false_instance(template, name, pid_dict[pid], popular_pid_values[pid])

                # Get aliases
                values = []
                additional_values = []
                for d in pid_dict[pid]['values']:
                    values += d['aliases']
                    additional_values += d['additional_aliases']

                # Append true fact
                amber_set['qids'][qid]['queries'].append({
                    'id':   pid_dict[pid]['amber_id'] + '=' + true_query_id,
                    'input': true_query,
                    'output': [{
                        'answer': 'SUPPORTS',
                        'provenance': pid_dict[pid]['provenance'],
                        'meta': {'values': values,
                                 'additional_values': additional_values}
                    }],
                    'meta': {
                        'pid': pid
                    }
                })

                # Append false fact
                amber_set['qids'][qid]['queries'].append({
                    'id': pid_dict[pid]['amber_id'] + '=' + false_query_id,
                    'input': false_query,
                    'output': [{
                        'answer': 'REFUTES',
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
    popular_pid_values_file = join("amber_sets", args.collection, "popular_pid_values.json")
    templates_file = join("amber_sets", args.collection, "fc_templates.json")
    output_data_file = join("amber_sets", args.collection, "fc/amber_sets.jsonl")

    amber_set_tuples = [line for line in jsonlines.open(input_data_file)]
    popular_pid_values = json.load(open(popular_pid_values_file, encoding='utf-8'))
    templates = json.load(open(templates_file))

    amber_sets = generate_queries(amber_set_tuples, popular_pid_values, templates)

    with open(output_data_file, 'w', encoding='utf-8') as f:
        for d in amber_sets:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
