from setuptools import setup, find_packages

setup(
    name="sky-api-python-client",
    version="0.4.2",
    author="Jon",
    author_email="jon.nguyen7@protonmail.com",
    description="Package for communicating with the Blackbaud Sky API",
    url="https://github.com/Hacky-The-Sheep/sky-api-python-client",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    test_suite="nose.collector",
)
