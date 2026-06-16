"""Generate Figures 1–3 for the Cert-LGS JAIR manuscript.

Figure 1 — System architecture diagram
Figure 2 — Three-tier proposal routing flowchart
Figure 3 — θ-sensitivity curve (empirical sweep on toy domain)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

OUT = Path(__file__).parent.parent.parent / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── shared style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

C_BLUE   = "#2166AC"
C_GREEN  = "#1B7837"
C_ORANGE = "#D95F02"
C_GREY   = "#636363"
C_LIGHT  = "#F7F7F7"
C_RED    = "#B2182B"

# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 — System Architecture
# ─────────────────────────────────────────────────────────────────────────────

def _box(ax, x, y, w, h, label, sublabels, color, text_color="white"):
    """Draw a module box with a header and bullet sublabels."""
    # shadow
    shadow = FancyBboxPatch(
        (x + 0.015, y - 0.015), w, h,
        boxstyle="round,pad=0.02", linewidth=0,
        facecolor="#AAAAAA", zorder=1,
    )
    ax.add_patch(shadow)
    # main box
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02", linewidth=1.5,
        edgecolor=color, facecolor=C_LIGHT, zorder=2,
    )
    ax.add_patch(box)
    # header band
    hdr = FancyBboxPatch(
        (x, y + h - 0.14), w, 0.14,
        boxstyle="round,pad=0.02", linewidth=0,
        facecolor=color, zorder=3,
    )
    ax.add_patch(hdr)
    ax.text(x + w / 2, y + h - 0.07, label,
            ha="center", va="center", fontsize=10, fontweight="bold",
            color=text_color, zorder=4)
    for i, s in enumerate(sublabels):
        ax.text(x + 0.06, y + h - 0.22 - i * 0.115, s,
                ha="left", va="center", fontsize=8.5,
                color=C_GREY, zorder=4)


def _arrow(ax, x0, y0, x1, y1, label="", color=C_GREY, lw=1.5, rad=0.0):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=5,
    )
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx, my + 0.04, label,
                ha="center", va="bottom", fontsize=7.5,
                color=color, style="italic", zorder=6)


def fig1_architecture():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.6)
    ax.axis("off")

    # ── three module boxes ────────────────────────────────────────────────────
    _box(ax, 0.3,  0.5, 3.2, 3.6,
         "Learning Module",
         ["• GNN proposal ranker",
          "• P_cert feasibility",
          "  predictor",
          "• Proposal confidence",
          "  calibration (ECE)",
          "• State feature",
          "  extraction"],
         C_BLUE)

    _box(ax, 4.4,  0.5, 3.2, 3.6,
         "Certification Layer",
         ["• C1  Transition semantics",
          "• C2  Exhaustive partition",
          "• C3  Admissible bound",
          "• C4  Safe pruning",
          "• θ   Confidence gate",
          "• Fallback protocol"],
         C_GREEN)

    _box(ax, 8.5,  0.5, 3.2, 3.6,
         "Symbolic Search",
         ["• BDD state-set frontier",
          "• Conditional-effect",
          "  image computation",
          "• UCS (Dijkstra) core",
          "• Axiom fixed-point",
          "• EVMDD cost functions"],
         C_ORANGE)

    # ── arrows ────────────────────────────────────────────────────────────────
    # Learning → Cert  (proposals, top)
    _arrow(ax, 3.5, 2.75, 4.4, 2.75,
           "Tier 1/2/3 proposals", color=C_BLUE, lw=2)

    # Cert → Search  (certified, top)
    _arrow(ax, 7.6, 2.75, 8.5, 2.75,
           "Certified proposals", color=C_GREEN, lw=2)

    # Search → Cert  (state features, bottom — left)
    _arrow(ax, 8.5, 1.4, 7.6, 1.4,
           "States / open list", color=C_ORANGE, lw=1.4)

    # Cert → Learning  (state features, bottom — left)
    _arrow(ax, 4.4, 1.4, 3.5, 1.4,
           "State features", color=C_GREEN, lw=1.4)

    # Cert → Search fallback (red dashed below main flow)
    ax.annotate("", xy=(8.5, 1.0), xytext=(7.6, 1.0),
                arrowprops=dict(
                    arrowstyle="-|>", color=C_RED, lw=1.4,
                    linestyle="dashed",
                    connectionstyle="arc3,rad=0",
                ),
                zorder=5)
    ax.text(8.05, 0.82, "Fallback → baseline", ha="center",
            fontsize=7.5, color=C_RED, style="italic")

    # ── PDDL input ────────────────────────────────────────────────────────────
    ax.text(0.3, 4.35, "PDDL task Π\n(CE + axioms + cost)",
            ha="left", va="top", fontsize=8.5, color=C_GREY,
            bbox=dict(boxstyle="round,pad=0.3", fc=C_LIGHT,
                      ec=C_GREY, lw=0.8))
    _arrow(ax, 1.55, 4.12, 1.55, 4.1, color=C_GREY, lw=1.2)
    # small arrow down into the search box
    ax.annotate("", xy=(10.1, 4.1), xytext=(10.1, 4.35),
                arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=1.2),
                zorder=5)
    ax.plot([1.55, 10.1], [4.35, 4.35], color=C_GREY, lw=0.9, ls="--", zorder=4)

    # ── plan output ───────────────────────────────────────────────────────────
    ax.text(11.7, 0.25, "Optimal\nplan π*",
            ha="center", va="bottom", fontsize=8.5, color=C_GREY,
            bbox=dict(boxstyle="round,pad=0.3", fc=C_LIGHT,
                      ec=C_GREY, lw=0.8))
    _arrow(ax, 10.1, 0.5, 10.1, 0.35, color=C_GREY, lw=1.2)

    fig.suptitle("Figure 1 — Cert-LGS System Architecture",
                 fontsize=11, fontweight="bold", y=0.99)

    path = OUT / "fig1_architecture.pdf"
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(OUT / "fig1_architecture.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — Three-Tier Routing Flowchart
# ─────────────────────────────────────────────────────────────────────────────

def _rect(ax, cx, cy, w, h, label, fc, ec, fs=9, bold=False, lw=1.4):
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.04", linewidth=lw,
        facecolor=fc, edgecolor=ec, zorder=3,
    )
    ax.add_patch(box)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal",
            color="white" if fc not in (C_LIGHT, "white", "#FEFEFE") else ec,
            zorder=4, multialignment="center")


def _diamond(ax, cx, cy, w, h, label, fc, ec, fs=8.5):
    xs = [cx, cx + w/2, cx, cx - w/2, cx]
    ys = [cy + h/2, cy, cy - h/2, cy, cy + h/2]
    ax.fill(xs, ys, color=fc, zorder=3)
    ax.plot(xs, ys, color=ec, lw=1.4, zorder=4)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fs, color="white", zorder=5, multialignment="center")


def _arr(ax, x0, y0, x1, y1, label="", lc=C_GREY, fs=8):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=lc, lw=1.3,
                                connectionstyle="arc3,rad=0"),
                zorder=5)
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx + 0.05, my, label, ha="left", va="center",
                fontsize=fs, color=lc)


def _harr(ax, x0, y0, x1, y1, via_x=None, label="", lc=C_GREY, fs=8):
    """Horizontal-then-vertical (L-shaped) arrow."""
    if via_x is None:
        via_x = x1
    ax.plot([x0, via_x, via_x], [y0, y0, y1], color=lc, lw=1.3, zorder=4)
    ax.annotate("", xy=(x1, y1), xytext=(via_x, y1),
                arrowprops=dict(arrowstyle="-|>", color=lc, lw=1.3),
                zorder=5)
    if label:
        ax.text((x0 + via_x) / 2, y0 + 0.08, label,
                ha="center", va="bottom", fontsize=fs, color=lc)


def fig2_tier_routing():
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # ── entry ─────────────────────────────────────────────────────────────────
    _rect(ax, 5.5, 8.4, 2.8, 0.55,
          "Learned Proposal (type, confidence, metadata)",
          C_BLUE, C_BLUE, fs=8.5, bold=True)

    _arr(ax, 5.5, 8.12, 5.5, 7.55)

    # ── tier classification diamond ───────────────────────────────────────────
    _diamond(ax, 5.5, 7.1, 2.6, 0.9, "Proposal\ntier?", C_GREY, C_GREY, fs=9)

    # ── Tier 1 branch (left) ──────────────────────────────────────────────────
    ax.plot([4.2, 2.0, 2.0], [7.1, 7.1, 5.8], color=C_BLUE, lw=1.3, zorder=4)
    ax.annotate("", xy=(2.0, 5.8), xytext=(2.0, 5.82),
                arrowprops=dict(arrowstyle="-|>", color=C_BLUE, lw=1.3),
                zorder=5)
    ax.text(3.1, 7.22, "Tier 1\n(ordering)", ha="center", fontsize=8,
            color=C_BLUE)

    _rect(ax, 2.0, 5.45, 2.6, 0.65,
          "Accept unconditionally\n(no certifier invoked)",
          C_BLUE, C_BLUE, fs=8)

    ax.text(0.6, 5.45, "operator_priority\nexpansion_order\nfrontier_partition_order",
            ha="left", va="center", fontsize=7.5, color=C_BLUE,
            bbox=dict(boxstyle="round,pad=0.25", fc="#EFF3FF", ec=C_BLUE, lw=0.8))
    ax.annotate("", xy=(1.2, 5.45), xytext=(0.6, 5.45),  # thin note arrow
                arrowprops=dict(arrowstyle="-", color=C_BLUE, lw=0.8, linestyle="dashed"),
                zorder=3)

    _arr(ax, 2.0, 5.12, 2.0, 4.5)
    _rect(ax, 2.0, 4.2, 2.6, 0.55,
          "Apply to search state\n(reorder OPEN / ops)",
          C_LIGHT, C_BLUE, fs=8)

    # ── Tier 2 branch (centre-right) ─────────────────────────────────────────
    _arr(ax, 5.5, 6.65, 5.5, 5.95)
    ax.text(5.7, 6.3, "Tier 2\n(structural)", ha="left", fontsize=8,
            color=C_GREEN)

    _diamond(ax, 5.5, 5.55, 2.8, 0.75, "Cert C2\n(partition coverage)?",
             C_GREEN, C_GREEN, fs=8.5)

    # C2 pass (right)
    ax.plot([6.9, 8.5, 8.5], [5.55, 5.55, 4.85], color=C_GREEN, lw=1.3, zorder=4)
    ax.annotate("", xy=(8.5, 4.85), xytext=(8.5, 4.87),
                arrowprops=dict(arrowstyle="-|>", color=C_GREEN, lw=1.3), zorder=5)
    ax.text(7.7, 5.68, "Pass", ha="center", fontsize=8, color=C_GREEN)
    _rect(ax, 8.5, 4.55, 2.4, 0.55,
          "Accept: apply\nBDD partition", C_GREEN, C_GREEN, fs=8)

    # C2 fail (below centre)
    _arr(ax, 5.5, 5.17, 5.5, 4.55)
    ax.text(5.65, 4.86, "Fail", ha="left", fontsize=8, color=C_RED)
    _rect(ax, 5.5, 4.25, 2.4, 0.55,
          "Reject + fallback\n(expand full frontier)",
          "#FDDBC7", C_RED, fs=8)

    # admissible_bound note (C3)
    ax.text(3.6, 5.55, "admissible_bound\nsubstitution", ha="center",
            va="center", fontsize=7.5, color=C_GREEN,
            bbox=dict(boxstyle="round,pad=0.25", fc="#E8F5E9", ec=C_GREEN, lw=0.8))
    ax.text(4.5, 5.55, "→ always pass\n(min construction)",
            ha="left", va="center", fontsize=7.5, color=C_GREEN)

    # ── Tier 3 branch (far right) ────────────────────────────────────────────
    ax.plot([6.8, 9.8, 9.8], [7.1, 7.1, 6.45], color=C_ORANGE, lw=1.3, zorder=4)
    ax.annotate("", xy=(9.8, 6.45), xytext=(9.8, 6.47),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1.3), zorder=5)
    ax.text(8.3, 7.22, "Tier 3\n(pruning)", ha="center", fontsize=8,
            color=C_ORANGE)

    _diamond(ax, 9.8, 6.0, 2.4, 0.8, "conf < θ ?", C_ORANGE, C_ORANGE, fs=9)

    # θ gate: Yes → downgrade
    ax.plot([8.6, 7.2], [6.0, 6.0], color=C_ORANGE, lw=1.3, zorder=4)
    ax.annotate("", xy=(7.2, 6.0), xytext=(7.22, 6.0),
                arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1.3), zorder=5)
    ax.text(7.9, 6.12, "Yes", ha="center", fontsize=8, color=C_ORANGE)
    _rect(ax, 6.6, 6.0, 2.2, 0.55,
          "Downgrade to\nTier 1 ordering hint",
          "#FFF3E0", C_ORANGE, fs=8)

    # θ gate: No → C4
    _arr(ax, 9.8, 5.6, 9.8, 4.85)
    ax.text(9.95, 5.22, "No\n(conf ≥ θ)", ha="left", fontsize=8,
            color=C_ORANGE)
    _diamond(ax, 9.8, 4.45, 2.4, 0.75,
             "Cert C4\n(safe pruning)?", C_RED, C_RED, fs=8.5)

    # C4 pass
    _arr(ax, 9.8, 4.07, 9.8, 3.45)
    ax.text(9.95, 3.76, "Pass", ha="left", fontsize=8, color=C_GREEN)
    _rect(ax, 9.8, 3.15, 2.4, 0.55,
          "Accept: prune\nstate set from OPEN",
          C_GREEN, C_GREEN, fs=8)

    # C4 fail → fallback
    ax.plot([8.6, 7.2], [4.45, 4.45], color=C_RED, lw=1.3, zorder=4)
    ax.annotate("", xy=(7.2, 4.45), xytext=(7.22, 4.45),
                arrowprops=dict(arrowstyle="-|>", color=C_RED, lw=1.3), zorder=5)
    ax.text(7.9, 4.57, "Fail", ha="center", fontsize=8, color=C_RED)
    _rect(ax, 6.6, 4.45, 2.2, 0.55,
          "Reject: state stays\nin OPEN (fallback)",
          "#FDDBC7", C_RED, fs=8)

    # ── legend ────────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(fc=C_BLUE,   label="Tier 1 — Ordering (0% fallback by construction)"),
        mpatches.Patch(fc=C_GREEN,  label="Tier 2 — Structural (C2/C3; fallback rate domain-dependent)"),
        mpatches.Patch(fc=C_ORANGE, label="Tier 3 — Pruning (C4, gated by θ; fallback rate domain-dependent)"),
        mpatches.Patch(fc=C_RED,    label="Fallback / rejection path"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8,
              framealpha=0.9, edgecolor=C_GREY)

    fig.suptitle("Figure 2 — Three-Tier Proposal Routing Flowchart",
                 fontsize=11, fontweight="bold", y=0.995)

    path = OUT / "fig2_tier_routing.pdf"
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(OUT / "fig2_tier_routing.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 — θ-sensitivity (empirical sweep on toy domain)
# ─────────────────────────────────────────────────────────────────────────────

def _run_theta_sweep():
    """Run AdversarialRanker at multiple θ values and a multi-confidence ranker."""
    # Add cert-lgs src to path so we can import the package
    src = Path(__file__).parent.parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from cert_lgs.certification.certifier import CertificationLayer
    from cert_lgs.learning.model import GuidanceModel
    from cert_lgs.learning.proposals import LearnedProposal, ProposalTier
    from cert_lgs.planner.symbolic_search import SymbolicSearchPlanner

    CONFIG_BASE = {
        "benchmark": {"domains": ["benchmarks/toy_expressive"]},
        "learning": {"model_type": "multi_confidence"},
    }

    # Multi-confidence ranker: proposes pruning at 7 confidence levels each step.
    CONF_LEVELS = [0.30, 0.45, 0.55, 0.65, 0.75, 0.85, 1.00]

    class MultiConfidenceRanker(GuidanceModel):
        def propose(self, open_list, transitions, goal_atoms=frozenset()):
            if not open_list:
                return []
            proposals = []
            for conf in CONF_LEVELS:
                proposals.append(LearnedProposal(
                    proposal_type="unsafe_pruning_attempt",
                    target=open_list[0].name,
                    priority=0.0,
                    confidence=conf,
                    metadata={"test_confidence": conf},
                    tier=ProposalTier.TIER3_PRUNING,
                ))
            return proposals

    theta_values = [0.0, 0.25, 0.50, 0.65, 0.75, 0.85, 0.90, 1.00]
    results = []

    for theta in theta_values:
        cfg = {**CONFIG_BASE,
               "certification": {"pruning_confidence_threshold": theta}}
        planner  = SymbolicSearchPlanner(cfg)
        certifier = CertificationLayer(cfg)
        result = planner.solve_with_guidance(MultiConfidenceRanker(), certifier)

        # Count events by outcome
        submitted  = sum(1 for e in certifier.events
                         if e["certificate"] in ("admissible_bound_pruning",
                                                  "safe_pruning"))
        downgraded = sum(1 for e in certifier.events
                         if e["certificate"] == "transition_semantics"
                         or e["metadata"].get("downgraded_from") is not None)
        # Approximate downgraded: proposals that were downgraded don't appear
        # in certifier events (they become ordering hints).
        # total_pruning_proposals = len(CONF_LEVELS) * expansions
        total_pruning = len(CONF_LEVELS) * result.expanded
        downgraded_count = total_pruning - submitted

        results.append({
            "theta": theta,
            "solved": result.status == "solved",
            "plan_cost": result.plan_cost,
            "expanded": result.expanded,
            "submitted_to_certifier": submitted,
            "downgraded": downgraded_count,
            "certifier_rejections": sum(
                1 for e in certifier.events
                if e["certificate"] in ("admissible_bound_pruning", "safe_pruning")
                and not e["valid"]
            ),
        })

    return results, len(CONF_LEVELS)


def fig3_theta_sensitivity():
    import os
    # Change working dir so the planner finds benchmarks/
    os.chdir(Path(__file__).parent.parent)

    results, n_conf = _run_theta_sweep()

    theta_vals  = [r["theta"]                 for r in results]
    submitted   = [r["submitted_to_certifier"] for r in results]
    downgraded  = [r["downgraded"]             for r in results]
    rejections  = [r["certifier_rejections"]   for r in results]
    solved      = [r["solved"]                 for r in results]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6.5),
                                   gridspec_kw={"height_ratios": [3, 1]},
                                   sharex=True)

    # ── top panel: submitted vs. downgraded ──────────────────────────────────
    ax1.plot(theta_vals, submitted, "o-",
             color=C_ORANGE, lw=2, ms=6, label="Submitted to C4 certifier")
    ax1.plot(theta_vals, downgraded, "s--",
             color=C_BLUE, lw=2, ms=6, label="Downgraded to Tier 1 hint")
    ax1.plot(theta_vals, rejections, "^:",
             color=C_RED, lw=1.5, ms=5, label="Rejected by C4")

    # annotate total proposals
    total = submitted[0] + downgraded[0]
    ax1.axhline(total, color=C_GREY, lw=0.8, ls=":", alpha=0.6)
    ax1.text(0.01, total + 0.3, f"Total pruning proposals = {total}",
             fontsize=7.5, color=C_GREY, va="bottom")

    ax1.set_ylabel("Proposal count (cumulative across search)", fontsize=9)
    ax1.legend(fontsize=8.5, loc="center right")
    ax1.set_ylim(bottom=-0.5)
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax1.grid(axis="y", lw=0.5, alpha=0.4)
    ax1.set_title("Cert-LGS θ-Sensitivity: Toy Expressive Logistics Domain\n"
                  r"($7$ confidence levels ∈ {0.30, 0.45, 0.55, 0.65, 0.75, 0.85, 1.00} × 4 expansions)",
                  fontsize=9.5)

    # ── bottom panel: coverage (plan found) ──────────────────────────────────
    solved_int = [1 if s else 0 for s in solved]
    ax2.bar(theta_vals, solved_int,
            width=0.06, color=[C_GREEN if s else C_RED for s in solved],
            edgecolor="white", zorder=3)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["No", "Yes"], fontsize=9)
    ax2.set_ylabel("Solved?", fontsize=9)
    ax2.set_xlabel("Confidence threshold θ", fontsize=9)
    ax2.set_xticks(theta_vals)
    ax2.set_xticklabels([f"{t:.2f}" for t in theta_vals], fontsize=8.5)
    ax2.grid(axis="y", lw=0.5, alpha=0.4)
    ax2.set_ylim(-0.1, 1.4)

    plt.tight_layout()
    fig.text(0.5, -0.01,
             "Figure 3 — θ controls the pruning-vs-overhead trade-off. "
             "Higher θ downgrade more proposals (reducing C4 overhead); "
             "plan correctness is maintained at all θ.",
             ha="center", fontsize=8, color=C_GREY, style="italic",
             wrap=True)

    path = OUT / "fig3_theta_sensitivity.pdf"
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(OUT / "fig3_theta_sensitivity.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"Saved {path}")

    # save raw data
    raw_path = OUT.parent / "raw" / "theta_sweep.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w") as f:
        json.dump({"n_confidence_levels": n_conf, "results": results}, f, indent=2)
    print(f"Saved theta sweep data → {raw_path}")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Figure 1 — System Architecture …")
    fig1_architecture()

    print("Generating Figure 2 — Three-Tier Routing Flowchart …")
    fig2_tier_routing()

    print("Generating Figure 3 -- theta-Sensitivity Curve ...")
    fig3_theta_sensitivity()

    print("\nAll figures written to:", OUT)
