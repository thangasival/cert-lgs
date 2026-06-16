from __future__ import annotations


def expected_calibration_error(confidences: list[float], outcomes: list[int], bins: int = 10) -> float:
    if not confidences:
        return 0.0
    total = len(confidences)
    ece = 0.0
    for b in range(bins):
        lo = b / bins
        hi = (b + 1) / bins
        idx = [i for i, c in enumerate(confidences) if lo <= c < hi or (b == bins - 1 and c == 1.0)]
        if not idx:
            continue
        acc = sum(outcomes[i] for i in idx) / len(idx)
        conf = sum(confidences[i] for i in idx) / len(idx)
        ece += (len(idx) / total) * abs(acc - conf)
    return ece
