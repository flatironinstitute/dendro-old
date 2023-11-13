from typing import Dict, Union, List
import uuid


class MockMongoClient:
    def __init__(self):
        self._dbs: Dict[str, MockMongoDatabase] = {}
    def __getitem__(self, key: str):
        if key not in self._dbs:
            self._dbs[key] = MockMongoDatabase()
        return self._dbs[key]
    def clear_databases(self):
        self._dbs = {}

class MockMongoDatabase:
    def __init__(self):
        self._collections: Dict[str, MockMongoCollection] = {}
    def __getitem__(self, key: str):
        if key not in self._collections:
            self._collections[key] = MockMongoCollection()
        return self._collections[key]

class MockMongoCollection:
    def __init__(self):
        self._documents: Dict[str, Dict] = {}
    def find(self, query: Dict):
        return MockMongoCursor(self._documents, query)
    async def find_one(self, query: Dict):
        for document in self._documents.values():
            if _document_matches_query(document, query):
                return document
        return None
    async def update_one(self, query: Dict, update: Dict, *, upsert=False):
        if '$set' not in update:
            raise NotImplementedError() # pragma: no cover
        update_val = update['$set']
        for document in self._documents.values():
            if _document_matches_query(document, query):
                document.update(update_val)
                return
        if upsert:
            # create a random ID
            update_val_2 = {
                **update_val,
                '_id': str(uuid.uuid4())
            }
            self._documents[update_val_2['_id']] = update_val_2
            return
        raise KeyError("No document matches query") # pragma: no cover
    async def insert_one(self, document: Dict):
        # create a random ID
        _id = str(uuid.uuid4())
        document2 = {
            **document,
            '_id': _id
        }
        self._documents[_id] = document2
    async def delete_one(self, query: Dict):
        for key, document in self._documents.items():
            if _document_matches_query(document, query):
                del self._documents[key]
                return
        raise KeyError("No document matches query") # pragma: no cover
    async def delete_many(self, query: Dict):
        document_items = list(self._documents.items()) # need to do it this way because we're deleting from the dict
        for key, document in document_items:
            if _document_matches_query(document, query):
                del self._documents[key]
        return

class MockMongoCursor:
    def __init__(self, documents: Dict[str, Dict], query: Dict):
        self._documents = documents
        self._query = query
    async def to_list(self, length: Union[int, None]) -> List[Dict]:
        assert length is None, 'non-None length is not supported for now'
        documents: List[Dict] = []
        for document in self._documents.values():
            if _document_matches_query(document, self._query):
                documents.append(document)
        return documents

def _document_matches_query(document: Dict, query: Dict) -> bool:
    # handle $in
    for key, value in query.items():
        if key not in document:
            return False # pragma: no cover
        if isinstance(value, dict):
            assert '$in' in value, 'Only $in is supported for now'
            if document[key] not in value['$in']:
                return False
        else:
            if isinstance(document[key], list):
                if value not in document[key]:
                    return False
            else:
                if document[key] != value:
                    return False
    return True
