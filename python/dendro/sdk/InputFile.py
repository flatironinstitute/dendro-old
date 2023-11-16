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
    job_id: Union[str, None] = None
    job_private_key: Union[str, None] = None

    def get_url(self) -> str:
        if self.url is not None:
            if self.local_file_name is not None:
                raise Exception('Cannot specify both url and local_file_name in InputFile')
            if self.job_id is not None:
                raise Exception('Cannot specify both url and job_id in InputFile')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both url and job_private_key in InputFile')
            return self.url
        elif self.local_file_name is not None:
            if self.job_id is not None:
                raise Exception('Cannot specify both local_file_name and job_id in InputFile')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both local_file_name and job_private_key in InputFile')
            raise Exception('Cannot get url for local_file in InputFile')
        else:
            if self.job_id is None:
                raise Exception('Unexpected: job_id is None')
            if self.job_private_key is None:
                raise Exception('Unexpected: job_private_key is None')
            from .Job import _get_download_url_for_input_file # avoid circular import
            if self.name is None:
                raise Exception('Unexpected: name is None in InputFile')
            return _get_download_url_for_input_file(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)

    def download(self, dest_file_path: str):
        if self.local_file_name is not None:
            # In the case of a local file, we just copy it
            print(f'Copying {self.local_file_name} to {dest_file_path}')
            import shutil
            shutil.copyfile(self.local_file_name, dest_file_path)
            return
        url = self.get_url()
        print(f'Downloading {url} to {dest_file_path}')
        # stream the download
        r = requests.get(url, stream=True, timeout=60 * 60 * 24 * 7)
        if r.status_code != 200:
            raise InputFileDownloadError(f'Error downloading file {url}: {r.status_code} {r.reason}')
        with open(dest_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def get_file(self, *, download: bool = False):
        if self.local_file_name is not None:
            # In the case of a local file, we just return a file object
            f = open(self.local_file_name, 'rb')
            # An issue here is that this file is never closed. Not sure how to fix that.
            return f

        if download:
            if not os.path.exists('_download_inputs'):
                os.mkdir('_download_inputs')
            tmp_fname = f'_download_inputs/{self.name}'
            self.download(tmp_fname)
            f = open(tmp_fname, 'rb')
            # An issue here is that this file is never closed. Not sure how to fix that.
            return f

        # self has a get_url() method
        # It's important to do it this way so that the url can renew as needed
        return remfile.File(self)

    def get_h5py_file(self):
        remf = self.get_file()
        return h5py.File(remf, 'r')

    # validator is needed to be an allowed pydantic type
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        else:
            raise ValueError(f'Unexpected type for InputFile: {type(v)}')
