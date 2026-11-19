"""
To run the tests using unittest, execute from the openhdemg/tests directory:
    python -m unittest discover

First, you should dowload all the files necessary for the testing and store
them inside openhdemg/tests/fixtures. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

WARNING!!! Since the library's functions perform complex tasks and return
complex data structures, these tests can verify that no critical errors occur,
but the accuracy of each function must be assessed independently upon creation,
or at each revision of the code.
"""


import unittest
import warnings
from unittest.mock import patch
from openhdemg.tests.unit.functions_for_unit_test import (
    get_directories as getd, get_module_fixture,
    validate_standard_emgfile_content,
)
from openhdemg.library.openfiles import (
    emg_from_samplefile, refsig_from_otb, emg_from_delsys,
    load_openhdemg_module,
)
from openhdemg.library.analysis import compute_dr
from openhdemg.library.tools import (
    showselect, standardise_emgfile_dtypes, create_binary_firings,
    mupulses_from_binary, resize_emgfile, EMGFileSectionsIterator, compute_idr,
    delete_mus, delete_empty_mus, sort_mus, compute_covsteady, filter_rawemg,
    filter_refsig, remove_offset, get_mvc, compute_rfd,
    find_duplicates_within, remove_duplicates_within,
    remove_powerline_harmonics, select_bad_channels,
)
from openhdemg.library.pic import compute_svr
import pandas as pd
import numpy as np
import scipy
import copy


