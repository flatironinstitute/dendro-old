from typing import Union
import os
import requests
import h5py
from pydantic import BaseModel
import remfile


class InputFileDownloadError(Exception):
    pass


class InputFile(BaseModel):
    name: Union[str, None] = None # the name of the input within the context of the processor (not needed when one of url or local_file_name is specified directly)
    url: Union[str, None] = None
    local_file_name: Union[str, None] = None
    project_file_uri: Union[str, None] = None
    project_file_name: str = ''
    job_id: Union[str, None] = None
    job_private_key: Union[str, None] = None

    def get_url(self) -> str:
        if self.url is not None:
            return self.url
        if self.local_file_name is not None:
            raise Exception('Cannot get url for local file in InputFile')
        uri = self.get_project_file_uri()
        if uri.startswith('http://') or uri.startswith('https://'):
            return uri
        from .Job import _get_download_url_for_uri # avoid circular import
        if self.job_id is None:
            raise Exception('Cannot get url for uri when job_id is None')
        if self.job_private_key is None:
            raise Exception('Cannot get url for uri when job_private_key is None')
        return _get_download_url_for_uri(uri=uri, job_id=self.job_id, job_private_key=self.job_private_key)

    def get_project_file_name(self) -> str:
        return self.project_file_name

    def get_project_file_uri(self) -> str:
        if self.project_file_uri:
            return self.project_file_uri
        if self.job_id is None:
            raise Exception('Unexpected: job_id is None')
        if self.job_private_key is None:
            raise Exception('Unexpected: job_private_key is None')
        from .Job import _get_uri_and_label_for_input_file # avoid circular import
        if self.name is None:
            raise Exception('name is None in InputFile and project_file_uri is also None')
        uri, label = _get_uri_and_label_for_input_file(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)
        self.project_file_uri = uri
        return uri

    def download(self, dest_file_path: Union[str, None] = None):
        # This should have already been checked when the InputFile was created
        # but it doesn't hurt to do it again
        self._check_file_cache()

        if self.local_file_name is not None:
            # In the case of a local file, we just copy it
            if dest_file_path is not None and dest_file_path != self.local_file_name:
                print(f'Copying {self.local_file_name} to {dest_file_path}')
                import shutil
                shutil.copyfile(self.local_file_name, dest_file_path)
                return
            else:
                # The file is already in the right place
                return
        url = self.get_url()
        file_id = self._get_project_file_id()
        FILE_CACHE_DIR = os.getenv('DENDRO_FILE_CACHE_DIR', None)
        if file_id and FILE_CACHE_DIR:
            cached_file_path = os.path.join(FILE_CACHE_DIR, file_id)
            if os.path.exists(cached_file_path):
                # this is unexpected because we should have checked the cache already
                raise Exception(f'Unexpected: file {cached_file_path} exists even though we already checked the cache')
            else:
                # download the file to the cache
                rnd = _random_string(10)
                print(f'Downloading {url} to {cached_file_path}.download.{rnd}')
                _download_file(url, f'{cached_file_path}.download.{rnd}')
                if os.path.exists(cached_file_path):
                    # I guess it was downloaded by someone else
                    print(f'File {cached_file_path} already exists. It must have been downloaded by someone else. Deleting {cached_file_path}.download.{rnd}')
                    os.remove(f'{cached_file_path}.download.{rnd}')
                else:
                    # This is the usual case
                    os.rename(f'{cached_file_path}.download.{rnd}', cached_file_path)
                if dest_file_path is not None:
                    # The file is in the cache and we have a destination file path
                    print(f'Copying {cached_file_path} to {dest_file_path}')
                    import shutil
                    shutil.copyfile(cached_file_path, dest_file_path)
                    self.local_file_name = dest_file_path
                    return
                else:
                    # The file is in the cache and we don't have a destination file path
                    self.local_file_name = cached_file_path
                    return
        else:
            if dest_file_path is not None:
                # We have a destination file path and we don't have a cache
                print(f'Downloading {url} to {dest_file_path}')
                _download_file(url, dest_file_path)
                self.local_file_name = dest_file_path
                return
            else:
                # We don't have a destination file path and we don't have a cache
                temp_file_path = f'/tmp/{_random_string(10)}.download'
                print(f'Downloading {url} to {temp_file_path}')
                _download_file(url, temp_file_path)
                self.local_file_name = temp_file_path
                return

    def is_local(self) -> bool:
        return self.local_file_name is not None

    def get_local_file_name(self) -> Union[str, None]:
        return self.local_file_name

    def get_file(self, *, download: bool = False):
        if self.local_file_name is not None:
            # In the case of a local file, we just return a file object
            f = open(self.local_file_name, 'rb')
            # An issue here is that this file is never closed. Not sure how to fix that.
            return f

        if download:
            self.download()

        # self has a get_url() method
        # It's important to do it this way so that the url can renew as needed
        return remfile.File(self)

    def get_h5py_file(self):
        remf = self.get_file()
        return h5py.File(remf, 'r')

    def _get_project_file_id(self) -> Union[str, None]:
        uri = self.get_project_file_uri()
        from .Job import _parse_dendro_uri # avoid circular import
        file_id, is_folder, label = _parse_dendro_uri(uri)
        return file_id

    def _check_file_cache(self):
        file_id = self._get_project_file_id()
        FILE_CACHE_DIR = os.getenv('DENDRO_FILE_CACHE_DIR', None)
        if file_id and FILE_CACHE_DIR:
            cached_file_path = os.path.join(FILE_CACHE_DIR, file_id)
            if os.path.exists(cached_file_path):
                print(f'Using input file {self.name} from cache: {cached_file_path}')
                self.local_file_name = cached_file_path

    # validator is needed to be an allowed pydantic type
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, cls):
            return value
        else:
            raise ValueError(f'Unexpected type for InputFile: {type(value)}')

def _download_file(url: str, dest_file_path: str):
    # stream the download
    r = requests.get(url, stream=True, timeout=60 * 60 * 24 * 7)
    if r.status_code != 200:
        raise InputFileDownloadError(f'Error downloading file {url}: {r.status_code} {r.reason}')
    with open(dest_file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def _random_string(length: int) -> str:
    import random
    import string
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))
