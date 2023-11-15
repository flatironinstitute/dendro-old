import shutil
import tempfile
from dendro.compute_resource.register_compute_resource import register_compute_resource


def test_register_compute_resource():
    with TemporaryDirectory() as tmpdir:
        register_compute_resource(
            dir=tmpdir
        )

class TemporaryDirectory:
    """A context manager for temporary directories"""
    def __init__(self):
        self._dir = None
    def __enter__(self):
        self._dir = tempfile.mkdtemp()
        return self._dir
    def __exit__(self, exc_type, exc_value, traceback):
        if self._dir:
            shutil.rmtree(self._dir)
