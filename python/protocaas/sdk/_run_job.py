import os
import threading
import queue
import time
import subprocess
import requests
from ..common._api_request import _processor_get_api_request, _processor_put_api_request


# This function is called internally by the compute resource daemon through the protocaas CLI
# * Sets the job status to running in the database via the API
# * Runs the job in a separate process by calling the app executable with the appropriate env vars
# * Monitors the job output, updating the database periodically via the API
# * Sets the job status to completed or failed in the database via the API

def _run_job(*, job_id: str, job_private_key: str, app_executable: str):
    _run_job_timer = time.time()

    _debug_log(f'Running job {job_id}')
    _set_job_status(job_id=job_id, job_private_key=job_private_key, status='running')

    cmd = app_executable
    env = os.environ.copy()
    env['JOB_ID'] = job_id
    env['JOB_PRIVATE_KEY'] = job_private_key
    env['JOB_INTERNAL'] = '1'
    env['PYTHONUNBUFFERED'] = '1'
    print(f'Running {app_executable} (Job ID: {job_id})) (Job private key: {job_private_key})')
    _debug_log('Opening subprocess')
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    def output_reader(proc, outq: queue.Queue):
        while True:
            try:
                x = proc.stdout.read(1)
            except:
                break
            if len(x) == 0:
                break
            outq.put(x)
    outq = queue.Queue()
    output_reader_thread = threading.Thread(target=output_reader, args=(proc, outq))
    output_reader_thread.start()

    all_output = b''
    last_newline_index_in_output = -1
    last_report_console_output_time = time.time()
    console_output_changed = False
    last_check_job_exists_time = time.time()

    console_output_upload_url: str = None
    console_output_upload_url_timestamp = 0
    def upload_console_output(output: str):
        nonlocal console_output_upload_url
        nonlocal console_output_upload_url_timestamp
        elapsed = time.time() - console_output_upload_url_timestamp
        if elapsed > 60 * 30:
            console_output_upload_url_timestamp = time.time()
            console_output_upload_url = _get_console_output_upload_url(job_id=job_id, job_private_key=job_private_key)
        if console_output_upload_url is not None:
            _upload_console_output(console_output_upload_url=console_output_upload_url, output=output)

    num_status_check_failures = 0
    succeeded = False
    try:
        while True:
            try:
                retcode = proc.wait(1)
                # don't check this now -- wait until after we had a chance to read the last console output
            except subprocess.TimeoutExpired:
                retcode = None
            while True:
                try:
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
            
            if console_output_changed:
                elapsed = time.time() - last_report_console_output_time
                run_job_elapsed_time = time.time() - _run_job_timer
                do_report = False
                if run_job_elapsed_time < 60 * 2:
                    # for the first 2 minutes, report every 10 seconds
                    if elapsed > 10:
                        do_report = True
                elif run_job_elapsed_time < 60 * 10:
                    # for the next 8 minutes, report every 30 seconds
                    if elapsed > 30:
                        do_report = True
                else:
                    # after that, report every 120 seconds
                    if elapsed > 60:
                        do_report = True
                if do_report:
                    last_report_console_output_time = time.time()
                    console_output_changed = False
                    try:
                        _debug_log('Setting job console output')
                        # _set_job_console_output(job_id=job_id, job_private_key=job_private_key, console_output=all_output.decode('utf-8'))
                        upload_console_output(output=all_output.decode('utf-8'))
                    except Exception as e:
                        _debug_log('WARNING: problem setting console output: ' + str(e))
                        print('WARNING: problem setting console output: ' + str(e))
                        pass
            if retcode is not None:
                if retcode != 0:
                    raise ValueError(f'Error running job: return code {retcode}')
                break

            elapsed = time.time() - last_check_job_exists_time
            if elapsed > 120:
                last_check_job_exists_time = time.time()
                try:
                    job_status = _get_job_status(job_id=job_id, job_private_key=job_private_key)
                    num_status_check_failures = 0
                except:
                    print('Failed to check job status')
                    num_status_check_failures += 1
                    if num_status_check_failures >= 3:
                        print('Failed to check job status 3 times in a row. Assuming job was canceled.')
                        raise
                if job_status is None:
                    raise ValueError('Job does not exist (was probably canceled)')
                if job_status != 'running':
                    raise ValueError(f'Unexpected job status: {job_status}')
            time.sleep(5)
        succeeded = True # No exception
    except Exception as e:
        _debug_log(f'Error running job: {str(e)}')
        succeeded = False
        error_message = str(e)
    finally:
        _debug_log('Closing subprocess')
        try:
            proc.stdout.close()
            proc.stderr.close()
            proc.terminate()
        except Exception:
            pass
        output_reader_thread.join()
    if console_output_changed:
        _debug_log('Setting final job console output')
        try:
            # _set_job_console_output(job_id=job_id, job_private_key=job_private_key, console_output=all_output.decode('utf-8'))
            upload_console_output(output=all_output.decode('utf-8'))
        except Exception as e:
            _debug_log('WARNING: problem setting final console output: ' + str(e))
            print('WARNING: problem setting final console output: ' + str(e))
            pass

    try:
        if succeeded:
            _debug_log('Setting job status to completed')
            print('Job completed')
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='completed')
        else:
            _debug_log('Setting job status to failed: ' + error_message)
            print('Job failed: ' + error_message)
            _set_job_status(job_id=job_id, job_private_key=job_private_key, status='failed', error=error_message)
    except Exception as e:
        _debug_log('WARNING: problem setting final job status: ' + str(e))
        print('WARNING: problem setting final job status: ' + str(e))
        pass
    
def _get_job_status(*, job_id: str, job_private_key: str) -> str:
    """Get a job from the protocaas API"""
    url_path = f'/api/processor/jobs/{job_id}/status'
    headers = {
        'job-private-key': job_private_key
    }
    res = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    return res['status']

def _set_job_status(*, job_id: str, job_private_key: str, status: str, error: str = None):
    """Set the status of a job in the protocaas API"""
    url_path = f'/api/processor/jobs/{job_id}/status'
    headers = {
        'job-private-key': job_private_key
    }
    data = {
        'status': status
    }
    if error is not None:
        data['error'] = error
    resp = _processor_put_api_request(
        url_path=url_path,
        headers=headers,
        data=data
    )
    if not resp['success']:
        raise Exception(f'Error setting job status: {resp["error"]}')

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

def _upload_console_output(*, console_output_upload_url: str, output: str):
    """Upload the console output of a job to the cloud bucket"""
    r = requests.put(console_output_upload_url, data=output.encode('utf-8'))
    if r.status_code != 200:
        raise Exception(f'Error uploading console output: {r.status_code} {r.text}')

# This was the old method
# def _set_job_console_output(*, job_id: str, job_private_key: str, console_output: str):
#     """Set the console output of a job in the protocaas API"""
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
    # write to protocaas-job.log
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
    with open('protocaas-job.log', 'a') as f:
        f.write(f'{timestamp_str} {msg}\n')