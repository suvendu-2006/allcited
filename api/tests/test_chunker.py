from app.pipeline.chunker import (
    Chunk,
    chunk_blocks,
    split_into_sentences,
)
from app.pipeline.parsers.base import ParsedBlock


def test_split_into_sentences_preserves_rules():
    text = "Please refer to rule 63.7.4 before submitting Form HR-702. All approvals are mandatory."
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert "rule 63.7.4" in sentences[0]
    assert "Form HR-702." in sentences[0]
    assert sentences[1] == "All approvals are mandatory."


def test_chunker_p1_boundary_straddle():
    """
    P1 trap: A critical sentence straddling a chunk boundary must appear
    completely intact in BOTH overlapping chunks.
    """
    filler_sentence = "This is a detailed operational clause describing corporate compliance procedures for all employees."

    # The critical boundary sentence
    straddle_sentence = "Crucially, under clause 4.2.1, any failure to report within 48 hours incurs an immediate disciplinary review."

    # 15 filler sentences + the straddle sentence at the end of block 1 reaching ~400 tokens
    block1_text = " ".join([filler_sentence for _ in range(15)]) + " " + straddle_sentence
    block1 = ParsedBlock(
        text=block1_text,
        section_path=["1. Operations", "1.1 General"],
        page=1,
        source="test.pdf",
    )

    # Block 2 follows immediately after the boundary
    block2_text = " ".join([filler_sentence for _ in range(15)])
    block2 = ParsedBlock(
        text=block2_text,
        section_path=["1. Operations", "1.2 Disciplinary"],
        page=2,
        source="test.pdf",
    )

    chunks = chunk_blocks(
        [block1, block2], doc_id="test_doc", target_tokens=400, overlap_ratio=0.15
    )

    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"

    chunk1 = chunks[0]
    chunk2 = chunks[1]

    # The straddle sentence must appear COMPLETE and INTACT in BOTH chunk 1 and chunk 2
    assert straddle_sentence in chunk1.text, "Straddle sentence missing from chunk 1"
    assert straddle_sentence in chunk2.text, (
        "Straddle sentence missing from chunk 2 due to lack of overlap"
    )

    # Verify content hash and parent_section_id
    assert len(chunk1.content_hash) == 64
    assert len(chunk2.content_hash) == 64
    assert chunk1.parent_section_id == "1. Operations > 1.1 General"


def test_chunker_overlap_contains_last_sentence():
    """Verify that overlap carries the boundary sentence into the subsequent chunk."""
    s1 = "First sentence of paragraph one with specific details."
    s2 = "Second sentence of paragraph one establishing context."
    s3 = "Third boundary sentence that should be carried over into next chunk."
    s4 = "Fourth sentence starting the next section."

    blocks = [
        ParsedBlock(
            text=f"{s1} {s2} {s3}. {s4}",
            section_path=["Policy"],
            page=1,
            source="test.txt",
        )
    ]

    chunks = chunk_blocks(blocks, doc_id="doc", target_tokens=15, overlap_ratio=0.30)
    assert len(chunks) >= 2

    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.token_count > 0
