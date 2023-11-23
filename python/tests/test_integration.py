import os
import pytest
import time
import tempfile
import shutil
import json


@pytest.mark.asyncio
@pytest.mark.api
async def test_integration(tmp_path):
    # important to put the imports inside so we don't get an import error when running the non-api tests
    from dendro.common.dendro_types import DendroProjectUser, DendroComputeResourceApp, CreateJobRequestInputParameter, CreateJobRequestInputFile, CreateJobRequestOutputFile
    from dendro.api_helpers.routers.gui._authenticate_gui_request import _create_mock_github_access_token
    from dendro.api_helpers.routers.gui.create_job_route import CreateJobRequest, CreateJobResponse
    from dendro.compute_resource.register_compute_resource import register_compute_resource
    from dendro.compute_resource.start_compute_resource import start_compute_resource
    from dendro.common._api_request import _use_api_test_client
    from dendro.mock import set_use_mock
    from dendro.api_helpers.clients._get_mongo_client import _clear_mock_mongo_databases
    from dendro.common._api_request import _gui_post_api_request, _client_get_api_request
    from dendro.common.dendro_types import ComputeResourceSlurmOpts

    tmpdir = str(tmp_path)

    from fastapi.testclient import TestClient
    app = _get_fastapi_app()
    test_client = TestClient(app)
    _use_api_test_client(test_client)
    set_use_mock(True)
    github_access_token = _create_mock_github_access_token()
    github_access_token_for_other_user = _create_mock_github_access_token()
    github_access_token_for_admin_user = _create_mock_github_access_token()
    admin_user_id = 'github|' + github_access_token_for_admin_user[len('mock:'):]

    this_dir = os.path.dirname(os.path.realpath(__file__))

    old_env = os.environ.copy()
    os.environ['ADMIN_USER_IDS'] = f'["{admin_user_id}"]'

    try:
        # Copy mock app source code
        shutil.copytree(src=this_dir + '/mock_app', dst=tmpdir + '/mock_app')
        shutil.copytree(src=this_dir + '/mock_app_2', dst=tmpdir + '/mock_app_2')

        # Create spec.json for mock_app and mock_app_2
        compute_resource_spec_app = _create_spec_json_for_mock_app(tmpdir + '/mock_app')
        compute_resource_spec_app_2 = _create_spec_json_for_mock_app(tmpdir + '/mock_app_2')

        # Create compute resource in a directory
        compute_resource_dir = tmpdir + '/compute_resource'
        os.mkdir(compute_resource_dir)
        compute_resource_id, compute_resource_private_key = register_compute_resource(dir=compute_resource_dir)

        # gui: Register compute resource
        _register_compute_resource(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, github_access_token=github_access_token, name='test-cr')

        # gui: Register the same compute resource again (should be okay)
        _register_compute_resource(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, github_access_token=github_access_token, name='test-cr-again')

        # gui: Fail register compute resource
        with pytest.raises(Exception):
            _register_compute_resource(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, github_access_token=github_access_token, name='test-cr', bad_resource_code=True)
        with pytest.raises(Exception):
            _register_compute_resource(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, github_access_token=github_access_token, name='test-cr', bad_signature=True)
        with pytest.raises(Exception):
            _register_compute_resource(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, github_access_token=github_access_token, name='test-cr', bad_resource_code_timestamp=True)

        # gui: set compute resource apps
        apps = [
            DendroComputeResourceApp(
                name='mock_app',
                specUri=f'file://{tmpdir}/mock_app/spec.json'
            ),
            DendroComputeResourceApp(
                name='mock_app_2',
                specUri=f'file://{tmpdir}/mock_app_2/spec.json',
                slurm=ComputeResourceSlurmOpts(
                    partition='test_partition',
                    time='1:00:00',
                    cpusPerTask=4,
                    otherOpts='--test=1'
                )
            )
        ]
        _set_compute_resource_apps(
            compute_resource_id=compute_resource_id,
            apps=apps,
            github_access_token=github_access_token
        )

        # gui: Fail at setting apps by other user
        with pytest.raises(Exception):
            _set_compute_resource_apps(
                compute_resource_id=compute_resource_id,
                apps=apps,
                github_access_token=github_access_token_for_other_user
            )

        # gui: Get compute resources for user
        _check_num_compute_resources_for_user(github_access_token=github_access_token, num_compute_resources=1)

        # gui: Try to get compute resource and one that does not exist
        _get_compute_resource(compute_resource_id=compute_resource_id, github_access_token=github_access_token)
        with pytest.raises(Exception):
            _get_compute_resource(compute_resource_id='compute-resource-does-not-exist', github_access_token=github_access_token)

        # gui: Get pubsub subscription
        _get_pubsub_subscription(compute_resource_id=compute_resource_id, github_access_token=github_access_token)

        # gui: Create projects
        project1_id = _create_project('project1', github_access_token=github_access_token)
        project2_id = _create_project('project2', github_access_token=github_access_token)

        # gui: Set project name
        _set_project_name(project_id=project1_id, name='project1_renamed', github_access_token=github_access_token)

        # gui: Set project description
        _set_project_description(project_id=project1_id, description='project1_description', github_access_token=github_access_token)

        # gui: Set project tags
        _set_project_tags(project_id=project1_id, tags=['tag1', 'tag2'], github_access_token=github_access_token)

        # gui: Fail because not authenticated
        with pytest.raises(Exception):
            _set_project_name(project_id=project1_id, name='project1_renamed_2', github_access_token='')
        with pytest.raises(Exception):
            _set_project_name(project_id=project1_id, name='project1_renamed_2', github_access_token=github_access_token + '-bad') # keep the mock: at the beginning

        # gui: Get project
        project = _get_project(project_id=project1_id, github_access_token=github_access_token)
        assert project.name == 'project1_renamed'
        assert project.description == 'project1_description'
        assert project.ownerId == 'github|' + github_access_token[len('mock:'):]
        assert project.users == []
        assert project.publiclyReadable is True
        assert project.tags == ['tag1', 'tag2']
        assert project.timestampCreated > 0
        assert project.timestampModified > 0
        assert project.computeResourceId is None

        # gui: Try to get project that does not exist
        with pytest.raises(Exception):
            _get_project(project_id='project-does-not-exist', github_access_token=github_access_token)

        # client: Get project
        _client_get_project(project_id=project1_id)

        # client: Try to get project that does not exist
        with pytest.raises(Exception):
            resp = _client_get_api_request(url_path='/api/client/projects/does_not_exist')

        # gui: Set the project to be not publicly readable
        _set_project_publicly_readable(project_id=project1_id, publicly_readable=False, github_access_token=github_access_token)

        # gui: Set projects compute resource id
        for project_id in [project1_id, project2_id]:
            _set_project_compute_resource_id(project_id=project_id, compute_resource_id=compute_resource_id, github_access_token=github_access_token)

        # gui: Set project users
        users = [
            DendroProjectUser(userId='github|user_viewer', role='viewer'),
            DendroProjectUser(userId='github|user_editor', role='editor'),
            DendroProjectUser(userId='github|user_admin', role='admin')
        ]
        _set_project_users(project_id=project1_id, users=users, github_access_token=github_access_token)

        # gui: Get project
        project = _get_project(project_id=project1_id, github_access_token=github_access_token)
        assert project.publiclyReadable is False
        assert project.computeResourceId == compute_resource_id
        assert project.users == users

        # gui: Get all projects
        projects = _get_all_projects_for_user(github_access_token=github_access_token)
        assert len(projects) == 2
        assert project1_id in [p.projectId for p in projects]
        assert project2_id in [p.projectId for p in projects]

        # gui: Admin get all projects
        projects = _admin_get_all_projects(github_access_token=github_access_token_for_admin_user)
        assert len(projects) == 2

        # gui: Get projects with tag
        projects = _get_projects_with_tag(tag='tag1', github_access_token=github_access_token)
        assert len(projects) == 1
        assert project1_id in [p.projectId for p in projects]

        # gui: Delete project
        _delete_project(project_id=project1_id, github_access_token=github_access_token)

        # gui: Get all projects
        projects = _get_all_projects_for_user(github_access_token=github_access_token)
        assert len(projects) == 1
        assert project2_id in [p.projectId for p in projects]

        # gui: Create a dummy input file (required for test job)
        _create_project_file(project_id=project2_id, file_name='mock-input', content='url:https://fake-url', github_access_token=github_access_token)

        # gui: Get file
        file = _get_project_file(project_id=project2_id, file_name='mock-input', github_access_token=github_access_token)
        assert file.fileName == 'mock-input'

        # gui: Try to get file that does not exist
        with pytest.raises(Exception):
            _get_project_file(project_id=project2_id, file_name='does_not_exist', github_access_token=github_access_token)

        # client: Get project files
        files = _client_get_project_files(project_id=project2_id)
        assert len(files) == 1

        # gui: Create and delete a file
        _create_project_file(project_id=project2_id, file_name='file-to-delete.txt', content='url:https://fake-url', github_access_token=github_access_token)
        _delete_project_file(project_id=project2_id, file_name='file-to-delete.txt', github_access_token=github_access_token)

        # gui: Try to delete a file that does not exist
        with pytest.raises(Exception):
            _delete_project_file(project_id=project2_id, file_name='does_not_exist', github_access_token=github_access_token)

        # gui: Get files
        files = _get_project_files(project_id=project2_id, github_access_token=github_access_token)
        assert len(files) == 1

        # gui: Create jobs for app 1
        job_id_1 = ''
        job_id_1_with_error = ''
        processor_name = 'mock-processor1'
        processor_spec = compute_resource_spec_app.processors[0]
        for intentional_error in [False, True]:
            req = CreateJobRequest(
                projectId=project2_id,
                processorName=processor_name,
                inputFiles=[
                    CreateJobRequestInputFile(name='input_file', fileName='mock-input'),
                    CreateJobRequestInputFile(name='input_list[0]', fileName='mock-input'),
                ],
                outputFiles=[
                    CreateJobRequestOutputFile(name='output_file', fileName='mock-output' if not intentional_error else 'mock-output-err')
                ],
                inputParameters=[
                    CreateJobRequestInputParameter(name='text1', value='this is text1'),
                    CreateJobRequestInputParameter(name='text2', value='this is text2'),
                    # text3 has a default
                    CreateJobRequestInputParameter(name='val1', value=12),
                    CreateJobRequestInputParameter(name='group.num', value=3),
                    CreateJobRequestInputParameter(name='group.secret_param', value='456'),
                    CreateJobRequestInputParameter(name='intentional_error', value=intentional_error)
                ],
                processorSpec=processor_spec,
                batchId=None,
                dandiApiKey=None,
            )
            resp = _gui_post_api_request(url_path='/api/gui/jobs', data=_model_dump(req), github_access_token=github_access_token)
            resp = CreateJobResponse(**resp)
            assert resp.success
            assert resp.jobId
            if not intentional_error:
                job_id_1 = resp.jobId
            else:
                job_id_1_with_error = resp.jobId

        # gui: Create job for app 2 (which uses slurm)
        processor_name_2 = 'mock-processor2'
        processor_spec_2 = compute_resource_spec_app_2.processors[0]
        req = CreateJobRequest(
            projectId=project2_id,
            processorName=processor_name_2,
            inputFiles=[],
            outputFiles=[],
            inputParameters=[
                CreateJobRequestInputParameter(
                    name='text1',
                    value='this is text1'
                )
            ],
            processorSpec=processor_spec_2,
            batchId=None,
            dandiApiKey=None,
        )
        resp = _gui_post_api_request(url_path='/api/gui/jobs', data=_model_dump(req), github_access_token=github_access_token)
        resp = CreateJobResponse(**resp)
        assert resp.success
        job_id_2 = resp.jobId
        assert job_id_2

        # gui: Test not providing a required parameter
        processor_name_2 = 'mock-processor2'
        processor_spec_2 = compute_resource_spec_app_2.processors[0]
        req = CreateJobRequest(
            projectId=project2_id,
            processorName=processor_name_2,
            inputFiles=[],
            outputFiles=[],
            inputParameters=[
            ],
            processorSpec=processor_spec_2,
            batchId=None,
            dandiApiKey=None,
        )
        with pytest.raises(Exception):
            _gui_post_api_request(url_path='/api/gui/jobs', data=_model_dump(req), github_access_token=github_access_token)

        # gui: Get job
        job = _get_job(job_id=job_id_1, github_access_token=github_access_token)
        assert job.projectId == project2_id
        assert job.processorName == processor_name
        assert job.processorSpec == processor_spec
        assert job.batchId is None
        assert job.dandiApiKey is None
        assert job.status == 'pending'
        assert job.timestampCreated > 0
        assert job.timestampStarted is None
        assert job.timestampFinished is None
        assert job.timestampQueued is None
        assert job.timestampStarting is None
        assert job.computeResourceId == compute_resource_id
        assert not job.jobPrivateKey # should not be exposed to GUI

        # gui: Try to get job that does not exist
        with pytest.raises(Exception):
            _get_job(job_id='job-does-not-exist', github_access_token=github_access_token)

        # gui: Get jobs
        jobs = _get_jobs(project_id=project2_id, github_access_token=github_access_token)
        assert len(jobs) == 3

        # gui: Get compute resource jobs
        jobs = _get_compute_resource_jobs(compute_resource_id=compute_resource_id, github_access_token=github_access_token)
        assert len(jobs) == 3

        # gui: Fail getting compute resource jobs by unauthorized user
        with pytest.raises(Exception):
            _get_compute_resource_jobs(compute_resource_id=compute_resource_id, github_access_token=github_access_token_for_other_user)

        # client: Get project jobs
        jobs = _client_get_project_jobs(project_id=project2_id)
        assert len(jobs) == 3

        # compute resource: get unfinished jobs
        jobs = _compute_resource_get_unfinished_jobs(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key)
        assert len(jobs) == 3
        job = jobs[0]
        assert job.jobPrivateKey

        # compute resource: fail getting unfinished jobs
        with pytest.raises(Exception):
            _compute_resource_get_unfinished_jobs(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, wrong_payload=True)
        with pytest.raises(Exception):
            _compute_resource_get_unfinished_jobs(compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key, wrong_signature=True)

        # processor: Get job output upload url
        url = _get_job_output_upload_url(job_id=job.jobId, job_private_key=job.jobPrivateKey, output_name='output_file')
        assert url

        # processor: Fail getting job output upload url for unknown output
        with pytest.raises(Exception):
            _get_job_output_upload_url(job_id=job.jobId, job_private_key=job.jobPrivateKey, output_name='unknown-output')

        # processor: Fail getting job output upload url do to incorrect private key
        with pytest.raises(Exception):
            _get_job_output_upload_url(job_id=job.jobId, job_private_key=job.jobPrivateKey + 'x', output_name='output_file')

        # Run the compute resource briefly (will handle the jobs)
        start_compute_resource(dir=compute_resource_dir, timeout=3, cleanup_old_jobs=False)

        # gui: Check that first job succeeded
        job = _get_job(job_id=job_id_1, github_access_token=github_access_token)
        assert job.status == 'completed'

        # gui: Get output file for first job
        file = _get_project_file(project_id=project2_id, file_name='mock-output', github_access_token=github_access_token)
        assert file.fileName == 'mock-output'

        # gui: Check that second job failed
        job = _get_job(job_id=job_id_1_with_error, github_access_token=github_access_token)
        assert job.status == 'failed'

        # gui: Check that job from slurm app succeeded
        job = _get_job(job_id=job_id_2, github_access_token=github_access_token)
        assert job.status == 'completed'

        # Check whether the appropriate compute resource spec was uploaded to the api
        compute_resource = _get_compute_resource(compute_resource_id=compute_resource_id, github_access_token=github_access_token)
        assert compute_resource.spec
        assert len(compute_resource.spec.apps) == 2

        # gui: Try delete job without proper github access token
        with pytest.raises(Exception):
            _delete_job(job_id=job_id_1, github_access_token='bad_access_token')

        # gui: Delete job (should trigger deletion of output file)
        _delete_job(job_id=job_id_1, github_access_token=github_access_token)

        # gui: Get jobs
        jobs = _get_jobs(project_id=project2_id, github_access_token=github_access_token)
        assert len(jobs) == 2

        # gui: Get files
        files = _get_project_files(project_id=project2_id, github_access_token=github_access_token)
        assert len(files) == 1
        assert files[0].fileName == 'mock-input'

        # gui: Fail at deleting compute resource by unauthorized user
        with pytest.raises(Exception):
            _delete_compute_resource(compute_resource_id=compute_resource_id, github_access_token=github_access_token_for_other_user)

        # gui: Delete compute resource
        _delete_compute_resource(compute_resource_id=compute_resource_id, github_access_token=github_access_token)

        # gui Get compute resources
        compute_resources = _get_compute_resources(github_access_token=github_access_token)
        assert len(compute_resources) == 0
    finally:
        _use_api_test_client(None)
        set_use_mock(False)
        _clear_mock_mongo_databases()
        os.environ = old_env

