import sys
import os
import time
from typing import Union, Optional, Dict, Any
import subprocess
from ..common._api_request import _processor_put_api_request
from ..mock import using_mock
from ..internal_job_monitoring.console_output_monitor import do_upload as _upload_final_console_output
import shutil


# This function is called internally by the compute resource daemon through the dendro CLI
# * Sets the job status to running in the database via the API
# * Runs the job in a separate process by calling the app executable with the appropriate env vars
# * Launches detached processes to monitor the console output, resource utilization, and job status
# * Finally, sets the job status to completed or failed in the database via the API

dendro_internal_folder = '_dendro'

def _run_job_parent_process(*, job_id: str, job_private_key: str, app_executable: str, job_timeout_sec: Union[int, None]):
    timescale = 1 if not using_mock() else 1000 # if using mock, run 1000x faster so that we can test timeouts

    _run_job_timer = time.time()

    if os.path.exists(dendro_internal_folder):
        shutil.rmtree(dendro_internal_folder)
    os.mkdir(dendro_internal_folder)
    console_out_fname = os.path.join(dendro_internal_folder, 'console_output.txt')
    cancel_out_fname = os.path.join(dendro_internal_folder, 'cancel.txt')
    console_out_monitor_output_fname = os.path.join(dendro_internal_folder, 'console_output_monitor_output.txt')
    resource_utilization_monitor_output_fname = os.path.join(dendro_internal_folder, 'resource_utilization_monitor_output.txt')
    job_status_monitor_output_fname = os.path.join(dendro_internal_folder, 'job_status_monitor_output.txt')

    # set the job status to running by calling the remote dendro API
    _debug_log(f'Running job {job_id}')
    _set_job_status(job_id=job_id, job_private_key=job_private_key, status='running')

    last_report_timestamp = 0

    proc = None

    with open(console_out_fname, 'w') as console_out_file, open(console_out_monitor_output_fname, 'w') as console_out_monitor_output_file, open(resource_utilization_monitor_output_fname, 'w') as resource_utilization_monitor_output_file, open(job_status_monitor_output_fname, 'w') as job_status_monitor_output_file:
        succeeded = False # whether we succeeded in running the job without an exception
        error_message = '' # if we fail, this will be set to the exception message
        try:
            if not using_mock():
                # start the console output monitor
                cmd = f'dendro internal-job-monitor console_output --parent-pid {os.getpid()}'
                env = {
                    'JOB_ID': job_id,
                    'JOB_PRIVATE_KEY': job_private_key,
                    'CONSOLE_OUT_FILE': os.path.abspath(console_out_fname)
                }
                _launch_detached_process(cmd=cmd, env=env, stdout=console_out_monitor_output_file, stderr=subprocess.STDOUT)

                # start the resource utilization monitor
                cmd = f'dendro internal-job-monitor resource_utilization --parent-pid {os.getpid()}'
                env = {
                    'JOB_ID': job_id,
                    'JOB_PRIVATE_KEY': job_private_key
                }
                _launch_detached_process(cmd=cmd, env=env, stdout=resource_utilization_monitor_output_file, stderr=subprocess.STDOUT)

                # start the status check monitor
                cmd = f'dendro internal-job-monitor job_status --parent-pid {os.getpid()}'
                env = {
                    'JOB_ID': job_id,
                    'JOB_PRIVATE_KEY': job_private_key,
                    'CANCEL_OUT_FILE': cancel_out_fname
                }
                _launch_detached_process(cmd=cmd, env=env, stdout=job_status_monitor_output_file, stderr=subprocess.STDOUT)

            # Launch the job in a separate process
            proc = _launch_job_child_process(
                job_id=job_id,
                job_private_key=job_private_key,
                app_executable=app_executable,
                console_out_file=console_out_file
            )

            first_iteration = True
            while True:
                skip_this_check = using_mock() and first_iteration
                if not skip_this_check:
                    try:
                        retcode = proc.wait(1 / timescale)
                        # don't check this now -- wait until after we had a chance to read the last console output
                    except subprocess.TimeoutExpired:
                        retcode = None # process is still running
                else:
                    retcode = None

                if retcode is not None:
                    if retcode != 0:
                        raise ValueError(f'Error running job: return code {retcode}')
                    # job has completed with exit code 0
                    break

                # check if the cancel file has been created
                if os.path.exists(cancel_out_fname):
                    with open(cancel_out_fname, 'r') as f:
                        cancel_msg = f.read()
                    _debug_log(f'Job canceled: {cancel_msg}')
                    raise Exception(f'Job canceled: {cancel_msg}')

                # check job timeout
                if job_timeout_sec is not None:
                    elapsed = time.time() - _run_job_timer
                    if elapsed > job_timeout_sec:
                        raise Exception(f'Job timed out: {elapsed} > {job_timeout_sec} seconds')

                first_iteration = False

                elapsed_since_report = time.time() - last_report_timestamp
                if elapsed_since_report >= 120:
                    last_report_timestamp = time.time()
                    _debug_log('Job still running')

                time.sleep(3 / timescale)
            succeeded = True # No exception
        except Exception as e: # pylint: disable=broad-except
            _debug_log(f'Error running job: {str(e)}')
            succeeded = False
            error_message = str(e)
        finally:
            if proc is not None:
                _debug_log('Closing subprocess')
                try:
                    if proc.stdout:
                        proc.stdout.close()
                    if proc.stderr:
                        proc.stderr.close()
                    proc.terminate()
                except Exception: # pylint: disable=broad-except
                    pass

            dendro_job_cleanup_dir = os.environ.get('DENDRO_JOB_CLEANUP_DIR', None)
            if dendro_job_cleanup_dir is not None:
                _debug_log(f'Cleaning up DENDRO_JOB_CLEANUP_DIR: {dendro_job_cleanup_dir}')
                try:
                    # delete files in the cleanup dir but do not delete the cleanup dir itself
                    def _delete_files_in_dir(dir: str):
                        for fname in os.listdir(dir):
                            fpath = os.path.join(dir, fname)
                            if os.path.isdir(fpath):
                                if fname == '_dendro':
                                    # don't delete the internal log folder
                                    continue
                                _delete_files_in_dir(fpath)
                            else:
                                _debug_log(f'Deleting {fpath}')
                                os.remove(fpath)
                    _delete_files_in_dir(dendro_job_cleanup_dir)
                except Exception as e:
                    _debug_log(f'WARNING: problem cleaning up DENDRO_JOB_CLEANUP_DIR: {str(e)}')
            else:
                _debug_log('No DENDRO_JOB_CLEANUP_DIR environment variable set. Not cleaning up.')

    if not using_mock():
        _debug_log('Uploading final console output')
        # this is needed because the console output monitor may get terminated before it has a chance to upload the final console output
        ok = _upload_final_console_output(
            job_id=job_id,
            job_private_key=job_private_key,
            console_out_file=console_out_fname
        )
        if not ok:
            _debug_log('WARNING: problem uploading final console output')

    # Set the final job status
    _debug_log('Finalizing job')
    _finalize_job(job_id=job_id, job_private_key=job_private_key, succeeded=succeeded, error_message=error_message)

    _debug_log('Exiting')

