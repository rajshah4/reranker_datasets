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
    num_bytes: 47642414
    num_examples: 500
  download_size: 27320919
  dataset_size: 47642414
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

This dataset is a reranking-formatted version of the FiQA-2018 dataset from the BEIR benchmark.

Original Dataset: FiQA (Financial Opinion Mining and Question Answering)  
BEIR Version: BeIR/fiqa  
License: Available for research purposes  
Task: Financial domain question answering