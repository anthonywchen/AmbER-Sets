""" Helper functions for computing end-to-end metrics """
import collections
import re
import string


#### Downstream Metrics
def normalize_answer(s):
    """Lower text and remove punctuation, articles and extra whitespace."""
    def remove_articles(text):
        regex = re.compile(r'\b(a|an|the)\b', re.UNICODE)
        return re.sub(regex, ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        # Replace dash with a space
        text = text.replace('-', ' ')
        # Replace other punctuation with empty string
        for punc in string.punctuation:
            text = text.replace(punc, '')
        return text

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s):
    if not s: return []
    return normalize_answer(s).split()


def em(ans, pred):
    return int(normalize_answer(ans) == normalize_answer(pred))


def f1(ans, pred):
    ans_tokens = get_tokens(ans)
    pred_tokens = get_tokens(pred)
    common = collections.Counter(ans_tokens) & \
             collections.Counter(pred_tokens)

    num_same = sum(common.values())
    if num_same == 0:
        return 0

    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(ans_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

####
def get_subset_scores(amber_sets, raw_metrics, head_subset: bool):
    raw_subset_metrics = collections.defaultdict(list)

    for amber_set in amber_sets:
        for qid in amber_set['qids']:
            if amber_set['qids'][qid]['is_topdog'] == head_subset:
                for query_dict in amber_set['qids'][qid]['queries']:
                    query_id = query_dict['id']

                    for metric in raw_metrics:
                        # This statement is because entity confusion is not
                        # computed over every query.
                        if query_id in raw_metrics[metric]:
                            raw_subset_metrics[metric].append(raw_metrics[metric][query_id])

    return {
        metric: 100*sum(raw_subset_metrics[metric])/len(raw_subset_metrics[metric])
        for metric in raw_subset_metrics
    }