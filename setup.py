# Copyright (C) 2023 Giacomo Valli, Paul Ritsche

# For the openhdemg version
# To read the content of the README or description file
from pathlib import Path

# To install required dependencies
from setuptools import setup

import openhdemg as emg

INSTALL_REQUIRES = [
    "customtkinter==5.2.1",
    "CTkMessagebox==2.5",
    "matplotlib==3.8.1",
    "numpy==1.26.1",
    "openpyxl==3.1.2",
    "pandas==2.0.3",
    "pandastable==0.13.1",
    "scipy==1.11.3",
    "seaborn==0.13.0",
    "joblib==1.3.2",
    # "pre-commit==3.7.0",
]

PACKAGES = [
    "openhdemg",
    "openhdemg.library",
    "openhdemg.library.decomposed_test_files",
    "openhdemg.compatibility",
    "openhdemg.gui",
    "openhdemg.gui.gui_files",
    "openhdemg.gui.gui_modules",
    "openhdemg.tests",
    "openhdemg.tests.fixtures",
    "openhdemg.tests.integration",
    "openhdemg.tests.unit",
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

this_directory = Path(__file__).parent
long_descr = (this_directory / "README.md").read_text()

if __name__ == "__main__":
    setup(
        name="openhdemg",
        maintainer="Giacomo Valli",
        maintainer_email="giacomo.valli@unibs.it",
        description="Open-source analysis of High-Density EMG data",
        long_description=long_descr,
        long_description_content_type="text/markdown",
        license="GPL-3.0",
        project_urls={
            "Documentation": "https://giacomovalli.com/openhdemg",
            "Release Notes": "https://giacomovalli.com/openhdemg/what%27s-new",
            "Source Code": "https://github.com/GiacomoValliPhD/openhdemg",
            "Bug Tracker": "https://github.com/GiacomoValliPhD/openhdemg/issues",
        },
        version=emg.__version__,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        packages=PACKAGES,
        package_data={"openhdemg": ["*"]},
        classifiers=CLASSIFIERS,
    )
