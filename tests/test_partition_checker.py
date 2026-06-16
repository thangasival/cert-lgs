from cert_lgs.certification.partition_checker import PartitionChecker
from cert_lgs.planner.types import SymbolicStateSet


def test_exhaustive_partition_passes():
    original = SymbolicStateSet("F", frozenset({"a", "b"}))
    parts = [
        SymbolicStateSet("F1", frozenset({"a"})),
        SymbolicStateSet("F2", frozenset({"b"})),
    ]
    cert = PartitionChecker().check_exhaustive(original, parts)
    assert cert.valid


def test_exhaustive_partition_fails_when_state_missing():
    original = SymbolicStateSet("F", frozenset({"a", "b"}))
    parts = [SymbolicStateSet("F1", frozenset({"a"}))]
    cert = PartitionChecker().check_exhaustive(original, parts)
    assert not cert.valid
