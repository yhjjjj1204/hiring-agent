from typing import Any, List, Optional

from openai import OpenAI
from pymongo import MongoClient
from pymongo.database import Database

import config

_client: MongoClient[Any] | None = None


def get_mongo_client() -> MongoClient[Any]:
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI)
    return _client


def get_database() -> Database[Any]:
    return get_mongo_client()[config.MONGODB_DB]


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generates an embedding for the given text using OpenAI API.
    """
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.embeddings.create(input=[text], model=model)
    # Best-effort usage tracking for embedding calls.
    try:
        from monitoring.usage_service import record_openai_usage

        record_openai_usage(response.usage, default_function_id="embedding")
    except Exception:
        # Never fail embedding generation due to monitoring issues.
        pass
    return response.data[0].embedding


def save_document_with_embedding(
    collection_name: str,
    document: dict[str, Any],
    text_to_embed: str,
    embedding_field: str = "embedding",
    model: str = "text-embedding-3-small",
) -> str:
    """
    Generates an embedding for the text, adds it to the document, and saves to MongoDB.
    Returns the inserted document ID (as string).
    """
    embedding = generate_embedding(text_to_embed, model=model)
    document[embedding_field] = embedding

    db = get_database()
    result = db[collection_name].insert_one(document)
    return str(result.inserted_id)


def create_vector_index(
    collection_name: str,
    field_name: str,
    dimensions: int,
    index_name: str,
    similarity: str = "COS",
    kind: str = "vector-hnsw",
    m: int = 16,
    ef_construction: int = 64,
) -> Any:
    """
    Creates a vector search index in FerretDB.
    """
    db = get_database()
    return db.command(
        {
            "createIndexes": collection_name,
            "indexes": [
                {
                    "name": index_name,
                    "key": {field_name: "cosmosSearch"},
                    "cosmosSearchOptions": {
                        "kind": kind,
                        "similarity": similarity,
                        "dimensions": dimensions,
                        "m": m,
                        "efConstruction": ef_construction,
                    },
                }
            ],
        }
    )


def vector_search(
    collection_name: str,
    query_vector: List[float],
    field_name: str,
    k: int = 10,
    projection: Optional[dict[str, Any]] = None,
) -> List[dict[str, Any]]:
    """
    Performs a vector search in FerretDB using the $search aggregation stage.
    """
    db = get_database()
    pipeline: List[dict[str, Any]] = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": query_vector,
                    "path": field_name,
                    "k": k,
                },
                "returnStoredSource": True,
            }
        }
    ]

    if projection:
        pipeline.append({"$project": projection})

    return list(db[collection_name].aggregate(pipeline))
