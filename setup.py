import setuptools

setuptools.setup(
    name="DL_Track_US",
    version="0.1.2",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: MSK Ultrasobography :: Deep Learning",
    ],
    install_requires=[
        "jupyter==1.0.0",
        "Keras==2.10.0",
        "matplotlib==3.6.1",
        "numpy==1.23.4",
        "opencv-contrib-python==4.6.0.66",
        "openpyxl==3.0.10",
        "pandas==1.5.1",
        "Pillow==9.2.0",
        "pre-commit==2.17.0",
        "scikit-image==0.19.3",
        "scikit-learn==1.1.2",
        "sewar==0.4.5",
        "tensorflow==2.10.0",
        "tqdm==4.64.1",
    ],
    python_requires="=3.10",
)
