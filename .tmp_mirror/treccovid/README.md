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
    num_bytes: 98208720
    num_examples: 50
  download_size: 52203779
  dataset_size: 98208720
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

This dataset is a reranking-formatted version of the TREC-COVID dataset from the BEIR benchmark.

Original Dataset: TREC-COVID from NIST  
BEIR Version: BeIR/trec-covid  
License: Available for research purposes  
Task: COVID-19 scientific literature retrieval