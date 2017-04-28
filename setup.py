from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='kpuglyparser',
    version='1.1',
    packages=find_packages(),
    install_requires=[
        'grab',
        'htmlmin',
        'dateparser',
        'delorean',
        'bs4',
        'requests',
        'beaker',
        'fake-useragent',
        'pydash==3.4.8',
    ]
)