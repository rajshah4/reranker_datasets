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
    num_bytes: 18137270
    num_examples: 500
  download_size: 8271034
  dataset_size: 18137270
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

This dataset is a reranking-formatted version of the MS MARCO dataset from the BEIR benchmark.  
Original Dataset: MS MARCO from Microsoft Research  
BEIR Version: BeIR/msmarco  
License: Available for research and commercial use  
Task: Passage ranking for question answering