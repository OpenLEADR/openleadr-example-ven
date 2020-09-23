from setuptools import setup
import os

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as file:
    version = file.read().strip()

setup(name='openleadr-demo-client',
      version=version,
      description='Example implementation of an OpenADR client using openLEADR',
      install_requires=[f'openleadr=={version}', 'pyyaml'])