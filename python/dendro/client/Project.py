from typing import List, Union
import os
import time
import requests
from ..common.dendro_types import DendroComputeResource, DendroProject, DendroFile, DendroJob
from ..common._api_request import _client_get_api_request


class ProjectException(Exception):
    pass

class Project:
    def __init__(self, *,
        project_data: DendroProject,
        files_data: List[DendroFile],
        jobs_data: List[DendroJob],
        compute_resource: Union[DendroComputeResource, None]
    ) -> None:
        self._project_id = project_data.projectId
        self._name = project_data.name
        self._description = project_data.description
        self._compute_resource_id = project_data.computeResourceId
        self._owner_id = project_data.ownerId
        self._timestamp_created = project_data.timestampCreated
        self._timestamp_modified = project_data.timestampModified

        self._files = [
            ProjectFile(f)
            for f in files_data
        ]

        self._jobs = [
            j # DendroJob
            for j in jobs_data
        ]

        self._compute_resource = compute_resource
    def get_file(self, file_name: str) -> 'ProjectFile':
        for f in self._files:
            if f._file_data.fileName == file_name:
                return f
        raise ProjectException(f'File not found: {file_name}')
    def get_folder(self, path: str) -> 'ProjectFolder':
        return ProjectFolder(self, path)

class ProjectFile:
    def __init__(self, file_data: DendroFile) -> None:
        self._file_data = file_data
        self._resolved_url: Union[str, None] = None
        self._resolved_url_timestamp: Union[float, None] = None
    def get_url(self) -> str:
        a = self._file_data.content
        if not a.startswith('url:'):
            raise ProjectException(f'Unexpected content for file {self._file_data.fileName}: {a}')
        url = a[len('url:'):]
        resolved_url = self._get_resolved_url(url=url)
        return resolved_url
    def _get_resolved_url(self, url: str) -> str:
        if self._resolved_url is not None and self._resolved_url_timestamp is not None:
            if time.time() - self._resolved_url_timestamp < 120:
                return self._resolved_url
        resolve_with_dandi_api_key = None
        if url.startswith('https://api.dandiarchive.org/api/'):
            dandi_api_key = os.environ.get('DANDI_API_KEY', None)
            if dandi_api_key is not None:
                resolve_with_dandi_api_key = dandi_api_key
        elif url.startswith('https://api-staging.dandiarchive.org/'):
            dandi_api_key = os.environ.get('DANDI_STAGING_API_KEY', None)
            if dandi_api_key is not None:
                resolve_with_dandi_api_key = dandi_api_key
        if resolve_with_dandi_api_key is not None:
            url0 = _resolve_dandi_url(url=url, dandi_api_key=resolve_with_dandi_api_key)
        else:
            url0 = url
        self._resolved_url = url0
        self._resolved_url_timestamp = time.time()
        return self._resolved_url

class ProjectJob:
    def __init__(self, job_data: DendroJob) -> None:
        self._job_data = job_data

class ProjectFolder:
    def __init__(self, project: Project, path: str) -> None:
        self._project = project
        self._path = path
    def get_files(self) -> List[ProjectFile]:
        ret: List[ProjectFile] = []
        for f in self._project._files:
            a = f._file_data.fileName.split('/')
            ok = False
            if len(a) <= 1:
                ok = (self._path == '')
            else:
                ok = '/'.join(a[:-1]) == self._path
            if ok:
                ret.append(f)
        return ret
    def get_folders(self) -> List['ProjectFolder']:
        folder_paths = set()
        for f in self._project._files:
            a = f._file_data.fileName.split('/')
            if len(a) <= 1:
                continue
            parent_path = '/'.join(a[:-1]) # the parent path for this file
            b = parent_path.split('/')
            for i in range(1, len(b)):
                b2 = b[:i]
                ok = False
                if len(b2) == 1:
                    # if the parent path is only one level deep, then include it if the self._path is empty
                    ok = (self._path == '')
                else:
                    ok = '/'.join(b2[:-1]) == self._path
                if ok:
                    folder_paths.add('/'.join(b2))
        sorted_folder_paths = sorted(list(folder_paths))
        return [
            ProjectFolder(self._project, p)
            for p in sorted_folder_paths
        ]

def load_project(project_id: str) -> Project:
    url_path = f'/api/client/projects/{project_id}'
    project_resp = _client_get_api_request(url_path=url_path)
    project: DendroProject = DendroProject(**project_resp['project'])

    url_path = f'/api/client/projects/{project_id}/files'
    files_resp = _client_get_api_request(url_path=url_path)
    files: List[DendroFile] = [DendroFile(**f) for f in files_resp['files']]

    url_path = f'/api/client/projects/{project_id}/jobs'
    jobs_resp = _client_get_api_request(url_path=url_path)
    jobs: List[DendroJob] = [DendroJob(**j) for j in jobs_resp['jobs']]

    if project.computeResourceId:
        url_path = f'/api/client/compute_resources/{project.computeResourceId}'
        compute_resource_resp = _client_get_api_request(url_path=url_path)
        compute_resource = DendroComputeResource(**compute_resource_resp['computeResource'])
    else:
        compute_resource = None

    return Project(project_data=project, files_data=files, jobs_data=jobs, compute_resource=compute_resource)

def _resolve_dandi_url(*, url: str, dandi_api_key: str):
    headers = {
        'Authorization': f'token {dandi_api_key}'
    }
    # do it synchronously here
    resp = requests.head(url, allow_redirects=True, headers=headers)
    return str(resp.url)
