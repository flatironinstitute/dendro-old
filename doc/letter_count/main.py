#!/usr/bin/env python3

import os
import json
from dendro.sdk import App, BaseModel, Field, ProcessorBase, InputFile, OutputFile


app = App(
    'letter_count',
    description="Example Dendro processing app for tutorial",
    app_image="",
    app_executable=os.path.abspath(__file__)
)

description = """
This is the a processor in the letter_count app. It counts the number of times a particular letter appears in a text file and produces and JSON file with the result.
"""

class LetterCountProcessorContext(BaseModel):
    input: InputFile = Field(description='Input text file')
    output: OutputFile = Field(description='Output JSON file')
    letter: str = Field(description='Letter to count')

class LetterCountProcessor(ProcessorBase):
    name = 'letter_count'
    label = 'Letter Count'
    description = description
    tags = ['tutorial']
    attributes = {'wip': True}

    @staticmethod
    def run(context: LetterCountProcessorContext):
        input_fname = 'input.txt'
        output_fname = 'output.json'
        context.input.download(input_fname)
        letter = context.letter

        with open(input_fname, 'r') as f:
            text = f.read()
        count = text.count(letter)

        output = {
            'count': count
        }
        with open(output_fname, 'w') as f:
            f.write(json.dumps(output))
        context.output.upload(output_fname)

app.add_processor(LetterCountProcessor)

if __name__ == '__main__':
    app.run()
