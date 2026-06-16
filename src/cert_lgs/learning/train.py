"""Composite training loss and training loop for Cert-LGS.

The five-term composite loss (Section 6 of the manuscript):

    L = L1_rank + L2_cert + L3_cal + L4_opt - L5_div

L1  Pairwise ranking loss    — proposals should rank low-cost states higher
L2  Cert-feasibility loss    — P_cert should predict accept/reject correctly
L3  Calibration loss         — confidence should match empirical acceptance rate
L4  Optimality regularisation — penalise ordering inversions relative to h* estimate
L5  Diversity bonus          — reward variety in proposal types (negative term)

All arithmetic uses numpy only (no autograd).  Gradient computation for the
GNN weights and P_cert predictor is handled via finite-difference SGD or an
external autograd framework (torch, jax).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cert_lgs.learning.calibrate import expected_calibration_error
from cert_lgs.learning.proposals import LearnedProposal


# ── Training episode (one search run) ────────────────────────────────────────

@dataclass
class TrainingEpisode:
    """A recorded search episode used as a training sample.

    Attributes
    ----------
    proposals       Proposals generated during the episode.
    passed_cert     Per-proposal bool: True iff the proposal passed certification.
    state_g_costs   Per-proposal accumulated cost of the targeted state.
    h_star_estimates Per-proposal admissible h* estimate (e.g., from backward search).
                    May be None when unavailable; those pairs are excluded from L4.
    """
    proposals: list[LearnedProposal]
    passed_cert: list[bool]
    state_g_costs: list[float]
    h_star_estimates: list[float | None] = field(default_factory=list)

    def __post_init__(self) -> None:
        n = len(self.proposals)
        if len(self.passed_cert) != n or len(self.state_g_costs) != n:
            raise ValueError("proposals, passed_cert, state_g_costs must have equal length")
        if not self.h_star_estimates:
            self.h_star_estimates = [None] * n


# ── Individual loss terms ─────────────────────────────────────────────────────

def _pairwise_ranking_loss(
    priorities: list[float],
    g_costs: list[float],
    h_star: list[float | None],
) -> float:
    """L1: pairwise hinge loss — penalise inverting (priority, cost) order.

    For every pair (i, j) where h*(i) < h*(j) (state i is better), we want
    priority[i] > priority[j].  Loss = max(0, priority[j] - priority[i]).
    Pairs with missing h* estimates are skipped.
    """
    loss = 0.0
    n = len(priorities)
    count = 0
    for i in range(n):
        if h_star[i] is None:
            continue
        for j in range(n):
            if h_star[j] is None or i == j:
                continue
            # f(s) = g(s) + h*(s): lower total is better
            fi = g_costs[i] + h_star[i]
            fj = g_costs[j] + h_star[j]
            if fi < fj:  # state i is strictly better
                margin = priorities[j] - priorities[i]
                loss += max(0.0, margin)
                count += 1
    return loss / max(count, 1)


def _cert_feasibility_loss(
    proposals: list[LearnedProposal],
    passed: list[bool],
    predictor_probs: list[float],
) -> float:
    """L2: binary cross-entropy — P_cert should match observed accept/reject.

    predictor_probs[i] = P_cert(proposals[i]) output.
    passed[i]          = 1 if the proposal passed the real certifier, else 0.
    """
    eps = 1e-9
    total = 0.0
    for y_true, y_pred in zip(passed, predictor_probs):
        y = 1.0 if y_true else 0.0
        p = float(np.clip(y_pred, eps, 1 - eps))
        total += -(y * np.log(p) + (1 - y) * np.log(1 - p))
    return total / max(len(proposals), 1)


def _calibration_loss(
    confidences: list[float],
    passed: list[bool],
    bins: int = 10,
) -> float:
    """L3: expected calibration error on proposal confidence vs. pass rate."""
    outcomes = [1 if p else 0 for p in passed]
    return expected_calibration_error(confidences, outcomes, bins=bins)


def _optimality_regularisation(
    proposals: list[LearnedProposal],
    passed: list[bool],
    h_star: list[float | None],
    g_costs: list[float],
) -> float:
    """L4: penalise accepted pruning proposals that would prune optimal-path states.

    A pruning proposal for state s is dangerous if g(s) + h*(s) equals the
    optimal cost (state is on an optimal path).  We penalise accepted
    pruning proposals on such states with a squared loss.
    """
    loss = 0.0
    count = 0
    for proposal, accepted, h, g in zip(proposals, passed, h_star, g_costs):
        if h is None:
            continue
        is_pruning = proposal.proposal_type in ("safe_pruning", "unsafe_pruning_attempt")
        if not is_pruning or not accepted:
            continue
        # Penalise pruning proposals on states where h* is small (likely optimal path)
        danger = max(0.0, 1.0 - h)  # higher danger when h* is small
        loss += danger ** 2
        count += 1
    return loss / max(count, 1)


def _diversity_bonus(proposals: list[LearnedProposal]) -> float:
    """L5 (negative term): reward type diversity across proposals.

    Returns the normalised entropy of the proposal-type distribution.
    Higher diversity → larger bonus → lower overall loss.
    """
    if not proposals:
        return 0.0
    from collections import Counter
    counts = Counter(p.proposal_type for p in proposals)
    if len(counts) <= 1:
        return 0.0
    total = len(proposals)
    entropy = 0.0
    for c in counts.values():
        prob = c / total
        entropy -= prob * np.log(prob)
    # Normalise by log(n_types) to get a value in [0, 1]
    max_entropy = np.log(len(counts))
    return float(entropy / max_entropy)


# ── Composite loss ────────────────────────────────────────────────────────────

@dataclass
class LossWeights:
    ranking:       float = 1.0
    cert_feas:     float = 1.0
    calibration:   float = 0.5
    optimality:    float = 2.0
    diversity:     float = 0.3


@dataclass
class LossBreakdown:
    total:       float
    L1_ranking:  float
    L2_cert:     float
    L3_cal:      float
    L4_opt:      float
    L5_div:      float

    def as_dict(self) -> dict[str, float]:
        return {
            "total": self.total,
            "L1_ranking": self.L1_ranking,
            "L2_cert": self.L2_cert,
            "L3_cal": self.L3_cal,
            "L4_opt": self.L4_opt,
            "L5_div_bonus": self.L5_div,
        }


def composite_loss(
    episode: TrainingEpisode,
    predictor_probs: list[float],
    weights: LossWeights | None = None,
) -> LossBreakdown:
    """Compute the full 5-term composite training loss for one episode.

    Parameters
    ----------
    episode         Recorded search episode.
    predictor_probs P_cert model outputs for each proposal (same order as episode).
    weights         Per-term loss weights (default: LossWeights()).
    """
    if weights is None:
        weights = LossWeights()

    priorities = [p.priority for p in episode.proposals]
    confidences = [p.confidence for p in episode.proposals]

    L1 = _pairwise_ranking_loss(priorities, episode.state_g_costs, episode.h_star_estimates)
    L2 = _cert_feasibility_loss(episode.proposals, episode.passed_cert, predictor_probs)
    L3 = _calibration_loss(confidences, episode.passed_cert)
    L4 = _optimality_regularisation(
        episode.proposals, episode.passed_cert,
        episode.h_star_estimates, episode.state_g_costs,
    )
    L5 = _diversity_bonus(episode.proposals)

    total = (
        weights.ranking    * L1
        + weights.cert_feas  * L2
        + weights.calibration * L3
        + weights.optimality * L4
        - weights.diversity  * L5   # bonus: subtract diversity
    )

    return LossBreakdown(total=total, L1_ranking=L1, L2_cert=L2,
                         L3_cal=L3, L4_opt=L4, L5_div=L5)


# ── Training loop stub ────────────────────────────────────────────────────────

def run_training_epoch(
    episodes: list[TrainingEpisode],
    predictor,           # PCertPredictor
    weights: LossWeights | None = None,
    lr: float = 0.01,
) -> dict[str, float]:
    """Run one training epoch over a list of episodes.

    Updates the P_cert predictor weights via online SGD.
    GNN weight updates require autograd (torch/jax) and are scaffolded here
    as a no-op: the loss breakdown is returned for logging.

    Returns average loss breakdown across the epoch.
    """
    if not episodes:
        return LossBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0).as_dict()

    totals: dict[str, float] = {k: 0.0 for k in LossBreakdown(0,0,0,0,0,0).as_dict()}

    for episode in episodes:
        probs = [
            predictor.predict_proba(p, open_list_size=max(len(episode.proposals), 1))
            for p in episode.proposals
        ]
        breakdown = composite_loss(episode, probs, weights)

        # Online SGD update for P_cert predictor
        for proposal, passed in zip(episode.proposals, episode.passed_cert):
            predictor.update(proposal, passed, lr=lr)

        for k, v in breakdown.as_dict().items():
            totals[k] += v

    n = len(episodes)
    return {k: v / n for k, v in totals.items()}


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train Cert-LGS guidance model.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--episodes", type=int, default=0,
                        help="Number of synthetic episodes for smoke-test")
    args = parser.parse_args()

    from cert_lgs.learning.predict import PCertPredictor
    from cert_lgs.learning.proposals import LearnedProposal, ProposalTier

    predictor = PCertPredictor()

    if args.episodes > 0:
        # Synthetic smoke-test episodes
        rng = np.random.default_rng(0)
        episodes = []
        for _ in range(args.episodes):
            n = rng.integers(3, 8)
            proposals = [
                LearnedProposal(
                    proposal_type=rng.choice(["operator_priority", "safe_pruning"]),
                    target="s",
                    priority=float(rng.uniform(0, 1)),
                    confidence=float(rng.uniform(0.5, 1)),
                    metadata={},
                    tier=ProposalTier.TIER1_ORDERING,
                )
                for _ in range(n)
            ]
            passed = [bool(rng.integers(0, 2)) for _ in range(n)]
            g_costs = [float(rng.uniform(0, 5)) for _ in range(n)]
            h_star = [float(rng.uniform(0, 3)) for _ in range(n)]
            episodes.append(TrainingEpisode(proposals, passed, g_costs, h_star))

        avg = run_training_epoch(episodes, predictor)
        print(f"Epoch loss (avg over {args.episodes} synthetic episodes):")
        for k, v in avg.items():
            print(f"  {k:20s}: {v:.4f}")
    else:
        print(f"Cert-LGS training loop initialised (config: {args.config})")
        print("Provide --episodes N for a synthetic smoke-test, or wire in real "
              "search traces from experiments/run_cert_lgs.py.")


if __name__ == "__main__":
    main()
