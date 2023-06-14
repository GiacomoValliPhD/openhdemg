# Copyright (C) 2023 Giacomo Valli, Paul Ritsche

import openhdemg as emg

# read the contents of the README file
from pathlib import Path
this_directory = Path(__file__).parent
LONG_DESCRIPTION = (this_directory / "long_description.md").read_text()

DESCRIPTION = "Open-source analysis of High-Density EMG data"
DISTNAME = "testgiacomovalli"
MAINTAINER = "Giacomo Valli"
MAINTAINER_EMAIL = "giacomo.valli@phd.unipd.it"
DOCUMENTATION_URL = "https://..."
SOURCECODE_URL = "https://github.com/GiacomoValliPhD/openhdemg"
BTRACKER_URL = "https://...."
VERSION = emg.__version__
LICENSE = "GPL-3.0"
PACKAGE_DATA = {"openhdemg": ["*"]}

INSTALL_REQUIRES = [
    "customtkinter>=5.1.3",
    "matplotlib>=3.7.1",
    "numpy>=1.24.3",
    "openpyxl>=3.1.2",
    "pandas>=2.0.2",
    "pandastable>=0.13.1",
    "pyperclip>=1.8.2",
    "scipy>=1.10.1",
    "seaborn>=0.12.2",
]

PACKAGES = [
    "openhdemg",
    "openhdemg.gui",
    "openhdemg.gui.gui_files",
    "openhdemg.library",
    "openhdemg.library.decomposed_test_files",
    "docs.md_graphics.Index",
]

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Human Machine Interfaces",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Operating System :: MacOS",
]

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if __name__ == "__main__":
    setup(
        name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        license=LICENSE,
        project_urls={
            'Documentation': DOCUMENTATION_URL,
            'Source Code': SOURCECODE_URL,
            'Bug Tracker': BTRACKER_URL,
        },
        version=VERSION,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        classifiers=CLASSIFIERS,
    )
