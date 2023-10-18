from typing import List
from ..common.protocaas_types import ProtocaasProject, ProtocaasFile, ProtocaasJob
from ..common._api_request import _client_get_api_request


class Project:
    def __init__(self, project_data: ProtocaasProject, files_data: List[ProtocaasFile], jobs_data: List[ProtocaasJob]) -> None:
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
            ProjectJob(j)
            for j in jobs_data
        ]
    def get_file(self, file_name: str) -> 'ProjectFile':
        for f in self._files:
            if f._file_data.fileName == file_name:
                return f
        raise Exception(f'File not found: {file_name}')

class ProjectFile:
    def __init__(self, file_data: ProtocaasFile) -> None:
        self._file_data = file_data
    def get_url(self) -> str:
        a = self._file_data.content
        if not a.startswith('url:'):
            raise Exception(f'Unexpected content for file {self._file_data.fileName}: {a}')
        return a[len('url:'):]

class ProjectFolder:
    def __init__(self, project: Project, path: str) -> None:
        self._project = project
        self._path = path
    def get_files(self) -> List[ProjectFile]:
        ret: List[ProjectFile] = []
        for f in self._project._files:
            a = f._file_name.split('/')
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
            a = f._file_name.split('/')
            if len(a) <= 1:
                continue
            parent_path = '/'.join(a[:-1])
            b = parent_path.split('/')
            ok = False
            if len(b) <= 1:
                ok = (self._path == '')
            else:
                ok = '/'.join(b[:-1]) == self._path
            if ok:
                folder_paths.add(parent_path)
        sorted_folder_paths = sorted(list(folder_paths))
        return [
            ProjectFolder(self._project, p)
            for p in sorted_folder_paths
        ]

class ProjectJob:
    def __init__(self, job_data: ProtocaasJob) -> None:
        self._job_data = job_data

def load_project(project_id: str) -> Project:
    url_path = f'/api/client/projects/{project_id}'
    project_resp = _client_get_api_request(url_path=url_path)
    project: ProtocaasProject = ProtocaasProject(**project_resp['project'])

    url_path = f'/api/client/projects/{project_id}/files'
    files_resp = _client_get_api_request(url_path=url_path)
    files: List[ProtocaasFile] = [ProtocaasFile(**f) for f in files_resp['files']]

    url_path = f'/api/client/projects/{project_id}/jobs'
    jobs_resp = _client_get_api_request(url_path=url_path)
    jobs: List[ProtocaasJob] = [ProtocaasJob(**j) for j in jobs_resp['jobs']]

    return Project(project, files, jobs)