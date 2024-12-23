"""
Date: 2024-10-23

Retriever wrapper class that use voyager as encoder and qdrant as vector database.

Dependency:
pip install voyageai, qdrant_client

Secrets management:
Add following secrets to secrets.toml
VOYAGE_API_KEY = ""
QDRANT_ENDPOINT = ""
QDRANT_API_KEY = ""
QDRANT_COLLECTION = ""
"""

import os
from typing import Optional

import voyageai
from qdrant_client import QdrantClient


class ArxivRetriever:
    def __init__(
        self,
        voyage_api: Optional[str] = None,
        qdrant_endpoint: Optional[str] = None,
        qdrant_api: Optional[str] = None,
        qdrant_collection_name: Optional[str] = None,
        retrieve_top_k: int = 10,
    ):
        """Retriever for Arxiv documents using Voyage as encoder and Qdrant as vector database.

        Example usage:
        ```
        from collaborative_gym.utils.retriever import ArxivRetriever
        from collaborative_gym.utils.utils import load_api_key
        load_api_key("secrets.toml")
        retriever = ArxivRetriever(retrieve_top_k=10)
        documents = retriever.retrieve(query="information retrieval")
        """
        voyage_api = voyage_api or os.getenv("VOYAGE_API_KEY")
        qdrant_endpoint = qdrant_endpoint or os.getenv("QDRANT_ENDPOINT")
        qdrant_api = qdrant_api or os.getenv("QDRANT_API_KEY")
        qdrant_collection_name = qdrant_collection_name or os.getenv(
            "QDRANT_COLLECTION"
        )
        self.encoder = voyageai.Client(api_key=voyage_api)
        self.qdrant_client = QdrantClient(
            url=qdrant_endpoint, api_key=qdrant_api, port=None, timeout=20
        )
        self.retrieve_top_k = retrieve_top_k
        self.qdrant_collection_name = qdrant_collection_name

    def retrieve(self, query: str):
        """Retrieve documents from Arxiv using the query.

        Args:
            query (str): Query to search for.
        Returns:
            List[Dict]: List of documents retrieved.
                - id (str): https://arxiv.org/pdf/{id}.pdf would be the link to the paper.
                - title (str): Title of the paper.
                - abstract (str): Abstract of the paper.
                - authors (str): Authors of the paper.
                - authors_parsed (List[str]): List of authors. [["last_name", "first_name"], ...]
                - comments (str): Comments field of the paper on arxiv.
                - journal_ref (str): Journal reference of the paper.
                - doi (str): DOI of the paper.
                - categories (str): Categories of the paper.
                - update_date (str): Last updated date of the paper.
        """
        query_embedding = self.encoder.embed(
            query, model="voyage-3", input_type="document"
        ).embeddings[0]
        res = self.qdrant_client.search(
            collection_name=self.qdrant_collection_name,
            query_vector=query_embedding,
            limit=self.retrieve_top_k,
        )
        return [data.payload for data in res]
