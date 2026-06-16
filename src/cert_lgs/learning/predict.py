"""P_cert: certification-feasibility predictor.

Predicts whether a learned proposal will pass certification before the (potentially
expensive) certifier is invoked.  Acts as the pre-screen at the θ confidence gate.

Architecture: logistic regression over a 12-dimensional feature vector.
    [4-d type one-hot | 1-d confidence | 3-d tier one-hot | 4-d extra stats]

Weights are initialised to small random values and intended to be trained via
train.py using observed accept/reject outcomes from real search episodes.
"""
from __future__ import annotations

import numpy as np

from cert_lgs.learning.proposals import LearnedProposal, ProposalTier


# proposal-type index (unknown → 0)
_TYPE_IDX: dict[str, int] = {
    "operator_priority":            0,
    "expansion_order":              0,
    "frontier_partition_order":     0,
    "bdd_partition":                1,
    "admissible_bound_substitution": 2,
    "safe_pruning":                 3,
    "unsafe_pruning_attempt":       3,
}
_TIER_IDX: dict[str, int] = {
    ProposalTier.TIER1_ORDERING:   0,
    ProposalTier.TIER2_STRUCTURAL: 1,
    ProposalTier.TIER3_PRUNING:    2,
}

N_FEATURES = 12   # 4 (type) + 1 (conf) + 3 (tier) + 4 (extra)


def _features(proposal: LearnedProposal, open_list_size: int = 1) -> np.ndarray:
    """Extract a 12-dim feature vector from a learned proposal."""
    # 4-d type one-hot
    type_oh = np.zeros(4)
    type_oh[_TYPE_IDX.get(proposal.proposal_type, 0)] = 1.0

    # 1-d calibrated confidence
    conf = float(np.clip(proposal.confidence, 0.0, 1.0))

    # 3-d tier one-hot
    tier_oh = np.zeros(3)
    tier_oh[_TIER_IDX.get(proposal.tier, 0)] = 1.0

    # 4-d extra: open list size (log), priority (clipped), is_high_conf, bias
    extra = np.array([
        np.log1p(float(open_list_size)),
        float(np.tanh(proposal.priority / 10.0)),
        1.0 if conf >= 0.75 else 0.0,
        1.0,  # bias
    ])

    return np.concatenate([type_oh, [conf], tier_oh, extra])


class PCertPredictor:
    """Logistic regression predictor: P(proposal passes certification).

    The model outputs a probability in [0, 1].  Proposals with predicted
    probability < threshold are downgraded before reaching the certifier,
    reducing unnecessary certifier calls.

    Training target: y_p = 1 if proposal passed C1–C4 in the last episode,
    else y_p = 0.  Updated via stochastic gradient descent (see train.py).
    """

    def __init__(self, seed: int = 42, threshold: float = 0.5) -> None:
        rng = np.random.default_rng(seed)
        # Small random init: model starts near 0.5 for all inputs
        self.weights: np.ndarray = rng.normal(0.0, 0.05, N_FEATURES)
        self.threshold = threshold

    # -- inference ---------------------------------------------------------

    def predict_proba(
        self,
        proposal: LearnedProposal,
        open_list_size: int = 1,
    ) -> float:
        """Return P(proposal passes certification) in [0, 1]."""
        x = _features(proposal, open_list_size)
        logit = float(np.dot(self.weights, x))
        return float(1.0 / (1.0 + np.exp(-logit)))

    def predict(
        self,
        proposal: LearnedProposal,
        open_list_size: int = 1,
    ) -> bool:
        """Return True iff the predicted certification probability >= threshold."""
        return self.predict_proba(proposal, open_list_size) >= self.threshold

    # -- online SGD update (single sample) --------------------------------

    def update(
        self,
        proposal: LearnedProposal,
        passed: bool,
        open_list_size: int = 1,
        lr: float = 0.01,
    ) -> float:
        """Logistic regression SGD step.  Returns the binary cross-entropy loss."""
        x = _features(proposal, open_list_size)
        y = 1.0 if passed else 0.0
        p = self.predict_proba(proposal, open_list_size)
        grad = (p - y) * x
        self.weights -= lr * grad
        eps = 1e-9
        loss = -(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
        return float(loss)

    # -- weight I/O --------------------------------------------------------

    def get_weights(self) -> np.ndarray:
        return self.weights.copy()

    def set_weights(self, weights: np.ndarray) -> None:
        if weights.shape != (N_FEATURES,):
            raise ValueError(f"Expected shape ({N_FEATURES},), got {weights.shape}")
        self.weights = weights.copy()


def load_model(path: str | None = None) -> PCertPredictor:
    """Load a trained P_cert model.  Returns a fresh predictor if path is None."""
    predictor = PCertPredictor()
    if path is not None:
        data = np.load(path)
        predictor.set_weights(data["weights"])
    return predictor
