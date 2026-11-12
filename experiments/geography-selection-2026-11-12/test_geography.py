"""Small selection and feasibility examples for the geographic experiment."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from solution.policies import helpers


class GeographyTests(unittest.TestCase):
    def setUp(self):
        self.distances = {
            "HUB": {"HUB": 0, "A": 10, "B": 15, "C": 20},
            "A": {"HUB": 10, "A": 0, "B": 20, "C": 3},
            "B": {"HUB": 15, "A": 20, "B": 0, "C": 25},
            "C": {"HUB": 20, "A": 3, "B": 25, "C": 0},
        }
        self.parcels = {
            "P1": self.parcel("A", 600),
            "P2": self.parcel("B", 610),
            "P3": self.parcel("C", 630),
        }
        self.context = {
            "current_time": 480, "departure_delay": 30, "capacity": 2,
            "travel_distance": self.distances, "return_cutoff": 1080,
            "max_trip_distance_km": 320,
        }

    @staticmethod
    def parcel(location, deadline):
        return {"arrival_time": 480, "delivery_location_id": location,
                "delivery_window_start": 480, "delivery_window_end": deadline,
                "size": 1.0, "vehicle_assigned": None, "trip_id": None,
                "delivery_time": None}

    def build(self, band):
        function = getattr(helpers, "build_anchor_geo_route", None)
        self.assertTrue(callable(function), "Geographic route builder is not implemented")
        return function(self.parcels, self.context, band)

    def test_anchor_stays_urgent_but_nearby_parcel_can_use_second_slot(self):
        self.assertEqual(self.build(30), ["P1", "P3"])

    def test_zero_band_does_not_skip_an_earlier_deadline(self):
        self.assertEqual(self.build(0), ["P1", "P2"])

    def test_geographic_choice_cannot_cross_deadline_band(self):
        self.parcels["P3"]["delivery_window_end"] = 641
        self.assertEqual(self.build(30), ["P1", "P2"])

    def test_unavailable_and_over_capacity_parcels_are_excluded(self):
        self.parcels["P1"]["vehicle_assigned"] = 2
        self.parcels["P2"]["delivery_time"] = 500
        self.parcels["P3"]["size"] = 3
        self.assertEqual(self.build(30), [])

    def test_current_cutoff_and_range_are_hard_constraints(self):
        self.context["return_cutoff"] = 529
        self.assertEqual(self.build(30), [])
        self.context["return_cutoff"] = 1080
        self.context["max_trip_distance_km"] = 19
        self.assertEqual(self.build(30), [])

    def test_inputs_are_not_modified(self):
        before = copy.deepcopy((self.parcels, self.context))
        self.build(30)
        self.assertEqual((self.parcels, self.context), before)


if __name__ == "__main__":
    unittest.main()
