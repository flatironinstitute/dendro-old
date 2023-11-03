import requests
from ..mock import using_mock
from pydantic import BaseModel


class SetOutputFileException(Exception):
    pass

class OutputFile(BaseModel):
    name: str
    job_id: str
    job_private_key: str
    was_uploaded: bool = False
    def set(self, local_file_path: str):
        print('output.set() is deprecated. Please use output.upload() instead.')
        self.upload(local_file_path)
    def upload(self, local_file_path: str):
        from .Job import _get_upload_url_for_output_file # avoid circular import
        upload_url = _get_upload_url_for_output_file(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)

        # Upload the file to the URL
        with open(local_file_path, 'rb') as f:
            if not using_mock():
                resp_upload = requests.put(upload_url, data=f, timeout=60 * 60 * 24 * 7)
                if resp_upload.status_code != 200:
                    print(upload_url)
                    raise SetOutputFileException(f'Error uploading file to bucket ({resp_upload.status_code}) {resp_upload.reason}: {resp_upload.text}')

        self.was_uploaded = True
