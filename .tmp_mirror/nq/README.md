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
    num_bytes: 31176873
    num_examples: 500
  download_size: 17597066
  dataset_size: 31176873
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

This dataset is a reranking-formatted version of the Natural Questions dataset from the BEIR benchmark.

Original Dataset: Natural Questions from Google Research  
BEIR Version: BeIR/nq  
License: CC-BY-SA-3.0 (based on Wikipedia content)  
Task: Open-domain question answering