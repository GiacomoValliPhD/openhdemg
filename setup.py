# Copyright (C) 2022 - 2026. The openhdemg community.

# To read the content of the README or description file
from pathlib import Path

# To install required dependencies
from setuptools import setup

import openhdemg

INSTALL_REQUIRES = [
    "matplotlib==3.9.3",
    "numpy<=2.2.0",
    "pandas==2.2.3",
    "PySide6==6.9.0",
    "scipy<=1.14.1",
    "scikit-learn==1.5.2",
]

EXTRAS_REQUIRE = {
    "gurobi": [
        "gurobipy",
    ],
}
# pip install "openhdemg[gurobi]"

PACKAGES = [
    "openhdemg",
    "openhdemg.library",
    "openhdemg.library.decomposed_test_files",
    "openhdemg.compatibility",
    "openhdemg.ui",
    "openhdemg.ui.icons",
    "openhdemg.tests",
    "openhdemg.tests.fixtures",
    "openhdemg.tests.integration",
    "openhdemg.tests.unit",
]

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
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
        license="BSD-3-Clause",
        project_urls={
            "Documentation": "https://giacomovalli.com/openhdemg",
            "Release Notes": "https://giacomovalli.com/openhdemg/what%27s-new",
            "Source Code": "https://github.com/GiacomoValliPhD/openhdemg",
            "Bug Tracker": "https://github.com/GiacomoValliPhD/openhdemg/issues",
        },
        version=openhdemg.__version__,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        include_package_data=True,
        packages=PACKAGES,
        package_data={"openhdemg": ["*"]},
        classifiers=CLASSIFIERS,
    )
