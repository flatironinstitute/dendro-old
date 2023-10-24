## Running the tests (vscode action)

```bash
pip install pytest pytest-asyncio pytest-cov pyright flake8
```

In vscode:

Command palette => Run Task => Test

This will check formatting using flake8 (see below), will check typing using pyright (see below), and will use pytest to run the tests in python/tests.

## Using pyright vscode extension

By default, vscode/pylance doesn't seem to pick up linter problems like this:

```python
def test1(a: str, b: str):
    print(a)

def test2():
    x = 23
    test1(a=None, b=x)
```

So you should install the pyright vscode extension (ms-pyright).

## Using flake8 vscode extension

Install the flake8 vscode extension.

The rules being ignored are in .flake8

You can run `cd python && flake8 --config ../.flake8` to see the errors.

