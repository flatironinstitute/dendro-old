#!/usr/bin/env python

import os
from dataclasses import dataclass
from dendro.sdk import App, ProcessorBase, field


@dataclass
class MockProcessor2Context:
    text1: str = field(help='Text 1', default='abc')

class MockProcessor2(ProcessorBase):
    name = 'mock-processor2'
    help = 'This is mock processor 2'
    label = 'Mock Processor 2'
    tags = ['mock-processor2', 'test']
    attributes = {'test': True}

    @staticmethod
    def run(context: MockProcessor2Context):
        print('Start mock processor2 in mock app')
        assert context.text1 != ''
        print('End mock processor2 in mock app')

app = App(
    name='test-app-2',
    help='This is a test app 2',
    app_image=None,
    app_executable=os.path.abspath(__file__)
)

app.add_processor(MockProcessor2)

if __name__ == '__main__':
    app.run()