def _get_fastapi_app():
    from fastapi import FastAPI

    # this code is duplicated with api/index.py, I know
    from dendro.api_helpers.routers.processor.router import router as processor_router
    from dendro.api_helpers.routers.compute_resource.router import router as compute_resource_router
    from dendro.api_helpers.routers.client.router import router as client_router
    from dendro.api_helpers.routers.gui.router import router as gui_router

    app = FastAPI()

    # requests from a processing job
    app.include_router(processor_router, prefix="/api/processor", tags=["Processor"])

    # requests from a compute resource
    app.include_router(compute_resource_router, prefix="/api/compute_resource", tags=["Compute Resource"])

    # requests from a client (usually Python)
    app.include_router(client_router, prefix="/api/client", tags=["Client"])

    # requests from the GUI
    app.include_router(gui_router, prefix="/api/gui", tags=["GUI"])

    return app

class TemporaryDirectory:
    """A context manager for temporary directories"""
    def __init__(self):
        self._dir = None
    def __enter__(self):
        self._dir = tempfile.mkdtemp()
        return self._dir
    def __exit__(self, exc_type, exc_value, traceback):
        if self._dir:
            shutil.rmtree(self._dir)

def _create_spec_json_for_mock_app(app_dir: str):
    from dendro.sdk._make_spec_file import make_app_spec_file_function
    from dendro.common.dendro_types import ComputeResourceSpecApp

    spec_fname = app_dir + '/spec.json'
    make_app_spec_file_function(app_dir=app_dir, spec_output_file=spec_fname)
    assert os.path.exists(spec_fname)
    with open(spec_fname, 'r') as f:
        spec = json.load(f)
    compute_resource_spec = ComputeResourceSpecApp(**spec)
    return compute_resource_spec

