from setuptools import setup, find_packages

__version__ = '0.1.5'

setup(
    name='dendro',
    version=__version__,
    author="Jeremy Magland, Luiz Tauffer",
    author_email="jmagland@flatironinstitute.org",
    url="https://github.com/flatironinstitute/dendro",
    description="Web framework for neurophysiology data analysis",
    packages=find_packages(include=['dendro']),
    include_package_data=True,
    install_requires=[
        'click',
        'simplejson',
        'numpy',
        'PyYAML',
        'remfile',
        'pydantic',
        'cryptography',
        'h5py>=3.10.0'
    ],
    extras_require={
        'compute_resource': [
            'pubnub>=7.2.0'
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
