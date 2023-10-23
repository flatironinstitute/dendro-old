## Running the tests (vscode action)

```bash
pip install pytest pytest-cov pyright autopep8
```

In vscode:

Command palette => Run Task => Test

This will test formatting (see autopep8 below), pyright, and will use pytest to run the tests in python/tests.

## Running autopep8 (vscode action)

This project is configured to run a very limited auto-formatting. In vscode:

Command palette => Run Task => autopep8

This will only apply the rules defined in python/setup.cfg.

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

## Running pylint (vscode action)

Although not all these rules are enforced it may be useful to run the pylint vscode task:

Command palette => Run Task => pylint