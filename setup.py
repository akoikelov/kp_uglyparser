from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='kp_uglyparser',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'grab',
        'htmlmin',
        'dateparser',
        'delorean',
        'bs4',
        'requests',
        'beaker'
    ]
)