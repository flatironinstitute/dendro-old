import os
import pytest
import time
import tempfile
import shutil
import json


@pytest.mark.asyncio
@pytest.mark.api
async def test_integration(tmp_path):
    # important to put the tests inside so we don't get an import error when running the non-api tests
    from protocaas.api_helpers.core.protocaas_types import ProtocaasProjectUser, ComputeResourceSpecApp, ProtocaasComputeResourceApp
    from protocaas.api_helpers.routers.gui._authenticate_gui_request import _create_mock_github_access_token
    from protocaas.common._crypto_keys import sign_message
    from protocaas.api_helpers.routers.gui.project_routes import CreateProjectRequest, CreateProjectResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectNameRequest, SetProjectNameResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectDescriptionRequest, SetProjectDescriptionResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectTagsRequest, SetProjectTagsResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectPubliclyReadableRequest, SetProjectPubliclyReadableResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectComputeResourceIdRequest, SetProjectComputeResourceIdResponse
    from protocaas.api_helpers.routers.gui.project_routes import SetProjectUsersRequest, SetProjectUsersResponse
    from protocaas.api_helpers.routers.gui.project_routes import GetProjectResponse
    from protocaas.api_helpers.routers.gui.project_routes import GetProjectsResponse
    from protocaas.api_helpers.routers.gui.project_routes import DeleteProjectResponse
    from protocaas.api_helpers.routers.gui.project_routes import GetJobsResponse
    from protocaas.api_helpers.routers.gui.create_job_route import CreateJobRequest, CreateJobResponse, CreateJobRequestInputParameter
    from protocaas.api_helpers.routers.gui.job_routes import GetJobResponse
    from protocaas.api_helpers.routers.gui.job_routes import DeleteJobResponse
    from protocaas.api_helpers.routers.gui.compute_resource_routes import SetComputeResourceAppsRequest, SetComputeResourceAppsResponse, GetComputeResourceResponse
    from protocaas.compute_resource.register_compute_resource import register_compute_resource
    from protocaas.compute_resource.start_compute_resource import start_compute_resource
    from protocaas.common._api_request import _use_api_test_client
    from protocaas.api_helpers.routers.gui.compute_resource_routes import RegisterComputeResourceRequest, RegisterComputeResourceResponse
    from protocaas.mock import set_use_mock
    from protocaas.api_helpers.clients._get_mongo_client import _clear_mock_mongo_databases
    from protocaas.common._api_request import _gui_get_api_request, _gui_post_api_request, _gui_put_api_request, _gui_delete_api_request
    from protocaas.sdk._make_spec_file import make_app_spec_file_function

    tmpdir = str(tmp_path)

    from fastapi.testclient import TestClient
    app = _get_fastapi_app()
    test_client = TestClient(app)
    _use_api_test_client(test_client)
    set_use_mock(True)
    github_access_token = _create_mock_github_access_token()

    this_dir = os.path.dirname(os.path.realpath(__file__))

    try:
        # Copy mock app source code
        shutil.copytree(src=this_dir + '/mock_app', dst=tmpdir + '/mock_app')

        # Create spec.json for mock app
        make_app_spec_file_function(app_dir=tmpdir + '/mock_app', spec_output_file=tmpdir + '/mock_app/spec.json')
        assert os.path.exists(tmpdir + '/mock_app/spec.json')
        with open(tmpdir + '/mock_app/spec.json', 'r') as f:
            spec = json.load(f)
        compute_resource_spec_app = ComputeResourceSpecApp(**spec)

        # Register compute resource in directory
        compute_resource_id, compute_resource_private_key = register_compute_resource(dir=tmpdir, node_name='test_node')

        # gui: Register compute resource
        resource_code_payload = {'timestamp': int(time.time())}
        resource_code_signature = sign_message(resource_code_payload, compute_resource_id, compute_resource_private_key)
        resource_code = f'{resource_code_payload["timestamp"]}-{resource_code_signature}'
        req = RegisterComputeResourceRequest(
            name='test_compute_resource',
            computeResourceId=compute_resource_id,
            resourceCode=resource_code
        )
        resp = _gui_post_api_request(url_path='/api/gui/compute_resources/register', data=req.dict(), github_access_token=github_access_token)
        resp = RegisterComputeResourceResponse(**resp)
        assert resp.success

        # gui: set compute resource apps
        req = SetComputeResourceAppsRequest(
            apps=[
                ProtocaasComputeResourceApp(
                    name='mock_app',
                    specUri=f'file://{tmpdir}/mock_app/spec.json'
                )
            ]
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}/apps', data=req.dict(), github_access_token=github_access_token)
        resp = SetComputeResourceAppsResponse(**resp)
        assert resp.success

        # # Generate compute resource keys
        # public_key_hex, private_key_hex = generate_keypair()
        # compute_resource_id = public_key_hex
        # compute_resource_private_key = private_key_hex

        # gui: Create projects
        req = CreateProjectRequest(
            name='project1'
        )
        resp = _gui_post_api_request(url_path='/api/gui/projects', data=req.dict(), github_access_token=github_access_token)
        resp = CreateProjectResponse(**resp)
        assert resp.success
        project1_id = resp.projectId
        req = CreateProjectRequest(
            name='project2'
        )
        resp = _gui_post_api_request(url_path='/api/gui/projects', data=req.dict(), github_access_token=github_access_token)
        resp = CreateProjectResponse(**resp)
        assert resp.success
        project2_id = resp.projectId

        # gui: Set project name
        req = SetProjectNameRequest(
            name='project1_renamed'
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project1_id}/name', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectNameResponse(**resp)
        assert resp.success

        # gui: Set project description
        req = SetProjectDescriptionRequest(
            description='project1_description'
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project1_id}/description', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectDescriptionResponse(**resp)
        assert resp.success

        # gui: Set project tags
        req = SetProjectTagsRequest(
            tags=['tag1', 'tag2']
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project1_id}/tags', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectTagsResponse(**resp)
        assert resp.success

        # gui: Get project
        resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project1_id}', github_access_token=github_access_token)
        resp = GetProjectResponse(**resp)
        project = resp.project
        assert project.projectId == project1_id
        assert project.name == 'project1_renamed'
        assert project.description == 'project1_description'
        assert project.ownerId == 'github|__mock__user'
        assert project.users == []
        assert project.publiclyReadable is True
        assert project.tags == ['tag1', 'tag2']
        assert project.timestampCreated > 0
        assert project.timestampModified > 0
        assert project.computeResourceId is None

        # gui: Set project publicly readable
        req = SetProjectPubliclyReadableRequest(
            publiclyReadable=False
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project1_id}/publicly_readable', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectPubliclyReadableResponse(**resp)
        assert resp.success

        # gui: Set project compute resource id
        for project_id in [project1_id, project2_id]:
            req = SetProjectComputeResourceIdRequest(
                computeResourceId=compute_resource_id
            )
            resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project_id}/compute_resource_id', data=req.dict(), github_access_token=github_access_token)
            resp = SetProjectComputeResourceIdResponse(**resp)
            assert resp.success

        # gui: Set project users
        req = SetProjectUsersRequest(
            users=[
                ProtocaasProjectUser(userId='github|user_viewer', role='viewer'),
                ProtocaasProjectUser(userId='github|user_editor', role='editor'),
                ProtocaasProjectUser(userId='github|user_admin', role='admin')
            ]
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project1_id}/users', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectUsersResponse(**resp)
        assert resp.success

        # gui: Get project
        resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project1_id}', github_access_token=github_access_token)
        resp = GetProjectResponse(**resp)
        project = resp.project
        assert project.publiclyReadable is False
        assert project.computeResourceId == compute_resource_id
        assert project.users == [
            ProtocaasProjectUser(userId='github|user_viewer', role='viewer'), # hmmm, how are these classes being compared?
            ProtocaasProjectUser(userId='github|user_editor', role='editor'),
            ProtocaasProjectUser(userId='github|user_admin', role='admin')
        ]

        # gui: Get all projects
        resp = _gui_get_api_request(url_path='/api/gui/projects', github_access_token=github_access_token)
        resp = GetProjectsResponse(**resp)
        projects = resp.projects
        assert len(projects) == 2
        assert project1_id in [p.projectId for p in projects]

        # gui: Delete project
        resp = _gui_delete_api_request(url_path=f'/api/gui/projects/{project1_id}', github_access_token=github_access_token)
        resp = DeleteProjectResponse(**resp)
        assert resp.success

        # gui: Get all projects
        resp = _gui_get_api_request(url_path='/api/gui/projects', github_access_token=github_access_token)
        resp = GetProjectsResponse(**resp)
        projects = resp.projects
        assert len(projects) == 1

        # gui: Set project compute resource id
        req = SetProjectComputeResourceIdRequest(
            computeResourceId=compute_resource_id
        )
        resp = _gui_put_api_request(url_path=f'/api/gui/projects/{project2_id}/compute_resource_id', data=req.dict(), github_access_token=github_access_token)
        resp = SetProjectComputeResourceIdResponse(**resp)
        assert resp.success

        # gui: Create job
        processor_name = 'mock-processor1'
        processor_spec = compute_resource_spec_app.processors[0]
        req = CreateJobRequest(
            projectId=project2_id,
            processorName=processor_name,
            inputFiles=[],
            outputFiles=[],
            inputParameters=[
                CreateJobRequestInputParameter(
                    name='text1',
                    value='this is text1'
                ),
                CreateJobRequestInputParameter(
                    name='text2',
                    value='this is text2'
                ),
                # text3 has a default
                CreateJobRequestInputParameter(
                    name='val1',
                    value=12
                )
            ],
            processorSpec=processor_spec,
            batchId=None,
            dandiApiKey=None,
        )
        resp = _gui_post_api_request(url_path='/api/gui/jobs', data=req.dict(), github_access_token=github_access_token)
        resp = CreateJobResponse(**resp)
        assert resp.success
        job_id = resp.jobId
        assert job_id

        # gui: Get job
        resp = _gui_get_api_request(url_path=f'/api/gui/jobs/{job_id}', github_access_token=github_access_token)
        resp = GetJobResponse(**resp)
        job = resp.job
        assert job.jobId == job_id
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

        # gui: Get jobs
        resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project2_id}/jobs', github_access_token=github_access_token)
        resp = GetJobsResponse(**resp)
        jobs = resp.jobs
        assert len(jobs) == 1

        # Run the compute resource briefly
        start_compute_resource(dir=tmpdir, timeout=1, cleanup_old_jobs=False)

        # gui: Get job
        resp = _gui_get_api_request(url_path=f'/api/gui/jobs/{job_id}', github_access_token=github_access_token)
        resp = GetJobResponse(**resp)
        job = resp.job
        if job.status == 'failed':
            raise Exception(f'Job failed: {job.error}')
        assert job.status == 'finished'

        # Check whether the appropriate compute resource spec was uploaded to the api
        resp = _gui_get_api_request(url_path=f'/api/gui/compute_resources/{compute_resource_id}', github_access_token=github_access_token)
        resp = GetComputeResourceResponse(**resp)
        assert resp.success
        compute_resource = resp.computeResource
        assert compute_resource.spec
        assert len(compute_resource.spec.apps) == 1

        # gui: Delete job
        resp = _gui_delete_api_request(url_path=f'/api/gui/jobs/{job_id}', github_access_token=github_access_token)
        resp = DeleteJobResponse(**resp)
        assert resp.success

        # gui: Get jobs
        resp = _gui_get_api_request(url_path=f'/api/gui/projects/{project2_id}/jobs', github_access_token=github_access_token)
        resp = GetJobsResponse(**resp)
        jobs = resp.jobs
        assert len(jobs) == 0
    finally:
        _use_api_test_client(None)
        set_use_mock(False)
        _clear_mock_mongo_databases()

def _get_fastapi_app():
    from fastapi import FastAPI

    # this code is duplicated with api/index.py, I know
    from protocaas.api_helpers.routers.processor.router import router as processor_router
    from protocaas.api_helpers.routers.compute_resource.router import router as compute_resource_router
    from protocaas.api_helpers.routers.client.router import router as client_router
    from protocaas.api_helpers.routers.gui.router import router as gui_router

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
