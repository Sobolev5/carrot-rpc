import os
import sys
import setuptools

__author__ = 'Sobolev Andrey <email.asobolev@gmail.com>'
__version__ = '0.2.7'

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='carrot-rpc',
    version=__version__,
    install_requires=['aiormq>=6.4.2', 'simple-print>=1.4.7', 'orjson>=3.8.0', 'pydantic>=1.10.2'],
    author='Sobolev Andrey',
    url="https://github.com/Sobolev5/carrot-rpc",        
    author_email='email.asobolev@gmail.com',
    description='Carrot it is a python asyncio RPC server/client for RabbitMQ with pydantic schema that allows you to make RPC calls.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=[".git", ".gitignore"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)