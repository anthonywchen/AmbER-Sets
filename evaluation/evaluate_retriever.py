""" Evaluates AmbER predictions """
import argparse
import json
from collections import defaultdict
from os.path import join

import jsonlines

from evaluation.utils import get_subset_scores


def extract_page_ids(pages):
    def get_page_ids(pages):
        return [page['wikipedia_id'] for page in pages]

    def remove_duplicates(page_ids):
        seen_ids = set()
        tmp = []
        for o in page_ids:
            if o not in seen_ids:
                seen_ids.add(o)
                tmp.append(o)
        return tmp

    def remove_errors(page_ids):
        return [id for id in page_ids if id != 'None']

    return remove_duplicates(remove_errors(get_page_ids(pages)))


def accuracy_at_k(gold_pages, retrieved_pages, k):
    gold_ids = extract_page_ids(gold_pages)
    retrieved_ids = extract_page_ids(retrieved_pages)[:k]
    return int(len(set(gold_ids).intersection(retrieved_ids)) > 0)


def get_raw_metrics(amber_sets, predictions, k):
    """ Computes metric scores at a per-query level

    For each query, this function computes accuracy@k and entity_confusion@k.
    """
    raw_metrics = defaultdict(dict)

    for amber_set in amber_sets:
        for qid in amber_set['qids']:
            # Iterate through queries for current entity
            for query_dict in amber_set['qids'][qid]['queries']:
                query_id = query_dict['id']
                if query_id not in predictions:
                    print('Missing prediction for %s' % query_id)

                gold_pages = query_dict['output']['provenance']
                retrieved_pages = predictions[query_id]['output']['provenance']

                raw_metrics['accuracy'][query_id] = accuracy_at_k(gold_pages, retrieved_pages, k)

    return raw_metrics


def get_consistency(amber_sets, raw_metrics):
    """ Consistency measures % of AmbER sets where all queries were 'correct'

    By correct, we mean that the gold document was retrieved (i.e, accuracy==1)
    """
    consistency_scores = []

    for amber_set in amber_sets:
        # Get all query IDs for the AmbER set
        query_ids = [query_dict['id'] for qid in amber_set['qids']
                     for query_dict in amber_set['qids'][qid]['queries']]

        # Get accuracy scores for all query IDs
        scores = [raw_metrics['accuracy'][query_id] for query_id in query_ids]

        # If all accuracy scores were `1`, then the retriever was consistent
        is_consistent = int(len(scores) == sum(scores))
        consistency_scores.append(is_consistent)

    # Average consistency across AmbER sets
    consistency = 100*sum(consistency_scores)/len(consistency_scores)
    return consistency


def evaluate_predictions(amber_sets: list, predictions: dict, k: int):
    # `raw_metrics` are the individual scores for each query
    raw_metrics = get_raw_metrics(amber_sets, predictions, k)
    # `metrics` aggregates the raw metrics into average scores
    metrics = {
        metric: 100*sum(raw_metrics[metric].values())/len(raw_metrics[metric].values())
        for metric in raw_metrics
    }
    # `consistency` is the % of AmbER sets where all queries in the set were retrieved
    metrics['consistency'] = get_consistency(amber_sets, raw_metrics)

    # For all scores in `metrics`, we split them based on head/tail entities
    metrics['head'] = get_subset_scores(amber_sets, raw_metrics, True)
    metrics['tail'] = get_subset_scores(amber_sets, raw_metrics, False)

    return metrics, raw_metrics


def load_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--annotations_file",
        help="Path to the AmbER sets file",
        required=True
    )
    parser.add_argument(
        "-p", "--predictions_file",
        help="Path to retrieved documents file corresponding to AmbER sets",
        required=True
    )
    parser.add_argument(
        "-k", "--k",
        help="Used to compute accuracy@k. By default, we compute accuracy@1.",
        type=int,
        default=1
    )
    parser.add_argument(
        "-m", "--metrics_dir",
        required=False,
        help="The directory to which we write out the metrics."
             " If not provided, we print metrics."
    )
    return parser.parse_args()


def main():
    args = load_args()
    amber_sets = list(jsonlines.open(args.annotations_file))
    predictions = {l['id']: l for l in jsonlines.open(args.predictions_file)}

    metrics, raw_metrics = evaluate_predictions(amber_sets, predictions, args.k)

    if args.metrics_dir:
        metrics_file = join(args.metrics_dir, f'metrics@{args.k}.json')
        with open(metrics_file, 'w') as f:
            f.write(json.dumps(metrics, indent=4))

        raw_metrics_file = join(args.metrics_dir, f'raw_metrics@{args.k}.json')
        with open(raw_metrics_file, 'w') as f:
            f.write(json.dumps(raw_metrics, indent=4))
    else:
        print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    main()
