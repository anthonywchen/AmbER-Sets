#!/usr/bin/python3
import argparse
import collections
import json
import os
import statistics
import typing

import jsonlines

from evaluation.utils import get_subset_scores


def extract_page_ids(pages: typing.List[dict]) -> typing.List[str]:
    """Extracts a list of page IDs from a list of Wikipedia page dictionaries.

    Extracts a certain key from a list of Wikipedia page dictionaries. Also does some
    filtering on the page IDs by removing duplicates. This is so that retrievers are
    comparable. Otherwise, retrievers like DPR which split an article into passages
    would be penalized against retrievers like TF-IDF which do not.

    Arguments:
        pages: ``list`` A list of dictionaries where each dictionary contains
            information about a single Wikipedia page.
    Returns:
        page_ids: ``list`` A list of page IDs where the ID was a key in the page
            dictionary.
    """
    # Extract list of page IDs from list of Wikipedia dictionaries
    page_ids = [page['wikipedia_id'] for page in pages]

    # Remove duplicates in the list of page IDs while preserving order
    seen_ids = set()
    tmp = []
    for o in page_ids:
        if o not in seen_ids:
            seen_ids.add(o)
            tmp.append(o)
    page_ids = tmp

    # Fix errors by removing "None" page IDs
    page_ids = [id for id in page_ids if id != 'None']

    return page_ids


def accuracy_at_k(
    gold_pages: typing.List[dict],
    retrieved_pages: typing.List[dict],
    k: int
) -> int:
    """Computes the retrieval accuracy@k metric.

    Arguments:
         gold_pages: ``list`` List of gold pages.
         retrieved_pages: ``list`` List of retrieved pages.
         k: ``int`` Top retrieved pages to compute accuracy over.
    Returns:
        ``int`` A 0 or 1 score if a gold page was in the top-k retrieved docs.
    """
    gold_ids = extract_page_ids(gold_pages)
    retrieved_ids = extract_page_ids(retrieved_pages)[:k]
    return int(len(set(gold_ids).intersection(retrieved_ids)) > 0)


def get_raw_metrics(
    amber_sets: typing.List[dict],
    predictions: typing.Dict[str, dict],
    k: int
) -> typing.Dict[str, int]:
    """Computes accuracy scores at a per-query level.

    Arguments:
        amber_sets: ``list`` List of AmbER sets.
        predictions: ``dict`` Dictionary of per-query predictions.
        k: ``int`` Top retrieved pages to compute accuracy over.
    Returns:
        raw_metrics: ``dict`` Mapping from query ID to a score for that query.
    """
    raw_metrics = collections.defaultdict(dict)

    for amber_set in amber_sets:
        for qid in amber_set['qids']:
            # Iterate through queries for current entity
            for query_dict in amber_set['qids'][qid]['queries']:
                query_id = query_dict['id']
                if query_id not in predictions:
                    print('Missing prediction for %s' % query_id)

                gold_pages = query_dict['output']['provenance']
                retr_pages = predictions[query_id]['output']['provenance']
                raw_metrics['accuracy'][query_id] = accuracy_at_k(gold_pages, retr_pages, k)

    return raw_metrics


def consistency_at_k(
    amber_sets: typing.List[dict],
    raw_metrics: typing.Dict[str, int]
) -> float:
    """Computes the set-level consistency metric.

    Consistency measures % of AmbER sets where all queries had a gold document
    correctly retrieved (i.e. the accuracy metric).

    Arguments:
        amber_sets: ``list`` List of AmbER sets
        raw_metrics: ``dict`` Dictionary of query-level accuracy scores
    Returns:
        consistency: ``float`` % of sets where all queries were correctly retrieved
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
    consistency = 100*statistics.mean(consistency_scores)
    return consistency


def evaluate_retriever(
    annotations_file: str,
    predictions_file: str,
    k: int,
    metrics_dir: str = None
) -> None:
    """Computes accuracy (overall and by head/tail) and consistency metrics.

    Computes accuracy metrics on all AmbER sets as well as on head/tail query splits.
    We also compute the set-level consistency metric. By default, the metrics are
    printed, however, by providing a metrics directory, the metrics are written to
    file.

    Arguments:
        annotations_file: ``str`` Path to annotations file.
        predictions_file: ``str`` Path to retrieval predictions file.
        k: ``int`` Top-k documents to do evaluation over.
        metrics_dir: ``str`` (Optional) Directory to write metric scores.
    """
    amber_sets = list(jsonlines.open(annotations_file))
    predictions = {l['id']: l for l in jsonlines.open(predictions_file)}

    # `raw_metrics` are the individual scores for each query
    raw_metrics = get_raw_metrics(amber_sets, predictions, k)

    # `metrics` aggregates the raw metrics into average scores
    metrics = {m: 100*statistics.mean(raw_metrics[m].values()) for m in raw_metrics}

    # For the scores in `metrics`, we split them based on head/tail entities
    metrics['head'] = get_subset_scores(amber_sets, raw_metrics, True)
    metrics['tail'] = get_subset_scores(amber_sets, raw_metrics, False)

    # `consistency` is the % of AmbER sets where all queries in the set were retrieved
    metrics['consistency'] = consistency_at_k(amber_sets, raw_metrics)

    if metrics_dir:
        metrics_file = os.path.join(metrics_dir, f'metrics@{k}.json')
        with open(metrics_file, 'w') as f:
            f.write(json.dumps(metrics, indent=4))

        raw_metrics_file = os.path.join(metrics_dir, f'raw_metrics@{k}.json')
        with open(raw_metrics_file, 'w') as f:
            f.write(json.dumps(raw_metrics, indent=4))
    else:
        print(json.dumps(metrics, indent=4))


def main():
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
    args = parser.parse_args()

    evaluate_retriever(
        args.annotations_file,
        args.predictions_file,
        args.k,
        args.metrics_dir
    )


if __name__ == "__main__":
    main()
