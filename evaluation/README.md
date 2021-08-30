# Evaluation

We have created our own evaluation script given your retriever's predictions on the KILT Wikipedia dump. 
To handle how different retrievers create passages out of documents (TF-IDF does not create passages while DPR does), our evaluation script computes document-level metrics.
 That is, if your retriever has retrieved multiple passages from the same document, the script will take the highest scoring passage as the rank of the document. 


To evaluate your retrieval system, run:
```bash
PYTHONPATH=. python evaluation/evaluate_retriever.py 
    --annotations_file data/<collection>/<task>/amber_sets.jsonl \
    --predictions_file <predictions_file>
    --k <top k retreived documents to evaluate with>
    --output_file <output file> Optional file to write evaluation results to. If not provided, results will be printed.
```

The evaluation script expects a prediction file in a JSONLines format where each line has the following structure. E.g.,
```JSON
{"id": "5f04dd5c7058b01405e64ddd3f59a8da=b33f81c2bbb8f9762333f843de698c8a", "output": {"provenance": [{"wikipedia_id": "6404979"}, {"wikipedia_id": "33169245"}, {"wikipedia_id": "5197325"}, ...]}}
```

* `id`: The ID of the query in the annotations file the line corresponds to.
* `provenance`: A list of retrieved documents sorted from highest scoring to lowest scoring. This field must be under the `output` key. The `wikipedia_id` values correspond to the IDs in the KILT Wikipedia dump. The length of the `provenance` list can be larger than `k` as the script will take the first `k` elements before doing the evaluation.