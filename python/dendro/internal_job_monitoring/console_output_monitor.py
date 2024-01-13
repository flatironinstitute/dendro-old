import os
import time
import traceback
from .common import _get_upload_url, _process_is_alive


def console_output_monitor(parent_pid: str):
    """
    Monitor console output of a job.
    """
    job_id = os.environ.get('JOB_ID', None)
    if job_id is None:
        raise KeyError('JOB_ID is not set')
    job_private_key = os.environ.get('JOB_PRIVATE_KEY', None)
    if job_private_key is None:
        raise KeyError('JOB_PRIVATE_KEY is not set')
    console_out_file = os.environ.get('CONSOLE_OUT_FILE', None)
    if console_out_file is None:
        raise KeyError('CONSOLE_OUT_FILE is not set')

    last_upload_timestamp = 0
    overall_timer = time.time()

    while True:
        if not _process_is_alive(parent_pid):
            print(f'Parent process {parent_pid} is no longer alive. Doing final upload.')
            do_upload(
                console_out_file=console_out_file,
                job_id=job_id,
                job_private_key=job_private_key
            )
            print('Exiting.')
            break

        elapsed_since_upload = time.time() - last_upload_timestamp
        overall_elapsed = time.time() - overall_timer
        if overall_elapsed < 60:
            interval = 10
        elif overall_elapsed < 60 * 5:
            interval = 30
        elif overall_elapsed < 60 * 20:
            interval = 60
        else:
            interval = 120
        if elapsed_since_upload >= interval:
            last_upload_timestamp = time.time()
            do_upload(
                console_out_file=console_out_file,
                job_id=job_id,
                job_private_key=job_private_key
            )

        time.sleep(1)

def do_upload(*, console_out_file, job_id, job_private_key):
    import requests
    if not os.path.exists(console_out_file):
        return True
    with open(console_out_file, 'r') as f:
        console_text = f.read()
    console_text_lines = console_text.split('\n')
    new_lines = []
    for line in console_text_lines:
        # handle carriage return (e.g. in progress bar)
        # find the last \r
        last_cr_index = line.rfind('\r')
        if last_cr_index != -1:
            new_lines.append(line[last_cr_index + 1:].encode('utf-8'))
        else:
            new_lines.append(line.encode('utf-8'))
    text_to_upload = b'\n'.join(new_lines)
    try:
        console_output_upload_url = _get_upload_url(job_id=job_id, job_private_key=job_private_key, output_name='_console_output')
        r = requests.put(console_output_upload_url, data=text_to_upload, timeout=5)
        if r.status_code != 200:
            raise Exception(f'Error uploading console output: {r.status_code} {r.text}')
        return True
    except: # noqa
        print('Error uploading console output')
        traceback.print_exc()
        return False
