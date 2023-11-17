# Dendro for developers

Here are some notes for developers. This is not a complete guide, but it should help you get started. Please contact the authors if you have any questions. We are happy to accept questions and pull requests.

* [Developing the Python package](#developing-the-python-package)
* [Developing the frontend](#developing-the-frontend)
* [About the API](#about-the-api)
* [Release strategy](#release-strategy)

# Developing the Python package

## Running the Python tests (vscode action)

```bash
# Install dendro
cd python
pip install -e .
```

```bash
# Install the dependencies needed for testing
pip install pytest pytest-asyncio pytest-cov pyright flake8
```

```bash
# Also install the dependencies for the API:
pip install -r requirements.txt
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

# Developing the frontend

## Setup

Install a modern version of nodejs (e.g. v18).

Install yarn (`npm install -g yarn`).

```bash
# Install the dependencies
cd dendro
yarn install
```

## Running a development frontend server without hosting a local API

**This is the simplest method if you are not working on the API.**

```bash
# Run the development server without the API
yarn dev

# Then open http://localhost:5173/?deployed-api=1
```

It is important to use the `deployed-api` query parameter, otherwise the frontend will attempt to connect to an API running on localhost:5172.

In order for all functionality to work, you will need to create a .env file in the root of the project with the following contents:

```bash
VITE_PUBNUB_SUBSCRIBE_KEY=...
VITE_GITHUB_CLIENT_ID=...
VITE_DEFAULT_COMPUTE_RESOURCE_ID=...
```

Contact the authors for the appropriate values of these environment variables.

## Running a development frontend server together with a local API

**Use this method only if you are working on the API.**

For this, you will need to
* Install the Python requirements as described above.
* Sign up for a vercel account
* Install the vercel command-line client
* Set up the appropriate cloud services
    - S3 bucket
    - MongoDB database
    - PubNub account
    - GitHub OAuth app
* Set up the vercel app and configure the appropriate environment variables
    - OUTPUT_BUCKET_CREDENTIALS, OUTPUT_BUCKET_BASE_URL, OUTPUT_BUCKET_URI, GITHUB_CLIENT_SECRET, VITE_GITHUB_CLIENT_ID, ADMIN_USER_IDS, VITE_PUBNUB_SUBSCRIBE_KEY, PUBNUB_PUBLISH_KEY, MONGO_URI, VITE_DEFAULT_COMPUTE_RESOURCE_ID

```bash
# Run the development server with the API
vercel dev
```

# About the API

See [./about_the_api.md](./about_the_api.md).

# Release strategy

This repo consists of two main components: the frontend and the Python package. The frontend may undergo frequent updates to enhance user experience and fix issues, while the Python package is expected to remain more stable.

**Frontend deployment:**

Generally speaking the main branch should always correspond to the currently deployed frontend. However, deployment is triggered in a GitHub action whenever changes are made to package.json, which usually results from manually bumping the frontend version. This should be performed regularly as changes are made to the frontend.

I followed this guide with some modifications to set up the GitHub action: https://vercel.com/guides/how-can-i-use-github-actions-with-vercel

A couple notes on creating the vercel_deploy.yaml. I found I needed to create the .vercel/project.json even though this step wasn't included in the guide. I had to trigger the build on vercel servers rather than building locally (as in the guide) in order to get the api to work.

The repository secrets are: VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_TOKEN

**Python package release:**

The main branch should also generally correspond to the currently deployed Python package on PyPI. However, deployment is triggered in a GitHub action whenever changes are made to python/dendro/version.txt, which results from manually bumping the version in this file. This should be performed regularly as changes are made within the python directory. Deployment will only occur if all CI tests pass. The GitHub action also adds a tag to the commit with the version number.
