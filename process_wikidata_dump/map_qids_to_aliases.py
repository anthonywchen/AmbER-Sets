from collections import defaultdict

import ujson as json
import tqdm


def main():
    pop_dict = json.load(open("processed_files/qid_popularities.json"))
    qids_to_aliases = defaultdict(list)

    with open("cands.tsv", encoding="utf-8") as cands_file:
        for line in tqdm.tqdm(cands_file):
            (locale, alias, qid) = line.strip().split("\t")

            if qid in pop_dict and locale == "en":
                qids_to_aliases[qid].append(alias)

    output_file = "processed_files/qid_to_aliases.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(qids_to_aliases, ensure_ascii=False))


if __name__ == "__main__":
    main()
