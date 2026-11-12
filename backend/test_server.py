import os
import unittest
from pathlib import Path

from server import GRID_VERSION, TERRITORY_ID, M2Store, ScopeError


class M2StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = M2Store(Path(os.environ["RECONNECT_M2_ZIP"]))

    def test_counts_and_science(self):
        self.assertEqual(len(self.store.minimal_grid()["features"]), 101)
        metadata = self.store.metadata()
        self.assertEqual(metadata["events_admitted"], 5336)
        self.assertEqual(metadata["cell_event_relations"], 5759)
        self.assertEqual(metadata["validated_recommendations"], 0)
        self.assertEqual(sum(metadata["documentary_leads"].values()), 165)

    def test_documentary_counts(self):
        levels = {}
        for feature in self.store.minimal_grid()["features"]:
            level = feature["properties"]["documentary_level"]
            levels[level] = levels.get(level, 0) + 1
            self.assertEqual(feature["properties"]["priority_category"], "INDETERMINATE")
        self.assertEqual(levels, {"rouge": 27, "orange": 33, "jaune": 9, "gris": 32})

    def test_composite_scope_and_sanitized_cell(self):
        cell_id = self.store.minimal_grid()["features"][0]["properties"]["maille_id"]
        cell = self.store.cell(cell_id, TERRITORY_ID, GRID_VERSION)
        self.assertNotIn("conflit_ids", cell)
        self.assertEqual(len(cell["investigations"]), 4)
        self.assertTrue(all(item["status"] == "non_evaluable" for item in cell["investigations"]))
        with self.assertRaises(ScopeError):
            self.store.cell(cell_id, TERRITORY_ID, "wrong-grid")


if __name__ == "__main__":
    unittest.main()
