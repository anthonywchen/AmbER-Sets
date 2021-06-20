import ujson as json
import math
import tqdm
from collections import defaultdict


def main():
    pop_dict = defaultdict(int)

    # Load page counts for QIDs
    with open("qids_with_pagecounts.tsv") as qid_pops:
        for line in tqdm.tqdm(qid_pops):
            (locale_wiki, qid, count) = line.strip().split("\t")
            locale = locale_wiki.split("#")[0].replace("wiki", "")

            # We're only working with the English instances
            if locale == "en":
                # The popularity is the log of the page counts.
                pop_dict[qid] = math.log10(int(count))

    with open("processed_files/qid_popularities.json", "w") as f:
        f.write(json.dumps(pop_dict))


if __name__ == "__main__":
    main()
