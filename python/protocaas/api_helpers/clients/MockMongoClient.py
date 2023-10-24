from typing import Dict, Union, List
import uuid


class MockMongoClient:
    def __init__(self):
        self._dbs: Dict[str, MockMongoDatabase] = {}
    def __getitem__(self, key: str):
        if key not in self._dbs:
            self._dbs[key] = MockMongoDatabase()
        return self._dbs[key]

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
            raise NotImplementedError()
        update_val = update['$set']
        for document in self._documents.values():
            if _document_matches_query(document, query):
                document.update(update_val)
                return
        if upsert:
            self._documents[str(uuid.uuid4())] = update_val
            return
        raise KeyError("No document matches query")
    async def insert_one(self, document: Dict):
        # create a random ID
        _id = str(uuid.uuid4())
        self._documents[_id] = document
    async def delete_one(self, query: Dict):
        for key, document in self._documents.items():
            if _document_matches_query(document, query):
                del self._documents[key]
                return
        raise KeyError("No document matches query")
    async def delete_many(self, query: Dict):
        for key, document in self._documents.items():
            if _document_matches_query(document, query):
                del self._documents[key]
        return
    async def count_documents(self, query: Dict):
        count = 0
        for document in self._documents.values():
            if _document_matches_query(document, query):
                count += 1
        return count

class MockMongoCursor:
    def __init__(self, documents: Dict[str, Dict], query: Dict):
        self._documents = documents
        self._query = query
    async def to_list(self, length: Union[int, None]) -> List[Dict]:
        documents: List[Dict] = []
        for document in self._documents.values():
            if _document_matches_query(document, self._query):
                documents.append(document)
        if length is not None:
            documents = documents[:length]
        return documents

def _document_matches_query(document: Dict, query: Dict) -> bool:
    # handle $in
    for key, value in query.items():
        if key not in document:
            return False
        if isinstance(value, dict):
            if '$in' in value:
                if document[key] not in value['$in']:
                    return False
            else:
                raise NotImplementedError()
        else:
            if document[key] != value:
                return False
    return True

# The below are used for reference. Uncomment to test the above in the linter.

# from typing import Union, List
# import time
# from ..core.protocaas_types import ProtocaasProject, ProtocaasFile, ProtocaasJob, ProtocaasComputeResource, ComputeResourceSpec
# from ._remove_id_field import _remove_id_field
# from ..core._get_project_role import _project_has_user
# from ..core._hide_secret_params_in_job import _hide_secret_params_in_job

# def _get_mongo_client() -> MockMongoClient:
#     return MockMongoClient()

# async def fetch_projects_for_user(user_id: Union[str, None]) -> List[ProtocaasProject]:
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     projects = await projects_collection.find({}).to_list(length=None) # type: ignore
#     for project in projects:
#         _remove_id_field(project)
#     projects = [ProtocaasProject(**project) for project in projects] # validate projects
#     projects2: List[ProtocaasProject] = []
#     for project in projects:
#         if _project_has_user(project, user_id):
#             projects2.append(project)
#     return projects2

