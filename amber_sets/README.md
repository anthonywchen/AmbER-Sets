# AmbER Sets
AmbER sets for AmbER-*H* and AmbER-*N* are stored under the `human/` and `nonhuman` directories respectively. 

### Files
Each collection directory has the following files:
* `entity_types_to_distinguishing_properties.json`: Contains the entity types that are allowed for each collection as well as the properties that are considered distinguishing for each entity type. 

* `fc_templates.json`: Contains fact checking templates for each property..

* `qa_templates.json`: Contains question answering templates for each property.

* `amber_set_tuples.jsonl`: Contains the AmbER set tuples which are used to instantiate task specific instances.

* `<task>/amber_sets.jsonl`: Contains the task-specific instances where the task is either `fc` (fact checking), `qa` (question answering), or `sf` (slot filling).


### Structure of an AmbER Set
AmbER sets all contain a similar structure. 
Here is an example AmbER set for the name "Abe Lincoln" for the question answering task.

<details>
<summary>Click to expand</summary>

```JSON
{
    "name": "Abe Lincoln",
    "qids": {
        "Q91": {
            "is_head": true,
            "popularity": 5.1942478558575464,
            "wikipedia": [
                {
                    "wikipedia_id": "307",
                    "title": "Abraham Lincoln"
                },
                {
                    "wikipedia_id": "42390831",
                    "title": "Abraham Lincoln's Life"
                }
            ],
            "queries": [
                {
                    "id": "6981ec17f0438a7cc94fff740cc9bb23=f12393b7ba0631871ea7126dd5127772",
                    "input": "Which battle did Abe Lincoln fight in?",
                    "output": {
                        "answer": [
                            "Black Hawk War",
                            "American Civil War",
                            "American Civil War",
                            "Civil War",
                            "The Civil War",
                            "U.S. Civil War",
                            "US Civil War",
                            "United States Civil War",
                            "War Between the States",
                            "War of the Rebellion"
                        ],
                        "provenance": [
                            {
                                "wikipedia_id": "307",
                                "title": "Abraham Lincoln"
                            }
                        ],
                        "meta": {
                            "values": [
                                "Black Hawk War",
                                "American Civil War",
                                "American Civil War",
                                "Civil War",
                                "The Civil War",
                                "U.S. Civil War",
                                "US Civil War",
                                "United States Civil War",
                                "War Between the States",
                                "War of the Rebellion"
                            ],
                            "additional_values": []
                        }
                    },
                    "meta": {
                        "pid": "P607"
                    }
                }
            ]
        },
        "Q4666410": {
            "is_head": false,
            "popularity": 1.7781512503836436,
            "wikipedia": [
                {
                    "wikipedia_id": "17039796",
                    "title": "Abe Lincoln (musician)"
                }
            ],
            "queries": [
                {
                    "id": "edf1ff070a3cbd5fdee738262db8e740=44a67ee4dd88179d1147102e9753a5fa",
                    "input": "What musical instrument does Abe Lincoln play?",
                    "output": {
                        "answer": [
                            "trombone",
                            "slide trombone",
                            "tenor trombone",
                            "valve trombone"
                        ],
                        "provenance": [
                            {
                                "wikipedia_id": "17039796",
                                "title": "Abe Lincoln (musician)"
                            }
                        ],
                        "meta": {
                            "values": [
                                "trombone",
                                "slide trombone",
                                "tenor trombone",
                                "valve trombone"
                            ],
                            "additional_values": []
                        }
                    },
                    "meta": {
                        "pid": "P1303"
                    }
                }
            ]
        }
    }
}
```
</details>

Here are some descriptions of important fields in each AmbER sets:
* `qids`: `Dict[str]` Maps QIDs (entity IDs) to each entities' associated queries.

* `is_head`: `Bool` Whether each entity (QID) is the head entity or not.

* `popularity`: `float` Each entities popularity (log of number of page views).

* `wikipedia`: `List[Dict]` The Wikipedia pages in the KILT dump which were associated with each entity. 
  Each page dictionary contains the ID into the KILT dump (`wikipedia_id`) as well as the title of the page. 

* `queries`: `List[Dict]` A list of instantiated queries for each entity. 
  For question answering and slot filling, each relation gets turned into one query while for fact checking, each relation gets turned into two queries (one true, and one false).
  
* `query_id`: `str` Each query gets a unique query ID. The query ID is broken up into two parts which are delinated by a `=` token. 
  The part before this token is the ID of the corresponding AmbER set tuple which can be used to index into the `amber_set_tuples.jsonl` file. 
  The part after this token is the hash of the query string.

* `provenance`: `List[Dict]` Each query gets a provenance field, which are Wikipedia pages that are considered gold documents. 
  The `provenance` pages are a subset of each entities' `wikipedia` pages. 
  The `wikipedia` pages which contain an answer in the first 350 tokens are treated as gold documents.

* `meta`: `Dict` Contains information such as which property (PID) instantiated each query.


