# Migrate to 0.2.0-beta.1

Version 0.2.0-beta.1 is a beta release with intentional changes to the way *openhdemg* stores data, handles user interfaces, represents `emgfile`s, and manages plotting. This tutorial gives you a practical migration checklist.

## What Changed

The main changes are:

- the legacy Tkinter GUI has been discontinued in favour of the new PySide6-based software and reusable UI architecture;
- binary modules and collections are now the recommended save/load workflow;
- the `emgfile` structure is more flexible and no longer needs to contain every standard key;
- some functions now support multiple reference-signal channels;
- plotting functions can use either pyplot or the object-oriented Matplotlib API;
- new decomposition, common-input, and result-plotting functions are available;
- some older parameters and classes are deprecated but still have compatibility paths.

## Before You Start

Keep your previous working environment until you have verified that your analysis scripts run correctly in v0.2.0-beta.1.

Recommended migration pattern:

1. Create a new Python environment for the beta release.
2. Keep a backup of original `.json`, `.mat`, `.csv`, or source files.
3. Install the beta or pre-release build in the new environment.
4. Load representative files and verify their content with `emg.info().data()`.
5. Save converted or edited data as binary modules.
6. Update scripts that assumed every standard `emgfile` key was always present.
7. Re-run analysis checks on a known dataset before using the beta for new results.

Install pre-release builds with:

```shell
pip install --pre --upgrade openhdemg
```

## Replace JSON-First Workflows

Older scripts often ended with:

```python
import openhdemg.library as emg

emg.asksavefile(emgfile)

# or

emg.save_json_emgfile(emgfile, ...)
```

This still works for compatibility, but new workflows should use binary modules:

```python
import openhdemg.library as emg

emg.save_openhdemg_module(
    emgfile=emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="participant_01_trial_01",
)
```

Load the module later with:

```python
emgfile = emg.load_openhdemg_module(
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="participant_01_trial_01",
)
```

If you prefer selecting folders from a dialog, use `asksavemodule()` and `askloadmodule()`.

## Convert Old JSON Files Into Modules

**You do not need a special conversion** class for v0.1.x JSON files that can already be loaded by the current `emg_from_json()` function. Simply load the old JSON file and save it as a module:

```python
import openhdemg.library as emg

old_emgfile = emg.emg_from_json(
    filepath="C:/Users/.../Desktop/old_file.json",
)

old_emgfile = emg.standardise_emgfile_dtypes(old_emgfile)

emg.save_openhdemg_module(
    emgfile=old_emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="old_file_converted",
)
```

Use the dedicated [Convert old .json files](convert_old_json_files.md) tutorial only when migrating files from older data structures that need `openhdemg.compatibility.convert_json_output`.

## Update `emgfile` Assumptions

Older code often assumed that every standard key was present:

```python
refsig = emgfile["REF_SIGNAL"]
ipts = emgfile["IPTS"]
mupulses = emgfile["MUPULSES"]
```

In v0.2.0, check whether optional data are present before using them:

```python
if "REF_SIGNAL" in emgfile:
    refsig = emgfile["REF_SIGNAL"]

if emgfile.get("NUMBER_OF_MUS", 0) > 0 and "MUPULSES" in emgfile:
    mupulses = emgfile["MUPULSES"]
```

When you manually create or edit an `emgfile`, standardise recognised data types:

```python
emgfile = emg.standardise_emgfile_dtypes(emgfile)
```

Read [Structure of the emgfile](emgfile_structure.md) for the full data-structure guide.

## Replace Deprecated Behaviour

### `askopenfile(initialdir=...)`

The old `initialdir="/"` behaviour is no longer exposed. The UI remembers the last accessed directory.

If your script used:

```python
emgfile = emg.askopenfile(filesource="OPENHDEMG", initialdir="/")
```

remove `initialdir`:

```python
emgfile = emg.askopenfile(filesource="OPENHDEMG")
```

### `compute_sil(ignore_negative_ipts=...)`

`ignore_negative_ipts` is deprecated. If you need to reproduce the previous behaviour, transform the IPTS before calling the function.

```python
import openhdemg.library as emg

mu_number = 0
ipts = emgfile["IPTS"][mu_number]
transformed_ipts = ipts * ipts.abs()

sil = emg.compute_sil(
    ipts=transformed_ipts,
    mupulses=emgfile["MUPULSES"][mu_number],
)
```

### `MUcv_gui`

`MUcv_gui` is deprecated. Use `run_mle_mucv_gui()` or `MLE_MUCV_gui` for the updated MLE conduction-velocity workflow.

```python
import openhdemg.library as emg

emg.run_mle_mucv_gui(
    emgfile=emgfile,
    sorted_rawemg=sorted_rawemg,
)
```

## Update Plotting Code

Plotting functions now return Matplotlib `Figure` objects. In scripts, the default `use_plt=True` keeps the familiar behaviour.

```python
fig = emg.plot_mupulses(emgfile)
```

When embedding plots in a GUI or when you want to manage figure display manually, use:

```python
fig = emg.plot_mupulses(
    emgfile,
    showimmediately=False,
    use_plt=False,
)
```

This avoids depending on pyplot's persistent global state.

## Update Reference-Signal Code

Several functions now accept `refsig_channel` or `refsig_channels`.

Use `refsig_channel` when a function needs one reference signal:

```python
results = emg.basic_mus_properties(
    emgfile=emgfile,
    mvc=634,
    refsig_channel=0,
)
```

Use `refsig_channels` when a function modifies one or more reference-signal channels:

```python
emgfile = emg.filter_refsig(
    emgfile=emgfile,
    cutoff=15,
    refsig_channels=[0, 1],
)
```

See [Multiple reference signals](multiple_reference_signals.md) for examples.

## Try the New Workflows

After the basic migration is complete, consider moving new projects to the v0.2.0 workflows:

- [Save and load binary modules](binary_modules.md)
- [Manage collections](collections.md)
- [Decomposition and cleaning](decomposition_and_cleaning.md)

## More Questions?

If you need additional information, read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}.
