import ujson as json
import tqdm
from collections import defaultdict


def main():
    pop_dict = json.load(open('processed_files/qid_popularities.json'))
    alias_dict = defaultdict(list)

    with open('cands.tsv', encoding='utf-8') as cands_file:
        for line in tqdm.tqdm(cands_file):
            (locale, alias, qid) = line.strip().split('\t')

            if qid in pop_dict and locale == 'en':
                alias_dict[alias].append({
                    'qid': qid,
                    'pop': pop_dict[qid]
                })

    # For each alias, mark the head entity
    for alias in list(alias_dict.keys()):
        top_pop = max([d['pop'] for d in alias_dict[alias]])

        for i in range(len(alias_dict[alias])):
            if alias_dict[alias][i]['pop'] == top_pop:
                alias_dict[alias][i]['is_head'] = True
            else:
                alias_dict[alias][i]['is_head'] = False


    output_file = 'processed_files/alias_to_qids.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(alias_dict, ensure_ascii=False))


if __name__ == "__main__":
    main()
