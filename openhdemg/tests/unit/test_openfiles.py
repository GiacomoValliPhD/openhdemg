"""
To run the tests using unittest, execute from the openhdemg/tests directory:
    python -m unittest discover

First, you should dowload all the files necessary for the testing and store
them inside openhdemg/tests/fixtures. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

NOTE: Fixtures contain an openhdemg module (folder) which is stored as a zip
file generated on windows 11 as "right-click the module folder, Send to >
Compressed (zipped) folder". Tests extract the ZIP beside it if the folder is
missing.

WARNING!!! Since the library's functions perform complex tasks and return
complex data structures, these tests can verify that no critical errors occur,
but the accuracy of each function must be assessed independently upon creation,
or at each revision of the code.

WARNING!!! - UNTESTED FUNCTIONS: askopenfile, asksavefile
"""


import json
import shutil
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import numpy as np
import pandas as pd
from openhdemg.tests.unit.functions_for_unit_test import (
    get_directories as getd, get_module_fixture, validate_emgfile_content,
    validate_emg_refsig_content, validate_standard_emgfile_content,
)
from openhdemg.library.openfiles import (
    is_safe_openhdemg_folder, sha256_file, save_openhdemg_module,
    asksavemodule, load_openhdemg_module, askloadmodule, openhdemg_Collection,
    emg_from_demuse, emg_from_otb, refsig_from_otb, emg_from_delsys,
    refsig_from_delsys, emg_from_customcsv, refsig_from_customcsv,
    save_json_emgfile, emg_from_json, askopenfile, asksavefile,
    emg_from_samplefile,
)


