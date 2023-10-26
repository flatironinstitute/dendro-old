#!/usr/bin/env python

import time
import os
from dataclasses import dataclass
from protocaas.sdk import App, ProcessorBase, InputFile, OutputFile, field


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
        print('Start Processor1 in mock app')
        assert context.text1 != ''
        print(f'text1: {context.text1}')
        print(f'text2: {context.text2}')
        print(f'text3: {context.text3}')
        print(f'val1: {context.val1}')
        time.sleep(0.3)
        print('End Processor1 in mock app')

app = App(
    name='test-app',
    help='This is a test app',
    app_image='mock-image',
    app_executable=os.path.abspath(__file__)
)

app.add_processor(Processor1)

if __name__ == '__main__':
    app.run()
