# Welcome to openhdemg
<p align="left">
    <a href="https://pypi.org/project/openhdemg/0.2.0b1/" alt="openhdemg version" target="_blank">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/openhdemg/0.2.0b1?label=pip&logo=PyPI&logoColor=gold&color=blue"></a>
    <a href="https://pypi.org/project/openhdemg/0.2.0b1/" alt="Python version" target="_blank">
        <img alt="PyPI" src="https://img.shields.io/pypi/pyversions/openhdemg/0.2.0b1?logo=Python&logoColor=gold&color=blue"></a>
    <a href="https://www.youtube.com/@openhdemg" alt="YouTube" target="_blank">
        <img src="https://img.shields.io/badge/youtube-Watch_videos-red.svg?color=blue&logoColor=gold&logo=youtube" /></a>
    <a href="https://twitter.com/openhdemg" alt="Twitter" target="_blank">
        <img src="https://img.shields.io/badge/twitter-Follow_us-red.svg?color=blue&logoColor=gold&logo=twitter" /></a>
    <a href="https://www.linkedin.com/company/openhdemg/" alt="LinkedIn" target="_blank">
        <img  src="https://img.shields.io/badge/linkedin-Follow_us-blue?logo=linkedin&logoColor=gold&color=blue" /> </a>
</p>

<br/>

<p align="center">
  <img src="https://www.giacomovalli.com/openhdemg/md_graphics/index/banner_logo.png" />
</p>

<br/>

## Overview

*openhdemg is a powerful toolbox for the analysis of HDsEMG recordings.*

*openhdemg* is an open-source framework written in Python 3 with many functionalities specifically designed for the analysis of High-Density surface Electromyography (HDsEMG) recordings. Some of its main features are listed below, but there is much more to discover! For a full list of available functions, please refer to the **API reference** section at [www.giacomovalli.com/openhdemg](https://www.giacomovalli.com/openhdemg/).

1. **Load** Raw HDsEMG signals or decomposed files from virtually any source (either via built-in or custom functions).
2. **Visualise** your EMG or force/reference signal, as well as the motor unit firing times and their action potential shapes.
3. **Decompose** your multichannel EMG signal into motor unit discharge times using convolutive blind source separation.
4. **Edit** your file changing the reference signal offset, filtering noise, calculating differential derivations and removing unwanted motor units.
5. **Analyse** motor unit recruitment/derecruitment thresholds, discharge rate, conduction velocity, action potentials amplitude and more...
6. **Track** motor units across different recording sessions.
7. **Save** the results of the analyses and the edited file.

## Start immediately
If you already know how to use Python, that's the way to go! Otherwise, have a look at the tutorial explaining how to [Setup your Python working environment](https://www.giacomovalli.com/openhdemg/tutorials/setup_working_env/).

*openhdemg* can be easily installed using pip:

```shell
pip install --upgrade openhdemg
```

To test pre-release builds (including v0.2.0-beta), use:

```shell
pip install --pre --upgrade openhdemg
```

If you want an overview of what you can do with the *openhdemg* library, have a look at the [Quick Start section](https://www.giacomovalli.com/openhdemg/quick-start/) and then explore all the functions in the **API reference**.

## Good to know
In addition to the rich set of modules and functions presented in the **API reference**, the *openhdemg* library is now integrated in the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}***, which offers a practical interface from which many tasks can be performed without writing a single line of code!

Please visit the official website page dedicated to the software for more info by clicking *[here](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*.

<br/>

![gui_preview](https://www.giacomovalli.com/openhdemg/md_graphics/index/software_preview.png)

## Why openhdemg
The *openhdemg* project was born in 2022 with the aim to provide the HDsEMG community with a free and open-source framework to analyse motor unit properties.

The field of EMG analysis in humans has always been characterized by a lack of available software for signal post-processing and analysis. This has forced users to code their own scripts, which can lead to problems when the scripts are not shared open-source. Why?

- If different users use different scripts, the results can differ.
- Any code can contain errors, if the code is not shared, the errors will never be known and them will repeat in the following analyses.
- There is a significant difference between the methods presented in research papers and the practical implementation of a script. Reproducing a script solely based on written instructions can be challenging, making the reproducibility of a study unrealistic.
- Anyone who doesn't code, will not be able to analyse the recordings.

In order to overcome these problems, we developed a fully transparent framework for the analysis of motor unit properties.

This project is intended for the users that already know the Python language, for those willing to learn it and even for those not interested in coding, thanks to the friendly ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}***.

Both the *openhdemg* project and its contributors adhere to the Open Science Principles and especially to the idea of public release of data and other scientific resources necessary for conducting honest research.