def _launch_job_child_process(*, job_id: str, job_private_key: str, app_executable: str, console_out_file: Any):
    if not using_mock(): # pragma: no cover
        # Set the appropriate environment variables and launch the job in a background process
        cmd = app_executable
        env = os.environ.copy()
        env = {
            **env,
            'JOB_ID': job_id,
            'JOB_PRIVATE_KEY': job_private_key,
            'JOB_INTERNAL': '1',
            'PYTHONUNBUFFERED': '1'
        }
        _debug_log(f'Running {app_executable} (Job ID: {job_id})) (Job private key: {job_private_key})')
        working_dir = os.environ.get('DENDRO_JOB_WORKING_DIR', None)
        if working_dir is not None:
            if not os.path.exists(working_dir):
                # make directory including parent directories
                os.makedirs(working_dir)
            if not os.path.isdir(working_dir + '/tmp'):
                os.mkdir(working_dir + '/tmp')
            env['DENDRO_JOB_WORKING_DIR'] = working_dir
            env['TMPDIR'] = working_dir + '/tmp'
            _debug_log(f'Using working directory {working_dir}')
        _debug_log('Opening subprocess')
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=console_out_file,
            stderr=subprocess.STDOUT,
            cwd=working_dir
        )
        return proc
    else:
        # it's not going to work to run the mock job in a separate proecess because the mock environment will not exist
        # so instead we are going to run a dummy mock jub, and then for test coverage,
        # we are also going to do execute _run_job on the app
        proc = subprocess.Popen(
            ['dendro', 'run-mock-job'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # here's where we execute _run_job for test coverage
        from ..compute_resource._start_job import _load_app_from_main
        old_working_dir = os.getcwd()
        os.chdir(os.path.dirname(app_executable))
        app_instance = _load_app_from_main(app_executable)
        try:
            from ._run_job_child_process import _run_job_child_process
            _run_job_child_process(job_id=job_id, job_private_key=job_private_key, processors=app_instance._processors)

            return proc
        finally:
            os.chdir(old_working_dir)
            if 'main' in sys.modules:
                del sys.modules['main'] # important to do this so that at a later time we can load a different main.py

def _finalize_job(*, job_id: str, job_private_key: str, succeeded: bool, error_message: str):
    try:
        if succeeded:
            # The job has completed successfully - update the status accordingly
            _debug_log('Setting job status to completed')
            print('Job completed')
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='completed')
        else:
            # The job has failed - update the status accordingly and set the error message
            _debug_log('Setting job status to failed: ' + error_message)
            print('Job failed: ' + error_message)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=error_message)
    except Exception as e: # pylint: disable=broad-except
        # This is unfortunate - we completed the job, but somehow failed to update the status in the dendro system - maybe there was a network error (maybe we should retry?)
        _debug_log('WARNING: problem setting final job status: ' + str(e))
        print('WARNING: problem setting final job status: ' + str(e))

class SetJobStatusError(Exception):
    pass

def _set_job_status(*, job_id: str, job_private_key: str, status: str, error: Optional[str] = None):
    """Set the status of a job in the dendro API"""
    url_path = f'/api/processor/jobs/{job_id}/status'
    headers = {
        'job-private-key': job_private_key
    }
    data: Dict[str, Any] = {
        'status': status
    }
    if error is not None:
        data['error'] = error
    if os.environ.get('DENDRO_FORCE_STATUS_UPDATES', None) == '1':
        data['force_update'] = True
    resp = _processor_put_api_request(
        url_path=url_path,
        headers=headers,
        data=data
    )
    if not resp['success']:
        raise SetJobStatusError(f'Error setting job status: {resp["error"]}')

def _launch_detached_process(*, cmd: str, env: Dict[str, str], stdout: Any, stderr: Any):
    _debug_log(f'Launching detached process: {cmd}')
    subprocess.Popen(
        cmd.split(' '),
        env={
            **os.environ.copy(),
            **env
        },
        stdout=stdout,
        stderr=stderr,
        start_new_session=True
    )

def _debug_log(msg: str):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    msg2 = f'{timestamp} {msg}'
    print(msg2)
    # write to dendro-job.log
    # this will be written to the working directory, which should be in the job dir
    with open(f'{dendro_internal_folder}/dendro-job.log', 'a', encoding='utf-8') as f:
        f.write(msg2 + '\n')
