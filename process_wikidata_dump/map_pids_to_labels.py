from collections import defaultdict

import ujson as json
import tqdm


def main():
    pid_to_label = defaultdict(str)

    with open("labels.tsv", encoding="utf-8") as labels_file:
        for line in tqdm.tqdm(labels_file):
            (locale, label, pid) = line.strip().split("\t")

            # If `pid` is a PID (i.e. first char is "P")
            if pid[0] == "P" and locale == "en":
                pid_to_label[pid] = label

    output_file = "processed_files/pid_to_label.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(pid_to_label, ensure_ascii=False))


if __name__ == "__main__":
    main()
