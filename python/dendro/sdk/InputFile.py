import requests
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Job import Job


class InputFileDownloadError(Exception):
    pass


class InputFile:
    def __init__(self, *, name: str, job: 'Job') -> None:
        self._name = name
        self._job = job

    def get_url(self) -> str:
        return self._job._get_download_url_for_input_file(name=self._name)

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

    def to_si_recording(self, electrical_series_path: str):
        from .utils.input_file import to_si_recording

        return to_si_recording(
            url=self.get_url(),
            electrical_series_path=electrical_series_path
        )
