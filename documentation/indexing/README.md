# Setting up vector database for arXiv

Date: 2024-10-24, by [@Yucheng-Jiang](https://github.com/Yucheng-Jiang)

## Obtain arXiv data dump
- arXiv metadata (consists of title, authors, abstract, etc.) can be downloaded from Kaggle [here](https://www.kaggle.com/datasets/Cornell-University/arxiv)
- arXiv CS domain (i.e. category name starts with `cs.`) consists of around 700,000 to 800,000 documents as of 2024-10

## Indexing
- In this directory we provide two scripts, [local_indexing.py](./local_indexing.py) provides script to index document using public available models. In the script, we use `Alibaba-NLP/gte-Qwen2-1.5B-instruct`. 

- To replicate the steps running this on Stanford NLP cluster

  ```bash
  ssh username@sc.stanford.edu
  cd /nlp/scr/username
  
  # download conda
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh -b -p /nlp/scr/username/miniconda3
  source /nlp/scr/username/miniconda3/bin/activate
  conda update -n base -c defaults conda
  
  # setup conda environment
  conda create -n arxiv_indexing python=3.11 -y
  conda activate arxiv_indexing
  pip install transformers torch tqdm ujson sentence-transformers
  
  # setup indexing script. Copy the actual script here
  vi local_indexing.py
  
  # setup necessary parameters and run the job
  # For `Alibaba-NLP/gte-Qwen2-1.5B-instruct` with batch size 128, need around 5 gpu from jag cluster
  nlprun -q jag -g 5 -r 40G -c 16 -p important 'source /nlp/scr/yuchengj/miniconda3/bin/activate qdrant-indexing; python indexing.py' 
  ```

- Alternatively, we can use [voyage_indexing.py](voyage_indexing.py) to index the documents. The rationale of switching to close source commercial model is because (1) it's hard to locally run `Alibaba-NLP/gte-Qwen2-1.5B-instruct` or similar models (best guest need 16Gb - 24Gb GPU memory) (2) Commercial embedding models are not expensive. Will cost less than $10 to index whole arXiv CS subdomain. With VoyageAI it has more than enough free credits to get this done.

- For the chocie of embedding models, [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) might be a good reference

## Upload to qdrant vector DB

- After indexing, we expect to have a directory having pairs of `embeddings_{batch_id}.npy` and `ids_{batch_id}.npy` where each pair stores a batch of embeddings. Side notes
  - `batch_id` here just simpy use first `doc_id` in the batch as the batch id
  - `doc_id` uses `arxiv_id_to_uuid()` function which can be found in [upload_to_qdrant.py](upload_to_qdrant.py)
- Setup Qdrant cloud [here](https://qdrant.tech)
  - Add a billing method
  - Refer to price calculator [here](https://cloud.qdrant.io/calculator?provider=aws&region=us-east-1&vectors=0&dimension=0&storageOptimized=false&replicas=1&quantization=None) to determine the best plan and configuration of the cluster
  - If using non-free cluster, remember to manually turn on "On disk" option to save RAM usage under Configuration tab of the cluster. By default its off. Do this before uploading data to the cluster
- For 70,000 to 90,000 documents, with embedding size 1024, no quantization, offload cache on disk, it costs around $30 / month.
- Run the script [upload_to_qdrant.py](upload_to_qdrant.py)

## Client side retrieval

Add following fields to existing / create a new `secrets.toml`

```toml
VOYAGE_API_KEY = ""
QDRANT_ENDPOINT = ""
QDRANT_API_KEY = ""
QDRANT_COLLECTION = ""
```

Then refer to the [retriever script](../../collaborative_gym/utils/retriever.py) `example()` function of actual usage.