class TestTools(unittest.TestCase):
    """
    Test the functions/classes in the tools module.
    """

    def setUp(self):
        """
        Initialize variables for each test.

        This method is called before each test function runs.
        """

        # Load the decomposed samplefile
        self.emgfile = emg_from_samplefile()

    def test_standardise_emgfile_dtypes(self):
        """Test dtype conversion and preservation of values and labels."""

        emgfile = {
            "SOURCE": np.str_("OTB"),
            "FILENAME": np.str_("example.mat"),
            "RAW_SIGNAL": pd.DataFrame(
                [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]], dtype=np.float32,
            ),
            "REF_SIGNAL": pd.DataFrame(
                {"force": [0.0, 0.5, 1.0]},
                index=pd.RangeIndex(3, name="sample"), dtype=np.float32,
            ),
            "ACCURACY": pd.DataFrame([0.75], dtype=np.float32),
            "IPTS": pd.DataFrame([1.0, 0.0, 1.0], dtype=np.float32),
            "BINARY_MUS_FIRING": pd.DataFrame([1, 0, 1], dtype=np.int16),
            "MUPULSES": [np.array([0, 2], dtype=np.int32)],
            "REFERENCE_MUPULSES": [np.array([1, 2], dtype=np.int32)],
            "ROA_WITH_REFERENCE_MUPULSES": pd.DataFrame(
                [75.0], dtype=np.float32,
            ),
            "FSAMP": np.float32(1000.0),
            "IED": np.float32(8.0),
            "EMG_LENGTH": np.int32(3),
            "NUMBER_OF_MUS": np.int32(1),
            "GOOD_CHANNELS": {0: True, 1: False},
            "EXTRAS": pd.DataFrame({"accepted": [True]}),
        }
        original = copy.deepcopy(emgfile)

        result = standardise_emgfile_dtypes(emgfile)

        validate_standard_emgfile_content(self, result)
        self.assertEqual(result.keys(), original.keys())
        for key in (
            "RAW_SIGNAL", "REF_SIGNAL", "ACCURACY", "IPTS",
            "BINARY_MUS_FIRING", "ROA_WITH_REFERENCE_MUPULSES", "EXTRAS",
        ):
            with self.subTest(field=key):
                pd.testing.assert_frame_equal(
                    result[key], original[key], check_dtype=(key == "EXTRAS"),
                )
                pd.testing.assert_frame_equal(emgfile[key], original[key])

        for key in ("MUPULSES", "REFERENCE_MUPULSES"):
            with self.subTest(field=key):
                np.testing.assert_array_equal(result[key][0], original[key][0])
                self.assertEqual(emgfile[key][0].dtype, np.int32)
                np.testing.assert_array_equal(
                    emgfile[key][0], original[key][0],
                )

        for key in (
            "SOURCE", "FILENAME", "FSAMP", "IED", "EMG_LENGTH", "NUMBER_OF_MUS",
        ):
            with self.subTest(field=key):
                self.assertEqual(result[key], original[key])
                self.assertIs(type(emgfile[key]), type(original[key]))
        self.assertIs(type(result["SOURCE"]), str)
        self.assertIs(type(result["FILENAME"]), str)
        self.assertEqual(result["GOOD_CHANNELS"], {"0": 1, "1": 0})
        for value in result["GOOD_CHANNELS"].values():
            self.assertIs(type(value), int)
        self.assertEqual(emgfile["GOOD_CHANNELS"], original["GOOD_CHANNELS"])

        result["EXTRAS"].iat[0, 0] = False
        pd.testing.assert_frame_equal(emgfile["EXTRAS"], original["EXTRAS"])

    def test_standardise_emgfile_dtypes_flattens_pulses(self):
        """Test the warning and conversion of legacy column arrays."""

        for key in ("MUPULSES", "REFERENCE_MUPULSES"):
            with self.subTest(field=key):
                pulses = np.array([[1], [3]], dtype=np.int32)
                with self.assertWarnsRegex(UserWarning, rf"{key}.*not 1D"):
                    result = standardise_emgfile_dtypes({key: [pulses]})
                self.assertEqual(set(result), {key})
                self.assertEqual(result[key][0].dtype, np.int64)
                np.testing.assert_array_equal(result[key][0], [1, 3])
                self.assertEqual(pulses.shape, (2, 1))

    def test_standardise_emgfile_dtypes_rejects_invalid_fields(self):
        """Test the required containers for signal frames and pulse arrays."""

        with self.assertRaisesRegex(
            TypeError, "REF_SIGNAL must be a pandas DataFrame",
        ):
            standardise_emgfile_dtypes({"REF_SIGNAL": [1.0, 2.0]})
        with self.assertRaisesRegex(
            TypeError, "MUPULSES must be a list of numpy arrays",
        ):
            standardise_emgfile_dtypes({"MUPULSES": [[1, 3]]})

    def test_showselect(self):
        """Test the plotted data and the returned sample positions."""

        emgfile = {
            "REF_SIGNAL": pd.DataFrame({
                "other": [10.0, 11.0, 12.0, 13.0],
                "force": [1.0, 2.0, 3.0, 4.0],
            }),
            "RAW_SIGNAL": pd.DataFrame({
                0: [1.0, 3.0, 5.0, 7.0],
                1: [3.0, 5.0, 7.0, 9.0],
            }),
        }
        for how, expected_data, label in (
            ("ref_signal", [1.0, 2.0, 3.0, 4.0], "Reference signal"),
            ("mean_emg", [2.0, 4.0, 6.0, 8.0], "Mean EMG signal"),
        ):
            with self.subTest(how=how), patch(
                "openhdemg.library.tools.run_point_selector",
                return_value=[(2.8, 10.0), (0.2, 20.0)],
            ) as mocked_selector:
                points = showselect(emgfile, how=how, refsig_channel="force")
                self.assertEqual(points, [0, 3])
                mocked_selector.assert_called_once()
                kwargs = mocked_selector.call_args.kwargs
                np.testing.assert_array_equal(kwargs["data"], expected_data)
                self.assertEqual(kwargs["y_label"], label)

    def test_select_bad_channels(self):
        """Test the results of accepting and cancelling channel selection."""

        emgfile = {"RAW_SIGNAL": pd.DataFrame([[0.0, 1.0]])}
        good_channels = {"0": True, "1": False}
        with patch(
            "openhdemg.library.tools.run_manual_emgchannels_selection_dialog",
            return_value={**emgfile, "GOOD_CHANNELS": good_channels},
        ) as mocked_dialog:
            result = select_bad_channels(emgfile, manual_offset=10)
            self.assertEqual(result["GOOD_CHANNELS"], good_channels)
            mocked_dialog.assert_called_once_with(
                emgfile=emgfile, manual_offset=10, parent=None,
            )

            mocked_dialog.return_value = None
            self.assertIsNone(select_bad_channels(emgfile))

    def test_create_binary_firings(self):
        """
        Test the create_binary_firings function.
        """

        res = create_binary_firings(
            emg_length=self.emgfile["EMG_LENGTH"],
            number_of_mus=self.emgfile["NUMBER_OF_MUS"],
            mupulses=self.emgfile["MUPULSES"],
        )

        self.assertIsInstance(res, pd.DataFrame)
        self.assertTrue(res.shape[0] == self.emgfile["EMG_LENGTH"])
        self.assertTrue(res.shape[1] == self.emgfile["NUMBER_OF_MUS"])
        for column in res.columns:
            self.assertTrue(pd.api.types.is_integer_dtype(res[column]))
        self.assertTrue(res.min().min() == 0)
        self.assertTrue(res.max().max() == 1)
        np.testing.assert_array_equal(
            res.to_numpy(),
            self.emgfile["BINARY_MUS_FIRING"].to_numpy(),
        )

        # Test an empty MU
        res = create_binary_firings(
            emg_length=10,
            number_of_mus=1,
            mupulses=[np.array([], dtype=np.int64)],
        )
        self.assertEqual(res.shape, (10, 1))
        self.assertEqual(res.to_numpy().sum(), 0)

        # Test no MUs
        res = create_binary_firings(
            emg_length=10,
            number_of_mus=0,
            mupulses=[],
        )
        self.assertEqual(res.shape, (10, 0))

        with self.assertRaises(ValueError):
            create_binary_firings(
                emg_length=10,
                number_of_mus=1,
                mupulses=np.array([], dtype=np.int64),
            )

    def test_mupulses_from_binary(self):
        """
        Test the mupulses_from_binary function.
        """

        res = mupulses_from_binary(
            binarymusfiring=self.emgfile["BINARY_MUS_FIRING"]
        )

        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertTrue(len(res) == self.emgfile["NUMBER_OF_MUS"])
        for pulses in res:
            self.assertEqual(pulses.dtype, int)
            self.assertTrue(
                np.min(pulses) >= 0 and
                np.max(pulses) < self.emgfile["EMG_LENGTH"]
            )
        for original, recovered in zip(self.emgfile["MUPULSES"], res):
            np.testing.assert_array_equal(original, recovered)

        # Test an empty MU
        res = mupulses_from_binary(
            pd.DataFrame(np.zeros((10, 1), dtype=np.uint8))
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].dtype, np.int64)
        self.assertEqual(res[0].size, 0)

        # Test no MUs
        res = mupulses_from_binary(
            pd.DataFrame(index=range(10), dtype=np.uint8)
        )
        self.assertEqual(res, [])

    def test_resize_emgfile(self):
        """
        Test the resize_emgfile function.
        """

        # Test the emgfile
        # Test multiple resizing and resizing outside the real area
        areas = [
            [10000, 30000],
            [-10, self.emgfile["EMG_LENGTH"] + 10],
            [5000, 10000]
        ]

        for area in areas:
            for accuracy in ["recalculate", "maintain"]:
                rs_emgfile, start_, end_ = resize_emgfile(
                    self.emgfile,
                    area=area,
                    how="ref_signal",
                    accuracy=accuracy,
                )

                validate_standard_emgfile_content(self, rs_emgfile)
                self.assertEqual(start_, max(area[0], 0))
                self.assertEqual(
                    end_, min(area[1], self.emgfile["EMG_LENGTH"])
                )
                self.assertEqual(rs_emgfile["EMG_LENGTH"], end_ - start_)
                self.assertEqual(rs_emgfile["RAW_SIGNAL"].index[0], 0)
                if accuracy == "maintain":
                    pd.testing.assert_frame_equal(
                        rs_emgfile["ACCURACY"],
                        self.emgfile["ACCURACY"],
                    )

        # Test compute_on_peaks_only
        rs_emgfile, _, _ = resize_emgfile(
            self.emgfile,
            area=areas[0],
            compute_on_peaks_only=False,
        )
        validate_standard_emgfile_content(self, rs_emgfile)
        peaks_emgfile, _, _ = resize_emgfile(
            self.emgfile,
            area=areas[0],
            compute_on_peaks_only=True,
        )
        self.assertFalse(
            rs_emgfile["ACCURACY"].equals(peaks_emgfile["ACCURACY"])
        )

        # Test custom_dataframes
        custom_emgfile = copy.deepcopy(self.emgfile)
        custom_emgfile["CUSTOM"] = custom_emgfile["RAW_SIGNAL"][[0]].copy()
        rs_emgfile, _, _ = resize_emgfile(
            custom_emgfile,
            area=areas[0],
            accuracy="maintain",
            custom_dataframes=["CUSTOM"],
        )
        self.assertEqual(rs_emgfile["CUSTOM"].shape[0], 20000)
        self.assertEqual(rs_emgfile["CUSTOM"].index[0], 0)

        rs_emgfile, _, _ = resize_emgfile(
            custom_emgfile,
            area=areas[0],
            accuracy="maintain",
            custom_dataframes=("CUSTOM",),
        )
        self.assertEqual(rs_emgfile["CUSTOM"].shape[0], 20000)

        # Test REFERENCE_MUPULSES and ROA_WITH_REFERENCE_MUPULSES
        module = get_module_fixture()
        reference_emgfile = load_openhdemg_module(
            module.parent, module.name,
        )
        recalculated, _, _ = resize_emgfile(
            reference_emgfile,
            area=areas[0],
            accuracy="maintain",
            roa_with_reference_mupulses="recalculate",
        )
        maintained, _, _ = resize_emgfile(
            reference_emgfile,
            area=areas[0],
            accuracy="maintain",
            roa_with_reference_mupulses="maintain",
        )
        # MU 0 fires at sample 10098 and its pulse trains match in this crop.
        self.assertEqual(recalculated["MUPULSES"][0][0], 98)
        np.testing.assert_array_equal(
            recalculated["REFERENCE_MUPULSES"][0],
            recalculated["MUPULSES"][0],
        )
        self.assertEqual(
            recalculated["ROA_WITH_REFERENCE_MUPULSES"].iat[0, 0], 100,
        )
        pd.testing.assert_frame_equal(
            maintained["ROA_WITH_REFERENCE_MUPULSES"],
            reference_emgfile["ROA_WITH_REFERENCE_MUPULSES"],
        )

        # Test interactive selection parameters without opening the GUI
        interactive_emgfile = copy.deepcopy(self.emgfile)
        interactive_emgfile["REF_SIGNAL"]["target"] = (
            interactive_emgfile["REF_SIGNAL"][0]
        )
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=areas[0],
        ) as mocked_showselect:
            rs_emgfile, start_, end_ = resize_emgfile(
                interactive_emgfile,
                area=None,
                how="mean_emg",
                refsig_channel="target",
                accuracy="maintain",
            )
        self.assertEqual((start_, end_), tuple(areas[0]))
        self.assertEqual(rs_emgfile["EMG_LENGTH"], 20000)
        self.assertEqual(
            mocked_showselect.call_args.kwargs["how"],
            "mean_emg",
        )
        self.assertEqual(
            mocked_showselect.call_args.kwargs["refsig_channel"],
            "target",
        )

        # Test invalid options
        with self.assertRaises(ValueError):
            resize_emgfile(self.emgfile, area=[100, 100])
        with self.assertRaises(ValueError):
            resize_emgfile(self.emgfile, area=[200, 100])
        with self.assertRaises(ValueError):
            resize_emgfile(
                self.emgfile,
                area=[0, 100],
                accuracy="invalid",
            )
        with self.assertRaisesRegex(ValueError, "invalid"):
            resize_emgfile(
                self.emgfile,
                area=[0, 100],
                accuracy="maintain",
                roa_with_reference_mupulses="invalid",
            )

        # Test the refsig_emgfile
        refsig_emgfile = standardise_emgfile_dtypes(
            refsig_from_otb(
                filepath=getd("library", "otb", "OTB_R.mat"),
            )
        )

        rs_emgfile, start_, end_ = resize_emgfile(
                    refsig_emgfile,
                    area=areas[0],
                )

        validate_standard_emgfile_content(self, rs_emgfile)

    def test_roa_tolerance(self):
        """Test ROA tolerance when resizing and splitting an emgfile."""

        emgfile = {
            "RAW_SIGNAL": pd.DataFrame(np.zeros(30, dtype=np.float64)),
            "NUMBER_OF_MUS": np.int64(1),
            "MUPULSES": [np.array([10, 20], dtype=np.int64)],
            "REFERENCE_MUPULSES": [np.array([11, 20], dtype=np.int64)],
            "ROA_WITH_REFERENCE_MUPULSES": pd.DataFrame([0.0]),
        }
        area = [5, 25]
        iterator = EMGFileSectionsIterator(emgfile)
        iterator.set_split_points_by_list(area)

        # One pair matches exactly, and the other is one sample apart.
        for tolerance, expected in ((0, 50.0), (1, 100.0)):
            with self.subTest(tolerance=tolerance):
                cropped, _, _ = resize_emgfile(
                    emgfile, area=area, roa_tolerance=tolerance,
                )
                iterator.split(roa_tolerance=tolerance)
                self.assertEqual(
                    cropped["ROA_WITH_REFERENCE_MUPULSES"].iat[0, 0],
                    expected,
                )
                self.assertEqual(
                    iterator.sections[0]["ROA_WITH_REFERENCE_MUPULSES"].iat[0, 0],
                    expected,
                )

    def test_EMGFileSectionsIterator(self):
        """
        Test the EMGFileSectionsIterator class.
        """

        iterator = EMGFileSectionsIterator(self.emgfile)

        self.assertEqual(
            iterator.file_length, self.emgfile["RAW_SIGNAL"].shape[0],
        )

        # Test fallback methods for determining the file length
        fallback_file = copy.deepcopy(self.emgfile)
        fallback_file.pop("EMG_LENGTH")
        fallback_iterator = EMGFileSectionsIterator(fallback_file)
        self.assertEqual(
            fallback_iterator.file_length,
            self.emgfile["RAW_SIGNAL"].shape[0],
        )

        fallback_file.pop("RAW_SIGNAL")
        fallback_iterator = EMGFileSectionsIterator(fallback_file)
        self.assertEqual(
            fallback_iterator.file_length,
            self.emgfile["REF_SIGNAL"].shape[0],
        )

        fallback_file.pop("REF_SIGNAL")
        with self.assertRaises(ValueError):
            EMGFileSectionsIterator(fallback_file)

        # Test set_split_points_by_showselect without opening the GUI
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=[-10, iterator.file_length + 10],
        ) as mocked_showselect:
            iterator.set_split_points_by_showselect(
                how="mean_emg",
                refsig_channel=0,
                title="Test",
                titlesize=8,
                nclic=2,
            )
        self.assertListEqual(
            iterator.split_points,
            [0, iterator.file_length],
        )
        self.assertEqual(
            mocked_showselect.call_args.kwargs["how"],
            "mean_emg",
        )
        iterator.split_points = []

        # Test set_split_points_by_equal_spacing
        iterator.set_split_points_by_equal_spacing(n_sections=4)
        self.assertListEqual(
            iterator.split_points,
            list(np.linspace(
                0, iterator.file_length, 5, dtype=int
            )),
        )
        iterator.split_points = []

        # Test set_split_points_by_time
        iterator.set_split_points_by_time(time_window=7, drop_shorter=True)
        self.assertEqual(len(iterator.split_points), 5)
        self.assertEqual(iterator.split_points[0], 0)
        self.assertLess(iterator.split_points[-1], iterator.file_length)
        iterator.split_points = []

        iterator.set_split_points_by_time(time_window=7, drop_shorter=False)
        self.assertEqual(len(iterator.split_points), 6)
        self.assertEqual(iterator.split_points[-1], iterator.file_length)
        iterator.split_points = []

        # Test set_split_points_by_samples
        iterator.set_split_points_by_samples(
            samples_window=15000, drop_shorter=True,
        )
        self.assertEqual(len(iterator.split_points), 5)
        self.assertLess(iterator.split_points[-1], iterator.file_length)
        iterator.split_points = []

        iterator.set_split_points_by_samples(
            samples_window=15000, drop_shorter=False,
        )
        self.assertEqual(len(iterator.split_points), 6)
        self.assertEqual(iterator.split_points[-1], iterator.file_length)
        iterator.split_points = []

        # Test set_split_points_by_list
        iterator.set_split_points_by_list(split_points=[0, 25000, 60000])
        self.assertListEqual(iterator.split_points, [0, 25000, 60000])
        iterator.split_points = []

        # Test split
        iterator.set_split_points_by_equal_spacing(n_sections=3)
        iterator.split(compute_on_peaks_only=False)
        for file in iterator.sections:
            validate_standard_emgfile_content(self, file)
        iterator.sections = []
        iterator.split_points = []

        # Test all split parameters
        split_emgfile = copy.deepcopy(self.emgfile)
        split_emgfile["CUSTOM"] = split_emgfile["RAW_SIGNAL"][[0]].copy()
        split_emgfile["REFERENCE_MUPULSES"] = [
            pulses.copy() for pulses in split_emgfile["MUPULSES"]
        ]
        split_emgfile["ROA_WITH_REFERENCE_MUPULSES"] = pd.DataFrame(
            np.zeros((split_emgfile["NUMBER_OF_MUS"], 1), dtype=np.float64)
        )
        split_iterator = EMGFileSectionsIterator(split_emgfile)
        split_iterator.set_split_points_by_equal_spacing(n_sections=2)
        split_iterator.split(
            accuracy="maintain",
            compute_on_peaks_only=False,
            roa_with_reference_mupulses="maintain",
            custom_dataframes=["CUSTOM"],
        )
        self.assertEqual(len(split_iterator.sections), 2)
        for file in split_iterator.sections:
            validate_standard_emgfile_content(self, file)
            self.assertEqual(
                file["CUSTOM"].shape[0],
                file["EMG_LENGTH"],
            )
            pd.testing.assert_frame_equal(
                file["ACCURACY"],
                split_emgfile["ACCURACY"],
            )
            pd.testing.assert_frame_equal(
                file["ROA_WITH_REFERENCE_MUPULSES"],
                split_emgfile["ROA_WITH_REFERENCE_MUPULSES"],
            )

        # Test iterate raises
        iterator.set_split_points_by_equal_spacing(n_sections=3)
        iterator.split()
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs="not a list", args_list=[[]], kwargs_list=[{}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr], args_list=["not a list"], kwargs_list=[{}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr], args_list=[[]], kwargs_list=["not a dict"],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr, compute_dr],
                args_list=[[], [], []], kwargs_list=[{}, {}, {}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr, compute_dr, compute_dr],
                args_list=[[]], kwargs_list=[{}, {}, {}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr, compute_dr, compute_dr],
                args_list=[[], [], []], kwargs_list=[{}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr], args_list=[], kwargs_list=[{}],
            )
        with self.assertRaises(ValueError):
            iterator.iterate(
                funcs=[compute_dr], args_list=[[]], kwargs_list=[],
            )
        iterator.sections = []
        iterator.split_points = []
        iterator.results = []

        # Test iterate successful
        iterator.set_split_points_by_equal_spacing(n_sections=3)
        iterator.split()
        iterator.iterate(
            funcs=[compute_dr],
            event_="rec",
        )
        self.assertGreater(len(iterator.results), 0)
        for df in iterator.results:
            self.assertIsInstance(df, pd.DataFrame)
        iterator.sections = []
        iterator.split_points = []
        iterator.results = []

        # Test positional arguments
        def count_firings(file, multiplier=1):
            counts = [
                len(pulses) * multiplier for pulses in file["MUPULSES"]
            ]
            return pd.DataFrame(counts)

        iterator.set_split_points_by_equal_spacing(n_sections=3)
        iterator.split()
        iterator.iterate(
            funcs=[count_firings],
            args_list=[[2]],
        )
        self.assertEqual(len(iterator.results), 3)
        self.assertTrue((iterator.results[0] % 2 == 0).all().all())
        iterator.sections = []
        iterator.split_points = []
        iterator.results = []

        # Test merge_dataframes
        iterator.set_split_points_by_equal_spacing(n_sections=3)
        iterator.split()
        iterator.iterate(
            funcs=[compute_dr, compute_dr, compute_dr],
            args_list=[[], [], []],
            kwargs_list=[
                {"event_": "rec"}, {"event_": "rec"}, {"event_": "rec"}
            ],
        )
        results = iterator.results  # Store to test merge_dataframes
        original_results = [df.copy(deep=True) for df in results]
        filled_results = [df.fillna(0) for df in results]
        merged_stack = pd.concat(
            filled_results,
            axis=0,
            keys=range(len(filled_results)),
        )
        expected_results = {
            "average": merged_stack.groupby(level=1).mean(),
            "median": merged_stack.groupby(level=1).median(),
            "sum": merged_stack.groupby(level=1).sum(),
            "min": merged_stack.groupby(level=1).min(),
            "max": merged_stack.groupby(level=1).max(),
            "std": merged_stack.groupby(level=1).std(),
        }
        expected_results["cv"] = (
            expected_results["std"] / expected_results["average"]
        )

        for method in expected_results:
            merged_df = iterator.merge_dataframes(method=method, fillna=0)
            pd.testing.assert_frame_equal(
                merged_df,
                expected_results[method],
            )

        for original, current in zip(original_results, iterator.results):
            pd.testing.assert_frame_equal(original, current)

        merged_long = iterator.merge_dataframes(method="long", fillna=0)
        total_rows = 0
        total_idxs = []
        for df in results:
            total_rows += df.shape[0]
            total_idxs += list(df.index)
        self.assertEqual(merged_long.columns[0], "source_idx")
        self.assertEqual(merged_long.columns[1], "original_idx")
        self.assertEqual(merged_long.shape[0], total_rows)
        self.assertListEqual(merged_long["original_idx"].tolist(), total_idxs)

        def custom_agg(dfs):
            if len(dfs) != 3:
                raise ValueError("Expected exactly 3 DataFrames")
            return dfs[0] + dfs[1] + dfs[2]
        merged_custom = iterator.merge_dataframes(
            method="custom", fillna=0, agg_func=custom_agg,
        )
        pd.testing.assert_frame_equal(
            merged_custom,
            filled_results[0] + filled_results[1] + filled_results[2],
        )

        # Test a named index in long format
        iterator.results = [
            pd.DataFrame(
                {"value": [1]},
                index=pd.Index([10], name="mu"),
            ),
            pd.DataFrame(
                {"value": [2]},
                index=pd.Index([20], name="mu"),
            ),
        ]
        merged_long = iterator.merge_dataframes(method="long")
        self.assertListEqual(
            merged_long["original_idx"].tolist(),
            [10, 20],
        )

        # Test merge_dataframes raises
        iterator.results = []
        with self.assertRaises(ValueError):
            iterator.merge_dataframes()

        iterator.results = [1]
        with self.assertRaises(ValueError):
            iterator.merge_dataframes()

        iterator.results = [pd.DataFrame({"value": [1]})]
        with self.assertRaises(ValueError):
            iterator.merge_dataframes(method="custom")
        with self.assertRaises(ValueError):
            iterator.merge_dataframes(method="invalid")

    def test_merge_dataframes_average_by_mu_index(self):
        """Test that averaging aligns MUs and fills only existing NaNs."""

        sections = [
            pd.DataFrame(
                {"value": [10.0, 20.0, np.nan]},
                index=pd.Index([0, 1, 2], name="mu"),
            ),
            pd.DataFrame(
                {"value": [40.0, 60.0, 80.0]},
                index=pd.Index([1, 2, 3], name="mu"),
            ),
        ]
        iterator = EMGFileSectionsIterator(self.emgfile)
        iterator.results = [frame.copy() for frame in sections]

        mu_index = pd.Index([0, 1, 2, 3], name="mu")
        expected = pd.DataFrame(
            {"value": [10.0, 30.0, 60.0, 80.0]}, index=mu_index,
        )
        expected_filled = pd.DataFrame(
            {"value": [10.0, 30.0, 30.0, 80.0]}, index=mu_index,
        )
        pd.testing.assert_frame_equal(
            iterator.merge_dataframes(method="average"),
            expected, check_exact=True,
        )
        pd.testing.assert_frame_equal(
            iterator.merge_dataframes(method="average", fillna=0),
            expected_filled, check_exact=True,
        )

        self.assertEqual(len(iterator.results), len(sections))
        for actual, original in zip(iterator.results, sections):
            pd.testing.assert_frame_equal(actual, original, check_exact=True)

    def test_compute_idr(self):
        """
        Test the compute_idr function.
        """

        res = compute_idr(self.emgfile)

        self.assertIsInstance(res, dict)
        self.assertTrue(len(res.keys()) == self.emgfile["NUMBER_OF_MUS"])
        self.assertTrue(np.isnan(res[0]["idr"].iloc[0]))
        self.assertAlmostEqual(res[0]["idr"].iloc[1], 1.227082, places=6)
        # Use np.isclose for floating point comparison, ignoring NaN values
        comparison = np.isclose(
            self.emgfile["FSAMP"] / res[0]["diff_mupulses"],
            res[0]["idr"],
            equal_nan=True,
        )
        # Assert that all values are close (or NaN in both)
        self.assertTrue(comparison.all())

        # Test a single MU
        single_mu = copy.deepcopy(self.emgfile)
        single_mu["NUMBER_OF_MUS"] = np.int64(1)
        single_mu["MUPULSES"] = [single_mu["MUPULSES"][0]]
        res = compute_idr(single_mu)
        self.assertEqual(len(res), 1)
        np.testing.assert_array_equal(
            res[0]["mupulses"].to_numpy(),
            single_mu["MUPULSES"][0],
        )

        # Test an empty MU
        single_mu["MUPULSES"] = [np.array([], dtype=np.int64)]
        res = compute_idr(single_mu)
        self.assertTrue(res[0].empty)

        # Test no MUs
        single_mu["NUMBER_OF_MUS"] = np.int64(0)
        single_mu["MUPULSES"] = []
        self.assertEqual(compute_idr(single_mu), {})

    def test_delete_mus(self):
        """
        Test the delete_mus function.
        """

        # Progressively delete all the MUs except 1
        res = copy.deepcopy(self.emgfile)
        for _ in range(self.emgfile["NUMBER_OF_MUS"]):
            res = delete_mus(
                res,
                munumber=0,
                if_single_mu="ignore",
            )
            if res["NUMBER_OF_MUS"] > 1:
                validate_standard_emgfile_content(self, res)
            elif res["NUMBER_OF_MUS"] == 1:
                self.assertTrue(res["NUMBER_OF_MUS"] == 1)
                self.assertTrue(res["ACCURACY"].shape == (1, 1))
                self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
                self.assertTrue(len(res["MUPULSES"]) == 1)
                self.assertTrue(
                    res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
                )
            else:
                raise ValueError(
                    "With if_single_mu='ignore', all MUs have been removed."
                )

        # Progressively delete all the MUs
        res = copy.deepcopy(self.emgfile)
        for _ in range(self.emgfile["NUMBER_OF_MUS"]):
            res = delete_mus(
                res,
                munumber=0,
                if_single_mu="remove",
            )
            if res["NUMBER_OF_MUS"] > 1:
                validate_standard_emgfile_content(self, res)
            elif res["NUMBER_OF_MUS"] == 1:
                self.assertTrue(res["NUMBER_OF_MUS"] == 1)
                self.assertTrue(res["ACCURACY"].shape == (1, 1))
                self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
                self.assertTrue(len(res["MUPULSES"]) == 1)
                self.assertTrue(
                    res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
                )
            else:
                self.assertTrue(res["NUMBER_OF_MUS"] == 0)
                self.assertTrue(res["ACCURACY"].empty)
                self.assertTrue(res["IPTS"].empty)
                self.assertTrue(len(res["MUPULSES"]) == 0)
                self.assertTrue(res["BINARY_MUS_FIRING"].empty)
                validate_standard_emgfile_content(self, res)

        # Test passing a list of MUs to munumber
        res = copy.deepcopy(self.emgfile)
        res = delete_mus(
            res,
            munumber=[*range(res["NUMBER_OF_MUS"])],
        )

        self.assertTrue(res["NUMBER_OF_MUS"] == 0)
        self.assertTrue(res["ACCURACY"].empty)
        self.assertTrue(res["IPTS"].empty)
        self.assertTrue(len(res["MUPULSES"]) == 0)
        self.assertTrue(res["BINARY_MUS_FIRING"].empty)
        validate_standard_emgfile_content(self, res)

        res = copy.deepcopy(self.emgfile)
        res = delete_mus(
            res,
            munumber=[*range(res["NUMBER_OF_MUS"] - 1)],
            if_single_mu="ignore",
        )

        self.assertTrue(res["NUMBER_OF_MUS"] == 1)
        self.assertTrue(res["ACCURACY"].shape == (1, 1))
        self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
        self.assertTrue(len(res["MUPULSES"]) == 1)
        self.assertTrue(
            res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
        )

        # Test optional MU-related fields
        optional_emgfile = copy.deepcopy(self.emgfile)
        optional_emgfile["REFERENCE_MUPULSES"] = [
            pulses.copy() for pulses in optional_emgfile["MUPULSES"]
        ]
        optional_emgfile["ROA_WITH_REFERENCE_MUPULSES"] = pd.DataFrame(
            np.arange(
                optional_emgfile["NUMBER_OF_MUS"],
                dtype=np.float64,
            )
        )
        optional_emgfile["MU_LABELS"] = {
            str(mu): f"MU {mu}"
            for mu in range(optional_emgfile["NUMBER_OF_MUS"])
        }
        original = copy.deepcopy(optional_emgfile)
        res = delete_mus(optional_emgfile, munumber=np.int64(1))
        self.assertEqual(res["NUMBER_OF_MUS"], 4)
        self.assertEqual(res["MU_LABELS"]["1"], "MU 2")
        np.testing.assert_array_equal(
            res["REFERENCE_MUPULSES"][1],
            original["REFERENCE_MUPULSES"][2],
        )
        self.assertEqual(
            res["ROA_WITH_REFERENCE_MUPULSES"].iloc[1, 0],
            original["ROA_WITH_REFERENCE_MUPULSES"].iloc[2, 0],
        )
        np.testing.assert_array_equal(
            optional_emgfile["MUPULSES"][1],
            original["MUPULSES"][1],
        )

        # Test invalid MU identifiers
        with self.assertRaises(TypeError):
            delete_mus(self.emgfile, munumber=[1.9])
        with self.assertRaises(ValueError):
            delete_mus(self.emgfile, munumber=-1)
        with self.assertRaises(ValueError):
            delete_mus(
                self.emgfile,
                munumber=self.emgfile["NUMBER_OF_MUS"],
            )

        # Test delete_delsys_muaps
        delsys_emgfile = standardise_emgfile_dtypes(
            emg_from_delsys(
                rawemg_filepath=getd(
                    "library",
                    ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                    "Raw_EMG_signal_withFakeRef.mat"
                ),
                mus_directory=getd(
                    "library",
                    ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                    "Bicep_Brachii_Motor_Units (Sensor 1)"
                ),
            )
        )

        res = delete_mus(
            delsys_emgfile,
            munumber=0,
            delete_delsys_muaps=False,
        )
        self.assertEqual(
            len(res["EXTRAS"].columns),
            len(delsys_emgfile["EXTRAS"].columns),
        )

        res = delete_mus(
            delsys_emgfile,
            munumber=[*range(delsys_emgfile["NUMBER_OF_MUS"])],
            if_single_mu="ignore",
            delete_delsys_muaps=True,
        )

        self.assertTrue(len(res["EXTRAS"].columns) == res["NUMBER_OF_MUS"] * 4)

    def test_delete_empty_mus(self):
        """
        Test the delete_empty_mus function.
        """

        emgfile = copy.deepcopy(self.emgfile)

        emgfile["MUPULSES"][0] = np.empty(0)

        res = delete_empty_mus(emgfile)

        self.assertTrue(res["NUMBER_OF_MUS"] == 4)
        validate_standard_emgfile_content(self, res)

        # Test no empty MUs
        res = delete_empty_mus(self.emgfile)
        self.assertEqual(
            res["NUMBER_OF_MUS"],
            self.emgfile["NUMBER_OF_MUS"],
        )
        validate_standard_emgfile_content(self, res)

        # Test all empty MUs
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["MUPULSES"] = [
            np.array([], dtype=np.int64)
            for _ in emgfile["MUPULSES"]
        ]
        res = delete_empty_mus(emgfile)
        self.assertEqual(res["NUMBER_OF_MUS"], 0)
        validate_standard_emgfile_content(self, res)

        # Test a file that already has no MUs
        res = delete_empty_mus(res)
        self.assertEqual(res["NUMBER_OF_MUS"], 0)
        validate_standard_emgfile_content(self, res)

    def test_find_and_remove_duplicates_within(self):
        """Test duplicate selection and alignment of the surviving MUs."""

        # MUs 0 and 1 fire together. MU 0 has higher accuracy, while MU 1
        # has perfectly regular intervals. MU 2 fires later on its own.
        pulses = [
            np.array([100, 200, 300, 402, 501], dtype=np.int64),
            np.array([100, 200, 300, 400, 500], dtype=np.int64),
            np.array([650, 780, 920, 1080, 1210], dtype=np.int64),
        ]
        emg_length = 1250
        emgfile = {
            "FSAMP": np.float64(1000),
            "EMG_LENGTH": np.int64(emg_length),
            "NUMBER_OF_MUS": np.int64(3),
            "MUPULSES": pulses,
            "BINARY_MUS_FIRING": create_binary_firings(
                emg_length, 3, pulses,
            ),
            "ACCURACY": pd.DataFrame([0.95, 0.55, 0.8]),
            "IPTS": pd.DataFrame(np.tile([1.0, 2.0, 3.0], (emg_length, 1))),
            "REFERENCE_MUPULSES": [train + 1 for train in pulses],
            "ROA_WITH_REFERENCE_MUPULSES": pd.DataFrame([90.0, 80.0, 70.0]),
            "MU_LABELS": {"0": "first", "1": "second", "2": "third"},
        }

        for which, removed_mu, survivors in (
            ("accuracy", 1, [0, 2]),
            ("covisi", 0, [1, 2]),
        ):
            with self.subTest(which=which):
                duplicates, info = find_duplicates_within(
                    emgfile, which=which,
                )
                self.assertEqual(duplicates, [removed_mu])
                self.assertEqual([item["pair"] for item in info], [(0, 1)])

                result = remove_duplicates_within(emgfile, which=which)
                self.assertEqual(result["NUMBER_OF_MUS"], 2)
                self.assertEqual(result["MU_LABELS"], {
                    "0": emgfile["MU_LABELS"][str(survivors[0])],
                    "1": "third",
                })
                for key in ("MUPULSES", "REFERENCE_MUPULSES"):
                    self.assertEqual(len(result[key]), 2)
                    for new_mu, original_mu in enumerate(survivors):
                        np.testing.assert_array_equal(
                            result[key][new_mu], emgfile[key][original_mu],
                        )
                for key in ("BINARY_MUS_FIRING", "IPTS"):
                    expected = emgfile[key][survivors].set_axis(
                        range(2), axis=1,
                    )
                    pd.testing.assert_frame_equal(result[key], expected)
                for key in ("ACCURACY", "ROA_WITH_REFERENCE_MUPULSES"):
                    expected = emgfile[key].iloc[survivors].reset_index(
                        drop=True,
                    )
                    pd.testing.assert_frame_equal(result[key], expected)

    def test_sort_mus(self):
        """
        Test the sort_mus function.
        """

        res = sort_mus(self.emgfile)

        for mu in range(1, res["NUMBER_OF_MUS"]):
            self.assertTrue(
                res["MUPULSES"][mu][0] > res["MUPULSES"][mu-1][0]
            )
        validate_standard_emgfile_content(self, res)

        # Test that all MU-related fields remain aligned
        sorting_order = sorted(
            range(self.emgfile["NUMBER_OF_MUS"]),
            key=lambda mu: self.emgfile["MUPULSES"][mu][0],
        )
        for new_mu, original_mu in enumerate(sorting_order):
            np.testing.assert_array_equal(
                res["MUPULSES"][new_mu],
                self.emgfile["MUPULSES"][original_mu],
            )
            np.testing.assert_array_equal(
                res["IPTS"][new_mu].to_numpy(),
                self.emgfile["IPTS"][original_mu].to_numpy(),
            )
            np.testing.assert_array_equal(
                res["BINARY_MUS_FIRING"][new_mu].to_numpy(),
                self.emgfile["BINARY_MUS_FIRING"][
                    original_mu
                ].to_numpy(),
            )
            self.assertEqual(
                res["ACCURACY"].iloc[new_mu, 0],
                self.emgfile["ACCURACY"].iloc[original_mu, 0],
            )

        # Test optional MU-related fields
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REFERENCE_MUPULSES"] = [
            pulses.copy() for pulses in emgfile["MUPULSES"]
        ]
        emgfile["ROA_WITH_REFERENCE_MUPULSES"] = pd.DataFrame(
            np.arange(emgfile["NUMBER_OF_MUS"], dtype=np.float64)
        )
        emgfile["MU_LABELS"] = {
            str(mu): f"MU {mu}"
            for mu in range(emgfile["NUMBER_OF_MUS"])
        }
        res = sort_mus(emgfile)
        for new_mu, original_mu in enumerate(sorting_order):
            np.testing.assert_array_equal(
                res["REFERENCE_MUPULSES"][new_mu],
                emgfile["REFERENCE_MUPULSES"][original_mu],
            )
            self.assertEqual(
                res["ROA_WITH_REFERENCE_MUPULSES"].iloc[new_mu, 0],
                emgfile["ROA_WITH_REFERENCE_MUPULSES"].iloc[original_mu, 0],
            )
            self.assertEqual(
                res["MU_LABELS"][str(new_mu)],
                emgfile["MU_LABELS"][str(original_mu)],
            )

        # Test an empty MU and files with zero or one MU
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["MUPULSES"][0] = np.array([], dtype=np.int64)
        res = sort_mus(emgfile)
        self.assertEqual(res["MUPULSES"][-1].size, 0)

        emgfile["NUMBER_OF_MUS"] = np.int64(1)
        emgfile["MUPULSES"] = [emgfile["MUPULSES"][1]]
        res = sort_mus(emgfile)
        self.assertEqual(res["NUMBER_OF_MUS"], 1)

        emgfile["NUMBER_OF_MUS"] = np.int64(0)
        emgfile["MUPULSES"] = []
        res = sort_mus(emgfile)
        self.assertEqual(res["NUMBER_OF_MUS"], 0)

    def test_compute_covsteady(self):
        """
        Test the compute_covsteady function.
        """

        # Ramps duration
        t_ramps = int(10 * self.emgfile["FSAMP"])

        res = compute_covsteady(
            self.emgfile,
            start_steady=0 + t_ramps,
            end_steady=self.emgfile["EMG_LENGTH"] - t_ramps,
        )

        self.assertAlmostEqual(res, 1.3167753, places=6)

        # Test refsig_channel
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"]["target"] = (
            emgfile["REF_SIGNAL"][0]
            + np.linspace(0, 10, emgfile["EMG_LENGTH"])
        )
        target = emgfile["REF_SIGNAL"]["target"].loc[
            t_ramps:emgfile["EMG_LENGTH"] - t_ramps
        ]
        expected = (target.std() / target.mean()) * 100
        res = compute_covsteady(
            emgfile,
            start_steady=t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            refsig_channel="target",
        )
        self.assertAlmostEqual(res, expected, places=6)

        # Test a reference signal containing only a named channel
        emgfile["REF_SIGNAL"] = emgfile["REF_SIGNAL"][["target"]]
        res = compute_covsteady(
            emgfile,
            start_steady=t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            refsig_channel="target",
        )
        self.assertIsInstance(res, float)
        self.assertAlmostEqual(res, expected, places=6)

        # Test interactive selection without opening the GUI
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=[
                t_ramps,
                emgfile["EMG_LENGTH"] - t_ramps,
            ],
        ) as mocked_showselect:
            interactive = compute_covsteady(
                emgfile,
                refsig_channel="target",
            )
        self.assertAlmostEqual(interactive, expected, places=6)
        self.assertEqual(
            mocked_showselect.call_args.kwargs["refsig_channel"],
            "target",
        )

    def test_filter_rawemg(self):
        """
        Test the filter_rawemg function.
        """

        order, lc, hc = 3, 30, 400
        original = self.emgfile["RAW_SIGNAL"].copy(deep=True)
        res = filter_rawemg(
            self.emgfile,
            order=order,
            lowcut=lc,
            highcut=hc,
        )

        f, S = scipy.signal.welch(
            self.emgfile["RAW_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )
        rms_unfiltered = np.sqrt(np.mean(S[(f < lc) | (f > hc)]**2))

        f, S = scipy.signal.welch(
            res["RAW_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )
        rms_filtered = np.sqrt(np.mean(S[(f < lc) | (f > hc)]**2))

        self.assertTrue(rms_filtered < rms_unfiltered)
        pd.testing.assert_frame_equal(self.emgfile["RAW_SIGNAL"], original)
        self.assertTrue(res["RAW_SIGNAL"].index.equals(original.index))
        self.assertTrue(res["RAW_SIGNAL"].columns.equals(original.columns))
        self.assertTrue(
            all(dtype == np.float64 for dtype in res["RAW_SIGNAL"].dtypes)
        )

    def test_filter_refsig(self):
        """
        Test the filter_refsig function.
        """

        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"][1] = emgfile["REF_SIGNAL"][0] * 2
        original = emgfile["REF_SIGNAL"].copy(deep=True)

        f, S = scipy.signal.welch(
            emgfile["REF_SIGNAL"][0].to_numpy(),
            emgfile["FSAMP"],
            nperseg=256,
        )

        # Calculate RMS value
        rms_unfiltered = np.sqrt(np.mean(S[f > 15]**2))

        res = filter_refsig(
            emgfile,
            order=4,
            cutoff=15,
            refsig_channels=0,
        )

        f, S = scipy.signal.welch(
            res["REF_SIGNAL"][0].to_numpy(),
            emgfile["FSAMP"],
            nperseg=256,
        )

        rms_filtered = np.sqrt(np.mean(S[f > 15]**2))

        self.assertTrue(rms_filtered < rms_unfiltered)
        pd.testing.assert_frame_equal(emgfile["REF_SIGNAL"], original)
        pd.testing.assert_series_equal(res["REF_SIGNAL"][1], original[1])
        self.assertTrue(res["REF_SIGNAL"].index.equals(original.index))
        self.assertTrue(res["REF_SIGNAL"].columns.equals(original.columns))
        self.assertTrue(
            all(dtype == np.float64 for dtype in res["REF_SIGNAL"].dtypes)
        )

        # Test a list containing integer and named channels
        emgfile["REF_SIGNAL"]["target"] = emgfile["REF_SIGNAL"][0]
        original = emgfile["REF_SIGNAL"].copy(deep=True)
        res = filter_refsig(
            emgfile,
            order=2,
            cutoff=10,
            refsig_channels=[0, "target"],
        )
        self.assertFalse(res["REF_SIGNAL"][0].equals(original[0]))
        self.assertFalse(
            res["REF_SIGNAL"]["target"].equals(original["target"])
        )
        pd.testing.assert_series_equal(res["REF_SIGNAL"][1], original[1])
        pd.testing.assert_frame_equal(emgfile["REF_SIGNAL"], original)

        with self.assertRaises(TypeError):
            filter_refsig(emgfile, refsig_channels=(0, "target"))

    def test_filter_refsig_float32_otb(self):
        """Test filtering a reference signal directly after OTB import."""

        emgfile = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R.mat"),
            refsig="subsampled",
            version="1.5.3.0",
        )
        original = emgfile["REF_SIGNAL"].copy()
        self.assertEqual(original[0].dtype, np.float32)

        # OTB can import float32 signals, while filtering computes float64.
        # Assigning that result into a float32 column raised a FutureWarning.
        # Exercise the direct import-to-filter path for the pandas upgrade.
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            expected = filter_refsig(standardise_emgfile_dtypes(emgfile))
            res = filter_refsig(emgfile)

        self.assertEqual(res["REF_SIGNAL"][0].dtype, np.float64)
        pd.testing.assert_frame_equal(
            res["REF_SIGNAL"], expected["REF_SIGNAL"],
        )
        pd.testing.assert_frame_equal(emgfile["REF_SIGNAL"], original)

    def test_remove_powerline_harmonics(self):
        """Test suppression of 50 Hz and 100 Hz on two channels."""

        fsamp = 1000
        # One second places each component exactly on its own FFT bin.
        time = np.arange(fsamp) / fsamp
        preserved = np.stack([
            np.sin(2 * np.pi * 17 * time),
            np.cos(2 * np.pi * 17 * time),
        ])
        mains = np.sin(2 * np.pi * 50 * time) + np.sin(2 * np.pi * 100 * time)

        result = remove_powerline_harmonics(preserved + mains, fsamp)

        np.testing.assert_allclose(result, preserved, rtol=0, atol=1e-12)

    def test_remove_offset(self):
        """
        Test the remove_offset function.
        """

        # Test auto
        auto = round(self.emgfile["FSAMP"] / 2)
        original = self.emgfile["REF_SIGNAL"].copy(deep=True)
        res = remove_offset(self.emgfile, auto=auto)

        self.assertAlmostEqual(
            res["REF_SIGNAL"][0].iloc[:auto].mean(),
            0,
            places=3,
        )
        pd.testing.assert_frame_equal(self.emgfile["REF_SIGNAL"], original)

        # Test offsetval
        res = remove_offset(res, offsetval=1)

        self.assertAlmostEqual(
            res["REF_SIGNAL"][0].iloc[:auto].mean(),
            -1,
            places=3,
        )

        # Test multiple channels and offset values
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"][1] = emgfile["REF_SIGNAL"][0] + 10
        original = emgfile["REF_SIGNAL"].copy(deep=True)
        res = remove_offset(
            emgfile,
            offsetval=[1, 2],
            refsig_channels=[0, 1],
        )
        pd.testing.assert_series_equal(
            res["REF_SIGNAL"][0],
            original[0] - 1,
        )
        pd.testing.assert_series_equal(
            res["REF_SIGNAL"][1],
            original[1] - 2,
        )
        pd.testing.assert_frame_equal(emgfile["REF_SIGNAL"], original)

        # Test manual selection and a named channel without opening the GUI
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"]["force"] = emgfile["REF_SIGNAL"][0]
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=[100, 200],
        ) as mocked_showselect:
            res = remove_offset(
                emgfile,
                offsetval=0,
                auto=0,
                refsig_channels="force",
            )
        self.assertAlmostEqual(
            res["REF_SIGNAL"]["force"].loc[100:200].mean(),
            0,
            places=12,
        )
        self.assertEqual(
            mocked_showselect.call_args.kwargs["refsig_channel"],
            "force",
        )

        # Test invalid options
        with self.assertRaises(TypeError):
            remove_offset(self.emgfile, auto=1.5)
        with self.assertRaises(TypeError):
            remove_offset(self.emgfile, refsig_channels=(0,))
        with self.assertRaises(ValueError):
            remove_offset(
                emgfile,
                offsetval=[1],
                refsig_channels=[0, "force"],
            )
        with self.assertRaises(TypeError):
            remove_offset(
                emgfile,
                offsetval=[1, "invalid"],
                refsig_channels=[0, "force"],
            )
        with self.assertRaises(TypeError):
            remove_offset(self.emgfile, offsetval={"invalid": 1})

    def test_get_mvc(self):
        """
        Test the get_mvc function.
        """

        res = get_mvc(self.emgfile, how="all")

        self.assertAlmostEqual(res, 27.170013427734375, places=6)

        # Test conversion_val
        res = get_mvc(self.emgfile, how="all", conversion_val=9.81)

        self.assertAlmostEqual(res, 266.5378317260742, places=6)

        # Test refsig_channel
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"]["force"] = emgfile["REF_SIGNAL"][0] + 10
        res = get_mvc(emgfile, how="all", refsig_channel="force")
        self.assertAlmostEqual(
            res,
            emgfile["REF_SIGNAL"]["force"].max(),
            places=6,
        )

        # Test interactive selection without opening the GUI
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=[100, 200],
        ) as mocked_showselect:
            res = get_mvc(
                emgfile,
                how="showselect",
                refsig_channel="force",
            )
        self.assertAlmostEqual(
            res,
            emgfile["REF_SIGNAL"]["force"].iloc[100:200].max(),
            places=6,
        )
        self.assertEqual(mocked_showselect.call_count, 1)

        with self.assertRaises(ValueError):
            get_mvc(self.emgfile, how="invalid")

    def test_compute_rfd(self):
        """
        Test the compute_rfd function.
        """

        res = compute_rfd(
            self.emgfile,
            ms=[50, 100, 150, 200],
            startpoint=1683,
            conversion_val=0,
        )

        expected_values = np.array([4.760742, 3.768921, 4.760742, 4.66156])

        self.assertTrue(np.allclose(expected_values, res.values[0], atol=1e-5))

        # Test conversion_val and refsig_channel
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["REF_SIGNAL"]["force"] = emgfile["REF_SIGNAL"][0]
        converted = compute_rfd(
            emgfile,
            ms=[50, 100, 150, 200],
            startpoint=1683,
            conversion_val=9.81,
            refsig_channel="force",
        )
        np.testing.assert_allclose(converted.to_numpy(), res.to_numpy() * 9.81)

        # Test interactive selection without opening the GUI
        with patch(
            "openhdemg.library.tools.showselect",
            return_value=[1683],
        ) as mocked_showselect:
            selected = compute_rfd(
                self.emgfile,
                ms=[50, 100, 150, 200],
                startpoint=None,
            )
        pd.testing.assert_frame_equal(selected, res)
        self.assertEqual(mocked_showselect.call_count, 1)

        # Test a NumPy integer startpoint
        selected = compute_rfd(
            self.emgfile,
            ms=[50, 100, 150, 200],
            startpoint=np.int64(1683),
        )
        pd.testing.assert_frame_equal(selected, res)

        # Test invalid startpoints and intervals
        with self.assertRaises(TypeError):
            compute_rfd(self.emgfile, startpoint=1.5)
        with self.assertRaises(ValueError):
            compute_rfd(self.emgfile, startpoint=-1)
        with self.assertRaises(ValueError):
            compute_rfd(
                self.emgfile,
                ms=[200],
                startpoint=self.emgfile["EMG_LENGTH"] - 1,
            )
        with self.assertRaises(ValueError):
            compute_rfd(self.emgfile, ms=[0], startpoint=1683)

    def test_compute_svr(self):
        """
        Test the compute_svr function.
        """

        # Test initial discontonuity and output dimensionality
        emgfile = copy.deepcopy(self.emgfile)
        emgfile["MUPULSES"][1] = np.insert(
            arr=emgfile["MUPULSES"][1],
            obj=0,
            values=int(emgfile["MUPULSES"][1][0] - emgfile["FSAMP"] * 2),
        )  # 2 sec discontinuity at the beginning on MU 1

        res = compute_svr(
            emgfile,
            gammain=0.5,
            regparam=2,
            endpointweights_numpulses=3,
            endpointweights_magnitude=4,
            discontfiring_dur=1,
        )

        self.assertSetEqual(set(res.keys()), {'svrfit', 'svrtime', 'gensvr'})
        for fits in res.values():
            self.assertIsInstance(fits, list)
            self.assertEqual(len(fits), emgfile["NUMBER_OF_MUS"])
            for mu_fit in fits:
                self.assertIsInstance(mu_fit, np.ndarray)
                self.assertEqual(mu_fit.ndim, 1)
        for mu_fit in res["gensvr"]:
            self.assertEqual(mu_fit.shape[0], emgfile["EMG_LENGTH"])


if __name__ == '__main__':
    unittest.main()
