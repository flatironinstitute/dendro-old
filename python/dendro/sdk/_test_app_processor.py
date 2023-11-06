import os
import subprocess
from pathlib import Path


def test_app_processor_function(app_dir: str, processor: str, context: str):
    # Ensure the directory path is an absolute path
    app_dir_path = Path(app_dir).resolve()

    executable_path = str(app_dir_path / 'main.py')

    env = os.environ.copy()
    env['TEST_APP_PROCESSOR'] = '1'
    env['PROCESSOR_NAME'] = processor
    env['CONTEXT_FILE'] = context
    subprocess.run([executable_path], env=env)
