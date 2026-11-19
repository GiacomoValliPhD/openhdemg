"""Collection tests using real files and the existing module fixture."""

import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from openhdemg.library.openfiles import (
    load_openhdemg_module, openhdemg_Collection,
)
from openhdemg.tests.unit.functions_for_unit_test import get_module_fixture


class TestCollectionRoundTrip(unittest.TestCase):
    """
    Build collections during the tests and check their saved contents.

    Only the module fixture is permanent. Collections and their files are
    created in temporary directories and removed when each test finishes.
    """

    def test_save_load_collection(self):
        """
        Restore two distinct modules, shared data and participant information.
        """

        module = get_module_fixture()
        first = load_openhdemg_module(
            module.parent, module.name, verify_checksum=True,
        )
        second = deepcopy(first)
        second["REF_SIGNAL"] = second["REF_SIGNAL"] + 1.0
        shared = pd.DataFrame({
            "reference_1": first["REF_SIGNAL"].iloc[:, 0],
            "reference_2": second["REF_SIGNAL"].iloc[:, 0],
        })
        participant = {"participant_id": "TEST_001", "notes": "Artificial"}

        with TemporaryDirectory() as directory:
            root = Path(directory) / "collection"
            collection = openhdemg_Collection()
            collection.set_root(root)
            collection.add_module(first, "module_1")
            collection.add_module(second, "module_2")
            collection.set_shared_dataframe(shared)
            collection.set_participant_info(participant)
            collection.save(add_checksum=True)

            restored = openhdemg_Collection()
            restored.set_root(root)
            restored.load(verify_checksum=True)

            self.assertEqual(set(restored.modules), {"module_1", "module_2"})
            for name, expected in (("module_1", first), ("module_2", second)):
                self.assertEqual(restored.modules[name]["FILENAME"], name)
                pd.testing.assert_frame_equal(
                    restored.modules[name]["REF_SIGNAL"],
                    expected["REF_SIGNAL"], check_exact=True,
                )
            pd.testing.assert_frame_equal(
                restored.get_shared_dataframe(), shared, check_exact=True,
            )
            self.assertEqual(restored.get_participant_info(), participant)

    def test_load_manifest_participant_info(self):
        """
        Restore participant information and clear old values when absent.
        """

        with TemporaryDirectory() as directory:
            restored = openhdemg_Collection()
            restored.set_root(directory)
            restored.set_participant_info({"participant_id": "PREVIOUS"})

            for participant in ({"participant_id": "TEST_001"}, None):
                with self.subTest(participant=participant):
                    collection = openhdemg_Collection()
                    collection.set_root(directory)
                    if participant is not None:
                        collection.set_participant_info(participant)
                    collection.save_manifest()

                    manifest = restored.load_manifest()
                    self.assertEqual(manifest, collection.manifest)
                    self.assertEqual(
                        restored.get_participant_info(), participant,
                    )


if __name__ == "__main__":
    unittest.main()
