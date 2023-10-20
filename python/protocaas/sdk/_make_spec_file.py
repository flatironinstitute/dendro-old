from pathlib import Path
import importlib.util

import protocaas.sdk as pr


def make_app_spec_file_function(app_dir: str, spec_output_file: str = None):
    # Ensure the directory path is an absolute path
    app_dir_path = Path(app_dir).resolve()

    if spec_output_file is None:
        spec_output_file = str(app_dir_path / 'spec.json')

    # Construct the absolute path to main.py in the specified directory
    main_module_path = app_dir_path / 'main.py'

    # Check if main.py exists
    if not main_module_path.exists():
        raise FileNotFoundError(f"main.py not found in {app_dir_path}")

    # Create a module name from the directory path
    module_name = app_dir_path.name

    # Use importlib to load the module
    spec = importlib.util.spec_from_file_location(module_name, str(main_module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Check if the App class exists in the loaded module
    if hasattr(module, 'app') and isinstance(getattr(module, 'app'), pr.App):
        # Create an instance of the App class
        app_instance = module.app

        # Call the make_spec_file method
        app_instance.make_spec_file(spec_output_file)
    else:
        raise AttributeError("App class not found in main.py")
