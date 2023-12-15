import os
import time
import traceback
import json
import psutil
from .common import _get_upload_url, _process_is_alive


def resource_utilization_monitor(parent_pid: str):
    """
    Monitor resource utilization of a job.
    """
    job_id = os.environ.get('JOB_ID', None)
    if job_id is None:
        raise KeyError('JOB_ID is not set')
    job_private_key = os.environ.get('JOB_PRIVATE_KEY', None)
    if job_private_key is None:
        raise KeyError('JOB_PRIVATE_KEY is not set')
    last_report_timestamp = 0
    last_upload_timestamp = 0
    overall_timer = time.time()
    all_lines = []

    while True:
        if not _process_is_alive(parent_pid):
            print(f'Parent process {parent_pid} is no longer alive. Doing final upload.')
            do_upload(
                all_lines=all_lines,
                job_id=job_id,
                job_private_key=job_private_key
            )
            print('Exiting.')
            break

        elapsed_since_report = time.time() - last_report_timestamp
        if elapsed_since_report >= 10:
            last_report_timestamp = time.time()
            cpu_percent = psutil.cpu_percent()
            virtual_memory = psutil.virtual_memory()
            disk_io_counters = psutil.disk_io_counters()
            net_io_counters = psutil.net_io_counters(pernic=False, nowrap=True)
            gpu_loads = _get_gpu_loads()
            log_record = {
                'timestamp': time.time(),
                'cpu': {
                    'percent': cpu_percent
                },
                'virtual_memory': {
                    'total': virtual_memory.total,
                    'available': virtual_memory.available,
                    'percent': virtual_memory.percent,
                    'used': virtual_memory.used,
                    'free': virtual_memory.free,
                    'active': virtual_memory.active,
                    'inactive': virtual_memory.inactive,
                    'buffers': virtual_memory.buffers,
                    'cached': virtual_memory.cached,
                    'shared': virtual_memory.shared,
                    'slab': virtual_memory.slab
                },
                'disk_io_counters': {
                    'read_count': disk_io_counters.read_count,
                    'write_count': disk_io_counters.write_count,
                    'read_bytes': disk_io_counters.read_bytes,
                    'write_bytes': disk_io_counters.write_bytes,
                    'read_time': disk_io_counters.read_time,
                    'write_time': disk_io_counters.write_time
                } if disk_io_counters else None,
                'net_io_counters': {
                    'bytes_sent': net_io_counters.bytes_sent,
                    'bytes_recv': net_io_counters.bytes_recv,
                    'packets_sent': net_io_counters.packets_sent,
                    'packets_recv': net_io_counters.packets_recv,
                    'errin': net_io_counters.errin,
                    'errout': net_io_counters.errout,
                    'dropin': net_io_counters.dropin,
                    'dropout': net_io_counters.dropout
                },
                'gpu': {
                    'loads': gpu_loads
                } if gpu_loads else None
            }
            line = (json.dumps(log_record) + '\n').encode('utf-8') # important to encode this string
            all_lines.append(line)
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
                    all_lines=all_lines,
                    job_id=job_id,
                    job_private_key=job_private_key
                )

        time.sleep(1)

def _get_gpu_loads():
    """This is a helper function for _resource_utilization_log_reader"""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return [gpu.load for gpu in gpus]
    except: # noqa
        return None

def do_upload(*, all_lines, job_id, job_private_key):
    import requests
    print(f'Uploading {len(all_lines)} lines of resource utilization data')
    text_to_upload = b'\n'.join(all_lines)
    try:
        resource_utilization_log_upload_url = _get_upload_url(job_id=job_id, job_private_key=job_private_key, output_name='_resource_utilization_log')
        r = requests.put(resource_utilization_log_upload_url, data=text_to_upload, timeout=5)
        if r.status_code != 200:
            raise Exception(f'Error uploading resource utilization log: {r.status_code} {r.text}')
    except: # noqa
        print('Error uploading resource utilization log')
        traceback.print_exc()
