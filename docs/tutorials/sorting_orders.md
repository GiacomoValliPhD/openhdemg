# Custom Channel Sorting Orders

Use a custom sorting order when the columns of `emgfile["RAW_SIGNAL"]` do not
follow the physical arrangement of the already available sorting orders.

A sorting order is a list of lists:

- the outer list represents grid columns, from left to right;
- each inner list represents positions within one column, from top to bottom;
- channel numbers refer to the columns of `RAW_SIGNAL` and must be base-0;
- `np.nan` represents a physical position without a channel.

For example, this grid has three rows and two columns:

| | Column 0 | Column 1 |
| --- | ---: | ---: |
| Row 0 | 0 | 3 |
| Row 1 | 1 | 4 |
| Row 2 | 2 | 5 |

Its sorting order is:

```python
custom_sorting_order = [
    [0, 1, 2],  # Column 0
    [3, 4, 5],  # Column 1
]
```

## Apply the Sorting Order

```python
import openhdemg.library as emg

sorted_rawemg = emg.sort_rawemg(
    emgfile=emgfile,
    code="Custom order",
    custom_sorting_order=custom_sorting_order,
    dividebycolumn=True,
)
```

With `dividebycolumn=True`, the result is a dictionary containing `col0`,
`col1`, and so on. With `dividebycolumn=False`, the result is one DataFrame,
ordered column by column.

The `orientation`, `n_rows`, and `n_cols` arguments are not needed for a custom
order because the grid shape is taken directly from `custom_sorting_order`.

## Example: Alternating Channel Direction

Channel numbering sometimes changes direction between adjacent columns. The
following synthetic grid uses an upward direction in its middle column:

| | Column 0 | Column 1 | Column 2 |
| --- | ---: | ---: | ---: |
| Row 0 | 0 | 5 | 6 |
| Row 1 | 1 | 4 | 7 |
| Row 2 | 2 | 3 | 8 |

```python
custom_sorting_order = [
    [0, 1, 2],
    [5, 4, 3],
    [6, 7, 8],
]
```

## Example: Empty Grid Position

Use `np.nan` when the physical grid contains a position without a recorded
channel:

| | Column 0 | Column 1 |
| --- | ---: | ---: |
| Row 0 | 0 | 4 |
| Row 1 | 1 | 5 |
| Row 2 | 2 | 6 |
| Row 3 | 3 | Empty |

```python
import numpy as np

custom_sorting_order = [
    [0, 1, 2, 3],
    [4, 5, 6, np.nan],
]
```

The sorted result contains an all-`NaN` column at the empty position. The
original signal is not modified.

## Quick Checks

Before sorting, make sure that:

- `RAW_SIGNAL` uses base-0 integer column names (`0`, `1`, `2`, ...);
- every recorded channel appears exactly once in the sorting order;
- all inner lists have the same length;
- empty physical positions use `np.nan`, not a channel number.

If a channel diagram uses base-1 numbering (`1`, `2`, `3`, ...), subtract one
from each channel number before creating the sorting order.
