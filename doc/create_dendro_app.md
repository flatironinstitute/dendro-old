# Creating and Dendro Processing App

If you want to learn by example you can take a look at the [source code for the currently-available processing apps](https://github.com/scratchrealm/pc-spike-sorting).


# Tutorial: Creating a Letter Counting Processing App in Dendro

This tutorial will walk you through the steps of creating a simple processing app within the Dendro platform that counts the number of times a certain letter occurs within a text file. The app will take a text file as input and produce an output JSON file containing the count.

Create a new git repository with the following content

```text
letter_count/
├── README.md
├── main.py (with executable permissions)
```

Here's the content of main.py

```python
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
This is the a processor in the letter_count app. It counts the number of times a particular letter appears in a text file and produces a JSON file with the result.
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
```

The next step is to generate a spec.json file describing the app.

```bash
cd letter_count
chmod a+x main.py
dendro make-app-spec-file --app-dir . --spec-output-file spec.json
```

This will create a spec.json file in the app directory. You can take a look at the contents of this file. It should look something like this:

```text
{
    "name": "letter_count",
    "description": "Example Dendro processing app for tutorial",
    "appImage": "",
    "appExecutable": ...,
    "executable": ...,
    "processors": [
        {
            "name": "letter_count",
            "description": ...,
            "inputs": ...
            ...
        }
    ]
}
```

Now you should have

```text
letter_count/
├── README.md
├── main.py (with executable permissions)
├── spec.json
```

You can now test the app...