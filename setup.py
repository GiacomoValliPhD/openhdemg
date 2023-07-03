# Copyright (C) 2023 Giacomo Valli, Paul Ritsche

# For the openhdemg version
import openhdemg as emg
# To read the content of the README or description file
from pathlib import Path

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

this_directory = Path(__file__).parent
long_descr = (this_directory / "README.md").read_text()

if __name__ == "__main__":
    setup(
        name="testgiacomovalli",
        maintainer="Giacomo Valli",
        maintainer_email="giacomo.valli@phd.unipd.it",
        description="Open-source analysis of High-Density EMG data",
        long_description=long_descr,
        long_description_content_type='text/markdown',
        license="GPL-3.0",
        project_urls={
            "Documentation": "https://giacomovalli.com/openhdemg",
            "release notes": "https://giacomovalli.com/openhdemg/What%27s-New",
            "Source Code": "https://github.com/GiacomoValliPhD/openhdemg",
            "Bug Tracker": "https://github.com/GiacomoValliPhD/openhdemg/issues",
        },
        version="0.1.0-beta.31",  # emg.__version__,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        packages=PACKAGES,
        package_data={"openhdemg": ["*"]},
        classifiers=CLASSIFIERS,
    )
