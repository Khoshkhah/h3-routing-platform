from setuptools import setup, find_packages

setup(
    name="h3-routing-platform-client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "dataclasses>=0.6;python_version<'3.7'",
        "PyYAML>=5.1"
    ],
    author="Routing Platform Team",
    description="Python client for the C++ Routing Engine",
)