def _register_compute_resource(compute_resource_id: str, compute_resource_private_key: str, github_access_token: str, name: str, bad_resource_code_timestamp: bool = False, bad_resource_code: bool = False, bad_signature: bool = False):
    from dendro.common._crypto_keys import sign_message
    from dendro.api_helpers.routers.gui.compute_resource_routes import RegisterComputeResourceRequest, RegisterComputeResourceResponse
    from dendro.common._api_request import _gui_post_api_request

    timestamp = int(time.time())
    if bad_resource_code_timestamp:
        timestamp = timestamp - 10000
    resource_code_payload = {'timestamp': timestamp}
    resource_code_signature = sign_message(resource_code_payload, compute_resource_id, compute_resource_private_key)
    if bad_signature:
        resource_code_signature = 'bad-signature'
    resource_code = f'{resource_code_payload["timestamp"]}-{resource_code_signature}'
    if bad_resource_code:
        resource_code = 'bad-resource-code'
    req = RegisterComputeResourceRequest(
        name=name,
        computeResourceId=compute_resource_id,
        resourceCode=resource_code
    )
    resp = _gui_post_api_request(url_path='/api/gui/compute_resources/register', data=_model_dump(req), github_access_token=github_access_token)
    resp = RegisterComputeResourceResponse(**resp)
    assert resp.success

