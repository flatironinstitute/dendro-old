from typing import Union
import os
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
        from .Job import _get_file_id_for_output_file # avoid circular import

        # The file will get deleted upon upload/move, so let's make sure it's not in the cache dir
        # because we don't want to inadvertently delete files in the cache dir
        FILE_CACHE_DIR = os.getenv('DENDRO_FILE_CACHE_DIR', None)
        if FILE_CACHE_DIR:
            if local_file_name.startswith(FILE_CACHE_DIR):
                raise Exception(f'Cannot upload file directly from file cache directory: {local_file_name}')

        if self.output_file_name is not None:
            if self.job_id is not None:
                raise Exception('Cannot specify both output_file_name and job_id in OutputFile')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both output_file_name and job_private_key in OutputFile')
            # copy local_file_name to output_file_name
            if local_file_name != self.output_file_name:
                print(f'Moving output {self.name} to {self.output_file_name}')
                shutil.move(local_file_name, self.output_file_name)
            else:
                print(f'Output {self.name} is already in the correct location')
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

            # Write to the file cache
            if FILE_CACHE_DIR:
                file_id = _get_file_id_for_output_file(name=self.name, job_id=self.job_id, job_private_key=self.job_private_key)
                file_cache_path = os.path.join(FILE_CACHE_DIR, file_id)
                if not os.path.exists(file_cache_path):
                    print(f'Moving {local_file_name} to {file_cache_path}')
                    shutil.move(local_file_name, file_cache_path)

            # In all cases we delete the local file because then we don't have different behavior in different cases
            print(f'Deleting local file {local_file_name}')
            if os.path.exists(local_file_name):
                os.remove(local_file_name)

        self.was_uploaded = True

    # validator is needed to be an allowed pydantic type
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, cls):
            return value
        else:
            raise ValueError(f'Unexpected type for OutputFile: {type(value)}')
