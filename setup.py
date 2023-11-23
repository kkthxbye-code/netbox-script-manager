#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = []

setup(
    author="kkthxbye-code",
    author_email="festll234@gmail.com",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="Improved custom script support for netbox",
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords=["netbox", "netbox-plugin"],
    name="netbox-script-manager",
    packages=find_packages(),
    test_suite="tests",
    url="https://github.com/kkthxbye-code/netbox_script_manager",
    version="0.3.13",
    zip_safe=False,
)
