'''
Created on 18.02.2014

@author: mend_ma
'''
from setuptools import setup, find_packages
import UAV_RC

setup(
    name='UAV-RC',
    version=UAV_RC.__version__,
    packages=find_packages(),
)