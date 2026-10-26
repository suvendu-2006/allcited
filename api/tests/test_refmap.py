
from app.pipeline.refmap import (
    extract_references,
    is_false_positive_reference,
)


def test_false_positive_rejection():
    """Verify that false positive strings are properly rejected."""
    false_positives = [
        "Software release v1.2.3 installed on machine",
        "Connected to server at 192.168.1.1 port 8000",
        "Effective starting on 2026.10.24 without notice",
        "As a general rule of thumb, always be punctual",
        "The item cost exactly $63.74 yesterday",
        "The mathematical ratio was approximately 3.14159",
    ]

    rejected_count = sum(1 for fp in false_positives if is_false_positive_reference(fp))
    # Gate requires rejecting >= 3 false-positive strings
    assert rejected_count >= 3, f"Expected >= 3 false positives rejected, got {rejected_count}"


def test_reference_extraction_valid():
    """Verify extraction of real reference patterns."""
    text = (
        "According to rule 63.7.4, all leave is settled in accordance with clause 4.2. "
        "Employees must submit Form HR-702 as defined in standard ISO-27001."
    )
    refs = extract_references(text)
    ref_ids = [r.ref_id for r in refs]

    assert "rule:63.7.4" in ref_ids
    assert "clause:4.2" in ref_ids
    assert "form:hr-702" in ref_ids
    assert "standard:iso-27001" in ref_ids


def test_handbook_fixture_reference_mapping(session_handbook):
    """
    Gate check: On the fixture, >=4 real cross-references are mapped.
    """
    ref_map = session_handbook.ref_map

    # Check mapped references across definitions and mentions
    all_mapped_keys = set(ref_map.definitions.keys()).union(set(ref_map.mentions.keys()))
    assert len(all_mapped_keys) >= 4, f"Expected >= 4 mapped refs, got {len(all_mapped_keys)}: {all_mapped_keys}"

    # Specifically check critical rule:63.7.4
    assert "rule:63.7.4" in ref_map.definitions or "rule:63.7.4" in ref_map.mentions
    # Check clause:4.2 or standard:iso-27001 or form:hr-702
    assert any(k in all_mapped_keys for k in ["clause:4.2", "form:hr-702", "rule:2.1.4"])
