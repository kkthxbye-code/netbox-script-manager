#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = []

setup(
    author="Simon Toft",
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
    include_package_data=True,
    keywords="netbox, plugin, script",
    name="netbox_script_manager",
    packages=find_packages(include=["netbox_script_manager", "netbox_script_manager.*"]),
    test_suite="tests",
    url="https://github.com/kkthxbye-code/netbox_script_manager",
    version="0.1.0",
    zip_safe=False,
)
