import sys
import os
from typing import Union, Optional, Dict, Any
import threading
import queue
import time
import subprocess
import requests
from ..common._api_request import _processor_get_api_request, _processor_put_api_request
from ..mock import using_mock


# This function is called internally by the compute resource daemon through the dendro CLI
# * Sets the job status to running in the database via the API
# * Runs the job in a separate process by calling the app executable with the appropriate env vars
# * Monitors the job output, updating the database periodically via the API
# * Sets the job status to completed or failed in the database via the API

def _run_job(*, job_id: str, job_private_key: str, app_executable: str):
    time_scale_factor = 1 if not using_mock() else 10000

    _run_job_timer = time.time()

    # set the job status to running by calling the remote dendro API
    _debug_log(f'Running job {job_id}')
    _set_job_status(job_id=job_id, job_private_key=job_private_key, status='running')

    # Launch the job in a separate process
    proc = _launch_job(job_id=job_id, job_private_key=job_private_key, app_executable=app_executable)

    # We are going to be monitoring the output of the job in a separate thread, and it will be communicated to this thread via a queue
    outq = queue.Queue()
    output_reader_thread = threading.Thread(target=_output_reader, args=(proc, outq))
    output_reader_thread.start()

    all_output = b''
    last_newline_index_in_output = -1
    last_report_console_output_time = time.time()
    console_output_changed = False
    last_check_job_exists_time = time.time() if not using_mock() else 0

    # Create a function that will handle uploading the latest console output to the dendro system
    console_output_upload_url: Union[str, None] = None
    console_output_upload_url_timestamp = 0

    def check_for_new_console_output():
        nonlocal outq
        nonlocal last_newline_index_in_output
        nonlocal all_output
        nonlocal console_output_changed
        while True:
            try:
                # get the latest output from the job
                x = outq.get(block=False)

                if x == b'\n':
                    last_newline_index_in_output = len(all_output)
                if x == b'\r':
                    # handle carriage return (e.g. in progress bar)
                    all_output = all_output[:last_newline_index_in_output + 1]
                all_output += x
                console_output_changed = True
            except queue.Empty:
                break

    def upload_console_output(output: str):
        nonlocal console_output_upload_url
        nonlocal console_output_upload_url_timestamp
        elapsed = time.time() - console_output_upload_url_timestamp
        if elapsed > 60 * 30 / time_scale_factor:
            # every 30 minutes, request a new upload url (the old one expires after 1 hour)
            console_output_upload_url_timestamp = time.time()
            # request a signed upload url for the console output
            console_output_upload_url = _get_console_output_upload_url(job_id=job_id, job_private_key=job_private_key)
        if console_output_upload_url is not None:
            _upload_console_output(console_output_upload_url=console_output_upload_url, output=output)
        if using_mock():
            print('MOCK: Console output: ' + output)

    num_status_check_failures = 0 # keep track of this so we don't do infinite retries
    succeeded = False # whether we succeeded in running the job without an exception
    error_message = '' # if we fail, this will be set to the exception message
    try:
        first_iteration = True
        while True:
            skip_this_check = using_mock() and first_iteration
            if not skip_this_check:
                try:
                    retcode = proc.wait(1)
                    # don't check this now -- wait until after we had a chance to read the last console output
                except subprocess.TimeoutExpired:
                    retcode = None # process is still running
            else:
                retcode = None
            check_for_new_console_output()

            if console_output_changed:
                elapsed = time.time() - last_report_console_output_time
                run_job_elapsed_time = time.time() - _run_job_timer
                do_report = False
                if retcode is not None:
                    # if the job is finished, report the console output
                    do_report = True
                elif run_job_elapsed_time < 60 * 2 / time_scale_factor:
                    # for the first 2 minutes, report every 10 seconds
                    if elapsed > 10 / time_scale_factor:
                        do_report = True
                elif run_job_elapsed_time < 60 * 10 / time_scale_factor:
                    # for the next 8 minutes, report every 30 seconds
                    if elapsed > 30 / time_scale_factor:
                        do_report = True
                else:
                    # after that, report every 120 seconds
                    if elapsed > 60 * 2 / time_scale_factor:
                        do_report = True
                if do_report:
                    # we are going to report the console output
                    last_report_console_output_time = time.time()
                    console_output_changed = False
                    try:
                        _debug_log('Setting job console output')
                        # _set_job_console_output(job_id=job_id, job_private_key=job_private_key, console_output=all_output.decode('utf-8'))
                        upload_console_output(output=all_output.decode('utf-8'))
                    except Exception as e: # pylint: disable=broad-except
                        _debug_log('WARNING: problem setting console output: ' + str(e))
                        print('WARNING: problem setting console output: ' + str(e))
            if retcode is not None:
                # now that we have set the final console output we can raise an exception if the job failed
                if retcode != 0:
                    raise ValueError(f'Error running job: return code {retcode}')
                break

            # check whether job was canceled due to it having been deleted from the dendro system
            elapsed = time.time() - last_check_job_exists_time
            if elapsed > 120 / time_scale_factor:
                last_check_job_exists_time = time.time()
                try:
                    job_status = _get_job_status(job_id=job_id, job_private_key=job_private_key)
                    num_status_check_failures = 0
                except: # noqa: E722
                    # maybe this failed due to a network error. we'll try this a couple or a few times before giving up
                    print('Failed to check job status')
                    num_status_check_failures += 1
                    if num_status_check_failures >= 3:
                        print('Failed to check job status 3 times in a row. Assuming job was canceled.')
                        raise
                    job_status = '<request-failed>'
                if job_status is None:
                    raise ValueError('Job does not exist (was probably canceled)')
                if job_status != 'running':
                    raise ValueError(f'Unexpected job status: {job_status}')
            time.sleep(5 / time_scale_factor) # wait 5 seconds before checking things again
            first_iteration = False
        succeeded = True # No exception
    except Exception as e: # pylint: disable=broad-except
        _debug_log(f'Error running job: {str(e)}')
        succeeded = False
        error_message = str(e)
    finally:
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
            print(f'Cleaning up DENDRO_JOB_CLEANUP_DIR: {dendro_job_cleanup_dir}')
            _debug_log(f'Cleaning up DENDRO_JOB_CLEANUP_DIR: {dendro_job_cleanup_dir}')
            try:
                # delete files in the cleanup dir but do not delete the cleanup dir itself
                def _delete_files_in_dir(dir: str):
                    for fname in os.listdir(dir):
                        if fname == 'denro-job.log':
                            # don't delete the log file
                            continue
                        fpath = os.path.join(dir, fname)
                        if os.path.isdir(fpath):
                            _delete_files_in_dir(fpath)
                        else:
                            print(f'Deleting {fpath}')
                            os.remove(fpath)
                _delete_files_in_dir(dendro_job_cleanup_dir)
            except Exception as e:
                print(f'WARNING: problem cleaning up DENDRO_JOB_CLEANUP_DIR: {str(e)}')
        else:
            print('No DENDRO_JOB_CLEANUP_DIR environment variable set. Not cleaning up.')

        output_reader_thread.join()

    check_for_new_console_output()
    if console_output_changed:
        _debug_log('Setting final job console output')
        try:
            # _set_job_console_output(job_id=job_id, job_private_key=job_private_key, console_output=all_output.decode('utf-8'))
            upload_console_output(output=all_output.decode('utf-8'))
        except Exception as e: # pylint: disable=broad-except
            _debug_log('WARNING: problem setting final console output: ' + str(e))
            print('WARNING: problem setting final console output: ' + str(e))

    # Set the final job status
    _debug_log('Finalizing job')
    _finalize_job(job_id=job_id, job_private_key=job_private_key, succeeded=succeeded, error_message=error_message)