# async def fetch_projects_with_tag(tag: str) -> List[ProtocaasProject]:
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     projects = await projects_collection.find({
#         # When you use a query like { "tags": tag } against an array field in MongoDB, it checks if any element of the array matches the value.
#         'tags': tag
#     }).to_list(length=None) # type: ignore
#     for project in projects:
#         _remove_id_field(project)
#     projects = [ProtocaasProject(**project) for project in projects] # validate projects
#     return projects

# async def fetch_project(project_id: str) -> Union[ProtocaasProject, None]:
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     project = await projects_collection.find_one({'projectId': project_id})
#     # here I'd like to validate project
#     _remove_id_field(project)
#     if project is None:
#         return None
#     return ProtocaasProject(**project) # validate project

# async def fetch_project_files(project_id: str) -> List[ProtocaasFile]:
#     client = _get_mongo_client()
#     files_collection = client['protocaas']['files']
#     files = await files_collection.find({'projectId': project_id}).to_list(length=None) # type: ignore
#     for file in files:
#         _remove_id_field(file)
#     files = [ProtocaasFile(**file) for file in files] # validate files
#     return files

# async def fetch_project_jobs(project_id: str, include_private_keys=False) -> List[ProtocaasJob]:
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     jobs = await jobs_collection.find({'projectId': project_id}).to_list(length=None) # type: ignore
#     for job in jobs:
#         _remove_id_field(job)
#     jobs = [ProtocaasJob(**job) for job in jobs] # validate jobs
#     if not include_private_keys:
#         for job in jobs:
#             job.jobPrivateKey = '' # hide the private key
#     for job in jobs:
#         job.dandiApiKey = None # hide the DANDI API key
#         _hide_secret_params_in_job(job)
#     return jobs

# async def update_project(project_id: str, update: dict):
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     await projects_collection.update_one({
#         'projectId': project_id
#     }, {
#         '$set': update
#     })

# async def delete_project(project_id: str):
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     await projects_collection.delete_one({
#         'projectId': project_id
#     })

# async def delete_all_files_in_project(project_id: str):
#     client = _get_mongo_client()
#     files_collection = client['protocaas']['files']
#     await files_collection.delete_many({
#         'projectId': project_id
#     })

# async def delete_all_jobs_in_project(project_id: str):
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     await jobs_collection.delete_many({
#         'projectId': project_id
#     })

# async def insert_project(project: ProtocaasProject):
#     client = _get_mongo_client()
#     projects_collection = client['protocaas']['projects']
#     await projects_collection.insert_one(project.dict(exclude_none=True))

# async def fetch_compute_resource(compute_resource_id: str):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']
#     compute_resource = await compute_resources_collection.find_one({'computeResourceId': compute_resource_id})
#     if compute_resource is None:
#         return None
#     _remove_id_field(compute_resource)
#     compute_resource = ProtocaasComputeResource(**compute_resource) # validate compute resource
#     return compute_resource

# async def fetch_compute_resources_for_user(user_id: str):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']
#     compute_resources = await compute_resources_collection.find({'ownerId': user_id}).to_list(length=None) # type: ignore
#     for compute_resource in compute_resources:
#         _remove_id_field(compute_resource)
#     compute_resources = [ProtocaasComputeResource(**compute_resource) for compute_resource in compute_resources] # validate compute resources
#     return compute_resources

# async def update_compute_resource(compute_resource_id: str, update: dict):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']
#     await compute_resources_collection.update_one({
#         'computeResourceId': compute_resource_id
#     }, {
#         '$set': update
#     })

# async def delete_compute_resource(compute_resource_id: str):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']
#     await compute_resources_collection.delete_one({
#         'computeResourceId': compute_resource_id
#     })

# async def register_compute_resource(compute_resource_id: str, name: str, user_id: str):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']

#     compute_resource = await compute_resources_collection.find_one({'computeResourceId': compute_resource_id})
#     if compute_resource is not None:
#         await compute_resources_collection.update_one({'computeResourceId': compute_resource_id}, {
#             '$set': {
#                 'ownerId': user_id,
#                 'name': name,
#                 'timestampModified': time.time()
#             }
#         })
#     else:
#         new_compute_resource = ProtocaasComputeResource(
#             computeResourceId=compute_resource_id,
#             ownerId=user_id,
#             name=name,
#             timestampCreated=time.time(),
#             apps=[]
#         )
#         await compute_resources_collection.insert_one(new_compute_resource.dict(exclude_none=True))

# async def fetch_compute_resource_jobs(compute_resource_id: str, statuses: Union[List[str], None], include_private_keys: bool) -> List[ProtocaasJob]:
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     if statuses is not None:
#         jobs = await jobs_collection.find({
#             'computeResourceId': compute_resource_id,
#             'status': {'$in': statuses}
#         }).to_list(length=None) # type: ignore
#     else:
#         jobs = await jobs_collection.find({
#             'computeResourceId': compute_resource_id
#         }).to_list(length=None) # type: ignore
#     for job in jobs:
#         _remove_id_field(job)
#     jobs = [ProtocaasJob(**job) for job in jobs] # validate jobs
#     if not include_private_keys:
#         for job in jobs:
#             job.jobPrivateKey = '' # hide the private key
#     for job in jobs:
#         job.dandiApiKey = None # hide the DANDI API key
#         _hide_secret_params_in_job(job)
#     return jobs

# async def update_compute_resource_node(compute_resource_id: str, compute_resource_node_id: str, compute_resource_node_name: str):
#     client = _get_mongo_client()
#     compute_resource_nodes_collection = client['protocaas']['computeResourceNodes']
#     await compute_resource_nodes_collection.update_one({
#         'computeResourceId': compute_resource_id,
#         'nodeId': compute_resource_node_id
#     }, {
#         '$set': {
#             'timestampLastActive': time.time(),
#             'computeResourceId': compute_resource_id,
#             'nodeId': compute_resource_node_id,
#             'nodeName': compute_resource_node_name
#         }
#     }, upsert=True)

# class ComputeResourceNotFoundError(Exception):
#     pass

# async def set_compute_resource_spec(compute_resource_id: str, spec: ComputeResourceSpec):
#     client = _get_mongo_client()
#     compute_resources_collection = client['protocaas']['computeResources']
#     compute_resource = await compute_resources_collection.find_one({'computeResourceId': compute_resource_id})
#     if compute_resource is None:
#         raise ComputeResourceNotFoundError(f"No compute resource with ID {compute_resource_id}")
#     await compute_resources_collection.update_one({'computeResourceId': compute_resource_id}, {
#         '$set': {
#             'spec': spec.dict(exclude_none=True)
#         }
#     })

# async def fetch_job(job_id: str, *, include_dandi_api_key: bool = False, include_secret_params: bool = False):
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     job = await jobs_collection.find_one({'jobId': job_id})
#     _remove_id_field(job)
#     if job is None:
#         return None
#     job = ProtocaasJob(**job) # validate job
#     if not include_dandi_api_key:
#         job.dandiApiKey = None
#     if not include_secret_params:
#         _hide_secret_params_in_job(job)
#     return job

# async def update_job(job_id: str, update: dict):
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     await jobs_collection.update_one({
#         'jobId': job_id
#     }, {
#         '$set': update
#     })

# async def delete_job(job_id: str):
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     await jobs_collection.delete_one({
#         'jobId': job_id
#     })

# async def insert_job(job: ProtocaasJob):
#     client = _get_mongo_client()
#     jobs_collection = client['protocaas']['jobs']
#     await jobs_collection.insert_one(job.dict(exclude_none=True))

# async def fetch_file(project_id: str, file_name: str):
#     client = _get_mongo_client()
#     files_collection = client['protocaas']['files']
#     file = await files_collection.find_one({
#         'projectId': project_id,
#         'fileName': file_name
#     })
#     _remove_id_field(file)
#     if file is None:
#         return None
#     file = ProtocaasFile(**file) # validate file
#     return file

# async def delete_file(project_id: str, file_name: str):
#     client = _get_mongo_client()
#     files_collection = client['protocaas']['files']
#     await files_collection.delete_one({
#         'projectId': project_id,
#         'fileName': file_name
#     })

# async def insert_file(file: ProtocaasFile):
#     client = _get_mongo_client()
#     files_collection = client['protocaas']['files']
#     await files_collection.insert_one(file.dict(exclude_none=True))
