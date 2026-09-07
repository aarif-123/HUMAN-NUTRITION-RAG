#!/usr/bin/env python
"""
evaluate.py
-----------
CLI runner for the Nutri-RAG evaluation framework.

Usage examples:
    # Run full benchmark evaluation
    python evaluate.py --mode benchmark

    # Evaluate a live query through the LangGraph RAG pipeline
    python evaluate.py --mode live --query "What are the major symptoms of scurvy?"

    # Export report to JSON and Markdown
    python evaluate.py --mode benchmark --output-json report.json --output-md report.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from typing import Optional

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import setup_logging
from app.evaluation.benchmark_dataset import get_benchmark_dataset
from app.evaluation.evaluator import RAGEvaluator
from app.evaluation.schemas import EvaluationReport, EvaluationResult, EvaluationSample
from app.services.langgraph_agent import query_agent


def _print_banner(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def _print_sample_result(res: EvaluationResult, idx: int, total: int) -> None:
    status_emoji = "[PASS]" if res.passed else "[FAIL]"
    print(f"\n[{idx}/{total}] {status_emoji} Sample: {res.sample_id}")
    print(f"Query: \"{res.query}\"")
    print(f"Overall Score: {res.overall_score * 100:.1f}% | Execution Time: {res.execution_time_seconds:.2f}s")
    print("-" * 80)
    
    # Print metrics breakdown table
    metrics = [
        ("Faithfulness (Groundedness)", res.faithfulness),
        ("Context Relevance", res.context_relevance),
        ("Answer Relevance", res.answer_relevance),
        ("Citation Accuracy", res.citation_accuracy),
    ]
    if res.refusal_adherence:
        metrics.append(("Refusal / Safety Adherence", res.refusal_adherence))

    print(f"{'Metric':<32} | {'Score':<8} | {'Pass?':<6} | {'Reasoning'}")
    print("-" * 80)
    for name, m in metrics:
        pass_str = "YES" if m.passed else "NO"
        reasoning_short = (m.reasoning[:45] + "...") if len(m.reasoning) > 48 else m.reasoning
        print(f"{name:<32} | {m.score * 100:>5.1f}%  | {pass_str:<6} | {reasoning_short}")

    # Print claim breakdown if claims were verified
    if res.claim_verifications:
        print("\n  [Verified Factual Claims]")
        for c_idx, c in enumerate(res.claim_verifications, 1):
            claim_text = (c.claim[:65] + "...") if len(c.claim) > 68 else c.claim
            print(f"    {c_idx}. [{c.status.value}] {claim_text}")


def _print_summary_report(report: EvaluationReport) -> None:
    _print_banner("EVALUATION SUMMARY REPORT")
    print(f"Total Samples Evaluated : {report.total_samples}")
    print(f"Passed Samples          : {report.passed_samples} ({report.pass_rate_percentage:.1f}%)")
    print(f"Failed Samples          : {report.failed_samples}")
    print("-" * 80)
    print(f"Mean Overall Score      : {report.mean_overall_score * 100:.1f}%")
    print(f"Mean Faithfulness       : {report.mean_faithfulness * 100:.1f}%")
    print(f"Mean Context Relevance  : {report.mean_context_relevance * 100:.1f}%")
    print(f"Mean Answer Relevance   : {report.mean_answer_relevance * 100:.1f}%")
    print(f"Mean Citation Accuracy  : {report.mean_citation_accuracy * 100:.1f}%")
    print("=" * 80 + "\n")


def generate_markdown_report(report: EvaluationReport) -> str:
    """Format the evaluation report as a clean GitHub Flavored Markdown document."""
    lines = [
        "# 🥗 Nutri-RAG Evaluation Report",
        f"\n**Timestamp:** `{report.timestamp}`",
        "\n## 📊 Executive Summary\n",
        "| Metric | Value |",
        "|---|---|",
        f"| **Total Samples** | `{report.total_samples}` |",
        f"| **Pass Rate** | **`{report.pass_rate_percentage:.1f}%`** (`{report.passed_samples}/{report.total_samples}`) |",
        f"| **Mean Overall Score** | **`{report.mean_overall_score * 100:.1f}%`** |",
        f"| **Mean Faithfulness (Groundedness)** | `{report.mean_faithfulness * 100:.1f}%` |",
        f"| **Mean Context Relevance** | `{report.mean_context_relevance * 100:.1f}%` |",
        f"| **Mean Answer Relevance** | `{report.mean_answer_relevance * 100:.1f}%` |",
        f"| **Mean Citation Accuracy** | `{report.mean_citation_accuracy * 100:.1f}%` |",
        "\n## 🧪 Detailed Results Breakdown\n",
    ]

    for idx, r in enumerate(report.results, 1):
        status_badge = "✅ **PASS**" if r.passed else "❌ **FAIL**"
        lines.append(f"### {idx}. `{r.sample_id}` — {status_badge}\n")
        lines.append(f"- **Query:** *\"{r.query}\"*")
        lines.append(f"- **Overall Score:** `{r.overall_score * 100:.1f}%`")
        lines.append(f"- **Execution Time:** `{r.execution_time_seconds:.2f}s`\n")
        
        lines.append("| Dimension | Score | Threshold | Passed | Justification |")
        lines.append("|---|---|---|---|---|")
        lines.append(f"| **Faithfulness** | `{r.faithfulness.score * 100:.1f}%` | `{r.faithfulness.threshold * 100:.0f}%` | {'Yes' if r.faithfulness.passed else '**No**'} | {r.faithfulness.reasoning} |")
        lines.append(f"| **Context Relevance** | `{r.context_relevance.score * 100:.1f}%` | `{r.context_relevance.threshold * 100:.0f}%` | {'Yes' if r.context_relevance.passed else '**No**'} | {r.context_relevance.reasoning} |")
        lines.append(f"| **Answer Relevance** | `{r.answer_relevance.score * 100:.1f}%` | `{r.answer_relevance.threshold * 100:.0f}%` | {'Yes' if r.answer_relevance.passed else '**No**'} | {r.answer_relevance.reasoning} |")
        lines.append(f"| **Citation Accuracy** | `{r.citation_accuracy.score * 100:.1f}%` | `{r.citation_accuracy.threshold * 100:.0f}%` | {'Yes' if r.citation_accuracy.passed else '**No**'} | {r.citation_accuracy.reasoning} |")
        if r.refusal_adherence:
            lines.append(f"| **Refusal Adherence** | `{r.refusal_adherence.score * 100:.1f}%` | `{r.refusal_adherence.threshold * 100:.0f}%` | {'Yes' if r.refusal_adherence.passed else '**No**'} | {r.refusal_adherence.reasoning} |")
        lines.append("\n---\n")

    return "\n".join(lines)


def run_benchmark(output_json: Optional[str] = None, output_md: Optional[str] = None) -> EvaluationReport:
    """Run evaluation on the built-in benchmark dataset."""
    _print_banner("RUNNING NUTRI-RAG BENCHMARK EVALUATION")
    evaluator = RAGEvaluator()
    dataset = get_benchmark_dataset()

    print(f"Loaded {len(dataset.samples)} benchmark test samples from '{dataset.name}'.")
    
    results = []
    for idx, sample in enumerate(dataset.samples, 1):
        print(f"\nEvaluating test sample {idx}/{len(dataset.samples)}: {sample.sample_id}...")
        res = evaluator.evaluate_sample(sample)
        results.append(res)
        _print_sample_result(res, idx, len(dataset.samples))

    report = evaluator.evaluate_dataset(dataset)
    _print_summary_report(report)

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        print(f"[OK] Exported JSON report to: {output_json}")

    if output_md:
        md_content = generate_markdown_report(report)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[OK] Exported Markdown report to: {output_md}")

    return report


def run_live_query(query: str, output_json: Optional[str] = None) -> EvaluationResult:
    """Execute query against live LangGraph agent and evaluate the response."""
    _print_banner(f"EVALUATING LIVE QUERY: \"{query}\"")
    
    # 1. Execute live pipeline
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    print(f"Executing LangGraph agent (session_id={session_id})...")
    output = query_agent.invoke({"query": query}, config=config)

    response = output.get("response", "")
    chunks = output.get("chunks", [])
    intent = output.get("intent", "UNKNOWN")

    print(f"Response received ({len(chunks)} chunks retrieved, intent={intent}).")
    print(f"\nResponse:\n{response}\n")

    sample = EvaluationSample(
        sample_id=f"LIVE_{session_id[:8]}",
        query=query,
        context_chunks=chunks,
        response=response,
        intent=intent,
    )

    evaluator = RAGEvaluator()
    print("Evaluating live response against RAG criteria...")
    res = evaluator.evaluate_sample(sample)
    _print_sample_result(res, 1, 1)

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(res.model_dump(), f, indent=2)
        print(f"[OK] Exported JSON result to: {output_json}")

    return res


def main() -> None:
    parser = argparse.ArgumentParser(description="Nutri-RAG Evaluation CLI")
    parser.add_argument(
        "--mode",
        choices=["benchmark", "live"],
        default="benchmark",
        help="Evaluation mode: 'benchmark' runs the standard suite, 'live' queries agent.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What is the role of Vitamin C in collagen synthesis?",
        help="Query to evaluate in live mode.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to export JSON evaluation report.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=None,
        help="Optional path to export Markdown evaluation report.",
    )
    args = parser.parse_args()

    setup_logging("INFO")

    if args.mode == "benchmark":
        run_benchmark(output_json=args.output_json, output_md=args.output_md)
    elif args.mode == "live":
        run_live_query(query=args.query, output_json=args.output_json)


if __name__ == "__main__":
    main()
