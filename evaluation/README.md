# Evaluation

### Evaluate Retrieval System
To evaluate your retrieval system, run:
```bash
PYTHONPATH=. python evaluation/evaluate_retriever.py 
    --annotations_file data/<collection>/<task>/amber_sets.jsonl \
    --predictions_file <predictions_file>
    --k <top k retreived documents to evaluate with>
    --output_file <output file> Optional file to write evaluation results to. If not provided, results will be printed.
```

The evaluation script expects a prediction file in a JSONLines format where each line has the following structure.

```JSON
{
  "id": "5f04dd5c7058b01405e64ddd3f59a8da=b33f81c2bbb8f9762333f843de698c8a",
  "output": {
    "provenance": [
      {"wikipedia_id": "6404979"}, 
      {"wikipedia_id": "33169245"}, 
      {"wikipedia_id": "5197325"},
      ...
    ]
  }
}
```

* `id`: The ID of the query in the annotations file the line corresponds to.
* `provenance`: A list of retrieved documents sorted from highest scoring to lowest scoring. This field must be under the `output` key.
