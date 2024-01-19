from typing import Union
import os
import requests
import h5py
from pydantic import BaseModel
import remfile
from .FileManifest import FileManifest


class InputFolderDownloadError(Exception):
    pass


class InputFolder(BaseModel):
    name: Union[str, None] = None # the name of the input within the context of the processor (not needed when one of url or local_folder_name is specified directly)
    url: Union[str, None] = None
    local_folder_name: Union[str, None] = None
    job_id: Union[str, None] = None
    job_private_key: Union[str, None] = None
    _file_manifest: Union[FileManifest, None] = None

    def get_url(self, relative_file_name: str) -> str:
        if self.url is not None:
            if self.local_folder_name is not None:
                raise Exception('Cannot specify both url and local_folder_name in InputFolder')
            if self.job_id is not None:
                raise Exception('Cannot specify both url and job_id in InputFolder')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both url and job_private_key in InputFolder')
            return self.url + '/' + relative_file_name
        elif self.local_folder_name is not None:
            if self.job_id is not None:
                raise Exception('Cannot specify both local_folder_name and job_id in InputFolder')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both local_folder_name and job_private_key in InputFolder')
            raise Exception('Cannot get url for local_folder in InputFolder')
        else:
            if self.job_id is None:
                raise Exception('Unexpected: job_id is None')
            if self.job_private_key is None:
                raise Exception('Unexpected: job_private_key is None')
            if self.name is None:
                raise Exception('Unexpected: name is None in InputFolder')
            from .Job import _get_file_manifest_for_input_folder # avoid circular import
            if self._file_manifest is None:
                self._file_manifest = _get_file_manifest_for_input_folder(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)
            ff = next((f for f in self._file_manifest.files if f.name == relative_file_name), None)
            if ff is None:
                raise Exception(f'Input folder file not found when trying to get download URL: {self.name} {relative_file_name}')
            return ff.url

    def download(self, dest_folder_path: str):
        if self.local_folder_name is not None:
            # In the case of a local folder, we just copy it
            print(f'Copying {self.local_folder_name} to {dest_folder_path}')
            import shutil
            shutil.copytree(self.local_folder_name, dest_folder_path)
            return
        if self.job_id is None:
            raise Exception('Unexpected: job_id is None')
        if self.job_private_key is None:
            raise Exception('Unexpected: job_private_key is None')
        if self.name is None:
            raise Exception('Unexpected: name is None in InputFolder')
        from .Job import _get_file_manifest_for_input_folder # avoid circular import
        if self._file_manifest is None:
            self._file_manifest = _get_file_manifest_for_input_folder(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)
        os.mkdir(dest_folder_path)
        for ff in self._file_manifest.files:
            file_name = ff.name
            file_url = ff.url
            dest_file_path = os.path.join(dest_folder_path, file_name)
            # make sure the parent directory exists
            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
            print(f'Downloading {file_url} to {dest_file_path}')
            # stream the download
            r = requests.get(file_url, stream=True, timeout=60 * 60 * 24 * 7)
            if r.status_code != 200:
                raise InputFolderDownloadError(f'Error downloading file {file_url}: {r.status_code} {r.reason}')
            with open(dest_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

    def get_file(self, relative_file_name, *, download: bool = False):
        if self.local_folder_name is not None:
            # In the case of a local file, we just return a file object
            f = open(os.path.join(self.local_folder_name, relative_file_name), 'rb')
            # An issue here is that this file is never closed. Not sure how to fix that.
            return f

        if download:
            if not os.path.exists('_download_inputs'):
                os.mkdir('_download_inputs')
            tmp_fname = f'_download_inputs/{self.name}'
            self.download(tmp_fname)
            f = open(os.path.join(tmp_fname, relative_file_name), 'rb')
            # An issue here is that this file is never closed. Not sure how to fix that.
            return f

        # We need to create an object that has a get_url() method
        # It's important to do it this way so that the url can renew as needed
        class FileInFolder:
            def __init__(self, input_folder: InputFolder, relative_file_name: str):
                self._input_folder = input_folder
                self._relative_file_name = relative_file_name

            def get_url(self):
                return self._input_folder.get_url(self._relative_file_name)
        the_file = FileInFolder(input_folder=self, relative_file_name=relative_file_name)
        return remfile.File(the_file)

    def get_h5py_file(self, relative_file_name):
        remf = self.get_file(relative_file_name)
        return h5py.File(remf, 'r')

    # validator is needed to be an allowed pydantic type
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, cls):
            return value
        else:
            raise ValueError(f'Unexpected type for InputFolder: {type(value)}')
