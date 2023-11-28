import json
import queue
import time
import psutil
import threading


def _resource_utilization_log_reader(outq: queue.Queue, exit_event: threading.Event):
    """This is a thread that makes a resource utilization log and puts it into a queue"""
    last_report_timestamp = 0
    while True:
        if exit_event.is_set():
            break
        elapsed_since_report = time.time() - last_report_timestamp
        if elapsed_since_report < 10:
            time.sleep(0.1)
            continue
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
        outq.put(line)

def _get_gpu_loads():
    """This is a helper function for _resource_utilization_log_reader"""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return [gpu.load for gpu in gpus]
    except: # noqa
        return None
