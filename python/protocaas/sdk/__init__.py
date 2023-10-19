from .InputFile import InputFile
from .OutputFile import OutputFile
from .App import App

from .decorators import processor, input, output, parameter, attribute, tags, input_list

import os
is_generating_spec = os.environ.get('SPEC_OUTPUT_FILE', None) is not None