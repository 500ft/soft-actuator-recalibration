"""The PDF-rendering route must be explicit, protected and hash-bound.

Historical docs/preprint_v1.pdf is the archived v1.3 release pinned by SHA-256 in
docs/publication-readiness.json. Before this route existed, `python -m scripts.make_preprint_pdf`
overwrote it with different bytes (verified 2026-09-12: 6a6681fe... -> c734259a...). These tests
hold the new contract: explicit paths, refusal to touch the archive, manifest with matching hashes,
and no author-approval claim anywhere in the output.
"""
import hashlib, json, os, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import make_preprint_pdf as R  # noqa: E402
from scripts import check_pdf_arxiv as G    # noqa: E402

HIST = ROOT / "docs/preprint_v1.pdf"
CAND = ROOT / "docs/preprint_v1_4_candidate.md"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
PINNED = json.loads((ROOT / "docs/publication-readiness.json").read_text())["historical_pdf_sha256"]


class RendererRouteTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(sha(HIST), PINNED, "historical PDF must match its pin before these tests run")

    def test_refuses_to_overwrite_historical_pdf(self):
        with self.assertRaises(R.ProtectedOutputError):
            R.build(str(CAND), str(HIST))
        self.assertEqual(sha(HIST), PINNED)

    def test_refuses_without_explicit_output(self):
        with self.assertRaises(R.ProtectedOutputError):
            R.build(str(CAND), None)

    def test_cli_refusal_exit_code_is_2(self):
        p = subprocess.run([sys.executable, "-m", "scripts.make_preprint_pdf", "--source", str(CAND), "--output", str(HIST)],
                           cwd=ROOT, capture_output=True, text=True, env={**os.environ, "MPLBACKEND": "Agg"})
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("REFUSED", p.stdout)
        self.assertEqual(sha(HIST), PINNED)

    def test_candidate_renders_with_matching_manifest_and_passes_arxiv_gate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "candidate.pdf"
            rec = R.build(str(CAND), str(out))
            self.assertTrue(out.is_file() and out.stat().st_size > 10_000)
            man = json.loads((Path(d) / "candidate.manifest.json").read_text())
            self.assertEqual(man["output_sha256"], sha(out))
            self.assertEqual(man["source_sha256"], sha(CAND))
            self.assertEqual(man["source_sha256"], json.loads((ROOT / "docs/publication-readiness.json").read_text())["candidate_manuscript_sha256"],
                             "candidate manuscript on disk must be the one the readiness record pins")
            self.assertIsNone(man["author_approval"])
            self.assertEqual(man["historical_pdf_sha256_verified_unchanged"], PINNED)
            self.assertEqual(rec["output_sha256"], man["output_sha256"])
            self.assertEqual(G.main(str(out)), 0, "candidate render must pass the same font-embedding gate as the archive")
        self.assertEqual(sha(HIST), PINNED)

    def test_render_does_not_touch_publication_readiness(self):
        import tempfile
        before = (ROOT / "docs/publication-readiness.json").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            R.build(str(CAND), str(Path(d) / "x.pdf"))
        self.assertEqual((ROOT / "docs/publication-readiness.json").read_bytes(), before)

    def test_arxiv_gate_default_is_still_the_historical_pdf(self):
        self.assertEqual(G.main(), 0)


class DestinationCollisionTests(unittest.TestCase):
    """Review finding 2026-09-12: --manifest was unprotected and --output could equal the source.
    Every destination must be validated against every protected file and alias BEFORE any write,
    and the protected set re-verified AFTER the last write (the manifest)."""
    PROTECTED = [HIST, ROOT / "docs/publication-readiness.json", ROOT / "docs/preprint_v1.md", CAND, ROOT / "docs/results.md"]

    def setUp(self):
        self.before = {p: sha(p) for p in self.PROTECTED}

    def tearDown(self):
        for p, h in self.before.items():
            self.assertEqual(sha(p), h, f"{p.name} changed during a collision test")

    def _refused(self, **kw):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            args = dict(source=str(CAND), output=str(Path(d) / "x.pdf"), manifest=None); args.update(kw)
            with self.assertRaises(R.ProtectedOutputError):
                R.build(args["source"], args["output"], args["manifest"])

    def test_manifest_cannot_be_the_archive(self):
        self._refused(manifest=str(HIST))

    def test_manifest_cannot_be_the_readiness_record(self):
        self._refused(manifest=str(ROOT / "docs/publication-readiness.json"))

    def test_manifest_cannot_be_the_source(self):
        self._refused(manifest=str(CAND))

    def test_output_cannot_be_the_source_or_any_docs_file(self):
        self._refused(output=str(CAND))
        self._refused(output=str(ROOT / "docs/results.md"))
        self._refused(output=str(ROOT / "docs/preprint_v1.md"))

    def test_output_must_be_pdf_and_distinct_from_manifest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(R.ProtectedOutputError):
                R.build(str(CAND), str(Path(d) / "x.txt"))
            with self.assertRaises(R.ProtectedOutputError):
                R.build(str(CAND), str(Path(d) / "x.pdf"), str(Path(d) / "x.pdf"))

    def test_symlink_and_case_aliases_of_the_archive_are_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            link = Path(d) / "alias.pdf"; link.symlink_to(HIST)
            self._refused(manifest=str(link))
            self._refused(output=str(link))
            upper = HIST.with_name(HIST.name.upper())
            if upper.exists():                       # case-insensitive filesystem: the alias is live
                self._refused(manifest=str(upper))

    def test_default_manifest_path_derives_from_pdf_stem(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            rec = R.build(str(CAND), str(Path(d) / "cand.pdf"))
            self.assertTrue((Path(d) / "cand.manifest.json").is_file())
            self.assertEqual(rec["manifest"], os.path.relpath(Path(d) / "cand.manifest.json", ROOT))
            self.assertEqual(rec["readiness_sha256_verified_unchanged"], sha(ROOT / "docs/publication-readiness.json"))


if __name__ == "__main__":
    unittest.main()
