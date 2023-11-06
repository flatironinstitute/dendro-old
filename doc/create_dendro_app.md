# Creating a Custom Dendro Processing App

Here we will walk through the steps of creating a simple Dendro processing app. Alternatively, you can view some more complicated WIP apps [here](https://github.com/scratchrealm/pc-spike-sorting).


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

Before connecting it to the web framework, it's best to test things locally first. Create a sample context file called `sample_context_1.yaml` with the following content

```yaml
input:
  url: https://filesamples.com/samples/document/txt/sample3.txt
output:
  output_file_name: sample_output_1.json
letter: "d"
```

This specifies that the input is coming from the internet, and the output should go to a local file.

```text
letter_count/
├── README.md
├── main.py (with executable permissions)
├── spec.json
├── sample_context_1.yaml
```

Now run the app locally

```bash
cd letter_count
dendro test-app-processor --app-dir . --processor letter_count --context sample_context.yaml
```

This should produce a file called `sample_output_1.json` with the following content

```json
{"count": 110}
```

because presumably the letter "d" appears 110 times in the text file.

To use a local file as input instead, you can use the following context file

```yaml
input:
  local_file_name: sample_input_1.txt
```

TODO: Explain how to prepare a docker image and make the app available on the Dendro system.
