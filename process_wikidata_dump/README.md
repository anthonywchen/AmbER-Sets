# The Wikidata Dump

AmbER sets are built in an automated pipeline starting with Wikidata tuples.

In order to download and process the dump, you will need the JSON processor package `jq`.
To make downloading the Wikidata dump faster, you can use `axel` instead of `wget`. 
See `process_wikidata_dump.sh` for how to do so.
The Wikidata dump takes up approximately 56 GB.

The Wikidata dump is a 2020 dump from [archives.org](archive.org).
We do not download directly from the Wikidata website since they don't keep around old dumps, making versioning a concern.

### Downloading and Extracting Wikidata Dump
Command to run: `./process_wikidata_dump.sh`.

This first downloads the dump, then runs a series of `bzcat` commands to extract info into `.tsv` files.
The `bzcat` are all run in parallel. 
You can remove parallel processing by removing the `&`'s at the end.
It also downloads pageviews for all Wikipedia files. 
The pageview file is from October 2019. 

### Processing Wikidiata Dump
We filter down the Wikidata information only into what is needed. 
Create the directory `process_wikidata_dump/processed_files`.
Processed `json` files will be written into this directory.
 
Run the following commands in order: 

1. `python build_qid_popularity_dictionary.py`: Takes the pageview counts and merges them with associated QIDs from Wikidata.

2. `python map_aliases_to_qids.py`: Maps from an alias (name) to all QIDs that share that name:

    ``` 
    QIDs for "Abe Lincoln":
    [
        {"qid": "Q91", "pop": 5.1942478558575464, "is_head": true},
        {"qid": "Q4669012", "pop": 2.303196057420489, "is_head": false},
        {"qid": "Q4666410", "pop": 1.7781512503836436, "is_head": false}
    ]
    ```

3. `python map_pids_to_labels.py`: Maps from a PID to it's label (basically it's English description).
    
4. `python map_qids_to_aliases.py`: Maps from a QID to all of it's aliases. 
    
    ``` 
    Aliases for Q91:
    ['Honest Abe', 'A. Lincoln', 'President Lincoln', 'Abe Lincoln', 'Lincoln', 'Abraham Lincoln']
    ```
    
5. `python map_qids_to_pids.py`: Maps from a QID to all it's relations (PIDs) and associated values.

