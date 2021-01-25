# AmbER Sets

AmbER sets are stored in a JSONLines format under the following path: 

`amber_sets/<collection>/<task>/amber_sets.jsonl`

Here is an example AmbER set for the name "Abe Lincoln" from the human collection (AmbER-H) for the question answering task:

```
{
    "name": "Abe Lincoln",
    "qids": {
        "Q91": {
            "is_head": true,
            "pop": 5.1942478558575464,
            "wikipedia": [
                {
                    "kilt_idx": 49,
                    "wikipedia_id": "307",
                    "title": "Abraham Lincoln"
                },
                {
                    "kilt_idx": 3767946,
                    "wikipedia_id": "42390831",
                    "title": "Abraham Lincoln's Life"
                }
            ],
            "queries": [
                {
                    "id": "6981ec17f0438a7cc94fff740cc9bb23=f12393b7ba0631871ea7126dd5127772",
                    "input": "Which battle did Abe Lincoln fight in?",
                    "output": [
                        {
                            "answer": [
                                "American Civil War"
                                ...
                            ],
                            "provenance": [
                                {
                                    "kilt_idx": 49,
                                    "wikipedia_id": "307",
                                    "title": "Abraham Lincoln"
                                }
                            ],
                            "meta": {...}
                        }
                    ],
                    "meta": {...}
                }
            ]
        },
        "Q4666410": {
            "is_head": false,
            "pop": 1.7781512503836436,
            "wikipedia": [
                {
                    "kilt_idx": 477649,
                    "wikipedia_id": "17039796",
                    "title": "Abe Lincoln (musician)"
                }
            ],
            "queries": [
                {
                    "id": "edf1ff070a3cbd5fdee738262db8e740=44a67ee4dd88179d1147102e9753a5fa",
                    "input": "What musical instrument does Abe Lincoln play?",
                    "output": [
                        {
                            "answer": [
                                "slide trombone",
                                ...
                            ],
                            "provenance": [
                                {
                                    "kilt_idx": 477649,
                                    "wikipedia_id": "17039796",
                                    "title": "Abe Lincoln (musician)"
                                }
                            ],
                            "meta": {...}
                        }
                    ],
                    "meta": {...}
                }
            ]
        }
    }
}
```