def _set_compute_resource_apps(compute_resource_id: str, apps: list, github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import SetComputeResourceAppsRequest, SetComputeResourceAppsResponse
    from dendro.common._api_request import _gui_put_api_request

    req = SetComputeResourceAppsRequest(
        apps=apps
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}/apps', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetComputeResourceAppsResponse(**resp)
    assert resp.success

def _check_num_compute_resources_for_user(github_access_token: str, num_compute_resources: int):
    from dendro.api_helpers.routers.gui.compute_resource_routes import GetComputeResourcesResponse
    from dendro.common._api_request import _gui_get_api_request

    resp = _gui_get_api_request(url_path='/api/gui/compute_resources', github_access_token=github_access_token)
    resp = GetComputeResourcesResponse(**resp)
    assert resp.success
    assert len(resp.computeResources) == num_compute_resources

def _get_compute_resource(compute_resource_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import GetComputeResourceResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}', github_access_token=github_access_token)
    resp = GetComputeResourceResponse(**resp)
    assert resp.success
    assert resp.computeResource.computeResourceId == compute_resource_id
    return resp.computeResource

def _get_pubsub_subscription(compute_resource_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import GetPubsubSubscriptionResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}/pubsub_subscription', github_access_token=github_access_token)
    resp = GetPubsubSubscriptionResponse(**resp)
    assert resp.success

def _create_project(name: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import CreateProjectRequest, CreateProjectResponse
    from dendro.common._api_request import _gui_post_api_request
    req = CreateProjectRequest(
        name='project1'
    )
    resp = _gui_post_api_request(url_path='/api/gui/projects', data=_model_dump(req), github_access_token=github_access_token)
    resp = CreateProjectResponse(**resp)
    assert resp.success
    project1_id = resp.projectId
    assert project1_id
    return project1_id

def _set_project_name(project_id: str, name: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectNameRequest, SetProjectNameResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectNameRequest(
        name='project1_renamed'
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/name', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectNameResponse(**resp)
    assert resp.success

def _set_project_description(project_id: str, description: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectDescriptionRequest, SetProjectDescriptionResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectDescriptionRequest(
        description='project1_description'
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/description', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectDescriptionResponse(**resp)
    assert resp.success

def _set_project_tags(project_id: str, tags: list, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectTagsRequest, SetProjectTagsResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectTagsRequest(
        tags=['tag1', 'tag2']
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/tags', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectTagsResponse(**resp)
    assert resp.success

def _get_project(project_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import GetProjectResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project_id}', github_access_token=github_access_token)
    resp = GetProjectResponse(**resp)
    project = resp.project
    assert project.projectId == project_id
    return project

def _client_get_project(project_id: str):
    from dendro.api_helpers.routers.client.router import GetProjectResponse as ClientGetProjectResponse
    from dendro.common._api_request import _client_get_api_request
    resp = _client_get_api_request(url_path=f'/api/client/projects/{project_id}')
    resp = ClientGetProjectResponse(**resp)
    assert resp.success
    assert resp.project.projectId == project_id

def _set_project_publicly_readable(project_id: str, publicly_readable: bool, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectPubliclyReadableRequest, SetProjectPubliclyReadableResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectPubliclyReadableRequest(
        publiclyReadable=publicly_readable
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/publicly_readable', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectPubliclyReadableResponse(**resp)
    assert resp.success

def _set_project_compute_resource_id(project_id: str, compute_resource_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectComputeResourceIdRequest, SetProjectComputeResourceIdResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectComputeResourceIdRequest(
        computeResourceId=compute_resource_id
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/compute_resource_id', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectComputeResourceIdResponse(**resp)
    assert resp.success

def _set_project_users(project_id: str, users: list, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import SetProjectUsersRequest, SetProjectUsersResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetProjectUsersRequest(
        users=users
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/users', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetProjectUsersResponse(**resp)
    assert resp.success

def _get_all_projects_for_user(github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import GetProjectsResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path='/api/gui/projects', github_access_token=github_access_token)
    resp = GetProjectsResponse(**resp)
    projects = resp.projects
    return projects

def _admin_get_all_projects(github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import AdminGetAllProjectsResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path='/api/gui/projects/admin/get_all_projects', github_access_token=github_access_token)
    resp = AdminGetAllProjectsResponse(**resp)
    projects = resp.projects
    return projects

def _get_projects_with_tag(tag: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import GetProjectsResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path='/api/gui/projects?tag=tag1', github_access_token=github_access_token)
    resp = GetProjectsResponse(**resp)
    projects = resp.projects
    return projects

def _delete_project(project_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import DeleteProjectResponse
    from dendro.common._api_request import _gui_delete_api_request
    resp = _gui_delete_api_request(url_path=f'/api/gui/projects/{project_id}', github_access_token=github_access_token)
    resp = DeleteProjectResponse(**resp)
    assert resp.success

def _create_project_file(project_id: str, file_name: str, content: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.file_routes import SetFileRequest, SetFileResponse
    from dendro.common._api_request import _gui_put_api_request
    req = SetFileRequest(
        content=content,
        size=1
    )
    resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/files/{file_name}', data=_model_dump(req), github_access_token=github_access_token)
    resp = SetFileResponse(**resp)
    assert resp.success

def _get_project_file(project_id: str, file_name: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.file_routes import GetFileResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project_id}/files/{file_name}', github_access_token=github_access_token)
    resp = GetFileResponse(**resp)
    assert resp.success
    return resp.file

def _client_get_project_files(project_id: str):
    from dendro.api_helpers.routers.client.router import GetProjectFilesResponse as ClientGetProjectFilesResponse
    from dendro.common._api_request import _client_get_api_request
    resp = _client_get_api_request(url_path=f'/api/client/projects/{project_id}/files')
    resp = ClientGetProjectFilesResponse(**resp)
    assert resp.success
    return resp.files

def _delete_project_file(project_id: str, file_name: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.file_routes import DeleteFileResponse
    from dendro.common._api_request import _gui_delete_api_request
    resp = _gui_delete_api_request(url_path=f'/api/gui/projects/{project_id}/files/{file_name}', github_access_token=github_access_token)
    resp = DeleteFileResponse(**resp)
    assert resp.success

def _get_project_files(project_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.file_routes import GetFilesResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project_id}/files', github_access_token=github_access_token)
    resp = GetFilesResponse(**resp)
    assert resp.success
    return resp.files

def _get_job(job_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.job_routes import GetJobResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/jobs/{job_id}', github_access_token=github_access_token)
    resp = GetJobResponse(**resp)
    job = resp.job
    assert job.jobId == job_id
    return job

def _get_jobs(project_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.project_routes import GetJobsResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project_id}/jobs', github_access_token=github_access_token)
    resp = GetJobsResponse(**resp)
    jobs = resp.jobs
    return jobs

def _get_compute_resource_jobs(compute_resource_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import GetJobsForComputeResourceResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}/jobs', github_access_token=github_access_token)
    resp = GetJobsForComputeResourceResponse(**resp)
    assert resp.success
    return resp.jobs

def _client_get_project_jobs(project_id: str):
    from dendro.api_helpers.routers.client.router import GetProjectJobsResponse as ClientGetProjectJobsResponse
    from dendro.common._api_request import _client_get_api_request
    resp = _client_get_api_request(url_path=f'/api/client/projects/{project_id}/jobs')
    resp = ClientGetProjectJobsResponse(**resp)
    assert resp.success
    return resp.jobs

def _delete_job(job_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.job_routes import DeleteJobResponse
    from dendro.common._api_request import _gui_delete_api_request
    resp = _gui_delete_api_request(url_path=f'/api/gui/jobs/{job_id}', github_access_token=github_access_token)
    resp = DeleteJobResponse(**resp)
    assert resp.success

def _delete_compute_resource(compute_resource_id: str, github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import DeleteComputeResourceResponse
    from dendro.common._api_request import _gui_delete_api_request
    resp = _gui_delete_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}', github_access_token=github_access_token)
    resp = DeleteComputeResourceResponse(**resp)
    assert resp.success

def _get_compute_resources(github_access_token: str):
    from dendro.api_helpers.routers.gui.compute_resource_routes import GetComputeResourcesResponse
    from dendro.common._api_request import _gui_get_api_request
    resp = _gui_get_api_request(url_path='/api/gui/compute_resources', github_access_token=github_access_token)
    resp = GetComputeResourcesResponse(**resp)
    assert resp.success
    return resp.computeResources

def _compute_resource_get_unfinished_jobs(compute_resource_id: str, compute_resource_private_key: str, wrong_payload: bool = False, wrong_signature: bool = False):
    from dendro.common.dendro_types import DendroJob
    from dendro.common._api_request import _compute_resource_get_api_request
    url_path = f'/api/compute_resource/compute_resources/{compute_resource_id}/unfinished_jobs'
    resp = _compute_resource_get_api_request(
        url_path=url_path,
        compute_resource_id=compute_resource_id,
        compute_resource_private_key=compute_resource_private_key,
        _wrong_payload_for_testing=wrong_payload,
        _wrong_signature_for_testing=wrong_signature
    )
    jobs = resp['jobs']
    jobs = [DendroJob(**job) for job in jobs]
    return jobs

def _get_job_output_upload_url(job_id: str, job_private_key: str, output_name: str):
    from dendro.api_helpers.routers.processor.router import ProcessorGetJobOutputUploadUrlResponse
    from dendro.common._api_request import _processor_get_api_request
    headers = {
        'job-private-key': job_private_key,
        'job-id': job_id
    }
    resp = _processor_get_api_request(url_path=f'/api/processor/jobs/{job_id}/outputs/{output_name}/upload_url', headers=headers)
    resp = ProcessorGetJobOutputUploadUrlResponse(**resp)
    return resp.uploadUrl

def _model_dump(model, exclude_none=False):
    # handle both pydantic v1 and v2
    if hasattr(model, 'model_dump'):
        return model.model_dump(exclude_none=exclude_none)
    else:
        return model.dict(exclude_none=exclude_none)
