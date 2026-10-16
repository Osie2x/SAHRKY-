# First slice: score a prediction without giving away the answer

This guide was prepared with Codex assistance. Reading it or passing agent-run
tests does not establish independent understanding.

## The problem and the user

A player sees a pitch and predicts a probability of a deal. The game must keep the
real outcome hidden until the player commits. A score should penalize a confident
wrong guess more heavily than a cautious wrong guess.

A Python dictionary maps names to values. A source CSV is a table whose rows arrive
as dictionaries of strings. The validator turns selected strings into numbers and
rejects missing or invalid values. A dataclass groups named Python fields; frozen
dataclasses prevent accidentally assigning new field values after construction.

## Follow one piece of data

1. `sharktank/audit.py`, `audit_archive`, verifies the exact source bytes against
   `data/manifest.json`. A SHA-256 checksum is a fingerprint of bytes; it detects a
   changed download but cannot prove that the historical facts are correct.
2. `sharktank/data.py`, `validate_row`, checks the label is exactly `0` or `1`,
   checks positive identifiers, and accepts only finite positive ask/equity values.
   Equity cannot exceed 100 percent. Amounts are numerical features, not payment
   calculations; this version uses floats rather than a money-accounting type.
3. `LabeledPitch` keeps `pitch` and `got_deal` separate. `pre_reveal()` constructs
   a dictionary from `Pitch` only. It never serializes the whole labelled record.
   A future API must explicitly use this representation and test its response too.
4. `validate_rows` returns accepted rows plus quarantine reasons and source line
   numbers. The first valid occurrence of a pitch ID is kept; later duplicate IDs
   are rejected. A repeated company with a different pitch ID is preserved.
5. After an outcome reveal, `sharktank/scoring.py`, `brier_score`, compares the
   predicted probability with the recorded integer outcome.

## Why these decisions?

**Brier loss instead of correct/incorrect only:** loss uses the confidence level.
With outcome `1`, a prediction of `0.75` loses `(0.75 - 1)^2 = 0.0625`.
A 50% prediction loses `0.25` regardless of the binary outcome. One correct guess
does not prove good calibration; that requires many predictions and evaluation.

**An explicit field list instead of removing known secret columns:** a source
update might add a new outcome-derived field. Removing only today's known fields
could expose tomorrow's new one. Selecting seven known public fields prevents
unknown columns from passing through automatically. A model needs a separate
feature policy; visible startup names can still enable memorization.

**Quarantine instead of filling blanks with zero:** in the real version-34 data,
four outcomes are blank. Treating those as zero would create four invented labels.
The audit also reports four missing ask and equity values, even though each row's
first quarantine reason is its missing outcome.

**Small standard-library modules instead of starting with a framework:** scoring
and data rules can be tested without HTTP, a database or a frontend. Those later
layers should call these same rules rather than reimplement them.

## Evidence and limitations

The [recorded data audit](../reports/dataset-audit-2026-10-16.json) processed 1,485
rows and accepted 1,481. The count is a validation result, not a factual accuracy
claim. Unit tests cover bad numbers, loss boundaries, outcome hiding, duplicate
identifiers, missing labels, source schema failure and modified archives. They use
synthetic fixtures; the real-data audit is a separate local execution. CI runs the
synthetic tests without downloading the dataset.

No ML model, latency benchmark, user trial or deployment has been completed here.
Do not claim prediction accuracy, training, real users or a working website.

## Your review

First explain what `probability`, `outcome` and `got_deal` mean without looking.
Then run the small scoring example and locate the exact pre-reveal field list.

**Interview question:** Why would using final deal equity as an input make a deal
prediction model look better during testing but fail its actual purpose?

**Independent exercise:** Before running code, calculate the Brier loss for a
60% deal prediction when no deal happens. Then add your own test for that case.
Explain why a 99% deal prediction should receive a worse score for the same outcome.
Attempt this before asking for the worked answer.

Allow 15-20 minutes on an available day, or combine this with the PolicyLens
walkthrough during a 45-60 minute weekend review. The next project subsystem waits
for your explanation and exercise attempt.
