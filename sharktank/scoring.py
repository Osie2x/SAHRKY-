"""Brier loss for one binary prediction: lower is better."""

import math
from numbers import Real


def brier_score(probability: float, outcome: int) -> float:
    """Score a probability of a deal against its recorded 0/1 outcome.

    Reject percentages such as 75, missing values, booleans and non-finite numbers.
    An observed on-show deal is not proof a transaction closed after filming.
    """
    if isinstance(probability, bool) or not isinstance(probability, Real):
        raise ValueError("probability must be a number between 0 and 1")
    if not 0 <= probability <= 1 or not math.isfinite(probability):
        raise ValueError("probability must be finite and between 0 and 1")
    if type(outcome) is not int or outcome not in (0, 1):
        raise ValueError("outcome must be integer 0 or 1")
    return (float(probability) - outcome) ** 2
