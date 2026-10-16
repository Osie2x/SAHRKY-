import unittest

from sharktank.data import validate_row, validate_rows
from sharktank.scoring import brier_score


def example(**changes):
    # Synthetic fixture, not a historical pitch or a measured model prediction.
    row = {
        "Pitch Number": "1",
        "Season Number": "2",
        "Episode Number": "3",
        "Startup Name": "Synthetic Example",
        "Industry": "Food and Beverage",
        "Original Ask Amount": "100000",
        "Original Offered Equity": "10",
        "Got Deal": "1",
    }
    row.update(changes)
    return row


class ScoringTests(unittest.TestCase):
    def test_known_probability_losses(self):
        for probability, outcome, expected in [
            (1, 1, 0),
            (0, 0, 0),
            (1, 0, 1),
            (0, 1, 1),
            (0.5, 1, 0.25),
            (0.75, 1, 0.0625),
        ]:
            with self.subTest(probability=probability, outcome=outcome):
                self.assertAlmostEqual(brier_score(probability, outcome), expected)

    def test_overconfident_mistake_costs_more(self):
        self.assertGreater(brier_score(0.99, 0), brier_score(0.6, 0))
        self.assertAlmostEqual(brier_score(0.8, 1), brier_score(0.2, 0))

    def test_invalid_probabilities(self):
        for invalid in [
            -0.1,
            1.1,
            75,
            10**400,
            float("nan"),
            float("inf"),
            -float("inf"),
            True,
            "0.5",
            None,
        ]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                brier_score(invalid, 1)

    def test_invalid_outcomes(self):
        for invalid in [-1, 2, 0.5, 1.0, True, "1", None]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                brier_score(0.5, invalid)


class DataTests(unittest.TestCase):
    def test_valid_fields_are_typed(self):
        pitch = validate_row(example())
        self.assertEqual(pitch.pitch.ask_amount_usd, 100000)
        self.assertEqual(pitch.pitch.season, 2)
        self.assertEqual(pitch.got_deal, 1)

    def test_outcome_columns_never_reach_pre_reveal(self):
        a = validate_row(
            example(**{"Total Deal Amount": "999999", "Guest Name": "WINNER"})
        )
        b = validate_row(
            example(
                **{
                    "Got Deal": "0",
                    "Total Deal Amount": "0",
                    "Future Secret Column": "outcome information",
                }
            )
        )
        self.assertEqual(a.pre_reveal(), b.pre_reveal())
        self.assertNotIn("got_deal", a.pre_reveal())
        self.assertNotIn("Total Deal Amount", a.pre_reveal())

    def test_missing_outcome_is_quarantined_instead_of_becoming_no_deal(self):
        accepted, rejected = validate_rows([example(**{"Got Deal": ""}), example()])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].got_deal, 1)
        self.assertEqual(rejected[0]["csv_line"], 2)
        self.assertIn("Got Deal", rejected[0]["reason"])

    def test_bad_ranges_and_missing_fields(self):
        for field, invalids in {
            "Original Ask Amount": ["", "0", "-1", "NaN", "inf"],
            "Original Offered Equity": ["0", "101", "NaN"],
            "Season Number": ["0", "1.5"],
            "Episode Number": ["-1"],
            "Pitch Number": ["0"],
            "Startup Name": ["  "],
            "Got Deal": ["yes", "2"],
        }.items():
            for value in invalids:
                with (
                    self.subTest(field=field, value=value),
                    self.assertRaises(ValueError),
                ):
                    validate_row(example(**{field: value}))
        row = example()
        del row["Industry"]
        with self.assertRaises(ValueError):
            validate_row(row)

    def test_duplicate_ids_are_rejected_after_first_valid_occurrence(self):
        accepted, rejected = validate_rows([example(), example()])
        self.assertEqual(len(accepted), 1)
        self.assertIn("duplicate ID", rejected[0]["reason"])

    def test_repeat_company_with_distinct_pitch_is_preserved(self):
        accepted, rejected = validate_rows(
            [example(), example(**{"Pitch Number": "2"})]
        )
        self.assertEqual(len(accepted), 2)
        self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