def _launch_job(*, job_id: str, job_private_key: str, app_executable: str):
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
        print(f'Running {app_executable} (Job ID: {job_id})) (Job private key: {job_private_key})')
        working_dir = os.environ.get('DENDRO_JOB_WORKING_DIR', None)
        if working_dir is not None:
            if not os.path.exists(working_dir):
                # make directory including parent directories
                os.makedirs(working_dir)
            if not os.path.isdir(working_dir + '/tmp'):
                os.mkdir(working_dir + '/tmp')
            env['DENDRO_JOB_WORKING_DIR'] = working_dir
            env['TMPDIR'] = working_dir + '/tmp'
            print(f'Using working directory {working_dir}')
        _debug_log('Opening subprocess')
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
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
            app_instance._run_job(job_id=job_id, job_private_key=job_private_key)

            return proc
        finally:
            os.chdir(old_working_dir)
            if 'main' in sys.modules:
                del sys.modules['main'] # important to do this so that at a later time we can load a different main.py

def _output_reader(proc, outq: queue.Queue):
    """This is a thread that reads the output of the job and puts it into a queue"""
    while True:
        try:
            x = proc.stdout.read(1)
        except: # noqa: E722
            break
        if len(x) == 0:
            break
        outq.put(x)

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

def _get_job_status(*, job_id: str, job_private_key: str) -> str:
    """Get a job status from the dendro API"""
    url_path = f'/api/processor/jobs/{job_id}/status'
    headers = {
        'job-private-key': job_private_key
    }
    res = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    return res['status']

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

def _get_console_output_upload_url(*, job_id: str, job_private_key: str) -> str:
    """Get a signed upload URL for the console output of a job"""
    url_path = f'/api/processor/jobs/{job_id}/outputs/_console_output/upload_url'
    headers = {
        'job-private-key': job_private_key
    }
    res = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    return res['uploadUrl']

class UploadConsoleOutputError(Exception):
    pass

def _upload_console_output(*, console_output_upload_url: str, output: str):
    """Upload the console output of a job to the cloud bucket"""
    if using_mock():
        return
    r = requests.put(console_output_upload_url, data=output.encode('utf-8'), timeout=60)
    if r.status_code != 200:
        raise UploadConsoleOutputError(f'Error uploading console output: {r.status_code} {r.text}')

# This was the old method
# def _set_job_console_output(*, job_id: str, job_private_key: str, console_output: str):
#     """Set the console output of a job in the dendro API"""
#     url_path = f'/api/processor/jobs/{job_id}/console_output'
#     headers = {
#         'job-private-key': job_private_key
#     }
#     data = {
#         'consoleOutput': console_output
#     }
#     resp = _processor_put_api_request(
#         url_path=url_path,
#         headers=headers,
#         data=data
#     )
#     if not resp['success']:
#         raise Exception(f'Error setting job console output: {resp["error"]}')

def _debug_log(msg: str):
    # write to dendro-job.log
    # this will be written to the working directory, which should be in the job dir
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
    with open('dendro-job.log', 'a', encoding='utf-8') as f:
        f.write(f'{timestamp_str} {msg}\n')
