---
dataset_info:
  features:
  - name: _id
    dtype: string
  - name: query
    dtype: string
  - name: gt_ids
    sequence: string
  - name: gt_qrels
    sequence: int64
  - name: candidate_ids
    sequence: string
  - name: candidate_docs
    sequence: string
  - name: gt_docs
    sequence: string
  splits:
  - name: test
    num_bytes: 18680540
    num_examples: 49
  download_size: 10026166
  dataset_size: 18680540
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

This dataset is a reranking-formatted version of the Touche 2020 dataset from the BEIR benchmark.

Original Dataset: Webis-Touche-2020 from TREC  
BEIR Version: BeIR/webis-touche2020  
License: CC-BY-SA-4.0 (as per BEIR version)  
Task: Argument Retrieval for controversial topics