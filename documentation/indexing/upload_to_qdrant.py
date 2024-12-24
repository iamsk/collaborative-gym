"""
Qdrant Embeddings and Metadata Uploader

This script uploads embeddings and their associated metadata to a Qdrant collection. The embeddings and metadata are 
loaded from local directory, processed by local_indexing.py or voyage_indexing.py, and the script supports uploading in parallel batches.

Example usage:
    python upload_to_qdrant.py \
        --qdrant_url "https://your-qdrant-url" \
        --api_key "your-api-key" \
        --collection_name "your_collection" \
        --embeddings_dir "./embeddings_output" \
        --metadata_file "./arxiv-metadata-oai-snapshot.json" \
        --vector_size 1024
"""

import argparse
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import numpy as np
import os
import json
from tqdm import tqdm
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed


def arxiv_id_to_uuid(arxiv_id):
    custom_namespace = uuid.uuid5(uuid.NAMESPACE_URL, "arxiv.com")
    return str(uuid.uuid5(custom_namespace, arxiv_id))

# Load the raw data to dynamically extract payloads
def load_data(file_path):
    data = {}
    with open(file_path, 'r') as f:
        for line in tqdm(f, desc="Loading metadata"):
            record = json.loads(line)
            categories = record.get("categories", "").split()
            for category in categories:
                if category.startswith("cs."):  # Only include cs category papers
                    data[record["id"]] = record
                    break  # Break after adding the record for the first valid category
    return data

# Upload embeddings and metadata to Qdrant
def upload_batch(qdrant_client, collection_name, embeddings_path, ids_path, metadata):
    # Load embeddings and IDs
    embeddings = np.load(embeddings_path)
    ids = np.load(ids_path)

    # Prepare points for Qdrant upload
    points = []
    for idx in range(len(ids)):
        point_id = arxiv_id_to_uuid(ids[idx])
        payload = metadata[ids[idx]]
        point = PointStruct(
            id=point_id,
            vector=embeddings[idx].tolist(),
            payload=payload
        )
        points.append(point)
    
    # Upload points to Qdrant
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Upload embeddings and metadata to Qdrant.")
    parser.add_argument('--qdrant_url', required=True, help="The URL of the Qdrant instance.")
    parser.add_argument('--api_key', required=True, help="API key for accessing Qdrant.")
    parser.add_argument('--collection_name', required=True, help="Name of the collection in Qdrant.")
    parser.add_argument('--embeddings_dir', required=True, help="Directory containing embeddings and ID files.")
    parser.add_argument('--metadata_file', required=True, help="Path to the raw Arxiv metadata JSON file.")
    parser.add_argument('--vector_size', type=int, default=1024, help="Size of the embedding vectors (default: 1024).")
    parser.add_argument('--max_workers', type=int, default=10, help="Number of parallel threads (default: 10).")

    args = parser.parse_args()

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=args.qdrant_url,
        api_key=args.api_key,
    )
    
    collection_name = args.collection_name
    embeddings_dir = args.embeddings_dir
    metadata_file = args.metadata_file
    vector_size = args.vector_size
    max_workers = args.max_workers

    # Load metadata (this can take time depending on the size of the dataset)
    metadata = load_data(metadata_file)

    # Check if the collection exists; if not, create it
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"Created collection '{collection_name}' with vector size {vector_size}.")
    else:
        print(f"Collection '{collection_name}' already exists.")
    
    # Get all batch numbers
    batch_numbers = sorted([
        f.replace("embeddings_", "").replace(".npy", "").strip()
        for f in os.listdir(embeddings_dir)
        if f.startswith('embeddings_') and f.endswith('.npy')
    ])
    
    def upload_batch_to_qdrant(batch_number, qdrant_client, collection_name, embeddings_dir, metadata):
        """
        Function to handle the upload of a single batch.
        """
        # Define file paths
        embeddings_path = os.path.join(embeddings_dir, f'embeddings_{batch_number}.npy')
        ids_path = os.path.join(embeddings_dir, f'ids_{batch_number}.npy')

         # Upload the batch to Qdrant
        upload_batch(qdrant_client, collection_name, embeddings_path, ids_path, metadata)

    # Initialize ThreadPoolExecutor with max_workers threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a progress bar
        futures = []
        with tqdm(total=len(batch_numbers), desc="Uploading batches to Qdrant") as pbar:
            # Submit each batch upload task to the executor
            for batch_number in batch_numbers:
                future = executor.submit(upload_batch_to_qdrant, batch_number, qdrant_client, collection_name, embeddings_dir, metadata)
                futures.append(future)

            # Update the progress bar as each batch completes
            for future in as_completed(futures):
                pbar.update(1)

    print("Completed uploading all batches to Qdrant.")

if __name__ == '__main__':
    main()
