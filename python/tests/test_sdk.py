import os
import shutil
import tempfile
from dataclasses import dataclass
from dendro.sdk import App, ProcessorBase, InputFile, OutputFile, field


def test_app():
    @dataclass
    class Processor1Context:
        input_file: InputFile = field(help='Input file')
        output_file: OutputFile = field(help='Output file')
        text1: str = field(help='Text 1', default='abc')
        text2: str = field(help='Text 2')
        text3: str = field(help='Text 3', default='xyz', options=['abc', 'xyz'])
        val1: float = field(help='Value 1', default=1.0)

    class Processor1(ProcessorBase):
        name = 'processor1'
        help = 'This is processor 1'
        label = 'Processor 1'
        tags = ['processor1', 'test']
        attributes = {'test': True}

        @staticmethod
        def run(context: Processor1Context):
            assert context.text1 != ''

    app = App(
        name='test-app',
        help='This is a test app',
        app_image='fake-image'
    )

    app.add_processor(Processor1)

    spec = app.get_spec()
    assert spec['name'] == 'test-app'

    with TemporaryDirectory() as tmpdir:
        os.environ['SPEC_OUTPUT_FILE'] = tmpdir + '/spec.json'
        app.run()
        assert os.path.exists(tmpdir + '/spec.json')

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
