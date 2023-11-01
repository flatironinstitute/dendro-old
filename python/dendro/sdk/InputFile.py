from typing import Union
import requests
import h5py
import remfile
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Job import Job


class InputFileDownloadError(Exception):
    pass


class InputFile:
    def __init__(self, *, name: str, job: Union['Job', None] = None, url: Union[str, None] = None) -> None:
        self._name = name
        self._job = job
        self._direct_url = url

        if self._job is None and self._direct_url is None:
            raise Exception('Either job or url must be specified in InputFile')

    def get_url(self) -> str:
        if self._direct_url is not None:
            return self._direct_url
        elif self._job is not None:
            return self._job._get_download_url_for_input_file(name=self._name)
        else:
            raise Exception('Unexpected: both direct_url and job are None')

    def download(self, dest_file_path: str):
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

    def get_h5py_file(self):
        url = self.get_url()
        remf = remfile.File(url)
        return h5py.File(remf, 'r')
