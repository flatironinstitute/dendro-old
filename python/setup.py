from setuptools import setup, find_packages

# read version from dendro/version.txt
with open('dendro/version.txt') as f:
    __version__ = f.read().strip()

setup(
    name='dendro',
    version=__version__,
    author="Jeremy Magland, Luiz Tauffer",
    author_email="jmagland@flatironinstitute.org",
    url="https://github.com/flatironinstitute/dendro",
    description="Web framework for neurophysiology data analysis",
    packages=find_packages(),
    include_package_data=True,
    package_data={'dendro': ['version.txt']},
    install_requires=[
        'click',
        'simplejson',
        'numpy',
        'PyYAML',
        'remfile',
        'pydantic', # intentionally do not specify version 1 or 2 since we support both
        'cryptography',
        'h5py>=3.10.0'
    ],
    extras_require={
        'compute_resource': [
            'pubnub>=7.2.0',
            'boto3'
        ],
        'api': [
            'fastapi',
            'motor',
            'simplejson',
            'pydantic',
            'aiohttp'
        ]
    },
    entry_points={
        "console_scripts": [
            "dendro=dendro.cli:main",
        ],
    }
)
