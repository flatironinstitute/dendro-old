import shutil
import tempfile
from dendro import BaseModel, Field
from dendro.sdk import App, ProcessorBase, InputFile, OutputFile
from dendro.mock import set_use_mock


def test_app():
    set_use_mock(True)

    try:
        class Processor1Context(BaseModel):
            input_file: InputFile = Field(description='Input file')
            output_file: OutputFile = Field(description='Output file')
            text1: str = Field(description='Text 1', default='abc')
            text2: str = Field(description='Text 2')
            text3: str = Field(description='Text 3', default='xyz', json_schema_extra={'options': ['abc', 'xyz']})
            val1: float = Field(description='Value 1', default=1.0)

        class Processor1(ProcessorBase):
            name = 'processor1'
            description = 'This is processor 1'
            label = 'Processor 1'
            tags = ['processor1', 'test']
            attributes = {'test': True}

            @staticmethod
            def run(context: Processor1Context):
                assert context.text1 != ''

        app = App(
            name='test-app',
            description='This is a test app',
            app_image='fake-image'
        )

        app.add_processor(Processor1)

        spec = app.get_spec()
        assert spec['name'] == 'test-app'
    finally:
        set_use_mock(False)

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
