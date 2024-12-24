"""
This script creates an index of Arxiv metadata (https://www.kaggle.com/datasets/Cornell-University/arxiv) 
using the Voyage embedding model (voyage-3), accessible through the Voyage AI API. 

The API key for this service can be obtained from Voyage AI's dashboard: https://dash.voyageai.com/api-keys. 
It supports multi-threading with configurable batch size (max 128) and logging.

Example usage:
python voyage_indexing.py \
    --data_file ./arxiv-metadata-oai-snapshot.json \
    --output_dir ./embeddings_output \
    --model_name "voyage-3" \
    --batch_size 128 \
    --num_workers 2 \
    --log_level INFO \
    --api_key YOUR_VOYAGEAI_API_KEY
"""

import os
import ujson as json
import numpy as np
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

import argparse
import voyageai

def load_data(file_path: str) -> List[Dict]:
    """Load and filter data for 'cs.' categories."""
    data = []
    with open(file_path, 'r') as f:
        for line in tqdm(f, desc="Loading data"):
            try:
                record = json.loads(line)
                categories = record.get("categories", "").split()
                if any(category.startswith("cs.") for category in categories):
                    data.append(record)
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping invalid JSON line: {e}")
    return data

def preprocess_data(data: List[Dict]) -> List[Dict[str, str]]:
    """Preprocess data by concatenating title and abstract."""
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

def embed_text(model: voyageai.Client, texts: List[str], model_name: str) -> np.ndarray:
    """Generate embeddings using VoyageAI model."""
    response = model.embed(texts, model=model_name, input_type="document")
    return response.embeddings

def save_batch_embeddings(ids: List[str], embeddings: np.ndarray, output_dir: str) -> None:
    """Save embeddings and corresponding IDs to .npy files."""
    batch_id = ids[0].replace("/", "-")
    embeddings_path = os.path.join(output_dir, f'embeddings_{batch_id}.npy')
    ids_path = os.path.join(output_dir, f'ids_{batch_id}.npy')

    np.save(embeddings_path, embeddings)
    np.save(ids_path, np.array(ids))

def generate_embeddings(documents: List[Dict[str, str]],
                       output_dir: str,
                       model: voyageai.Client,
                       model_name: str,
                       input_type: str,
                       batch_size: int = 32,
                       num_workers: int = 4) -> None:
    """Generate and save embeddings concurrently."""
    os.makedirs(output_dir, exist_ok=True)
    total_docs = len(documents)

    # Prepare batches
    batches = [
        (i, documents[i:i + batch_size])
        for i in range(0, total_docs, batch_size)
    ]

    logging.info(f"Total batches to process: {len(batches)}")

    def process_batch(start_index: int, batch: List[Dict[str, str]]) -> None:
        """Process a single batch: generate embeddings and save them."""
        try:
            texts = [doc['text'] for doc in batch]
            ids = [doc['id'] for doc in batch]
            embeddings_path = os.path.join(output_dir, f'embeddings_{ids[0].replace("/", "-")}.npy')
            ids_path = os.path.join(output_dir, f'ids_{ids[0].replace("/", "-")}.npy')

            if os.path.exists(embeddings_path) and os.path.exists(ids_path):
                logging.debug(f"Batch starting at index {start_index} already processed. Skipping.")
                return

            embeddings = embed_text(model, texts, model_name)
            if embeddings is None or len(embeddings) != len(texts):
                raise ValueError("Embeddings returned are invalid or do not match the number of texts.")

            save_batch_embeddings(ids, embeddings, output_dir)
            logging.debug(f"Batch starting at index {start_index} processed successfully.")
        except Exception as e:
            logging.error(f"Error processing batch starting at index {start_index}: {e}")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_batch = {
            executor.submit(process_batch, start_index, batch): (start_index, batch)
            for start_index, batch in batches
        }

        with tqdm(total=len(batches), desc="Embedding documents") as pbar:
            for future in as_completed(future_to_batch):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Batch processing raised an exception: {e}")
                finally:
                    pbar.update(1)

    logging.info("All batches have been processed.")

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Embed arXiv metadata and save embeddings.")

    # File paths
    parser.add_argument('--data_file', type=str, default='./arxiv-metadata-oai-snapshot.json',
                        help='Path to the input JSON data file.')
    parser.add_argument('--output_dir', type=str, default='./embeddings_output',
                        help='Directory to save the output embeddings.')

    # Processing parameters
    parser.add_argument('--batch_size', type=int, default=128,
                        help='Number of documents to process in each batch.')
    parser.add_argument('--num_workers', type=int, default=2,
                        help='Number of worker threads for concurrent processing.')

    # Model parameters
    parser.add_argument('--model_name', type=str, default='voyage-3',
                        help='Name of the VoyageAI model to use for embeddings.')

    # API Key
    parser.add_argument('--api_key', type=str, default=None,
                        help='VoyageAI API key. If not provided, will use the VOYAGEAI_API_KEY environment variable.')

    # Logging
    parser.add_argument('--log_level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level.')

    return parser.parse_args()

def main():
    args = parse_arguments()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format='%(asctime)s %(levelname)s:%(message)s'
    )

    logging.info("Starting the embedding process.")
    logging.info(f"Data file: {args.data_file}")
    logging.info(f"Output directory: {args.output_dir}")
    logging.info(f"Batch size: {args.batch_size}")
    logging.info(f"Number of workers: {args.num_workers}")
    logging.info(f"Model name: {args.model_name}")
    logging.info(f"Input type: {args.input_type}")

    # Retrieve API key
    api_key = args.api_key or os.getenv('VOYAGEAI_API_KEY')
    if not api_key:
        logging.error("VoyageAI API key not provided. Use --api_key argument or set VOYAGEAI_API_KEY environment variable.")
        exit(1)

    # Initialize VoyageAI client
    try:
        model_client = voyageai.Client(api_key=api_key)
        logging.info("VoyageAI client initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize VoyageAI client: {e}")
        exit(1)

    # Load data
    logging.info("Loading data...")
    data = load_data(args.data_file)
    logging.info(f"Loaded {len(data)} records with 'cs.' categories.")

    # Preprocess data
    documents = preprocess_data(data)
    logging.info(f"Preprocessed {len(documents)} documents.")

    if not documents:
        logging.warning("No documents to process. Exiting.")
        exit(0)

    # Generate embeddings
    logging.info("Starting embedding generation...")
    generate_embeddings(
        documents=documents,
        output_dir=args.output_dir,
        model=model_client,
        model_name=args.model_name,
        input_type=args.input_type,
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )

    logging.info("Embedding process completed successfully.")

if __name__ == '__main__':
    main()
