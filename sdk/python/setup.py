from setuptools import setup, find_packages

setup(
    name="h3_routing_client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "PyYAML>=5.1"
    ],
    author="Routing Platform Team",
    description="Python client for the H3 Routing Platform",
    python_requires=">=3.7",
)
