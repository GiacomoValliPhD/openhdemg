# Multiple Reference Signals

Version 0.2.0 improves support for files containing more than one reference-signal channel.

In *openhdemg*, reference signals are stored in:

```python
emgfile["REF_SIGNAL"]
```

`REF_SIGNAL` is a pandas DataFrame. Each column is one reference-signal channel.

Common examples include:

- force and torque recorded together;
- multiple force transducers;
- target force and measured force;
- original and processed reference traces kept in the same file.

## Inspect Reference-Signal Channels

```python
import openhdemg.library as emg

emgfile = emg.emg_from_samplefile()

print(emgfile["REF_SIGNAL"].head())
print(emgfile["REF_SIGNAL"].columns)
```

The sample file contains one reference-signal column named `0`, but your imported file can contain more columns.

## Rename Columns

`REF_SIGNAL` columns can be named either with base-0 integers, such as `0`, `1`, `2`, or with strings, such as `"force"` and `"target"`.

String names can make analysis scripts easier to read:

```python
emgfile["REF_SIGNAL"] = emgfile["REF_SIGNAL"].rename(
    columns={
        0: "force",
        1: "target",
    }
)
```

However, integer-based column names can make interaction with the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*** more straightforward, because channel selection is often naturally expressed as channel `0`, channel `1`, and so on.

Therefore, this is mostly a personal preference:

- use string names if you prefer readability in Python scripts;
- use base-0 integer names if you prefer simpler interaction with the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*** or want to keep the file closer to the default *openhdemg* structure.

## `refsig_channel` and `refsig_channels`

There are two related argument names.

Use `refsig_channel` when a function needs one reference signal:

- selecting an interval with `showselect()`;
- plotting one reference channel;
- calculating MVC, RFD, thresholds, discharge-rate properties, and basic MU properties;
- showing the reference signal in tracking GUIs.

Use `refsig_channels` when a function can modify one or more reference signals:

- filtering reference signals with `filter_refsig()`;
- removing offsets with `remove_offset()`.

## Plot One Reference Signal

```python
import openhdemg.library as emg

emg.plot_refsig(
    emgfile=emgfile,
    refsig_channel="force",
)
```

With integer column names:

```python
emg.plot_refsig(
    emgfile=emgfile,
    refsig_channel=0,
)
```

## Add One Reference Signal to MU Plots

Most MU plots can add one selected reference signal.

```python
emg.plot_idr(
    emgfile=emgfile,
    addrefsig=True,
    refsig_channel="force",
)
```

## Filter Selected Reference Channels

Filter one channel:

```python
filtered = emg.filter_refsig(
    emgfile=emgfile,
    order=4,
    cutoff=15,
    refsig_channels=["force"],
)
```

Filter more than one channel:

```python
filtered = emg.filter_refsig(
    emgfile=emgfile,
    order=4,
    cutoff=15,
    refsig_channels=["force", "target"],
)
```

Only the selected channels are modified. Other `REF_SIGNAL` columns are preserved.

## Remove Offset From Selected Channels

Automatically remove the offset using the first 1024 samples:

```python
offset_removed = emg.remove_offset(
    emgfile=filtered,
    auto=1024,
    refsig_channels=["force"],
)
```

Apply the same manual offset to multiple channels:

```python
offset_removed = emg.remove_offset(
    emgfile=filtered,
    offsetval=2.5,
    refsig_channels=["force", "target"],
)
```

Apply different offsets to different channels:

```python
offset_removed = emg.remove_offset(
    emgfile=filtered,
    offsetval=[2.5, 1.0],
    refsig_channels=["force", "target"],
)
```

The length of `offsetval` must match the length of `refsig_channels` when different offsets are passed.

## Resize Using a Selected Reference Channel

```python
resized_emgfile, start_, end_ = emg.resize_emgfile(
    emgfile=emgfile,
    how="ref_signal",
    refsig_channel="force",
)
```

If you already know the sample range:

```python
resized_emgfile, start_, end_ = emg.resize_emgfile(
    emgfile=emgfile,
    area=[12000, 50000],
)
```

## Calculate Force-Based Metrics

Use the channel representing the signal of interest.

```python
mvc = emg.get_mvc(
    emgfile=emgfile,
    how="all",
    refsig_channel="force",
)
```

## Analyse MU Properties With One Reference Channel

```python
properties = emg.basic_mus_properties(
    emgfile=emgfile,
    mvc=634,
    refsig_channel="force",
)
```

The selected channel is used for recruitment and derecruitment thresholds, steady-state region selection, and related reference-signal calculations.

## More Questions?

If you need additional information, read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}.
