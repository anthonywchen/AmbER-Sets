# AmbER Sets
[**Data**](#Data) |
[**Citation**](#Citation) | [**License**](#License) | [**Paper**](https://arxiv.org/abs/2106.06830) | [**Landing Page**](https://machinelearning.apple.com/research/evaluating-entity-disambiguation-amber)

**AmbER** (**Amb**igiuous **E**ntity **R**etrieval) sets are collections of queries which individually test a retriever's ability to do entity disambiguation.
Each AmbER set contains queries about entities which share a name. 
See our [**ACL-IJNLP 2021 paper "Evaluating Entity Disambiguation and the Role of Popularity in Retrieval-Based NLP"**](https://arxiv.org/abs/2106.06830) to learn more about AmbER sets.

### Environment Setup
To install the required packages, run `pip install -r requirements.txt`

Alternatively, you can use Poetry by running `poetry install` followed by `poetry shell` to activate the environment.

### AmbER Sets Data
AmbER sets are generated from Wikidata tuples and are aligned to a Wikipedia dump. 
To see reproduce our pipeline, see the [generate_amber_sets](generate_amber_sets) directory.
This step is optional as the generated AmbER sets are provided in the [data](data) directory.

### AmbER Sets Evaluation
To evaluate your retriever's predictions on AmbER sets, see the [evaluation](evaluation) directory.

### Citation
```bibtex
@inproceedings{chen-etal-2021-evaluating,
    title = "Evaluating Entity Disambiguation and the Role of Popularity in Retrieval-Based {NLP}",
    author = "Chen, Anthony  and
      Gudipati, Pallavi  and
      Longpre, Shayne  and
      Ling, Xiao  and
      Singh, Sameer",
    booktitle = "Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.acl-long.345",
    doi = "10.18653/v1/2021.acl-long.345",
    pages = "4472--4485",
}
```

### License
The AmbER sets data in the [data](data) directory is licensed under the [Creative Commons Zero v1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/). All code provided in this respository is licensed under the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0.html).

### Contact
For questions or comments on AmbER sets, please open a pull request or issue or contact Anthony Chen at <anthony.chen@uci.edu>.
