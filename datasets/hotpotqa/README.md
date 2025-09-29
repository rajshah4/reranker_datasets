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
    num_bytes: 21930589
    num_examples: 500
  download_size: 12281664
  dataset_size: 21930589
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---


This dataset is a reranking-formatted version of the HotpotQA dataset from the BEIR benchmark.

Original Dataset: HotpotQA from Stanford NLP  
BEIR Version: BeIR/hotpotqa  
License: CC-BY-SA-4.0 (based on Wikipedia content)  
Task: Multi-hop reasoning question answering  
