# Manage Collections

!!! note "Important note for collections"
    *openhdemg* collections are currently supported by the Python library, but not yet by the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*** (as of June 2026). If you plan to use the same data in the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}***, save each `emgfile` as an individual module for now. Use collections only for Python-based workflows until software integration is finalised.

An `openhdemg_Collection` manages multiple *openhdemg* modules together with shared data and participant-level metadata.

Use collections when you want to keep related `emgfile`s together, for example:

- multiple trials from one participant;
- multiple muscles (or grids) from the same recording session;
- several contractions from the same recording session;
- files that share a reference signal or participant metadata;
- a batch that should be saved, loaded, and archived as one unit.

For saving a single `emgfile`, use a binary module instead. See how to [Save and load binary modules](binary_modules.md).

## Collection Structure

A saved collection is a structured folder containing:

- `.openhdemg_collection`, a marker file identifying the folder as an *openhdemg* collection;
- `manifest.json`, a readable index describing the collection;
- one folder per saved module;
- optional shared data saved as binary files;
- optional participant metadata in the manifest.

The class supports both full loading and selective loading, so you can load only one module or the shared dataframe when you do not need the whole collection in memory.

## Create a Collection

Start by creating the collection object and setting its root folder.

```python
import openhdemg.library as emg

collection = emg.openhdemg_Collection()

collection.set_root(
    "C:/Users/.../Desktop/openhdemg_collections/participant_01"
)
```

`set_root()` defines where the collection will be saved or loaded.

## Add Participant Metadata

Participant information is stored in the collection manifest.

```python
collection.set_participant_info(
    {
        "participant_id": "P01",
        "session": "S01",
        "muscle": "Tibialis anterior",
        "notes": "Example metadata for the collection tutorial",
    }
)
```

Keep metadata simple and JSON-serialisable. Strings, numbers, booleans, lists, and dictionaries are usually safe.

## Add Shared Data

A collection can store a shared dataframe. This is useful when multiple modules share the same participant-level information, external reference signal, target profile, or trial table.

```python
import pandas as pd

shared_df = pd.DataFrame(
    {
        "trial": ["ramp_01", "ramp_02"],
        "target_force_percent_mvc": [30, 50],
    }
)

collection.set_shared_dataframe(shared_df)
```

If each trial has its own `REF_SIGNAL`, keep that signal inside the corresponding module. Use the shared dataframe for information that belongs to the collection as a whole.

## Add Modules

Each module is an `emgfile`.

```python
trial_01 = emg.emg_from_samplefile()
trial_02 = emg.emg_from_samplefile()

collection.add_module(
    module=trial_01,
    module_name="ramp_01",
)

collection.add_module(
    module=trial_02,
    module_name="ramp_02",
)
```

If a module with the same name already exists in the in-memory collection, `replace=True` is the default.

```python
collection.add_module(
    module=trial_01,
    module_name="ramp_01",
    replace=True,
)
```

## Save the Collection

Save the complete collection with:

```python
collection.save()
```

This saves the manifest, modules, shared dataframe, and participant metadata.

If you want to choose the destination with a user interface:

```python
collection.asksave()
```

## Load the Whole Collection

Create a new collection object, set the root, and load.

```python
import openhdemg.library as emg

collection = emg.openhdemg_Collection()
collection.set_root(
    "C:/Users/.../Desktop/openhdemg_collections/participant_01"
)

collection.load()
```

You can then access modules and metadata:

```python
participant_info = collection.get_participant_info()
shared_df = collection.get_shared_dataframe()
ramp_01 = collection.get_module("ramp_01")
```

## Selectively Load One Module

For large collections, you may not want to load everything.

```python
collection = emg.openhdemg_Collection()
collection.set_root(
    "C:/Users/.../Desktop/openhdemg_collections/participant_01"
)

collection.load_manifest()

ramp_01 = collection.load_module(module_name="ramp_01")
```

This pattern is useful when processing many trials in a loop.

## Save One Updated Module

After changing one module, save it without rewriting the entire collection.

```python
ramp_01 = collection.get_module("ramp_01")

ramp_01 = emg.filter_refsig(
    emgfile=ramp_01,
    cutoff=15,
    refsig_channels=[0],
)

collection.add_module(
    module=ramp_01,
    module_name="ramp_01",
    replace=True,
)

collection.save_module(
    module_name="ramp_01",
    save_updated_manifest=True,
)
```

Use `save_updated_manifest=True` when changes should be reflected in the collection manifest immediately.

## Remove a Module

Remove a module from the in-memory collection:

```python
collection.remove_module("ramp_02")
```

Then save the collection to persist the change.

## Suggested Naming

Use simple, stable names for modules.

Good examples:

- `participant_01_ramp_30mvc`
- `participant_01_ramp_50mvc`
- `session_02_trial_03`
- `baseline_raw`
- `baseline_decomposed`

Avoid names that depend on local folder structure or temporary analysis decisions.

## More Questions?

If you need additional information, read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}.
