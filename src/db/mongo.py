from typing import Any

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
