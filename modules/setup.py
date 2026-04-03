from setuptools import setup, find_packages

setup(
    name='commonmodulelib',
    version='0.1',
    packages=find_packages(),  # __init__.py 있는 모든 폴더 자동 포함
    install_requires=[],
)