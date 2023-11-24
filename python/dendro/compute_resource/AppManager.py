from typing import List, Union
from pathlib import Path
import json

from ..sdk.App import App
from ..common.dendro_types import DendroComputeResourceApp
from ..common._api_request import _compute_resource_get_api_request, _compute_resource_put_api_request


class AppManager:
    def __init__(self, *,
                 compute_resource_id: str,
                 compute_resource_private_key: str,
                ):
        self._compute_resource_id = compute_resource_id
        self._compute_resource_private_key = compute_resource_private_key

        self._compute_resource_apps: List[DendroComputeResourceApp] = []
        self._apps: List[App] = []

    def update_apps(self):
        url_path = f'/api/compute_resource/compute_resources/{self._compute_resource_id}/apps'
        resp = _compute_resource_get_api_request(
            url_path=url_path,
            compute_resource_id=self._compute_resource_id,
            compute_resource_private_key=self._compute_resource_private_key
        )

        # It would be nice to do it this way, but we can't because we don't want to import stuff from the api here
        # from ..api_helpers.routers.compute_resource.router import GetAppsResponse
        # resp = GetAppsResponse(**resp)
        # compute_resource_apps = resp.apps

        # instead:
        compute_resource_apps_from_response = resp['apps']
        compute_resource_apps_from_response = [DendroComputeResourceApp(**app) for app in compute_resource_apps_from_response]
        something_changed = False
        for app in self._apps:
            matching_cr_app = next((cr_app for cr_app in compute_resource_apps_from_response if _app_matches(app, cr_app)), None)
            if not matching_cr_app:
                assert app._spec_uri is not None, 'Unexpected: app has no spec uri'
                self._unload_app(app._spec_uri)
                something_changed = True
        for cr_app_from_response in compute_resource_apps_from_response:
            matching_app = next((app for app in self._apps if _app_matches(app, cr_app_from_response)), None)
            if not matching_app:
                try:
                    self._load_app(cr_app_from_response)
                except Exception as e:
                    print(f'Error loading app {cr_app_from_response.specUri}')
                    print(e)
                    print('')
                    print('')
                    continue
                something_changed = True
        if something_changed:
            # Report the compute resource spec
            print('Reporting the compute resource spec')
            url_path = f'/api/compute_resource/compute_resources/{self._compute_resource_id}/spec'
            spec = {
                'apps': [a._spec_dict for a in self._apps]
            }
            _compute_resource_put_api_request(
                url_path=url_path,
                compute_resource_id=self._compute_resource_id,
                compute_resource_private_key=self._compute_resource_private_key,
                data={
                    'spec': spec
                }
            )
    def find_app_with_processor(self, processor_name: str) -> Union[App, None]:
        for app in self._apps:
            for p in app._processors:
                if p._name == processor_name:
                    return app
        return None
    def _unload_app(self, spec_uri: str):
        print(f'Unloading app {spec_uri}')
        self._apps = [app for app in self._apps if app._spec_uri != spec_uri]
    def _load_app(self, cr_app: DendroComputeResourceApp):
        print(f'Loading app {cr_app.specUri}')
        app = App.from_spec_uri(
            spec_uri=cr_app.specUri,
            aws_batch_opts=cr_app.awsBatch,
            slurm_opts=cr_app.slurm
        )
        self._apps.append(app)

        if app._aws_batch_opts is not None:
            from ..iaac.aws_batch_job_definition.job_definition import create_job_definition
            if app._slurm_opts is not None:
                raise Exception('App with awsBatch opts also has slurm opts')
            if app._app_image is None:
                raise Exception('App with awsBatch opts has no app image')
            stack_id = 'DendroBatchStack'
            dendro_home_path = Path().home() / ".dendro"
            created_resources_path = str(Path(dendro_home_path) / f"{stack_id}-created-resources.json")
            with open(created_resources_path, 'r') as f:
                created_resources = json.load(f)
            job_role_name = created_resources['batch_jobs_access_role_name']
            efs_fs_name = created_resources['efs_file_system_name']
            print(f'Creating AWS batch job definition for app {app._name}')
            create_job_definition(
                dendro_app_name=app._name,
                dendro_app_image_uri=app._app_image,
                job_role_name=job_role_name,
                efs_fs_name=efs_fs_name,
            )

        # print info about the app so we can see what's going on
        s = []
        if cr_app.awsBatch is not None:
            if cr_app.slurm is not None:
                print('WARNING: App has awsBatch opts but also has slurm opts')
            s.append(f'Use AWS Batch: {cr_app.awsBatch.useAwsBatch}')
        if cr_app.slurm is not None:
            slurm_cpus_per_task = cr_app.slurm.cpusPerTask
            slurm_partition = cr_app.slurm.partition
            slurm_time = cr_app.slurm.time
            slurm_other_opts = cr_app.slurm.otherOpts
            s.append(f'slurmCpusPerTask: {slurm_cpus_per_task}')
            s.append(f'slurmPartition: {slurm_partition}')
            s.append(f'slurmTime: {slurm_time}')
            s.append(f'slurmOtherOpts: {slurm_other_opts}')
        print(f'  {" | ".join(s)}')
        print(f'  {len(app._processors)} processors')
        print('')
        print('')

def _app_matches(app: App, cr_app: DendroComputeResourceApp) -> bool:
    return (
        app._spec_uri == cr_app.specUri and
        app._aws_batch_opts == cr_app.awsBatch and
        app._slurm_opts == cr_app.slurm
    )
