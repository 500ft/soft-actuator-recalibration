#!/usr/bin/env python3
"""Assert load-bearing manuscript numbers against committed study JSONs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "docs" / "preprint_v1.md"
CANDIDATE = ROOT / "docs" / "preprint_v1_4_candidate.md"
ARXIV_ABSTRACT = ROOT / "docs" / "arxiv_abstract.txt"
STUDY3 = ROOT / "data" / "sim" / "phaseD" / "study3_results.json"
STUDY3_CLUSTER = ROOT / "data" / "sim" / "phaseD" / "study3_cluster_ci_results.json"
STUDY4 = ROOT / "data" / "sim" / "phaseD" / "study4_results.json"

# Documents that also quote the load-bearing correlation interval. Previously only the
# manuscript was gated, which let the secondary docs drift.
SECONDARY_DOCS = (
    ROOT / "docs" / "results.md",
    ROOT / "docs" / "result_spine.md",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(text: str, snippet: str):
    normalized_text = " ".join(text.split())
    normalized_snippet = " ".join(snippet.split())
    normalized_text = normalized_text.replace("*", "")
    normalized_snippet = normalized_snippet.replace("*", "")
    if normalized_snippet not in normalized_text:
        raise AssertionError(f"missing manuscript snippet: {snippet!r}")


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def frontier_point(s3, tau: float):
    points = s3["lead_frontier_heldout"]["points"]
    for point in points:
        if abs(point["tau"] - tau) < 1e-12:
            return point
    raise AssertionError(f"missing frontier tau={tau}")


def check_manuscript(manuscript):
    text = manuscript.read_text(encoding="utf-8")
    s3 = load_json(STUDY3)
    s4 = load_json(STUDY4)

    corr = s3["leading_indicator_corr"]
    cl = load_json(STUDY3_CLUSTER)["correlation"]
    cb, lz = cl["actuator_cluster_bootstrap"], cl["leave_one_actuator_out_fisher_z"]
    # The reported interval is now cluster-based; the point-level interval is retained in the
    # text only as the superseded v1 value, so both are gated against their sources.
    require(text, f"Pearson *r* = {cl['r']:.3f}")
    require(text, f"95% CI [{cb['ci_low']:.3f}, {cb['ci_high']:.3f}]")
    require(text, f"[{lz['ci_low']:.3f}, {lz['ci_high']:.3f}]")
    require(text, f"[{corr['ci_low']:.3f}, {corr['ci_high']:.3f}]")
    require(text, f"{cb['n_resamples']:,} actuator resamples")

    per = s3["per_actuator_r"]
    require(text, f"per-actuator *r* has median {per['median']:.3f} and range [{per['min']:.4f}, {per['max']:.4f}]")

    lead = s3["lead_time_heldout"]
    require(text, f"life {lead['median_trigger_life']:.2f}")
    require(text, f"median {lead['median_budget_violation_life']:.2f}, range "
                  f"{lead['min_budget_violation_life']:.2f}-{lead['max_budget_violation_life']:.2f}")
    require(text, f"median lead = {lead['median_lead_life']:.3f} normalized life")
    require(text, f"range [{lead['min_lead_life']:.3f}, {lead['max_lead_life']:.3f}]")
    require(text, f"{lead['status_counts']['nonpositive_lead']}/6 held-out")
    require(text, "no positive temporal lead")
    require(text, f"{round(lead['min_lead_cycles']):,} to {round(lead['max_lead_cycles']):,} cycles")

    policies = s3["policies_on_heldout"]
    budget = s3["accuracy_budget_mm"]
    tau = s3["tau_selected"]
    period = s3["period_selected_cycles"]
    if manuscript == MANUSCRIPT:
        require(text, f"{budget:.3f} mm accuracy budget")
    else:
        require(text, f"train-derived {budget:.3f} mm budget")
    require(text, f"τ\\*={tau:.2f}")
    require(text, f"*T*\\* = {period:,.0f} cycles")
    for name in ("fixed", "scheduled", "triggered", "always"):
        pol = policies[name]
        require(text, f"{pol['mean_pose_rmse_mm']:.2f} mm")
        recal = pol["recal_per_actuator"]
        recal_str = f"{recal:.1f}".rstrip("0").rstrip(".")
        require(text, f"| {recal_str} |")
    savings = 1.0 - policies["triggered"]["recal_per_actuator"] / policies["always"]["recal_per_actuator"]
    require(text, f"{savings:.0%} fewer recalibrations")

    f005 = frontier_point(s3, 0.005)
    f001 = frontier_point(s3, 0.01)
    f002 = frontier_point(s3, 0.02)
    f0050 = frontier_point(s3, 0.05)
    if f0050["mean_pose_rmse_mm"] != policies["triggered"]["mean_pose_rmse_mm"]:
        raise AssertionError("tau=0.05 frontier error must equal deployed triggered error")
    if f0050["recal_per_actuator"] != policies["triggered"]["recal_per_actuator"]:
        raise AssertionError("tau=0.05 frontier recals must equal deployed triggered recals")
    if f005["mean_pose_rmse_mm"] != policies["always"]["mean_pose_rmse_mm"]:
        raise AssertionError("tau=0.005 frontier error must equal always-on error")
    if f005["recal_per_actuator"] != policies["always"]["recal_per_actuator"]:
        raise AssertionError("tau=0.005 frontier recals must equal always-on recals")
    require(text, f"τ=0.01 triggers at median life {f001['trigger_life_median']:.2f}")
    require(text, f"median lead +{f001['lead_life_median']:.3f} normalized life")
    require(text, f"range +{f001['lead_life_min']:.3f} to +{f001['lead_life_max']:.3f}")
    require(text, f"{f001['recal_per_actuator']:.0f} recalibrations per actuator")
    require(text, f"{f001['mean_pose_rmse_mm']:.3f} mm")
    require(text, f"τ=0.02 still meets budget at {f002['mean_pose_rmse_mm']:.3f} mm")
    require(text, f"{f002['n_nonpositive_lead']}/6 held-out actuators has nonpositive lead")
    require(text, f"τ=0.005 fires at every life stage")
    require(text, f"{f005['recal_per_actuator']:.0f} recalibrations, {f005['mean_pose_rmse_mm']:.3f} mm")
    dyn = s3["lead_frontier_heldout"]["signal_dynamic_range_median"]
    require(text, f"{100 * dyn:.1f}% over life")
    require(text, f"{100 * s3['tau_selected'] / dyn:.0f}% of the available range")

    require(text, pct(s4["default_coupling"]))
    rs = s4["softness_multiplier_at_threshold"]["R_s"]
    require(text, f"≈{rs['0.10']:.1f}×")
    require(text, f"≈{rs['0.20']:.1f}×")
    cm_vals = s4["coupling_vs_multiplier"]["C_m"]
    require(text, f"{100 * min(cm_vals):.1f}–{100 * max(cm_vals):.1f}%")

    # ── arXiv metadata abstract gates (docs/SUBMISSION.md Phase 1c) ──────────
    ab = ARXIV_ABSTRACT.read_text(encoding="utf-8").strip()
    if len(ab) > 1920:
        raise AssertionError(f"arXiv abstract is {len(ab)} chars; the metadata cap is 1920")
    if not ab.isascii():
        bad = sorted({c for c in ab if not c.isascii()})
        raise AssertionError(f"arXiv abstract must be ASCII-only; found {bad!r}")
    for token in ("**", "`", "##", "]("):
        if token in ab:
            raise AssertionError(f"arXiv abstract carries markdown token {token!r}")
    # Every load-bearing number quoted in the metadata abstract, from the JSONs.
    # arXiv caps the metadata abstract at 1920 chars, so it carries only the headline
    # cluster interval; the manuscript and secondary docs carry both intervals.
    require(ab, f"r = {cl['r']:.3f}, 95% CI [{cb['ci_low']:.3f}, {cb['ci_high']:.3f}]")
    require(ab, f"median lead {lead['median_lead_life']:.3f} normalized life")
    require(ab, f"{lead['status_counts']['nonpositive_lead']}/6 actuators nonpositive")
    require(ab, f"median +{f001['lead_life_median']:.3f}")
    front_savings = 1.0 - f001["recal_per_actuator"] / policies["always"]["recal_per_actuator"]
    require(ab, f"{front_savings:.0%} fewer recalibrations")
    require(ab, f"{savings:.0%} fewer recalibrations")
    require(ab, f"({policies['triggered']['recal_per_actuator']:.0f} vs "
                f"{policies['always']['recal_per_actuator']:.0f} per actuator)")

    # Figure 4b plots actuator MEANS while section 4.4 quotes medians. Gate both against
    # their sources so the two passages cannot drift into looking like one contradictory claim.
    fr01 = next(p for p in load_json(STUDY3_CLUSTER)["lead_frontier_with_cluster_ci"]
                if abs(p["tau"] - 0.01) < 1e-12)
    require(text, f"mean lead is +{fr01['mean_lead_life']:.3f} normalized life")
    require(text, f"[{fr01['lead_ci_low']:.3f}, {fr01['lead_ci_high']:.3f}]")
    require(text, f"median of +{f001['lead_life_median']:.3f}")

    # Cross-document gate: every doc that quotes the correlation interval must quote the
    # cluster interval, so a future edit cannot leave one of them behind.
    for doc in SECONDARY_DOCS:
        body = doc.read_text(encoding="utf-8")
        if "0.885" not in body:
            continue
        require(body, f"[{cb['ci_low']:.3f}, {cb['ci_high']:.3f}]")
        require(body, f"[{lz['ci_low']:.3f}, {lz['ci_high']:.3f}]")
        print(f"  {doc.relative_to(ROOT)}: cluster interval present")

    print("manuscript numbers match study JSONs (incl. arXiv abstract and secondary docs)")


def main():
    for manuscript in (MANUSCRIPT, CANDIDATE):
        check_manuscript(manuscript)
        print(f"  checked manuscript: {manuscript.name}")


if __name__ == "__main__":
    main()
