"""Integration tests for saving and loading altered openhdemg modules."""

import unittest
from copy import deepcopy
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
from openhdemg.library.openfiles import (
    load_openhdemg_module, save_openhdemg_module,
)
from openhdemg.tests.unit.functions_for_unit_test import get_module_fixture


class TestModuleRoundTrip(unittest.TestCase):
    """
    Test saving modules and loading them back.

    Check that changing reference-signal columns, compression and overwriting
    preserves module contents without modifying the input. Also document the
    precision loss possible with mixed integer/float reference-signal data.
    All output goes to temporary directories; the original fixture is
    unchanged.
    """

    def test_save_load_reference_signals(self):
        """
        Preserve module contents when reference columns and compression change.
        """

        module = get_module_fixture()
        original = load_openhdemg_module(
            module.parent, module.name, verify_checksum=True,
        )
        reference = original["REF_SIGNAL"].iloc[:, 0]

        # Unique column labels: integers, strings, mixed labels and a wide
        # frame.
        cases = [
            ([0], None),
            ([0, 1, 2], None),
            ([7, 2, 15], None),
            (["force", "torque", "angle"], None),
            ([0, "0", "force"], None),
            (list(range(32)), None),
        ]
        for level in (0, 1, 9):
            cases.append(([0, "0", "force"], level))
            cases.append((list(range(32)), level))
        cases.append((["final_signal"], None))

        with TemporaryDirectory() as directory:
            for columns, level in cases:
                with self.subTest(columns=columns, compresslevel=level):
                    emgfile = deepcopy(original)
                    # Different values in each column expose swaps or
                    # duplication.
                    emgfile["REF_SIGNAL"] = pd.DataFrame({
                        column: reference + offset
                        for offset, column in enumerate(columns)
                    })
                    expected = deepcopy(emgfile)

                    # Overwrite the same module, including 32 columns down to
                    # one.
                    save_openhdemg_module(
                        emgfile, directory, "module",
                        compresslevel=level, add_checksum=True,
                    )
                    restored = load_openhdemg_module(
                        directory, "module", verify_checksum=True,
                    )

                    # Check the complete round trip and that saving left input
                    # intact.
                    for result in (restored, emgfile):
                        self.assertEqual(result.keys(), expected.keys())
                        for key, value in expected.items():
                            with self.subTest(field=key):
                                actual = result[key]
                                if isinstance(value, pd.DataFrame):
                                    pd.testing.assert_frame_equal(
                                        actual, value, check_exact=True,
                                    )
                                elif isinstance(value, list):
                                    self.assertEqual(len(actual), len(value))
                                    for array, expected_array in zip(actual, value):
                                        np.testing.assert_array_equal(
                                            array, expected_array,
                                        )
                                        self.assertEqual(
                                            array.dtype, expected_array.dtype,
                                        )
                                else:
                                    self.assertEqual(actual, value)

    def test_save_load_mixed_dtype_precision(self):
        """
        Document why standard dtypes are preferred when saving modules.

        Prefer the dtypes defined by standardise_emgfile_dtypes: float64 for
        signal/accuracy frames, int64 for pulse arrays, and uint8 for binary
        firings. Saving/loading support alternative dtypes, but users are
        responsible for checking their range, precision and round-trip
        behaviour. Custom fields such as EXTRAS are not standardised.

        This test deliberately uses nonstandard int64 data in REF_SIGNAL.
        Saving combines int64 and float64 columns into one float64 array.
        Above 2**53, float64 cannot represent every integer. These examples
        lose 1 and 128 units even though loading restores the int64 dtype.
        Standardising first would also round these integers.
        """

        reference = pd.DataFrame({
            "integer": pd.Series(
                [2**53 - 1, 2**53, 2**53 + 1, 2**60 + 128], dtype="int64",
            ),
            "fraction": pd.Series([0.25, 0.5, 0.75, 1.0], dtype="float64"),
        })
        emgfile = {
            "FILENAME": "precision", "FSAMP": 2048.0,
            "REF_SIGNAL": reference,
            # The same integers saved without a floating-point column
            "EXTRAS": reference[["integer"]].copy(),
        }
        with TemporaryDirectory() as directory:
            save_openhdemg_module(emgfile, directory, "precision")
            restored = load_openhdemg_module(directory, "precision")

        # Subtract Python integers so float rounding cannot hide the error
        errors = [
            int(actual) - int(expected)
            for actual, expected in zip(
                restored["REF_SIGNAL"]["integer"], reference["integer"],
            )
        ]
        self.assertEqual(errors, [0, 0, -1, -128])
        self.assertEqual(
            restored["REF_SIGNAL"]["integer"].dtype, np.dtype("int64"),
        )
        pd.testing.assert_series_equal(
            restored["REF_SIGNAL"]["fraction"], reference["fraction"],
            check_exact=True,
        )
        pd.testing.assert_frame_equal(
            restored["EXTRAS"], emgfile["EXTRAS"], check_exact=True,
        )


if __name__ == "__main__":
    unittest.main()
