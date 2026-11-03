"""PV-D02: hold docs/figure-manifest.json to the tree, and the tree to the manifest.

The manifest is what docs/data-and-figures.md calls the machine-readable companion, and it is what
an external regeneration audit runs from. Until now nothing checked it: an output could be deleted,
a generator renamed, or a new figure committed, without any test noticing. These checks make the
manifest a gate rather than a description. They do not run the generators.
"""
import json, re, subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "figure-manifest.json"
FIGURE_ROOTS = ("data/gate0", "data/sim")
FIGURE_SUFFIXES = (".png", ".pdf", ".svg")
REQUIRED_KEYS = {"id", "evidence_type", "generator", "command", "inputs", "outputs", "boundary", "numeric"}
EVIDENCE_TYPES = {"simulation", "measurement", "hand_authored", "mixed"}


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


@pytest.fixture(scope="module")
def tracked():
    # Inputs also live outside FIGURE_ROOTS. A filesystem fallback cannot prove
    # the commitment requirement and would silently accept local-only inputs.
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, "manifest commitment checks require a Git checkout"
    return set(filter(None, out.stdout.split("\0")))


def modules_in(command: str):
    return re.findall(r"python -m ([\w.]+)", command)


def test_every_entry_has_the_required_keys_and_a_unique_id(manifest):
    ids = [f["id"] for f in manifest["figures"]]
    assert len(ids) == len(set(ids)), "duplicate figure ids"
    for f in manifest["figures"]:
        missing = REQUIRED_KEYS - set(f)
        assert not missing, f"{f.get('id')}: missing {sorted(missing)}"
        assert f["evidence_type"] in EVIDENCE_TYPES, f"{f['id']}: evidence_type {f['evidence_type']!r}"
        assert f["outputs"], f"{f['id']}: declares no outputs"


MATLAB_RENDER = "matlab -batch \"addpath('figures/matlab'); render_figures\""


def test_generators_and_command_modules_exist(manifest):
    for f in manifest["figures"]:
        assert (ROOT / f["generator"]).is_file(), f"{f['id']}: generator {f['generator']} not in tree"
        mods = modules_in(f["command"])
        assert mods, f"{f['id']}: command has no `python -m` module"
        for m in mods:
            assert (ROOT / (m.replace(".", "/") + ".py")).is_file(), f"{f['id']}: module {m} does not resolve"
        python_generator = f["generator"]
        if f["generator"].endswith(".m"):
            # MATLAB draws the image from what the Python data generator writes, so the command must run both.
            assert f["command"].endswith(MATLAB_RENDER), f"{f['id']}: command does not end with the MATLAB render"
            assert f["generator"] in f["inputs"], f"{f['id']}: MATLAB generator not listed as an input"
            python_generator = f["data_generator"]
        assert python_generator == mods[-1].replace(".", "/") + ".py", f"{f['id']}: generator is not the last command module"


def test_every_declared_output_is_committed(manifest, tracked):
    # `git ls-files` reports tracked paths whether or not they exist on disk, so check both:
    # a deleted-but-still-tracked output would otherwise pass silently.
    untracked = [o for f in manifest["figures"] for o in f["outputs"] if o not in tracked]
    absent = [o for f in manifest["figures"] for o in f["outputs"] if not (ROOT / o).is_file()]
    assert not untracked, f"declared outputs not tracked: {untracked}"
    assert not absent, f"declared outputs missing from disk: {absent}"


def test_every_committed_figure_is_declared(manifest, tracked):
    declared = {o for f in manifest["figures"] for o in f["outputs"]}
    undeclared = sorted(t for t in tracked if t.startswith(tuple(r + "/" for r in FIGURE_ROOTS))
                        and t.endswith(FIGURE_SUFFIXES) and t not in declared)
    assert not undeclared, f"committed figures with no manifest entry (unauditable): {undeclared}"


def test_numeric_sources_exist_and_parse(manifest):
    for f in manifest["figures"]:
        p = ROOT / f["numeric"]
        assert p.is_file(), f"{f['id']}: numeric source {f['numeric']} missing"
        json.loads(p.read_text())


def test_inputs_are_committed_or_declared_generated(manifest, tracked):
    gen = manifest.get("generated_inputs", {})
    for f in manifest["figures"]:
        for i in f["inputs"]:
            if i not in gen:
                assert i in tracked, f"{f['id']}: input {i} is neither tracked nor declared under generated_inputs"
                assert (ROOT / i).is_file(), f"{f['id']}: committed input {i} is missing from disk"
                continue
            # A previous local regeneration must not disable provenance checks.
            assert gen[i]["command"] in f["command"], (
                f"{f['id']}: consumes generated input {i} but its command does not run {gen[i]['command']!r} first")
            assert f["id"] in gen[i]["consumers"], f"{f['id']}: not listed as a consumer of {i}"


def test_generated_inputs_are_not_silently_committed(manifest, tracked):
    # If one of these ever lands in the tree, the declaration is stale and the manifest must say so.
    for i in manifest.get("generated_inputs", {}):
        assert i not in tracked, f"{i} is declared generated-not-committed but is tracked; update the manifest"
