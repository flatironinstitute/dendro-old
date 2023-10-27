#!/usr/bin/env python

import time
import os
from dataclasses import dataclass
from protocaas.sdk import App, ProcessorBase, InputFile, OutputFile, field


@dataclass
class MockProcessor1Context:
    input_file: InputFile = field(help='Input file')
    output_file: OutputFile = field(help='Output file')
    text1: str = field(help='Text 1', default='abc')
    text2: str = field(help='Text 2')
    text3: str = field(help='Text 3', default='xyz', options=['abc', 'xyz'])
    val1: float = field(help='Value 1', default=1.0)

class MockProcessor1(ProcessorBase):
    name = 'mock-processor1'
    help = 'This is mock processor 1'
    label = 'Mock Processor 1'
    tags = ['mock-processor1', 'test']
    attributes = {'test': True}

    @staticmethod
    def run(context: MockProcessor1Context):
        print('Start mock processor1 in mock app')
        assert context.text1 != ''
        print(f'text1: {context.text1}')
        print(f'text2: {context.text2}')
        print(f'text3: {context.text3}')
        print(f'val1: {context.val1}')
        time.sleep(1)
        print('End mock processor1 in mock app')

app = App(
    name='test-app',
    help='This is a test app',
    app_image=None,
    app_executable=os.path.abspath(__file__)
)

app.add_processor(MockProcessor1)

if __name__ == '__main__':
    app.run()
