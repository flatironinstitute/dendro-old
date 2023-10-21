import os
import subprocess
from ..sdk.App import App
from ._run_job_in_aws_batch import _run_job_in_aws_batch
from ..common._api_request import _processor_put_api_request
from ..common.protocaas_types import ComputeResourceSlurmOpts


def _set_job_status_to_starting(*,
    job_id: str,
    job_private_key: str
):
    url_path = f'/api/processor/jobs/{job_id}/status'
    headers = {
        'job-private-key': job_private_key
    }
    resp = _processor_put_api_request(
        url_path=url_path,
        headers=headers,
        data={
            'status': 'starting'
        }
    )
    if not resp['success']:
        raise Exception(f'Error setting job status to starting: {resp["error"]}')

def _start_job(*,
    job_id: str,
    job_private_key: str,
    processor_name: str,
    app: App,
    run_process: bool = True,
    return_shell_command: bool = False
):
    if return_shell_command and run_process:
        raise Exception('Cannot set both run_process and return_shell_command to True')
    if not return_shell_command and not run_process:
        raise Exception('Cannot set both run_process and return_shell_command to False')

    _set_job_status_to_starting(
        job_id=job_id,
        job_private_key=job_private_key
    )
    if not getattr(app, '_app_executable'):
        raise Exception(f'App does not have an executable path')
    app_executable: str = app._app_executable
    app_image: str = app._app_image
    aws_batch_job_queue: str = app._aws_batch_job_queue
    aws_batch_job_definition: str = app._aws_batch_job_definition
    slurm_opts: ComputeResourceSlurmOpts = app._slurm_opts

    if slurm_opts is not None:
        if run_process:
            raise Exception('Not expecting to see slurm_opts here')

    if aws_batch_job_queue is not None:
        if return_shell_command:
            raise Exception('Cannot return shell command for AWS Batch job')
        if aws_batch_job_definition is None:
            raise Exception(f'aws_batch_job_queue is set but aws_batch_job_definition is not set')
        if not app_image:
            raise Exception(f'aws_batch_job_queue is set but container is not set')
        print(f'Running job in AWS Batch: {job_id} {processor_name} {aws_batch_job_queue} {aws_batch_job_definition}')
        try:
            _run_job_in_aws_batch(
                job_id=job_id,
                job_private_key=job_private_key,
                aws_batch_job_queue=aws_batch_job_queue,
                aws_batch_job_definition=aws_batch_job_definition,
                container=app_image, # for verifying consistent with job definition
                command=app_executable # for verifying consistent with job definition
            )
        except Exception as e:
            raise Exception(f'Error running job in AWS Batch: {e}')
        return

    # Note for future: it is not necessary to use a working dir if the job is to run in a container
    working_dir = os.getcwd() + '/jobs/' + job_id
    os.makedirs(working_dir, exist_ok=True)

    env_vars = {
        'PYTHONUNBUFFERED': '1',
        'JOB_ID': job_id,
        'JOB_PRIVATE_KEY': job_private_key,
        'APP_EXECUTABLE': app_executable,
        'PROTOCAAS_URL': 'https://protocaas.vercel.app'
    }
    kachery_cloud_client_id, kachery_cloud_private_key = _get_kachery_cloud_credentials()
    if kachery_cloud_client_id is not None:
        env_vars['KACHERY_CLOUD_CLIENT_ID'] = kachery_cloud_client_id
        env_vars['KACHERY_CLOUD_PRIVATE_KEY'] = kachery_cloud_private_key

    if not app_image:
        if run_process:
            print(f'Running: {app_executable}')
            process = subprocess.Popen(
                [app_executable],
                cwd=working_dir,
                start_new_session=True, # This is important so it keeps running even if the compute resource is stopped
                # Important to set output to devnull so that we don't get a broken pipe error if this parent process is closed
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={
                    **os.environ,
                    **env_vars
                }
            )
        elif return_shell_command:
            return f'cd {working_dir} && PYTHONUNBUFFERED=1 JOB_ID={job_id} JOB_PRIVATE_KEY={job_private_key} APP_EXECUTABLE={app_executable} {app_executable}'
    else:
        container_method = os.environ.get('CONTAINER_METHOD', 'docker')
        if container_method == 'docker':
            tmpdir = working_dir + '/tmp'
            os.makedirs(tmpdir, exist_ok=True)
            os.makedirs(tmpdir + '/working', exist_ok=True)
            cmd2 = [
                'docker', 'run', '-it'
            ]
            cmd2.extend(['v', f'{tmpdir}:/tmp'])
            cmd2.extend(['--workdir', '/tmp/working']) # the working directory will be /tmp/working
            for k, v in env_vars.items():
                cmd2.extend(['-e', f'{k}={v}'])
            cmd2.extend([app_image])
            cmd2.extend([app_executable])
            if run_process:
                print(f'Running: {" ".join(cmd2)}')
                process = subprocess.Popen(
                    cmd2,
                    cwd=working_dir,
                    start_new_session=True, # This is important so it keeps running even if the compute resource is stopped
                    # Important to set output to devnull so that we don't get a broken pipe error if this parent process is closed
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif return_shell_command:
                return f'cd {working_dir} && {" ".join(cmd2)}'
        elif container_method == 'singularity':
            tmpdir = working_dir + '/tmp' # important to provide a /tmp directory for singularity so that it doesn't run out of disk space
            os.makedirs(tmpdir, exist_ok=True)
            os.makedirs(tmpdir + '/working', exist_ok=True)
            cmd2 = ['singularity', 'exec']
            cmd2.extend(['--bind', f'{tmpdir}:/tmp'])
            # The working directory should be /tmp/working so that if the container wants to write to the working directory, it will not run out of space
            cmd2.extend(['--pwd', '/tmp/working'])
            cmd2.extend(['--cleanenv']) # this is important to prevent singularity from passing environment variables to the container
            cmd2.extend(['--contain']) # we don't want singularity to mount the home or tmp directories of the host
            cmd2.extend(['--nv'])
            for k, v in env_vars.items():
                cmd2.extend(['--env', f'{k}={v}'])
            cmd2.extend([f'docker://{app_image}'])
            cmd2.extend([app_executable])
            if run_process:
                print(f'Running: {" ".join(cmd2)}')
                process = subprocess.Popen(
                    cmd2,
                    cwd=working_dir,
                    start_new_session=True, # This is important so it keeps running even if the compute resource is stopped
                    # Important to set output to devnull so that we don't get a broken pipe error if this parent process is closed
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif return_shell_command:
                return f'cd {working_dir} && {" ".join(cmd2)}'
        else:
            raise Exception(f'Unexpected container method: {container_method}')
    
    # This was the method used previously when we wanted to capture the output of the process and display it to the console
    # However, that was problematic, because when this parent closes, we don't want a broken pipe
    # prefix = f'{job_id} {processor_name}: '
    # t1 = threading.Thread(target=stream_output, args=(process.stdout, prefix))
    # t1.start()
    # prefix = f'{job_id} {processor_name} ERR: '
    # t2 = threading.Thread(target=stream_output, args=(process.stderr, prefix))
    # t2.start()

# previously did this (see above)
# def stream_output(pipe, prefix: str):
#     while True:
#         try:
#             line = pipe.readline()
#         except:
#             break
#         if line:
#             print(prefix + line.decode('utf-8'))
#         else:
#             break

def _get_kachery_cloud_credentials():
    try:
        from kachery_cloud._client_keys import _get_client_keys_hex
    except:
        print(f'Warning: unable to import client keys from kachery_cloud')
        return None, None
    client_id, private_key = _get_client_keys_hex()
    return client_id, private_key