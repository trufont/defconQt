#!/usr/bin/env python
from setuptools import setup

try:
    import fontTools  # noqa
except:
    print("*** Warning: defconQt requires fontTools, see:")
    print("    https://github.com/behdad/fonttools")

try:
    import ufoLib  # noqa
except:
    print("*** Warning: defconQt requires ufoLib, see:")
    print("    https://github.com/unified-font-object/ufoLib")

try:
    import defcon  # noqa
except:
    print("*** Warning: defconQt requires defcon, see:")
    print("    https://github.com/typesupply/defcon")

setup(
    name="defconQt",
    version="0.1.0",
    description="A set of Qt objects for use in defcon applications.",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="http://adrientetar.github.io",
    packages=[
        "defconQt",
        "defconQt.controls",
        "defconQt.representationFactories",
        "defconQt.tools",
        "defconQt.windows",
    ],
    package_dir={"": "Lib"},
    platforms=["Win32", "Mac OS X", "Linux"],
    classifiers=[
        "Environment :: GUI",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Fonts",
    ],
)
