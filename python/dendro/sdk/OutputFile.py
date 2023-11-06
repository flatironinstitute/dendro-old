from typing import Union
import shutil
import requests
from ..mock import using_mock
from pydantic import BaseModel


class SetOutputFileException(Exception):
    pass

class OutputFile(BaseModel):
    name: Union[str, None] = None # the name of the output within the context of the processor (not needed when output_file_name is specified for local testing)
    job_id: Union[str, None] = None
    job_private_key: Union[str, None] = None
    was_uploaded: bool = False
    output_file_name: Union[str, None] = None # for local testing
    def set(self, local_file_name: str):
        print('output.set() is deprecated. Please use output.upload() instead.')
        self.upload(local_file_name)
    def upload(self, local_file_name: str):
        from .Job import _get_upload_url_for_output_file # avoid circular import

        if self.output_file_name is not None:
            if self.job_id is not None:
                raise Exception('Cannot specify both output_file_name and job_id in OutputFile')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both output_file_name and job_private_key in OutputFile')
            # copy local_file_name to output_file_name
            print(f'Writing output {self.name} to {self.output_file_name}')
            shutil.copy(local_file_name, self.output_file_name)
        else:
            if self.name is None:
                raise Exception('Unexpected: name is None in OutputFile')
            if self.job_id is None:
                raise Exception('Unexpected: job_id is None in OutputFile')
            if self.job_private_key is None:
                raise Exception('Unexpected: job_private_key is None in OutputFile')
            upload_url = _get_upload_url_for_output_file(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)

            # Upload the file to the URL
            print(f'Uploading output file {self.name}') # it could be a security issue to provide the url in this print statement
            with open(local_file_name, 'rb') as f:
                if not using_mock():
                    resp_upload = requests.put(upload_url, data=f, timeout=60 * 60 * 24 * 7)
                    if resp_upload.status_code != 200:
                        print(upload_url)
                        raise SetOutputFileException(f'Error uploading file to bucket ({resp_upload.status_code}) {resp_upload.reason}: {resp_upload.text}')

        self.was_uploaded = True
