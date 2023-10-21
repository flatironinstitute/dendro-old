## Running the tests (vscode action)

```bash
pip install pytest pytest-cov pyright
```

Command palette => Run Task => Test

## Linting the Python using pyright

By default, vscode/pylance doesn't seem to pick up linter problems like this:

```python
def test1(a: str, b: str):
    print(a)

def test2():
    x = 23
    test1(a=None, b=x)
```

So you should install the pyright vscode extension (ms-pyright).