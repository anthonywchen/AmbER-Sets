import ujson as json
import tqdm

from collections import defaultdict


def construct_answer_dictionary(value_dict):
    if value_dict is None:
        return None
    type = value_dict["type"]

    if type == "wikibase-entityid":
        answer_dict = {"type": "entityid", "qid": value_dict["value"]["id"]}
    elif type == "quantity":
        answer_dict = {
            "type": type,
            "amount": value_dict["value"]["amount"],
            "unit": value_dict["value"]["unit"],
        }
    else:  # Skip answers that are strings, GPS location, etc.
        answer_dict = None

    return answer_dict


def map_qids_to_pids():
    pop_dict = json.load(open("processed_files/qid_popularities.json"))
    qids_to_pids = defaultdict(lambda: defaultdict(list))

    with open("pids.tsv", encoding="utf-8") as f:
        for line in tqdm.tqdm(f):
            qid, pid, value_dict = line.split("\t")
            if qid not in pop_dict:
                continue

            # For the values of the PID, construct an answer dictionary
            try:
                value_dict = json.loads(value_dict)
                answer_dict = construct_answer_dictionary(value_dict)
                if answer_dict:
                    qids_to_pids[qid][pid].append(answer_dict)
            except:
                pass

    return qids_to_pids


def filter_useless_qids(qids_to_pids):
    """Removes QIDs that only have one PID"""
    print("Removing useless QIDs...")
    for qid in tqdm.tqdm(list(qids_to_pids.keys())):
        pids = list(qids_to_pids[qid].keys())
        if len(pids) == 1:
            del qids_to_pids[qid]

    return qids_to_pids


def main():
    qids_to_pids = map_qids_to_pids()
    qids_to_pids = filter_useless_qids(qids_to_pids)

    with open("processed_files/qid_to_pids.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(qids_to_pids, ensure_ascii=False))


if __name__ == "__main__":
    main()
