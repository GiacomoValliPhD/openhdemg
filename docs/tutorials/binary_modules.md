# Save and Load Binary Modules

Starting from version 0.2.0, binary modules are the recommended way to save and load individual *openhdemg* files.

A module is a structured folder that contains:

- `.openhdemg_module`, a marker file identifying the folder as an *openhdemg* module;
- `manifest.json`, a readable index describing the saved content;
- `files/`, a folder containing binary data files, optionally compressed.

This workflow is designed to be faster and more portable than the previous JSON-centred workflow, while still keeping the saved data inspectable through a manifest.

## When to Use a Module

Use a module when you want to save one `emgfile`.

Typical examples:

- a file imported from another platform;
- a cleaned file after deleting MUs or filtering reference signals;
- a raw file prepared for decomposition;
- a decomposed file produced by `EMGDecomposer`;
- a file containing optional validation keys such as `REFERENCE_MUPULSES` or `ROA_WITH_REFERENCE_MUPULSES`.

Use a collection instead when you want to manage multiple modules from the same participant, session, study, or batch. See [Manage collections](collections.md).

!!! note "Important note for collections"
    *openhdemg* collections are currently supported by the Python library, but not yet by the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*** (as of June 2026). If you plan to use the same data in the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}***, save each `emgfile` as an individual module for now. Use collections only for Python-based workflows until software integration is finalised.

## Save a Module

Load or create an `emgfile`, then call `save_openhdemg_module()`.

```python
import openhdemg.library as emg

emgfile = emg.emg_from_samplefile()

module_path = emg.save_openhdemg_module(
    emgfile=emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="sample_file",
    compresslevel=None,
    add_checksum=True,
)

print(module_path)
```

The function creates:

```text
openhdemg_modules/
`-- sample_file/
    |-- .openhdemg_module
    |-- manifest.json
    `-- files/
        |-- RAW_SIGNAL.bin.gz
        |-- REF_SIGNAL.bin.gz
        `-- ...
```

The exact files depend on the keys present in the `emgfile`.

## Choose a Compression Level

`compresslevel` controls whether binary files are compressed.

| Value | Behaviour | Suggested use |
| --- | --- | --- |
| `None` | PREFERRED! Save uncompressed binary files. | Large files, fast access, future random-access workflows. |
| `0` | Use gzip container with no compression. | Rarely needed. |
| `1` | Light compression. | Recommended balance for many workflows. |
| `2` to `6` | Moderate compression. | When storage space matters more than save/load speed. |
| `7` to `9` | Strong compression. | Archival use when speed is less important. |

For most users, `compresslevel=1` is a good starting point.

## Add Checksums

Set `add_checksum=True` to store SHA-256 checksums for saved binary files.

```python
emg.save_openhdemg_module(
    emgfile=emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="sample_file",
    compresslevel=1,
    add_checksum=True,
)
```

Checksums are useful when files are:

- shared between computers;
- uploaded to a repository;
- archived for long-term storage;
- copied to external drives or network folders.

## Load a Module

Use `load_openhdemg_module()` and point it to the parent folder and module name.

```python
import openhdemg.library as emg

emgfile = emg.load_openhdemg_module(
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="sample_file",
    verify_checksum=True,
)
```

Set `verify_checksum=True` when the module was saved with checksums and you want to verify file integrity during loading.

## Return Metadata

If you want to inspect the manifest metadata together with the loaded `emgfile`, use `return_metadata=True`.

```python
emgfile, metadata = emg.load_openhdemg_module(
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="sample_file",
    verify_checksum=True,
    return_metadata=True,
)

print(metadata)
```

This is useful when tracking which *openhdemg* version, operating system, or Python version created the module.

## Save and Load With Dialogs

Use `asksavemodule()` when you want to select the destination through a user interface:

```python
import openhdemg.library as emg

emgfile = emg.emg_from_samplefile()

emg.asksavemodule(emgfile=emgfile)
```

Use `askloadmodule()` to select a module folder and load it:

```python
emgfile = emg.askloadmodule()
```

If your workflow needs the selected path as well:

```python
emgfile, module_path = emg.askloadmodule(return_path=True)
```

## Overwriting Modules

When saving a module with an existing `module_name`, *openhdemg* overwrites only folders that look like safe *openhdemg* module folders. A folder is considered safe when it contains the expected marker and manifest, or when it is empty.

This protects users from accidentally deleting unrelated folders.

If a save fails because the destination folder is not recognised as an *openhdemg* module, choose a different `module_name` or move the unrelated folder manually.

## JSON Compatibility

The older JSON workflow is still available:

```python
emg.save_json_emgfile(emgfile, filepath="C:/Users/.../Desktop/file.json")
emgfile = emg.emg_from_json(filepath="C:/Users/.../Desktop/file.json")
```

Use JSON when you need compatibility with old scripts. Use binary modules for new v0.2.0 workflows.

## Recommended Pattern

For a typical analysis script:

```python
import openhdemg.library as emg

emgfile = emg.emg_from_samplefile()

emgfile = emg.sort_mus(emgfile)
emgfile = emg.filter_refsig(emgfile, cutoff=15, refsig_channels=[0])
emgfile = emg.remove_offset(emgfile, auto=1024, refsig_channels=[0])

results = emg.basic_mus_properties(
    emgfile=emgfile,
    mvc=634,
    refsig_channel=0,
)

results.to_csv("C:/Users/.../Desktop/sample_file_results.csv")

emg.save_openhdemg_module(
    emgfile=emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="sample_file_cleaned",
    compresslevel=None,
    add_checksum=True,
)
```

## More Questions?

If you need additional information, read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}.
