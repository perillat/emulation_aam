# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
setup(
    name="dosecoef",
    version="2.0.0",
    description="Module qui fournit les coef de dose.",
    author="Damien Didier",
    url="http://localhost:8081",
    download_url="http://localhost:8081",
    packages=find_packages("src"),  # include all packages under src
    package_dir={"": "src"},  # tell distutils packages are under src
    # Data
    package_data={"dosecoef": ["data/*"]},
    # Dependencies
    # install_requires=["numpy>=1.3.0", "pxnc>=2.0.0", "dosecoef>=2.0.0"]
)
