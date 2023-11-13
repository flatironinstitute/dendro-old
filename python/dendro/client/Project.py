from typing import List
from ..common.dendro_types import DendroProject, DendroFile, DendroJob
from ..common._api_request import _client_get_api_request


class ProjectException(Exception):
    pass

class Project:
    def __init__(self, project_data: DendroProject, files_data: List[DendroFile], jobs_data: List[DendroJob]) -> None:
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
        raise ProjectException(f'File not found: {file_name}')
    def get_folder(self, path: str) -> 'ProjectFolder':
        return ProjectFolder(self, path)

class ProjectFile:
    def __init__(self, file_data: DendroFile) -> None:
        self._file_data = file_data
    def get_url(self) -> str:
        a = self._file_data.content
        if not a.startswith('url:'):
            raise ProjectException(f'Unexpected content for file {self._file_data.fileName}: {a}')
        return a[len('url:'):]

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

class ProjectJob:
    def __init__(self, job_data: DendroJob) -> None:
        self._job_data = job_data

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

    return Project(project, files, jobs)
