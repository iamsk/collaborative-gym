"""
This script creates an index of Arxiv metadata (https://www.kaggle.com/datasets/Cornell-University/arxiv)using pre-trained language model embeddings. 
 leverages publicly available embedding models from Hugging Face, compatible with the SentenceTransformer framework. 
 The embeddings can be computed on multi-GPU, single-GPU, or CPU setups (though CPU is not recommended for performance reasons).

Example command:
python local_indexing.py \
    --data_file ./arxiv-metadata-oai-snapshot.json \
    --output_dir ./embeddings_output \
    --model_name "Alibaba-NLP/gte-Qwen2-1.5B-instruct" \
    --batch_size 128 
"""
import argparse
import logging
import numpy as np
import os
import torch
import ujson as json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer


def load_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in tqdm(f, desc="Loading data"):
            record = json.loads(line)
            categories = record["categories"].split()
            for category in categories:
                if category.startswith("cs."):
                    data.append(record)
                    break
    return data

def preprocess_data(data):
    documents = []
    for record in data:
        title = record.get('title', '')
        abstract = record.get('abstract', '')
        text = f"{title}\n{abstract}"
        documents.append({
            'id': record['id'],
            'text': text
        })
    return documents

def embed_text(model, texts):
    if isinstance(model, torch.nn.DataParallel):
        return model.module.encode(texts, show_progress_bar=False)
    else:
        return model.encode(texts, show_progress_bar=False)

def save_batch_embeddings(ids, embeddings, output_dir):
    # Use a unique filename for each batch
    batch_id = ids[0]  # Or use a timestamp or batch number
    batch_id = batch_id.replace("/", "-")
    embeddings_path = os.path.join(output_dir, f'embeddings_{batch_id}.npy')
    ids_path = os.path.join(output_dir, f'ids_{batch_id}.npy')

    # Save embeddings and IDs
    np.save(embeddings_path, embeddings)
    np.save(ids_path, np.array(ids))

def generate_embeddings(model, documents, output_dir, batch_size, index_file):
    os.makedirs(output_dir, exist_ok=True)

    # Initialize counters and lists
    total_docs = len(documents)
    saved_indices = set()

    # Check for existing progress
    if os.path.exists(index_file):
        saved_indices = set(np.load(index_file).tolist())

    for i in tqdm(range(0, total_docs, batch_size), desc="Embedding documents"):
        logging.info(f'Processed batch starting at index {i} / {total_docs}')
        batch_indices = range(i, min(i + batch_size, total_docs))
        # Skip batches that have already been processed
        if all(idx in saved_indices for idx in batch_indices):
            continue

        batch = [documents[idx] for idx in batch_indices]
        texts = [doc['text'] for doc in batch]
        ids = [doc['id'] for doc in batch]

        batch_id = ids[0].replace("/", "-")
        embeddings_path = os.path.join(output_dir, f'embeddings_{batch_id}.npy')
        ids_path = os.path.join(output_dir, f'ids_{batch_id}.npy')
        if os.path.exists(embeddings_path) and os.path.exists(ids_path):
            saved_indices.update(batch_indices)
            continue
        embeddings = embed_text(model, texts)

        # Save embeddings and IDs for this batch
        save_batch_embeddings(ids, embeddings, output_dir)

        # Update and save processed indices
        saved_indices.update(batch_indices)
        np.save(index_file, np.array(list(saved_indices)))

def merge_embeddings(output_dir):
    embedding_files = sorted([f for f in os.listdir(output_dir) if f.startswith('embeddings_')])
    ids_files = sorted([f for f in os.listdir(output_dir) if f.startswith('ids_')])

    all_embeddings = []
    all_ids = []

    for emb_file, id_file in zip(embedding_files, ids_files):
        embeddings = np.load(os.path.join(output_dir, emb_file))
        ids = np.load(os.path.join(output_dir, id_file))
        all_embeddings.append(embeddings)
        all_ids.extend(ids)

    # Concatenate all embeddings
    all_embeddings = np.vstack(all_embeddings)
    all_ids = np.array(all_ids)

    # Save the merged arrays
    np.save(os.path.join(output_dir, 'embeddings.npy'), all_embeddings)
    np.save(os.path.join(output_dir, 'ids.npy'), all_ids)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate and save embeddings for CS-related arXiv metadata.")
    
    # Data and output paths
    parser.add_argument('--data_file', type=str, default='./arxiv-metadata-oai-snapshot.json',
                        help='Path to the input JSON data file.')
    parser.add_argument('--output_dir', type=str, default='./embeddings_output',
                        help='Directory to save the output embeddings and IDs.')
    
    # Model parameters
    parser.add_argument('--model_name', type=str, default='Alibaba-NLP/gte-Qwen2-1.5B-instruct',
                        help='Name or path of the SentenceTransformer model to use.')
    parser.add_argument('--batch_size', type=int, default=128,
                        help='Batch size for embedding generation.')
    
    # Device settings
    parser.add_argument('--use_cpu', action='store_true',
                        help='Force the use of CPU even if GPU is available.')
    parser.add_argument('--device_ids', type=int, nargs='*', default=None,
                        help='List of GPU device IDs to use (e.g., --device_ids 0 1 2).')
    
    # Logging
    parser.add_argument('--log_level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level.')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), None),
        format='%(asctime)s %(levelname)s:%(message)s'
    )
    
    # Load data
    logging.info("Loading data...")
    data = load_data(args.data_file)
    documents = preprocess_data(data)
    logging.info(f"Loaded and preprocessed {len(documents)} documents.")
    
    # Device configuration
    if args.use_cpu or not torch.cuda.is_available():
        device = "cpu"
        device_ids = []
        logging.info("Using CPU for embedding generation.")
    else:
        if args.device_ids is not None:
            device = f"cuda:{args.device_ids[0]}"
            device_ids = args.device_ids
        else:
            device = "cuda:0"
            device_ids = list(range(torch.cuda.device_count()))
        logging.info(f"Using device(s): {device_ids}")
    
    # Load model
    logging.info(f"Loading model '{args.model_name}'...")
    model = SentenceTransformer(args.model_name, device=device, trust_remote_code=True)
    if device_ids and len(device_ids) > 1:
        logging.info(f"Using DataParallel with devices {device_ids}.")
        model = torch.nn.DataParallel(model, device_ids=device_ids)
    else:
        logging.info("Using a single device.")
    
    # Generate embeddings
    index_file = os.path.join(args.output_dir, 'processed_indices.npy')
    logging.info("Starting embedding generation...")
    generate_embeddings(model, documents, args.output_dir, args.batch_size, index_file)
    
    # Merge embeddings after processing
    logging.info("Merging embeddings...")
    merge_embeddings(args.output_dir)
    logging.info("Embedding generation and merging completed successfully.")

if __name__ == '__main__':
    main()
