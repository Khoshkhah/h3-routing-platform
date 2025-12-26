from setuptools import setup, find_packages

setup(
    name="osm-road-network",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyrosm>=0.6.1",
        "osmnx>=1.9.1",
        "networkx>=3.0",
        "geopandas>=0.12.0",
        "shapely>=2.0",
        "pandas>=1.5.0",
        "h3>=3.7.0",
        "osmium>=3.6.0",
        "pyyaml>=6.0",
    ],
)
