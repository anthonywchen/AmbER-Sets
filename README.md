# AmbER Sets
[**Data**](#Data) |
[**Citation**](#Citation) | [**License**](#License) | [**Paper**](https://arxiv.org/abs/2106.06830) | [**Landing Page**](https://machinelearning.apple.com/research/evaluating-entity-disambiguation-amber)

**AmbER** (**Amb**igiuous **E**ntity **R**etrieval) sets are collections of queries which individually test a retriever's ability to do entity disambiguation.
Each AmbER set contains queries about entities which share a name. 
See our [**ACL 2021 paper**](https://arxiv.org/abs/2106.06830) to learn more about AmbER sets.

### Environment Setup
To install the required packages, run 
```
pip install requirements.txt
```

If you use Poetry, you can alternatively run 
```
poetry install
```

### Generating AmbER Sets
AmbER sets are generated from Wikidata tuples and are aligned to a Wikipedia dump. 
To see replicate our pipeline, see the [generate_amber_sets](generate_amber_sets) directory.
This step is optional as we provide the output of this step in the next section.

### Data
The output of the generation pipeline is provided in the [amber_sets](amber_sets) directory.
See this directory for more information on the data.

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
The AmbER data is licensed under the [Creative Commons Zero v1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/).