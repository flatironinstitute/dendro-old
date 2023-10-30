from setuptools import setup, find_packages

# read the contents of README.md
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

__version__ = '0.1.3'

setup(
    name='dendro',
    version=__version__,
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    url="https://github.com/flatironinstitute/dendro",
    description="Create, run, and share neuroscience analyses in the browser",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(include=['dendro', 'dendro_sdk']),
    include_package_data=True,
    install_requires=[
        'click',
        'simplejson',
        'numpy',
        'PyYAML',
        'remfile>=0.1.8',
        'pubnub>=7.2.0',
        'pydantic',
        'cryptography'
    ],
    entry_points={
        "console_scripts": [
            "dendro=dendro.cli:main",
        ],
    }
)