class TestOpenFiles(unittest.TestCase):
    """
    Test the functions/classes in the openfiles module.
    """

    def test_is_safe_openhdemg_folder(self):
        """
        Test which folders can safely be overwritten as modules.
        """

        module = get_module_fixture()
        self.assertTrue(is_safe_openhdemg_folder(module))
        self.assertFalse(is_safe_openhdemg_folder(module.anchor))

        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertTrue(is_safe_openhdemg_folder(root))
            self.assertFalse(is_safe_openhdemg_folder(root / "missing"))

            # An unrelated file must not make its directory safe to overwrite
            unrelated = root / "notes.txt"
            unrelated.touch()
            self.assertFalse(is_safe_openhdemg_folder(unrelated))
            self.assertFalse(is_safe_openhdemg_folder(root))

            # Both the marker and manifest are required in a nonempty folder
            marker = root / ".openhdemg_module"
            manifest = root / "manifest.json"
            marker.touch()
            self.assertFalse(is_safe_openhdemg_folder(root))
            marker.unlink()
            manifest.touch()
            self.assertFalse(is_safe_openhdemg_folder(root))
            marker.touch()
            self.assertTrue(is_safe_openhdemg_folder(root))

            marker.rename(root / ".custom_marker")
            self.assertFalse(is_safe_openhdemg_folder(root))
            self.assertTrue(is_safe_openhdemg_folder(root, ".custom_marker"))

    def test_sha256_file(self):
        """
        Test known checksums and reading the file in different chunk sizes.
        """

        with TemporaryDirectory() as directory:
            path = Path(directory) / "data.bin"
            path.write_bytes(b"abc")
            expected = (
                "sha256:"
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
            )
            self.assertEqual(sha256_file(path), expected)
            self.assertEqual(sha256_file(path, chunk_size=1), expected)

            # Check the SHA-256 checksum of an empty file
            path.write_bytes(b"")
            self.assertEqual(
                sha256_file(path),
                "sha256:"
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )

    def test_save_openhdemg_module(self):
        """
        Test module round trips, compression, checksums and safe overwriting.
        """

        module = get_module_fixture()
        emgfile = load_openhdemg_module(module.parent, module.name)
        original = deepcopy(emgfile)

        with TemporaryDirectory() as directory:
            # Level 0 still writes gzip files; None writes raw binary files
            for level, checksum, filename in (
                (None, False, None), (0, True, "custom_name"), (1, True, None),
            ):
                with self.subTest(compresslevel=level, add_checksum=checksum):
                    saved_path = save_openhdemg_module(
                        emgfile, directory, "saved_module", filename=filename,
                        compresslevel=level, add_checksum=checksum,
                    )
                    self.assertEqual(
                        saved_path, Path(directory).resolve() / "saved_module",
                    )
                    self.assertTrue(
                        (saved_path / ".openhdemg_module").is_file()
                    )
                    self.assertTrue((saved_path / "files").is_dir())
                    manifest = json.loads(
                        (saved_path / "manifest.json").read_text(),
                    )
                    for info in manifest.values():
                        if "data_file_path" not in info:
                            continue
                        binary = saved_path / info["data_file_path"]
                        self.assertTrue(binary.is_file())
                        self.assertEqual(
                            info["compression"],
                            None if level is None else "gzip",
                        )
                        self.assertEqual(
                            info["checksum"],
                            sha256_file(binary) if checksum else None,
                        )

                    restored = load_openhdemg_module(
                        directory, "saved_module", verify_checksum=True,
                    )
                    self.assertEqual(restored.keys(), original.keys())
                    self.assertEqual(
                        restored["FILENAME"],
                        original["FILENAME"] if filename is None else filename,
                    )
                    self.assertEqual(emgfile["FILENAME"], original["FILENAME"])
                    # Compare all saved data and check that saving did not
                    # mutate it.
                    for key, expected in original.items():
                        if key == "FILENAME":
                            continue
                        with self.subTest(field=key):
                            for actual in (restored[key], emgfile[key]):
                                if isinstance(expected, pd.DataFrame):
                                    pd.testing.assert_frame_equal(
                                        actual, expected, check_exact=True,
                                    )
                                elif isinstance(expected, list):
                                    self.assertEqual(len(actual), len(expected))
                                    for array, expected_array in zip(actual, expected):
                                        np.testing.assert_array_equal(
                                            array, expected_array,
                                        )
                                        self.assertEqual(
                                            array.dtype, expected_array.dtype,
                                        )
                                else:
                                    self.assertEqual(actual, expected)

            # A recognised module is overwritten, including obsolete files
            obsolete = saved_path / "obsolete.txt"
            obsolete.touch()
            save_openhdemg_module(emgfile, directory, "saved_module")
            self.assertFalse(obsolete.exists())

            # Refuse to overwrite an unrelated folder and preserve its contents
            unrelated = Path(directory) / "unrelated"
            unrelated.mkdir()
            notes = unrelated / "notes.txt"
            notes.write_text("keep this file")
            with self.assertRaisesRegex(RuntimeError, "Unsafe or unknown folder"):
                save_openhdemg_module(emgfile, directory, "unrelated")
            self.assertEqual(notes.read_text(), "keep this file")

            # Empty pulse entries, an empty pulse list and labelled empty
            # EXTRAS.
            small_module = {
                "SOURCE": "OPENHDEMG",
                "FILENAME": "empty_pulses",
                "FSAMP": 2048.0,
                "MUPULSES": [
                    np.array([], dtype="int64"), np.array([1, 3], dtype="int32"),
                ],
                "REFERENCE_MUPULSES": [],
                "EXTRAS": pd.DataFrame(columns=[0, 1.5, "label"]),
            }
            save_openhdemg_module(small_module, directory, "empty_pulses")
            restored = load_openhdemg_module(directory, "empty_pulses")
            self.assertEqual(restored.keys(), small_module.keys())
            self.assertEqual(len(restored["MUPULSES"]), 2)
            for actual, expected in zip(restored["MUPULSES"], small_module["MUPULSES"]):
                np.testing.assert_array_equal(actual, expected)
                self.assertEqual(actual.dtype, expected.dtype)
            self.assertEqual(restored["REFERENCE_MUPULSES"], [])
            pd.testing.assert_frame_equal(restored["EXTRAS"], small_module["EXTRAS"])

    def test_asksavemodule(self):
        """
        Test saving through the directory dialog without opening a GUI.
        """

        module = get_module_fixture()
        emgfile = load_openhdemg_module(module.parent, module.name)
        with TemporaryDirectory() as directory:
            selected = Path(directory) / "selected_module"
            for filename, level, checksum, parent in (
                (None, None, False, None), ("custom_name", 1, True, object()),
            ):
                with self.subTest(filename=filename):
                    with patch(
                        "openhdemg.library.openfiles.run_custom_directory_dialog",
                        return_value=str(selected),
                    ) as dialog:
                        result = asksavemodule(
                            emgfile, filename=filename, compresslevel=level,
                            add_checksum=checksum, gui_parent=parent,
                        )
                    dialog.assert_called_once_with(
                        window_title="Select a folder to save the module",
                        mode="save", parent=parent,
                    )
                    self.assertEqual(result, selected.resolve())
                    restored = load_openhdemg_module(
                        selected.parent, selected.name, verify_checksum=True,
                    )
                    self.assertEqual(
                        restored["FILENAME"],
                        selected.name if filename is None else filename,
                    )
                    pd.testing.assert_frame_equal(
                        restored["REF_SIGNAL"], emgfile["REF_SIGNAL"],
                    )
                    manifest = json.loads((selected / "manifest.json").read_text())
                    self.assertEqual(
                        manifest["REF_SIGNAL"]["compression"],
                        None if level is None else "gzip",
                    )
                    self.assertEqual(
                        manifest["REF_SIGNAL"]["checksum"] is not None, checksum,
                    )

    def test_load_openhdemg_module(self):
        """
        Test the saved fixture independently of the current writer.
        """

        module = get_module_fixture()
        with TemporaryDirectory() as directory:
            # Match older files without checksums, without using the current writer
            without_checksum = Path(directory) / "without_checksum"
            shutil.copytree(module, without_checksum)
            manifest_path = without_checksum / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for info in manifest.values():
                if "data_file_path" in info:
                    info["checksum"] = None
            manifest_path.write_text(json.dumps(manifest))

            for path in (module, without_checksum):
                manifest = json.loads((path / "manifest.json").read_text())
                for verify in (False, True):
                    with self.subTest(module=path.name, verify_checksum=verify):
                        emgfile, metadata = load_openhdemg_module(
                            path.parent, path.name,
                            verify_checksum=verify, return_metadata=True,
                        )
                        self.assertEqual(metadata, manifest["_metadata"])
                        self.assertEqual(emgfile.keys(), manifest.keys() - {"_metadata"})
                        self.assertEqual(emgfile["SOURCE"], "OPENHDEMG")
                        self.assertEqual(emgfile["FILENAME"], manifest["FILENAME"]["text"])
                        for key, expected in (
                            ("FSAMP", 2048.0), ("IED", 8.0),
                            ("EMG_LENGTH", 66560), ("NUMBER_OF_MUS", 24),
                        ):
                            self.assertEqual(emgfile[key], expected)
                            self.assertIsInstance(emgfile[key], type(expected))
                        for key in (
                            "DECOMPOSITION_PARAMETERS", "MU_LABELS", "GOOD_CHANNELS",
                        ):
                            self.assertEqual(emgfile[key], manifest[key]["value"])

                        # Compare every sample against the existing binary files
                        for key, shape, dtype in (
                            ("RAW_SIGNAL", (66560, 64), "float64"),
                            ("REF_SIGNAL", (66560, 1), "float64"),
                            ("ACCURACY", (24, 1), "float64"),
                            ("IPTS", (66560, 24), "float64"),
                            ("BINARY_MUS_FIRING", (66560, 24), "uint8"),
                            ("ROA_WITH_REFERENCE_MUPULSES", (24, 1), "float64"),
                        ):
                            with self.subTest(field=key):
                                values = np.fromfile(
                                    path / "files" / f"{key}.bin", dtype=dtype,
                                ).reshape(shape)
                                pd.testing.assert_frame_equal(
                                    emgfile[key], pd.DataFrame(values), check_exact=True,
                                )
                        self.assertIsInstance(emgfile["EXTRAS"], pd.DataFrame)
                        self.assertEqual(emgfile["EXTRAS"].shape, (0, 0))

                        for key in ("MUPULSES", "REFERENCE_MUPULSES"):
                            self.assertIsInstance(emgfile[key], list)
                            self.assertEqual(len(emgfile[key]), 24)
                            self.assertEqual(
                                [len(a) for a in emgfile[key]], manifest[key]["lengths"],
                            )
                            for array in emgfile[key]:
                                self.assertIsInstance(array, np.ndarray)
                                self.assertEqual(array.ndim, 1)
                                self.assertEqual(array.dtype, np.dtype("int64"))
                            np.testing.assert_array_equal(
                                np.concatenate(emgfile[key]),
                                np.fromfile(path / "files" / f"{key}.bin", dtype="int64"),
                            )
                        for info in manifest.values():
                            if "data_file_path" in info:
                                if path == module:
                                    self.assertTrue(info["checksum"].startswith("sha256:"))
                                else:
                                    self.assertIsNone(info["checksum"])

            # Corrupt temporary copies, never the compatibility fixture
            for key in ("REF_SIGNAL", "MUPULSES", "REFERENCE_MUPULSES"):
                with self.subTest(corrupted_field=key):
                    copied = Path(directory) / key
                    shutil.copytree(module, copied)
                    with (copied / "files" / f"{key}.bin").open("r+b") as binary:
                        first_byte = binary.read(1)
                        binary.seek(0)
                        binary.write(bytes([first_byte[0] ^ 1]))
                    with self.assertRaisesRegex(
                        ValueError, f"Checksum mismatch for {key}\\.",
                    ):
                        load_openhdemg_module(directory, key, verify_checksum=True)
                    restored = load_openhdemg_module(
                        directory, key, verify_checksum=False,
                    )
                    self.assertEqual(restored["NUMBER_OF_MUS"], 24)

            with self.assertRaises(FileNotFoundError):
                load_openhdemg_module(directory, "missing")

            # Restore mixed dtypes with unique integer, float and string labels
            extras = pd.DataFrame({
                0: pd.Series([1, 2], dtype="int64"),
                1.5: pd.Series([0.25, 0.75], dtype="float32"),
                "signal": pd.Series([3.5, 4.5], dtype="float64"),
            })
            save_openhdemg_module(
                {"FILENAME": "dtypes", "FSAMP": 2048.0, "EXTRAS": extras},
                directory, "dtypes",
            )
            restored = load_openhdemg_module(directory, "dtypes")
            pd.testing.assert_frame_equal(
                restored["EXTRAS"], extras, check_exact=True,
            )

    def test_askloadmodule(self):
        """
        Test directory selection, return options and checksum forwarding.
        """

        module = get_module_fixture()
        manifest = json.loads((module / "manifest.json").read_text())
        parent = object()
        for metadata, path in (
            (False, False), (True, False), (False, True), (True, True),
        ):
            with self.subTest(return_metadata=metadata, return_path=path):
                with patch(
                    "openhdemg.library.openfiles.run_custom_directory_dialog",
                    return_value=str(module),
                ) as dialog:
                    result = askloadmodule(
                        verify_checksum=True, return_metadata=metadata,
                        return_path=path, gui_parent=parent,
                    )
                dialog.assert_called_once_with(
                    window_title="Select the module folder to load", parent=parent,
                )
                if path:
                    self.assertIsInstance(result, tuple)
                    self.assertEqual(len(result), 2)
                    result, returned_path = result
                    self.assertEqual(returned_path, module.resolve())
                if metadata:
                    self.assertIsInstance(result, tuple)
                    self.assertEqual(len(result), 2)
                    result, returned_metadata = result
                    self.assertEqual(returned_metadata, manifest["_metadata"])
                self.assertIsInstance(result, dict)
                self.assertEqual(result["FILENAME"], manifest["FILENAME"]["text"])
                self.assertEqual(result["NUMBER_OF_MUS"], 24)

        with patch(
            "openhdemg.library.openfiles.run_custom_directory_dialog",
            return_value=None,
        ):
            self.assertIsNone(askloadmodule())

        with TemporaryDirectory() as directory:
            (Path(directory) / "notes.txt").touch()
            with patch(
                "openhdemg.library.openfiles.run_custom_directory_dialog",
                return_value=directory,
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "not a valid openhdemg module",
                ):
                    askloadmodule()

            # Verify the wrapper honours the requested checksum setting
            copied = Path(directory) / "module"
            shutil.copytree(module, copied)
            manifest["REF_SIGNAL"]["checksum"] = "sha256:" + "0" * 64
            (copied / "manifest.json").write_text(json.dumps(manifest))
            with patch(
                "openhdemg.library.openfiles.run_custom_directory_dialog",
                return_value=str(copied),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Checksum mismatch for REF_SIGNAL",
                ):
                    askloadmodule(verify_checksum=True)
                self.assertIsInstance(askloadmodule(verify_checksum=False), dict)

    def test_from_demuse(self):
        """
        Test loading various decomposed files saved from the DEMUSE software.
        """

        # Load decomposed file with multiple MUs and reference signal
        demuse_D_R_mMU = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_mMU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_mMU)

        # Load decomposed file with only 1 MU and reference signal
        demuse_D_R_1MU = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_1MU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_1MU)

        # Load decomposed file with multiple MUs (some empty) and reference
        # signal
        demuse_D_R_E_mMU = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_E_mMU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_E_mMU)

    def test_from_otb(self):
        """
        Test loading various files saved from the OTBiolab+ software.
        """

        # Load decomposed file with multiple MUs and reference signal
        otb_D_R_mMU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_mMU.mat"),
            ext_factor=0,
            refsig=[True, "subsampled"],
            version="1.5.3.0",
            )
        validate_emgfile_content(self, otb_D_R_mMU)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        otb_D_R_EX_mMU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_EX_mMU.mat"),
            extras="requested|AUX  Force"
            )
        validate_emgfile_content(self, otb_D_R_EX_mMU)

        # Load decomposed file with only 1 MU without the reference signal
        with self.assertWarns(UserWarning):
            otb_D_R_1_MU = emg_from_otb(
                filepath=getd("library", "otb", "OTB_D_R_1MU.mat"),
                refsig=[False, "fullsampled"],
                )
        validate_emgfile_content(self, otb_D_R_1_MU)
        self.assertTrue(otb_D_R_1_MU["REF_SIGNAL"].empty)

        # Load file with only the reference signal
        otb_R = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R.mat"),
            refsig="subsampled",
            version="1.5.3.0",
            )
        validate_emg_refsig_content(self, otb_R)

        # Load file with only the reference signal and EXTRAS
        otb_R_EX = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R_EX.mat"),
            extras="requested path",
            )
        validate_emg_refsig_content(self, otb_R_EX)

    def test_from_delsys(self):
        """
        Test loading various files saved from the Delsys software.
        """

        # Load decomposed file with multiple MUs, reference signal and MUAPs
        delsys_D_R_MUAPs_mMU = emg_from_delsys(
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
            emg_sensor_name="Galileo",
            refsig_sensor_name="Trigno",
            filename_from="rawemg_file",
        )
        validate_emgfile_content(self, delsys_D_R_MUAPs_mMU)
        self.assertEqual(
            delsys_D_R_MUAPs_mMU["FILENAME"],
            "Raw_EMG_signal_withFakeRef.mat",
        )

        # Load decomposed file with multiple MUs and MUAPs
        delsys_D_MUAPs_mMU = emg_from_delsys(
            rawemg_filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Raw_EMG_signal.mat"
            ),
            mus_directory=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Bicep_Brachii_Motor_Units (Sensor 1)"
            ),
        )
        validate_emgfile_content(self, delsys_D_MUAPs_mMU)

        # Load file with only the reference signal
        delsys_R = refsig_from_delsys(
            filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Raw_EMG_signal_withFakeRef.mat",
            )
        )
        validate_emg_refsig_content(self, delsys_R)

        # Load file with only the reference signal using a custom sensor name
        delsys_R_custom_name = refsig_from_delsys(
            filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Raw_EMG_signal_withFakeRef.mat",
            ),
            refsig_sensor_name="Trigno",
        )
        validate_emg_refsig_content(self, delsys_R_custom_name)

    def test_from_customcsv(self):
        """
        Test loading various files saved in a custom .csv file.
        """

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        custom_csv_D_R_EX_mMU = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_mMU.csv"),
            ref_signal="REF",
            raw_signal="RAW",
            ipts="IPT",
            mupulses="MUP",
            binary_mus_firing="BINARY",
            accuracy="ACC",
            extras="EXT",
            fsamp=1000,
            ied=10,
            )
        validate_emgfile_content(self, custom_csv_D_R_EX_mMU)
        self.assertEqual(custom_csv_D_R_EX_mMU["FSAMP"], 1000)
        self.assertEqual(custom_csv_D_R_EX_mMU["IED"], 10)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        custom_csv_D_R_EX_1MU = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_1MU.csv"),
            )
        validate_emgfile_content(self, custom_csv_D_R_EX_1MU)

        # Load file with only the reference signal EXTRAS
        custom_csv_R_EX = refsig_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_R_EX.csv"),
            )
        validate_emg_refsig_content(self, custom_csv_R_EX)

        # Load file using custom labels and sampling frequency
        custom_csv_R_EX_custom_labels = refsig_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_R_EX.csv"),
            ref_signal="REF",
            extras="EXT",
            fsamp=1000,
            )
        validate_emg_refsig_content(self, custom_csv_R_EX_custom_labels)
        self.assertEqual(custom_csv_R_EX_custom_labels["FSAMP"], 1000)

    def test_from_samplefile(self):
        """
        Test loading the decomposed sample file.
        """

        # Load decomposed file with multiple MUs and reference signal
        emgfile = emg_from_samplefile()
        validate_standard_emgfile_content(self, emgfile)

    def test_from_json(self):
        """
        Test loading various files saved in .json.
        """

        # Load decomposed file with multiple MUs and reference signal
        openhdemg_D_R_mMU = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_D_R_mMU.json"),
            )
        validate_emgfile_content(self, openhdemg_D_R_mMU)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        openhdemg_D_R_EX_mMU = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_D_R_EX_mMU.json"),
            )
        validate_emgfile_content(self, openhdemg_D_R_EX_mMU)

        # Load file with only reference signal
        openhdemg_R = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_R.json"),
            )
        validate_emg_refsig_content(self, openhdemg_R)

        # Load file with only reference signal and EXTRAS
        openhdemg_R_EX = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_R_EX.json"),
            )
        validate_emg_refsig_content(self, openhdemg_R_EX)

    def test_saving_and_reloading(self):
        """
        Test saving (various) and reloading (.json) files.
        """

        # Test with sample file
        emgfile = emg_from_samplefile()
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Test with DEMUSE files
        # Load decomposed file with multiple MUs and reference signal
        emgfile = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_mMU.mat"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load decomposed file with only 1 MU and reference signal
        emgfile = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_1MU.mat"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load decomposed file with multiple MUs (some empty) and reference
        # signal
        emgfile = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_E_mMU.mat"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Test with OTB files
        # Load decomposed file with multiple MUs and reference signal
        emgfile = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_mMU.mat"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        emgfile = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_EX_mMU.mat"),
            extras="requested|AUX  Force"
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load decomposed file with only 1 MU and reference signal
        emgfile = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_1MU.mat"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load file with only the reference signal
        emg_refsig = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R.mat"),
            )
        save_json_emgfile(
            emg_refsig, filepath=getd("library", "saved", "temp.json")
        )
        emg_refsig = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emg_refsig_content(self, emg_refsig)

        # Load file with only the reference signal and EXTRAS
        emg_refsig = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R_EX.mat"),
            extras="requested path",
            )
        save_json_emgfile(
            emg_refsig, filepath=getd("library", "saved", "temp.json")
        )
        emg_refsig = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emg_refsig_content(self, emg_refsig)

        # Test with Delsys files
        # Load decomposed file with multiple MUs, reference signal and MUAPs
        emgfile = emg_from_delsys(
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
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile=emgfile)

        # Load decomposed file with multiple MUs and MUAPs
        emgfile = emg_from_delsys(
            rawemg_filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Raw_EMG_signal.mat"
            ),
            mus_directory=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Bicep_Brachii_Motor_Units (Sensor 1)"
            ),
        )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile=emgfile)

        # Load file with only the reference signal
        emg_refsig = refsig_from_delsys(
            filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Raw_EMG_signal_withFakeRef.mat",
            )
        )
        save_json_emgfile(
            emg_refsig, filepath=getd("library", "saved", "temp.json")
        )
        emg_refsig = emg_from_json(
            filepath=getd("library", "saved", "temp.json"),
        )
        validate_emg_refsig_content(self, emg_refsig)

        # Test with CUSTOMCSV files
        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        emgfile = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_mMU.csv"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        emgfile = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_1MU.csv"),
            )
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Load file with only the reference signal, with EXTRAS
        emg_refsig = refsig_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_R_EX.csv"),
            )
        save_json_emgfile(
            emg_refsig, filepath=getd("library", "saved", "temp.json")
        )
        emg_refsig = emg_from_json(
            filepath=getd("library", "saved", "temp.json"),
        )
        validate_emg_refsig_content(self, emg_refsig)

    def test_compression_level(self):
        """
        Test saving (various) and reloading (.json) files.
        """

        # Test with sample file, no compression
        emgfile = emg_from_samplefile()
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json"),
            compresslevel=0,
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Normal compression
        emgfile = emg_from_samplefile()
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json"),
            compresslevel=4,
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)

        # Maximum compression
        emgfile = emg_from_samplefile()
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json"),
            compresslevel=9,
        )
        emgfile = emg_from_json(filepath=getd("library", "saved", "temp.json"))
        validate_emgfile_content(self, emgfile)


