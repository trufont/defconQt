#!/usr/bin/env python
from setuptools import setup, find_packages


# TODO: add README.rst, so we can use on both Github and PyPI
# with open('README.rst', 'r') as f:
#     long_description = f.read()

setup(
    name="defconQt",
    version="0.5.0",
    description="A set of Qt objects for use in defcon applications.",
    # long_description=long_description,
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="https://github.com/trufont/defconQt",
    license="GNU LGPL v3/GNU GPL v3",
    package_dir={"": "Lib"},
    packages=find_packages("Lib"),
    platforms=["Win32", "Mac OS X", "Linux"],
    install_requires=[
        "pyqt5>=5.5.0",
        "fonttools>=3.3.1",
        "ufoLib>=2.0.0",
        "defcon>=0.2.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Fonts",
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)
