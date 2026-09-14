"""Compare regenerated outputs of two clones: byte-identical except PDF timestamps."""
import hashlib, re, sys
from pathlib import Path
import numpy as np
base, new = Path(sys.argv[1]), Path(sys.argv[2])
def norm(p):
    b = p.read_bytes()
    if p.suffix == ".pdf":
        b = re.sub(rb"/(CreationDate|ModDate) \([^)]*\)", b"", b)
    return hashlib.sha256(b).hexdigest()
files = sorted(str(p.relative_to(base)) for p in (base / "data").rglob("*") if p.is_file() and not p.name.startswith("."))
same, diff, missing = [], [], []
for f in files:
    q = new / f
    if not q.exists(): missing.append(f); continue
    if f.endswith(".npz"):
        a, b = np.load(base / f), np.load(q)
        ok = set(a.files) == set(b.files) and all(np.array_equal(a[k], b[k]) for k in a.files)
        (same if ok else diff).append(f + f"  [{len(a.files)} arrays, per-array]")
    else:
        (same if norm(base / f) == norm(q) else diff).append(f)
print(f"{len(same)} identical, {len(diff)} different, {len(missing)} missing in new")
for f in diff: print("DIFF   ", f)
for f in missing: print("MISSING", f)
sys.exit(1 if diff or missing else 0)