class TestOpenhdemgCollection(unittest.TestCase):
    """
    Test collection state, manifests, shared data and selective module I/O.

    Each test has a fresh collection and temporary directory. Module contents
    come from the existing fixture; only directory dialogs are mocked.
    Detailed module serialization is covered by the module tests.
    """

    @classmethod
    def setUpClass(cls):
        module = get_module_fixture()
        cls.module_fixture = load_openhdemg_module(
            module.parent, module.name, verify_checksum=True,
        )

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.collection = openhdemg_Collection()
        self.collection.set_root(self.root)
        self.module = deepcopy(self.module_fixture)
        self.shared = pd.DataFrame({
            0: [0.5, 1.5], 1.5: [2.0, 3.0], "force": [4.0, 5.0],
        })
        self.participant = {
            "participant_id": "TEST_001", "session": {"label": "Artificial"},
        }

    def test_initial_state(self):
        """
        Start with no root, modules, shared data or participant information.
        """

        collection = openhdemg_Collection()
        self.assertIsNone(collection.root)
        self.assertIsNone(collection.manifest_path)
        self.assertIsNone(collection.marker_path)
        self.assertEqual(collection.modules, {})
        self.assertIsNone(collection.get_shared_dataframe())
        self.assertIsNone(collection.get_participant_info())
        self.assertEqual(collection.manifest["modules"], [])
        self.assertIsNone(collection.manifest["shared_dataframe"])
        self.assertIsNone(collection.manifest["participant_info"])
        self.assertIsNone(collection.manifest["_metadata"]["edited"])
        self.assertEqual(
            collection.manifest["_metadata"]["data_structure_version"], "1.0",
        )

    def test_root(self):
        """
        Keep root, manifest and marker paths consistent when set or reset.
        """

        self.assertEqual(self.collection.get_root(), str(self.root))
        target = self.root / "collection"
        self.collection.set_root(str(target))
        self.assertEqual(self.collection.root, target)
        self.assertEqual(
            self.collection.manifest_path, target / "manifest.json",
        )
        self.assertEqual(
            self.collection.marker_path, target / ".openhdemg_collection",
        )
        self.collection.reset_root()
        self.assertIsNone(self.collection.root)
        self.assertIsNone(self.collection.manifest_path)
        self.assertIsNone(self.collection.marker_path)

    def test_shared_dataframe(self):
        """
        Set and retrieve independent copies, then reset shared data.
        """

        expected = self.shared.copy()
        self.collection.set_shared_dataframe(self.shared)
        self.shared.iloc[0, 0] = -1.0
        returned = self.collection.get_shared_dataframe()
        pd.testing.assert_frame_equal(returned, expected)
        returned.iloc[0, 0] = -2.0
        pd.testing.assert_frame_equal(
            self.collection.get_shared_dataframe(), expected,
        )
        self.collection.reset_shared_dataframe()
        self.assertIsNone(self.collection.get_shared_dataframe())

    def test_participant_info(self):
        """
        Copy participant information, reject unsupported values and reset it.
        """

        expected = deepcopy(self.participant)
        self.collection.set_participant_info(self.participant)
        self.participant["session"]["label"] = "changed input"
        returned = self.collection.get_participant_info()
        self.assertEqual(returned, expected)
        returned["session"]["label"] = "changed result"
        self.assertEqual(self.collection.get_participant_info(), expected)
        with self.assertRaisesRegex(TypeError, "not JSON serialisable"):
            self.collection.set_participant_info({"unsupported": object()})
        self.assertEqual(self.collection.get_participant_info(), expected)
        self.collection.reset_participant_info()
        self.assertIsNone(self.collection.get_participant_info())

    def test_modules(self):
        """
        Add, retrieve, replace and remove modules by name.
        """

        self.assertIsNone(self.collection.get_module("missing"))
        self.collection.add_module(self.module, "module", replace=False)
        returned = self.collection.get_module("module")
        returned["REF_SIGNAL"].iloc[0, 0] = -999.0
        pd.testing.assert_frame_equal(
            self.collection.get_module("module")["REF_SIGNAL"],
            self.module["REF_SIGNAL"],
        )

        replacement = deepcopy(self.module)
        replacement["FILENAME"] = "replacement"
        with self.assertWarnsRegex(UserWarning, "already present"):
            self.collection.add_module(replacement, "module", replace=False)
        self.assertEqual(
            self.collection.get_module("module")["FILENAME"],
            self.module["FILENAME"],
        )
        self.collection.add_module(replacement, "module", replace=True)
        self.assertEqual(
            self.collection.get_module("module")["FILENAME"], "replacement",
        )

        self.collection.save_module("module")
        removed = self.collection.remove_module("module")
        self.assertEqual(removed["FILENAME"], "replacement")
        self.assertEqual(self.collection.modules, {})
        self.assertEqual(self.collection.manifest["modules"], [])
        removed["REF_SIGNAL"].iloc[0, 0] = -999.0
        pd.testing.assert_frame_equal(
            replacement["REF_SIGNAL"], self.module["REF_SIGNAL"],
        )
        with self.assertRaises(KeyError):
            self.collection.remove_module("missing")
        self.collection.add_module(self.module, "unsaved")
        self.collection.remove_module("unsaved")
        self.assertEqual(self.collection.modules, {})

    def test_save_module(self):
        """
        Save one module and optionally persist its collection manifest entry.
        """

        with self.assertRaisesRegex(ValueError, "not found"):
            self.collection.save_module("missing")
        self.collection.add_module(self.module, "module")
        self.collection.save_module(
            "module", filename="custom", compresslevel=1,
            add_checksum=True, save_updated_manifest=False,
        )
        self.assertFalse(self.collection.manifest_path.exists())
        self.assertEqual(self.collection.manifest["modules"], ["module"])
        module_manifest = json.loads(
            (self.root / "module" / "manifest.json").read_text(),
        )
        self.assertEqual(module_manifest["REF_SIGNAL"]["compression"], "gzip")
        self.assertIsNotNone(module_manifest["REF_SIGNAL"]["checksum"])
        restored = load_openhdemg_module(
            self.root, "module", verify_checksum=True,
        )
        self.assertEqual(restored["FILENAME"], "custom")

        self.collection.save_module("module")
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertEqual(manifest["modules"], ["module"])
        restored = load_openhdemg_module(self.root, "module")
        self.assertEqual(restored["FILENAME"], self.module["FILENAME"])

    def test_save_shared_dataframe(self):
        """
        Save shared data and control when its manifest entry reaches disk.
        """

        with self.assertWarnsRegex(UserWarning, "No shared_dataframe"):
            self.collection.save_shared_dataframe()
        self.assertIsNone(self.collection.manifest["shared_dataframe"])
        self.collection.set_shared_dataframe("invalid")
        with self.assertRaisesRegex(ValueError, "must be a pd.DataFrame"):
            self.collection.save_shared_dataframe()

        self.collection.set_shared_dataframe(self.shared)
        self.collection.save_shared_dataframe(
            compresslevel=1, add_checksum=True, save_updated_manifest=False,
        )
        self.assertFalse(self.collection.manifest_path.exists())
        info = self.collection.manifest["shared_dataframe"]
        self.assertTrue((self.root / info["data_file_path"]).is_file())
        self.assertEqual(info["compression"], "gzip")
        self.assertIsNotNone(info["checksum"])
        self.collection.save_shared_dataframe()
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertEqual(
            manifest["shared_dataframe"],
            self.collection.manifest["shared_dataframe"],
        )
        self.assertIsNone(manifest["shared_dataframe"]["compression"])
        self.assertIsNone(manifest["shared_dataframe"]["checksum"])

    def test_save_manifest(self):
        """
        Persist collection descriptions and update editing metadata.
        """

        created = self.collection.manifest["_metadata"]["created"]
        self.collection.set_participant_info(self.participant)
        self.collection.save_manifest()
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertEqual(manifest, self.collection.manifest)
        self.assertEqual(
            manifest["participant_info"]["value"], self.participant,
        )
        self.assertEqual(manifest["_metadata"]["created"], created)
        self.assertIsNotNone(manifest["_metadata"]["edited"])

    def test_save_manifest_after_participant_reset(self):
        """
        Do not retain participant information after it has been reset.
        """

        self.collection.set_participant_info(self.participant)
        self.collection.save_manifest()
        self.collection.reset_participant_info()
        self.collection.save_manifest()
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertIsNone(manifest["participant_info"])

    def test_save(self):
        """
        Forward save options, overwrite collections and protect other folders.
        """

        with self.assertRaisesRegex(ValueError, "No modules"):
            self.collection.save()
        self.collection.add_module(self.module, "first")
        self.collection.add_module(deepcopy(self.module), "second")
        self.collection.set_shared_dataframe(self.shared)
        for update_filename, level, checksum in (
            (False, None, False), (True, 1, True),
        ):
            with self.subTest(update_filename=update_filename):
                self.collection.save(
                    update_filename=update_filename,
                    compresslevel=level, add_checksum=checksum,
                )
                self.assertTrue(self.collection.marker_path.is_file())
                manifest = json.loads(
                    self.collection.manifest_path.read_text(),
                )
                self.assertEqual(manifest["modules"], ["first", "second"])
                for name in manifest["modules"]:
                    saved = json.loads(
                        (self.root / name / "manifest.json").read_text(),
                    )
                    self.assertEqual(
                        saved["FILENAME"]["text"],
                        name if update_filename else self.module["FILENAME"],
                    )
                    self.assertEqual(
                        saved["REF_SIGNAL"]["compression"],
                        "gzip" if level is not None else None,
                    )
                    self.assertEqual(
                        saved["REF_SIGNAL"]["checksum"] is not None, checksum,
                    )
                self.assertEqual(
                    manifest["shared_dataframe"]["compression"],
                    "gzip" if level is not None else None,
                )
                self.assertEqual(
                    manifest["shared_dataframe"]["checksum"] is not None,
                    checksum,
                )

        self.collection.remove_module("second")
        self.collection.save()
        self.assertFalse((self.root / "second").exists())
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertEqual(manifest["modules"], ["first"])

        unrelated = self.root / "unrelated"
        unrelated.mkdir()
        notes = unrelated / "notes.txt"
        notes.write_text("keep this file")
        self.collection.set_root(unrelated)
        with self.assertRaisesRegex(RuntimeError, "Unsafe or unknown folder"):
            self.collection.save()
        self.assertEqual(notes.read_text(), "keep this file")

    def test_save_after_shared_dataframe_reset(self):
        """
        Remove the shared-data manifest entry when saving after a reset.
        """

        self.collection.add_module(self.module, "module")
        self.collection.set_shared_dataframe(self.shared)
        self.collection.save()
        self.collection.reset_shared_dataframe()
        self.collection.save()
        manifest = json.loads(self.collection.manifest_path.read_text())
        self.assertIsNone(manifest["shared_dataframe"])
        self.assertFalse((self.root / "shared_dataframe.bin").exists())

    def test_asksave(self):
        """
        Save to the selected directory using the requested options.
        """

        self.collection.add_module(self.module, "module")
        self.collection.set_shared_dataframe(self.shared)
        selected = self.root / "selected"
        parent = object()
        with patch(
            "openhdemg.library.openfiles.run_custom_directory_dialog",
            return_value=str(selected),
        ) as dialog:
            self.collection.asksave(
                update_filename=False, compresslevel=1,
                add_checksum=True, gui_parent=parent,
            )
        dialog.assert_called_once_with(
            window_title=(
                "Select or create a folder to contain the saved collection"
            ),
            parent=parent,
        )
        self.assertEqual(self.collection.root, selected)
        restored = load_openhdemg_module(
            selected, "module", verify_checksum=True,
        )
        self.assertEqual(restored["FILENAME"], self.module["FILENAME"])
        saved = json.loads((selected / "module" / "manifest.json").read_text())
        self.assertEqual(saved["REF_SIGNAL"]["compression"], "gzip")
        self.assertIsNotNone(saved["REF_SIGNAL"]["checksum"])

    def test_asksave_cancelled(self):
        """
        Cancelling directory selection leaves the collection untouched.
        """

        with patch(
            "openhdemg.library.openfiles.run_custom_directory_dialog",
            return_value=None,
        ):
            self.assertIsNone(self.collection.asksave())
        self.assertEqual(self.collection.root, self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_load_manifest(self):
        """
        Require a saved manifest and return an independent copy of it.
        """

        with self.assertRaises(FileNotFoundError):
            self.collection.load_manifest()
        self.collection.set_participant_info(self.participant)
        self.collection.save_manifest()
        restored = openhdemg_Collection()
        restored.set_root(self.root)
        manifest = restored.load_manifest()
        self.assertEqual(manifest, self.collection.manifest)
        manifest["modules"].append("changed")
        manifest["participant_info"]["value"]["session"]["label"] = "changed"
        self.assertEqual(restored.manifest, self.collection.manifest)
        self.assertEqual(restored.get_participant_info(), self.participant)

    def test_load_module(self):
        """
        Load only requested modules, with optional metadata and checksums.
        """

        self.collection.add_module(self.module, "first")
        self.collection.add_module(deepcopy(self.module), "second")
        self.collection.save_module("first", add_checksum=True)
        self.collection.save_module("second", filename="second")
        restored = openhdemg_Collection()
        restored.set_root(self.root)
        with self.assertRaisesRegex(ValueError, "No module detected"):
            restored.load_module("first")
        restored.load_manifest()
        with self.assertRaisesRegex(ValueError, "not listed"):
            restored.load_module("missing")

        first = restored.load_module("first", verify_checksum=True)
        self.assertEqual(set(restored.modules), {"first"})
        self.assertEqual(first["FILENAME"], self.module["FILENAME"])
        second, metadata = restored.load_module("second", return_metadata=True)
        self.assertEqual(second["FILENAME"], "second")
        self.assertEqual(set(restored.modules), {"first", "second"})
        second_manifest = json.loads(
            (self.root / "second" / "manifest.json").read_text(),
        )
        self.assertEqual(metadata, second_manifest["_metadata"])

        path = self.root / "first" / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["REF_SIGNAL"]["checksum"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            restored.load_module("first", verify_checksum=True)
        self.assertIsInstance(
            restored.load_module("first", verify_checksum=False), dict,
        )
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            restored.load_module("first")

    def test_load_shared_dataframe(self):
        """
        Read shared data independently, including its own checksum checks.
        """

        with self.assertWarnsRegex(UserWarning, "No 'shared_dataframe'"):
            self.assertIsNone(self.collection.load_shared_dataframe())
        del self.collection.manifest["shared_dataframe"]
        with self.assertRaisesRegex(ValueError, "No 'shared_dataframe' key"):
            self.collection.load_shared_dataframe()

        self.collection.set_shared_dataframe(self.shared)
        restored = openhdemg_Collection()
        restored.set_root(self.root)
        for level, checksum in ((None, True), (1, False)):
            with self.subTest(compresslevel=level, add_checksum=checksum):
                self.collection.save_shared_dataframe(
                    compresslevel=level, add_checksum=checksum,
                )
                restored.load_manifest()
                result = restored.load_shared_dataframe(verify_checksum=True)
                pd.testing.assert_frame_equal(
                    result, self.shared, check_exact=True,
                )
                result.iloc[0, 0] = -1.0
                pd.testing.assert_frame_equal(
                    restored.get_shared_dataframe(), self.shared,
                )

        self.collection.save_shared_dataframe(add_checksum=True)
        restored.load_manifest()
        binary_path = self.root / "shared_dataframe.bin"
        with binary_path.open("r+b") as binary:
            first_byte = binary.read(1)
            binary.seek(0)
            binary.write(bytes([first_byte[0] ^ 1]))
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            restored.load_shared_dataframe(verify_checksum=True)
        result = restored.load_shared_dataframe(verify_checksum=False)
        self.assertNotEqual(result.iloc[0, 0], self.shared.iloc[0, 0])
        binary_path.unlink()
        with self.assertRaises(FileNotFoundError):
            restored.load_shared_dataframe()

    def test_shared_dataframe_mixed_dtypes(self):
        """
        Preserve each shared column's values and numeric dtype on save/load.
        """

        shared = pd.DataFrame({
            "sample": pd.Series([0, 1], dtype="int64"),
            "force": pd.Series([-0.5, 1.25], dtype="float32"),
            "time": pd.Series([0.1, 0.2], dtype="float64"),
        })
        self.collection.set_shared_dataframe(shared)
        self.collection.save_shared_dataframe()

        restored = openhdemg_Collection()
        restored.set_root(self.root)
        restored.load_manifest()
        result = restored.load_shared_dataframe()
        pd.testing.assert_frame_equal(result, shared, check_exact=True)

    def test_load(self):
        """
        Validate collection paths and forward checksum verification.
        """

        self.collection.set_root(self.root / "missing")
        with self.assertRaises(FileNotFoundError):
            self.collection.load()
        self.collection.set_root(self.root)
        with self.assertRaises(FileNotFoundError):
            self.collection.load()
        self.collection.add_module(self.module, "module")
        self.collection.set_shared_dataframe(self.shared)
        self.collection.save(add_checksum=True)
        self.collection.marker_path.unlink()
        with self.assertRaisesRegex(RuntimeError, "not a valid"):
            self.collection.load()
        self.collection.marker_path.touch()

        self.collection.manifest["shared_dataframe"]["checksum"] = "invalid"
        self.collection.save_manifest()
        restored = openhdemg_Collection()
        restored.set_root(self.root)
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            restored.load(verify_checksum=True)
        restored.load(verify_checksum=False)
        self.assertEqual(set(restored.modules), {"module"})
        pd.testing.assert_frame_equal(
            restored.get_shared_dataframe(), self.shared,
        )

    def test_load_replaces_previous_state(self):
        """
        Loading another collection must not retain old modules or shared data.
        """

        self.collection.add_module(self.module, "current")
        self.collection.save()
        restored = openhdemg_Collection()
        restored.set_root(self.root)
        restored.add_module(self.module, "previous")
        restored.set_shared_dataframe(self.shared)
        restored.set_participant_info(self.participant)
        with self.assertWarnsRegex(UserWarning, "No 'shared_dataframe'"):
            restored.load()
        with self.subTest(field="modules"):
            self.assertEqual(set(restored.modules), {"current"})
        with self.subTest(field="shared_dataframe"):
            self.assertIsNone(restored.get_shared_dataframe())
        self.assertIsNone(restored.get_participant_info())

    def test_askload(self):
        """
        Load the selected collection and honour checksum verification.
        """

        self.collection.add_module(self.module, "module")
        self.collection.set_shared_dataframe(self.shared)
        self.collection.set_participant_info(self.participant)
        self.collection.save(add_checksum=True)
        restored = openhdemg_Collection()
        parent = object()
        with patch(
            "openhdemg.library.openfiles.run_custom_directory_dialog",
            return_value=str(self.root),
        ) as dialog:
            restored.askload(verify_checksum=True, gui_parent=parent)
            dialog.assert_called_once_with(
                window_title="Select the collection folder to load",
                parent=parent,
            )
            self.assertEqual(restored.root, self.root)
            self.assertEqual(set(restored.modules), {"module"})
            self.assertEqual(restored.get_participant_info(), self.participant)
            pd.testing.assert_frame_equal(
                restored.get_shared_dataframe(), self.shared,
            )

            self.collection.manifest["shared_dataframe"]["checksum"] = (
                "invalid"
            )
            self.collection.save_manifest()
            with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                restored.askload(verify_checksum=True)
            restored.askload(verify_checksum=False)

    def test_askload_cancelled(self):
        """
        Cancelling directory selection leaves the current collection intact.
        """

        self.collection.add_module(self.module, "module")
        with patch(
            "openhdemg.library.openfiles.run_custom_directory_dialog",
            return_value=None,
        ):
            self.assertIsNone(self.collection.askload())
        self.assertEqual(self.collection.root, self.root)
        self.assertEqual(set(self.collection.modules), {"module"})

    def test_root_required(self):
        """
        All direct persistence methods require a root before doing I/O.
        """

        collection = openhdemg_Collection()
        for method, args in (
            (collection.save_module, ("module",)),
            (collection.save_shared_dataframe, ()),
            (collection.save_manifest, ()),
            (collection.save, ()),
            (collection.load_manifest, ()),
            (collection.load_module, ("module",)),
            (collection.load_shared_dataframe, ()),
            (collection.load, ()),
        ):
            with self.subTest(method=method.__name__):
                with self.assertRaisesRegex(ValueError, "'root' not set"):
                    method(*args)


if __name__ == '__main__':
    unittest.main()
