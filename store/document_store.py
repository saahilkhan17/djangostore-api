import copy
import uuid
from typing import Any, Dict, List, Optional
from django.conf import settings


class InsertOneResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count: int, modified_count: int):
        self.matched_count = matched_count
        self.modified_count = modified_count


class DocumentStore:
    """
    MongoDB-compatible document store interface.
    Stores documents in-memory when DOCUMENT_STORE_URL is unset.
    Can be swapped with pymongo:
        client = pymongo.MongoClient(self.url)
        collection = client.get_default_database()[self.collection_name]
    """
    _memory_store: Dict[str, Dict[str, Any]] = {}

    def __init__(self, collection_name: str = "reviews", url: Optional[str] = None):
        self.collection_name = collection_name
        self.url = url or getattr(settings, "DOCUMENT_STORE_URL", "")

    def _get_collection(self) -> Dict[str, Dict[str, Any]]:
        if self.collection_name not in DocumentStore._memory_store:
            DocumentStore._memory_store[self.collection_name] = {}
        return DocumentStore._memory_store[self.collection_name]

    def insert_one(self, document: Dict[str, Any]) -> InsertOneResult:
        doc = copy.deepcopy(document)
        doc_id = str(doc.get("_id") or doc.get("id") or uuid.uuid4().hex[:12])
        doc["_id"] = doc_id
        doc["id"] = doc_id
        self._get_collection()[doc_id] = doc
        return InsertOneResult(inserted_id=doc_id)

    def find(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = query or {}
        results = []
        for doc in self._get_collection().values():
            matches = True
            for k, v in query.items():
                if doc.get(k) != v:
                    matches = False
                    break
            if matches:
                results.append(copy.deepcopy(doc))
        return results

    def find_one(self, query: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        results = self.find(query)
        return results[0] if results else None

    def update_one(self, filter_query: Dict[str, Any], update_spec: Dict[str, Any]) -> UpdateResult:
        matched_count = 0
        modified_count = 0
        updates = update_spec.get("$set", update_spec)
        for doc_id, doc in self._get_collection().items():
            matches = True
            for k, v in filter_query.items():
                if doc.get(k) != v:
                    matches = False
                    break
            if matches:
                matched_count = 1
                for uk, uv in updates.items():
                    if uk not in ("_id", "id"):
                        doc[uk] = uv
                modified_count = 1
                break
        return UpdateResult(matched_count=matched_count, modified_count=modified_count)

    def clear(self):
        if self.collection_name in DocumentStore._memory_store:
            DocumentStore._memory_store[self.collection_name].clear()


review_store = DocumentStore("reviews")
