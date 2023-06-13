import setuptools
import openhdemg as emg

setuptools.setup(
    name="openhdemg",
    version=emg.__version__,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: High Density EMG :: Muscle",
    ],
    python_requires="=3",
)
