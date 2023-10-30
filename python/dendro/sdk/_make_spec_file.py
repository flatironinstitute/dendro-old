import os
import subprocess
from pathlib import Path


def make_app_spec_file_function(app_dir: str, spec_output_file: str):
    # Ensure the directory path is an absolute path
    app_dir_path = Path(app_dir).resolve()

    if spec_output_file is None:
        spec_output_file = str(app_dir_path / 'spec.json')

    executable_path = str(app_dir_path / 'main.py')

    env = os.environ.copy()
    env['SPEC_OUTPUT_FILE'] = spec_output_file
    subprocess.run([executable_path], env=env)

    # When we do it the following way, the inspection of type hints in the processor context does not work

    # # Construct the absolute path to main.py in the specified directory
    # main_module_path = app_dir_path / 'main.py'

    # # Check if main.py exists
    # if not main_module_path.exists():
    #     raise FileNotFoundError(f"main.py not found in {app_dir_path}")

    # # Create a module name from the directory path
    # module_name = app_dir_path.name

    # # Use importlib to load the module
    # spec = importlib.util.spec_from_file_location(module_name, str(main_module_path))
    # if spec is None:
    #     raise ImportError(f"Unable to get spec for module {module_name} from {main_module_path}")
    # module = importlib.util.module_from_spec(spec)
    # if spec.loader is None:
    #     raise ImportError(f"Unable to get loader for module {module_name} from {main_module_path}")
    # spec.loader.exec_module(module)

    # # Check if the App class exists in the loaded module
    # if hasattr(module, 'app') and isinstance(getattr(module, 'app'), pr.App):
    #     # Create an instance of the App class
    #     app_instance = module.app

    #     # Call the make_spec_file method
    #     app_instance.make_spec_file(spec_output_file)
    # else:
    #     raise AttributeError("App class not found in main.py")
