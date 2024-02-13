#!/usr/bin/env python

from typing import List, Optional
import time
import os
from dendro import BaseModel, Field
from dendro.sdk import App, ProcessorBase, InputFile, OutputFile


class MockParameterGroup(BaseModel):
    num: int = Field(description='Number', default=1)
    secret_param: str = Field(description='Secret param', default='123', json_schema_extra={'secret': True})

class MockProcessor1Context(BaseModel):
    input_file: InputFile = Field(description='Input file')
    input_list: List[InputFile] = Field(description='Input file list')
    output_file: OutputFile = Field(description='Output file')
    text1: str = Field(description='Text 1', default='abc')
    text2: str = Field(description='Text 2')
    text3: str = Field(description='Text 3', default='xyz', json_schema_extra={'options': ['abc', 'xyz']})
    val1: float = Field(description='Value 1', default=1.0)
    val2: Optional[float] = Field(description='Value 2 could be a float or it could be None')
    group: MockParameterGroup = Field(description='Group', default=MockParameterGroup())
    intentional_error: bool = Field(description='Intentional error', default=False)

class MockProcessor1(ProcessorBase):
    name = 'mock-processor1'
    description = 'This is mock processor 1'
    label = 'Mock Processor 1'
    tags = ['mock-processor1', 'test']
    attributes = {'test': True}

    @staticmethod
    def run(context: MockProcessor1Context):
        if context.intentional_error:
            raise Exception('Received intentional error parameter')

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
        time.sleep(0.001) # important not to wait too long because we are calling this synchronously during testing
        with open('mock-output-file.txt', 'w') as f:
            f.write('mock output')
        context.output_file.upload('mock-output-file.txt')
        print('End mock processor1 in mock app')

app = App(
    name='test-app',
    description='This is a test app',
    app_image=None,
    app_executable=os.path.abspath(__file__)
)

app.add_processor(MockProcessor1)

if __name__ == '__main__':
    app.run()
