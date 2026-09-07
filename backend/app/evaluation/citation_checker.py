"""
citation_checker.py
-------------------
Deterministic and lexical citation verification engine for RAG outputs.

Verifies:
1. Syntax and structure of citation markers (e.g., `[1]`, `[2]`, `[1, 2]`).
2. Index validity against the actual number of retrieved research chunks.
3. Sentence-level citation coverage (ensuring factual statements cite sources).
4. Lexical word overlap between cited sentences and the referenced chunk content.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple
from app.evaluation.schemas import MetricScore


# Regex pattern to capture single citations like [1] or compound [1, 2] or [1][2]
_CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\*\#])|\n+")


def extract_citations(text: str) -> List[int]:
    """
    Extract all integer citation indices present in a text string.
    
    Examples
    --------
    >>> extract_citations("Vitamin C helps collagen synthesis [1] and scurvy prevention [2, 3].")
    [1, 2, 3]
    """
    indices: List[int] = []
    for match in _CITATION_PATTERN.finditer(text):
        raw_content = match.group(1)
        for part in raw_content.split(","):
            part = part.strip()
            if part.isdigit():
                indices.append(int(part))
    return indices


def extract_cited_sentences(text: str) -> List[Tuple[str, List[int]]]:
    """
    Split text into meaningful statements/sentences and associate each with its cited indices.
    
    Returns
    -------
    List[Tuple[str, List[int]]]
        List of (sentence_text, list_of_cited_indices) pairs.
    """
    # Clean markdown headers and bullet markers for sentence tokenization
    raw_lines = text.split("\n")
    cleaned_sentences: List[str] = []
    
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # Remove leading bullet symbols (*, -, #)
        cleaned_line = re.sub(r"^[\*\-\#\>\d\.\s]+", "", line).strip()
        if len(cleaned_line) > 10:
            cleaned_sentences.append(cleaned_line)

    results: List[Tuple[str, List[int]]] = []
    for sent in cleaned_sentences:
        cites = extract_citations(sent)
        results.append((sent, cites))
    return results


def _compute_lexical_overlap(sentence: str, chunk_content: str) -> float:
    """
    Compute word token overlap Jaccard coefficient between sentence and chunk.
    """
    # Remove citation tags and punctuation
    cleaned_s = re.sub(r"\[\d+\]|[^\w\s]", "", sentence.lower())
    cleaned_c = re.sub(r"\[\d+\]|[^\w\s]", "", chunk_content.lower())
    
    words_s: Set[str] = set(cleaned_s.split()) - {"the", "a", "an", "and", "or", "in", "on", "of", "to", "is", "are", "for", "with"}
    words_c: Set[str] = set(cleaned_c.split()) - {"the", "a", "an", "and", "or", "in", "on", "of", "to", "is", "are", "for", "with"}
    
    if not words_s:
        return 1.0
    
    overlap = words_s.intersection(words_c)
    return len(overlap) / len(words_s)


def verify_citations(
    response: str,
    chunks: List[Dict[str, Any]],
    threshold: float = 0.8,
) -> MetricScore:
    """
    Perform rigorous deterministic citation verification.

    Parameters
    ----------
    response:
        The generated response string.
    chunks:
        The list of context chunks retrieved for this turn.
    threshold:
        Passing score threshold (default: 0.8).

    Returns
    -------
    MetricScore
        Detailed metric score evaluating citation validity, coverage, and lexical fidelity.
    """
    num_chunks = len(chunks)
    
    # If no chunks were provided, response shouldn't contain research citations
    if num_chunks == 0:
        found_cites = extract_citations(response)
        if not found_cites:
            return MetricScore(
                name="citation_accuracy",
                score=1.0,
                threshold=threshold,
                reasoning="No context chunks provided; response correctly contained no citations.",
                details={"num_chunks": 0, "found_citations": []},
            )
        else:
            return MetricScore(
                name="citation_accuracy",
                score=0.0,
                threshold=threshold,
                reasoning=f"Hallucinated citations {found_cites} when zero context chunks were retrieved.",
                details={"num_chunks": 0, "hallucinated_citations": found_cites},
            )

    sentence_cites = extract_cited_sentences(response)
    if not sentence_cites:
        return MetricScore(
            name="citation_accuracy",
            score=0.0,
            threshold=threshold,
            reasoning="Response is empty or contains no extractable statements.",
            details={"sentence_count": 0},
        )

    all_citations: List[int] = []
    valid_citations: List[int] = []
    invalid_out_of_bounds: List[int] = []
    cited_sentences_count = 0
    overlap_scores: List[float] = []

    for sentence, cites in sentence_cites:
        if cites:
            cited_sentences_count += 1
            all_citations.extend(cites)
            for c in cites:
                if 1 <= c <= num_chunks:
                    valid_citations.append(c)
                    # Verify overlap with the targeted chunk
                    target_chunk = chunks[c - 1]
                    content = target_chunk.get("content", "")
                    overlap = _compute_lexical_overlap(sentence, content)
                    overlap_scores.append(overlap)
                else:
                    invalid_out_of_bounds.append(c)

    # 1. Bounds Validity (Precision of cited index targets)
    bounds_precision = (
        len(valid_citations) / len(all_citations) if all_citations else 0.0
    )

    # 2. Citation Coverage (Fraction of meaningful sentences with at least one citation)
    citation_coverage = (
        cited_sentences_count / len(sentence_cites) if sentence_cites else 0.0
    )

    # 3. Mean Lexical Overlap with cited chunks
    mean_overlap = (
        sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
    )

    # Composite citation score: 40% bounds validity + 30% coverage + 30% content alignment
    if not all_citations:
        final_score = 0.0
        reasoning = "Response lacks any inline research citations ([1], [2], etc.)."
    elif invalid_out_of_bounds:
        final_score = max(0.0, bounds_precision * 0.5)
        reasoning = (
            f"Found out-of-bounds citations {set(invalid_out_of_bounds)} "
            f"exceeding chunk count ({num_chunks})."
        )
    else:
        final_score = round(
            0.4 * bounds_precision + 0.3 * min(1.0, citation_coverage * 1.25) + 0.3 * min(1.0, mean_overlap * 2.0),
            4,
        )
        reasoning = (
            f"Valid citations across {cited_sentences_count}/{len(sentence_cites)} statements. "
            f"Bounds validity: {bounds_precision * 100:.0f}%, Content overlap: {mean_overlap * 100:.0f}%."
        )

    return MetricScore(
        name="citation_accuracy",
        score=min(1.0, max(0.0, final_score)),
        threshold=threshold,
        reasoning=reasoning,
        details={
            "total_citations": len(all_citations),
            "valid_citations": len(valid_citations),
            "out_of_bounds_citations": list(set(invalid_out_of_bounds)),
            "sentence_count": len(sentence_cites),
            "cited_sentence_count": cited_sentences_count,
            "bounds_precision": round(bounds_precision, 4),
            "citation_coverage": round(citation_coverage, 4),
            "mean_lexical_overlap": round(mean_overlap, 4),
        },
    )
