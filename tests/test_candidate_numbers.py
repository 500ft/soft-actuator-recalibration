"""The publication candidate must be checked, not only its historical sibling."""
from pathlib import Path

import pytest

from scripts import check_manuscript_numbers as checker


def test_unchanged_manuscripts_pass():
    checker.main()


@pytest.mark.parametrize("old,new", [("[0.853, 0.950]", "[0.835, 0.958]"), ("60% fewer", "90% fewer")])
def test_candidate_numeric_drift_is_rejected(tmp_path, monkeypatch, old, new):
    candidate = Path(checker.ROOT / "docs/preprint_v1_4_candidate.md").read_text()
    assert old in candidate
    path = tmp_path / "candidate.md"
    path.write_text(candidate.replace(old, new))
    monkeypatch.setattr(checker, "CANDIDATE", path, raising=False)
    with pytest.raises(AssertionError, match="missing manuscript snippet") as error:
        checker.main()
    assert old in str(error.value)
