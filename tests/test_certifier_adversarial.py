from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.learning.model import AdversarialRanker
from cert_lgs.planner.types import SymbolicStateSet, TransitionRelation


def test_adversarial_pruning_is_rejected_without_bound_certificate():
    config = {"certification": {"enabled": True}}
    certifier = CertificationLayer(config)
    guide = AdversarialRanker()
    open_list = [SymbolicStateSet("I", frozenset({"s0"}), g_cost=0.0)]
    transitions = [TransitionRelation("a", "a()", cost=1.0)]
    proposals = guide.propose(open_list, transitions)

    queue = certifier.filter_proposals(
        proposals=proposals,
        open_list=open_list,
        closed=[],
        incumbent_cost=float("inf"),
    )

    assert certifier.rejected >= 1
    assert all(p.proposal_type != "unsafe_pruning_attempt" for p in queue.proposals)
