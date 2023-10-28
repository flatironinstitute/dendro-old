#!/usr/bin/env python

from typing import List
import time
import os
from dataclasses import dataclass
from protocaas.sdk import App, ProcessorBase, InputFile, OutputFile, field


@dataclass
class MockParameterGroup:
    num: int = field(help='Number', default=1)
    secret_param: str = field(help='Secret param', default='123', secret=True)

@dataclass
class MockProcessor1Context:
    input_file: InputFile = field(help='Input file')
    input_list: List[InputFile] = field(help='Input file list')
    output_file: OutputFile = field(help='Output file')
    text1: str = field(help='Text 1', default='abc')
    text2: str = field(help='Text 2')
    text3: str = field(help='Text 3', default='xyz', options=['abc', 'xyz'])
    val1: float = field(help='Value 1', default=1.0)
    group: MockParameterGroup = field(help='Group', default=MockParameterGroup())

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
        assert context.input_file.get_url()
        assert len(context.input_list) > 0
        for input_file in context.input_list:
            assert input_file.get_url()
        print(f'text1: {context.text1}')
        print(f'text2: {context.text2}')
        print(f'text3: {context.text3}')
        print(f'val1: {context.val1}')
        print(f'group.num: {context.group.num}')
        time.sleep(1)
        with open('mock-output-file.txt', 'w') as f:
            f.write('mock output')
        context.output_file.set('mock-output-file.txt')
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
