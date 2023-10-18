from typing import TYPE_CHECKING
import requests

if TYPE_CHECKING:
    from .Job import Job


class OutputFile:
    def __init__(self, *, name: str, job: 'Job') -> None:
        self._name = name
        self._job = job
        self._was_set = False
    def set(self, local_file_path: str):
        upload_url = self._job._get_upload_url_for_output_file(name=self._name)

        # Upload the file to the URL
        with open(local_file_path, 'rb') as f:
            resp_upload = requests.put(upload_url, data=f)
            if resp_upload.status_code != 200:
                print(upload_url)
                raise Exception(f'Error uploading file to bucket ({resp_upload.status_code}) {resp_upload.reason}: {resp_upload.text}')
        
        self._was_set = True