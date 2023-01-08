from setuptools import setup, find_packages

setup(
    name="sky-api-python-client",
    version="0.4.2",
    author="Jon",
    author_email="warren.hyson5@gmail.com",
    description="Package for communicating with the Blackbaud Sky API",
    url="https://github.com/LearnThinkCreate/sky-api-python-client",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    test_suite="nose.collector",
)
