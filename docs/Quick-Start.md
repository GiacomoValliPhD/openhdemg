Let's implement together, step-by-step, a script to analyse all the relevant
motor units' (MUs) properties.

In particular, we will go through:

1. **Install** *opendemg*
2. **Load** a file
3. **Visualise** the content of the file
4. **Filter** the reference signal
5. **Remove** unwanted MUs
6. **Analyse** fundamental MUs properties
7. **Save** the edited file and the results of the analysis

## 1. Install

*openhdemg* can be easily installed using pip:

```shell
pip install openhdemg
```

or conda:

```shell
conda install -c conda-forge openhdemg
```

Once the installation of *openhdemg* is succesfull, you can install all the
required packages from the reqirements.txt file.

## 2. Load a file

In this example, we will use the sample file provided with *openhdemg*.
This can be simply loaded calling the function `emg_from_samplefile`:

```Python
emgfile = emg.emg_from_samplefile()
```