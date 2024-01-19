from typing import Union, List
import os
import shutil
import requests
from ..mock import using_mock
from pydantic import BaseModel


class SetOutputFolderException(Exception):
    pass

class OutputFolder(BaseModel):
    name: Union[str, None] = None # the name of the output within the context of the processor (not needed when output_folder_name is specified for local testing)
    job_id: Union[str, None] = None
    job_private_key: Union[str, None] = None
    was_uploaded: bool = False
    output_folder_name: Union[str, None] = None # for local testing
    def upload(self, local_folder_name: str):
        from .Job import _get_upload_url_for_output_folder_file # avoid circular import

        if self.output_folder_name is not None:
            if self.job_id is not None:
                raise Exception('Cannot specify both output_folder_name and job_id in OutputFolder')
            if self.job_private_key is not None:
                raise Exception('Cannot specify both output_folder_name and job_private_key in OutputFolder')
            # copy local_folder_name to output_folder_name
            print(f'Copying output {self.name} to {self.output_folder_name}')
            shutil.copytree(local_folder_name, self.output_folder_name)
        else:
            if self.name is None:
                raise Exception('Unexpected: name is None in OutputFolder')
            if self.job_id is None:
                raise Exception('Unexpected: job_id is None in OutputFolder')
            if self.job_private_key is None:
                raise Exception('Unexpected: job_private_key is None in OutputFolder')

            all_relative_file_names = _get_all_relative_file_names(local_folder_name)
            if 'file_manifest.json' in all_relative_file_names:
                raise Exception('Cannot have a file named file_manifest.json in the output folder.')
            file_manifest = {
                'files': [
                    {
                        'name': relative_file_name,
                        'size': os.path.getsize(local_folder_name + '/' + relative_file_name)
                    }
                    for relative_file_name in all_relative_file_names
                ]
            }
            with open(local_folder_name + '/file_manifest.json', 'w') as f:
                import json
                json.dump(file_manifest, f)
            all_relative_file_names.append('file_manifest.json')
            for relative_file_name in all_relative_file_names:
                local_file_name = local_folder_name + '/' + relative_file_name
                upload_url = _get_upload_url_for_output_folder_file(name=self.name, relative_file_name=relative_file_name, job_id=self.job_id, job_private_key=self.job_private_key)

                # Upload the file to the URL
                print(f'Uploading output file {self.name} {relative_file_name}')

                with open(local_file_name, 'rb') as f:
                    if not using_mock():
                        resp_upload = requests.put(upload_url, data=f, timeout=60 * 60 * 24 * 7)
                        if resp_upload.status_code != 200:
                            print(upload_url)
                            raise SetOutputFolderException(f'Error uploading folder file to bucket ({resp_upload.status_code}) {resp_upload.reason}: {resp_upload.text}')

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
            raise ValueError(f'Unexpected type for OutputFolder: {type(value)}')

def _get_all_relative_file_names(local_folder_name: str):
    import os
    ret: List[str] = []
    for root, dirs, files in os.walk(local_folder_name):
        for file in files:
            relative_file_name = os.path.relpath(os.path.join(root, file), local_folder_name)
            ret.append(relative_file_name)
    return ret
