"""Provided trace, failure and run-recording utilities for the evaluation notebooks."""

import asyncio
import hashlib
import importlib.metadata
import itertools
import json
import math
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


def content_text(content):
    """Normalize text and LangChain content blocks without stringifying whole objects."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block if isinstance(block, str) else block["text"]
            for block in content if isinstance(block, str) or
            (isinstance(block, dict) and isinstance(block.get("text"), str))
        )
    return ""


def _field(item, name, default=None):
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def final_answer(state):
    """Only a final assistant message is an answer; tool output is not one."""
    messages = state.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    if _field(last, "type", _field(last, "role")) not in ("ai", "assistant"):
        return ""
    if _field(last, "tool_calls", []):
        return ""
    return content_text(_field(last, "content", "")).split("</think>")[-1].strip()


def retrieval_trace(state, tool_name="company_llc_it_knowledge_base"):
    """Read the actual retrieved artifacts, including rewrites and repeated calls."""
    calls, trace = {}, []
    for message in state.get("messages", []):
        for call in _field(message, "tool_calls", []) or []:
            calls[call["id"]] = call
        call_id = _field(message, "tool_call_id")
        call = calls.get(call_id, {})
        if _field(message, "name", call.get("name")) != tool_name:
            continue
        documents = []
        for document in _field(message, "artifact", []) or []:
            metadata = dict(_field(document, "metadata", {}) or {})
            documents.append({"page_content": _field(document, "page_content", ""),
                              "metadata": metadata})
        trace.append({"tool_call_id": call_id, "query": call.get("args", {}).get("query"),
                      "status": _field(message, "status", "success"),
                      "content": content_text(_field(message, "content", "")),
                      "documents": documents})
    return trace


def trace_contexts(trace):
    """Keep the order of documents actually observed by the agent; never re-retrieve."""
    return [f"[KB:{d['metadata'].get('source_id', 'unknown')}]\n{d['page_content']}"
            for call in trace if call["status"] != "error" for d in call["documents"]]


def search_evidence(state):
    return "\n\n".join(content_text(_field(m, "content", ""))
                       for m in state.get("messages", [])
                       if _field(m, "name") == "search_tavily"
                       and _field(m, "type", _field(m, "role")) == "tool"
                       and _field(m, "status", "success") != "error")


def error_summary(exc):
    """Record a useful status without copying credential-bearing request URLs."""
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    if status is None:
        match = re.search(r"(?:HTTP\s*|\[|status[\s:=]+)([45]\d\d)", str(exc), re.I)
        status = int(match.group(1)) if match else None
    return f"{type(exc).__name__}" + (f" (HTTP {status})" if status else "")


def _transient(exc):
    status = error_summary(exc)
    return any(str(code) in status for code in (408, 429, 500, 502, 503, 504)) or isinstance(exc, (TimeoutError, ConnectionError)) or type(exc).__name__ in ("ReadTimeout", "ConnectError", "APITimeoutError", "APIConnectionError")


def _retry_delay(exc, attempt):
    # Respect provider backpressure; immediate retries can prolong a rate limit.
    headers = getattr(getattr(exc, "response", None), "headers", {})
    try:
        retry_after = float(headers.get("retry-after", 0))
    except (ValueError, TypeError):
        retry_after = 0
    fallback = 10 * 2 ** attempt if "429" in error_summary(exc) else 2 ** attempt
    return min(max(retry_after, fallback), 60)


def invoke_with_retry(call, attempts=4):
    """Retry only transient transport/provider failures, with a bounded delay."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as exc:
            if attempt + 1 == attempts or not _transient(exc):
                raise
            time.sleep(_retry_delay(exc, attempt))


async def ainvoke_with_retry(call, attempts=4):
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as exc:
            if attempt + 1 == attempts or not _transient(exc):
                raise
            await asyncio.sleep(_retry_delay(exc, attempt))


def citation_check(answer, trace):
    """Resolve source IDs. This checks citation validity, not claim entailment."""
    cited = re.findall(r"[\[【]KB:([^\]】]+)[\]】]", answer)
    observed = {d["metadata"].get("source_id") for call in trace
                if call["status"] != "error" for d in call["documents"]}
    valid = [source for source in cited if source in observed]
    invalid = [source for source in cited if source not in observed]
    return {"citation_ids": cited, "invalid_citation_ids": invalid,
            "has_valid_citation": bool(valid),
            "all_citations_resolve": bool(cited) and not invalid}


def store_scores(row, evaluations):
    """Keep missing/failed measurements null, separate from valid low scores."""
    for metric, result in evaluations.items():
        row[f"{metric}_score"] = result.score / 5 if result.status == "ok" else None
        row[f"{metric}_status"] = result.status
        row[f"{metric}_explanation"] = result.explanation
    applicable = [r for r in evaluations.values() if r.status != "not_applicable"]
    row["aggregate_metrics"] = sorted(name for name, result in evaluations.items()
                                      if result.status != "not_applicable")
    complete = bool(applicable) and all(r.status == "ok" for r in applicable)
    row["judge_status"] = "ok" if complete else "error"
    row["aggregate_score"] = (sum(r.score for r in applicable) / len(applicable) / 5
                              if complete else None)


def skip_scores(row, metrics, reason="Agent did not produce an answer"):
    row["judge_status"] = "skipped"
    row["aggregate_score"] = None
    for metric in metrics:
        row[f"{metric}_score"] = None
        row[f"{metric}_status"] = "skipped"
        row[f"{metric}_explanation"] = reason


def score_text(value):
    return "not measured" if value is None or not math.isfinite(float(value)) else f"{value:.3f}"


def quality_summary(rows, metrics):
    """Every average travels with its own successful-measurement denominator."""
    summary = {"attempted": len(rows),
               "answers": sum(r.get("agent_status") == "ok" for r in rows),
               "fully_graded": sum(all(r.get(f"{name}_status") == "ok" for name in metrics)
                                   for r in rows),
               "metrics": {}}
    for name in metrics:
        values = [r.get(f"{name}_score") for r in rows]
        valid = [float(v) for v in values if v is not None and math.isfinite(float(v))]
        summary["metrics"][name] = {"mean": sum(valid) / len(valid) if valid else None,
                                    "valid": len(valid), "attempted": len(rows)}
    summary["complete"] = bool(rows) and summary["fully_graded"] == len(rows)
    return summary


def _json_ready(value):
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def start_run(kind, dataset_path, config, output_root):
    """Create a unique comparable run; never overwrite another experiment."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = Path(output_root) / "runs" / f"{kind}-{run_id}"
    directory.mkdir(parents=True)
    (directory / "dataset.json").write_bytes(Path(dataset_path).read_bytes())
    versions = {}
    for package in ("langchain", "langgraph", "langchain-nvidia-ai-endpoints", "ragas"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    manifest = {"run_id": run_id, "kind": kind, "created_at": datetime.now(timezone.utc).isoformat(),
                "dataset": str(dataset_path),
                "dataset_sha256": hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest(),
                "configuration": config, "package_versions": versions,
                "score_scale": "rubric score / 5; valid range 0.2–1.0; missing = null"}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return directory


def checkpoint(directory, rows, **artifacts):
    for name, value in {"results": rows, **artifacts}.items():
        destination = Path(directory) / f"{name}.json"
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(json.dumps(_json_ready(value), indent=2, default=str, allow_nan=False))
        temporary.replace(destination)


def compare_runs(before, after, metric="aggregate_score"):
    """Pair measured cases from the same dataset and criterion set; show config changes."""
    import pandas as pd
    directories = [Path(before), Path(after)]
    manifests = [json.loads((d / "manifest.json").read_text()) for d in directories]
    if manifests[0]["dataset_sha256"] != manifests[1]["dataset_sha256"]:
        raise ValueError("Different datasets: select runs of the same saved dataset for a paired comparison.")
    by_case = [{r["case_id"]: r for r in json.loads((d / "results.json").read_text())
                if r.get("agent_status") == "ok" and r.get(metric) is not None
                and (metric != "aggregate_score" or r.get("judge_status") == "ok")}
               for d in directories]
    shared = sorted(by_case[0].keys() & by_case[1].keys())
    excluded = []
    if metric == "aggregate_score":
        excluded = [key for key in shared
                    if not by_case[0][key].get("aggregate_metrics")
                    or by_case[0][key].get("aggregate_metrics") != by_case[1][key].get("aggregate_metrics")]
    pairs = [{"case_id": key, "before": by_case[0][key][metric], "after": by_case[1][key][metric],
              "delta": by_case[1][key][metric] - by_case[0][key][metric]}
             for key in shared if key not in excluded]
    configs = [m["configuration"] for m in manifests]
    changes = {k: {"before": configs[0].get(k), "after": configs[1].get(k)}
               for k in configs[0].keys() | configs[1].keys() if configs[0].get(k) != configs[1].get(k)}
    return {"paired_cases": len(pairs), "configuration_changes": changes,
            "excluded_missing_or_different_criteria": excluded,
            "scores": pd.DataFrame(pairs, columns=["case_id", "before", "after", "delta"])}


def record_config(directory, **changes):
    """Record later optional metrics in the same comparison manifest."""
    path = Path(directory) / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["configuration"].update(changes)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, default=str))
    temporary.replace(path)


_TYPOGRAPHY = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
                             "\u2212": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def quote_is_present(quote, source):
    """Check wording while ignoring Markdown decoration, typographic dashes/quotes and whitespace only.

    This locates a span; it does not establish that the span entails an answer.
    """
    def normalize(text):
        text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|[-*+]\s+)", "", text.translate(_TYPOGRAPHY))
        # A quoted bulleted list is often flattened onto one line: "details: - Current asset tag".
        text = re.sub(r"\s[-*+]\s+", " ", text)
        return " ".join(text.replace("**", "").replace("__", "").replace("`", "").split())
    value = normalize(quote)
    return bool(value) and value != "UNSUPPORTED" and value in normalize(source)


_CITATION_OR_URL = re.compile(r"[\[【](?:\d+(?:\s*[,\u2013-]\s*\d+)*|KB:[^\]】]*)[\]】]|https?://\S+")
_NUMBER = re.compile(r"(?<![\w.,])(?<![A-Za-z]-)\d+(?:[.,]\d+)*(?!\w)")
# Not claims: a report's own date stamp, and section or list numbers at the start of a line.
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_SECTION_OR_LIST_NUMBER = re.compile(r"(?m)^\s*(?:#{1,6}\s*\d+(?:\.\d+)*\.?|\d+[.)])(?=\s)")


def _numbers(text, min_digits=1):
    """Numbers as values, so "3,600" matches "3600"; citation markers and URLs are skipped."""
    values = []
    for token in _NUMBER.findall(_CITATION_OR_URL.sub(" ", text.translate(_TYPOGRAPHY))):
        value = token.replace(",", "")
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        if sum(ch.isdigit() for ch in value) >= min_digits and value not in values:
            values.append(value)
    return values


def unsupported_numbers(text, evidence):
    """List numbers in the text that never appear in the evidence: values to look up, not a verdict.

    Single digits, ISO dates (a report's date stamp) and section or list numbers are ignored. A
    number written differently in the evidence, such as 1.4 TW for 1,400 GW, is listed too.
    """
    found = set(_numbers(evidence))
    text = _SECTION_OR_LIST_NUMBER.sub(" ", _ISO_DATE.sub(" ", text.translate(_TYPOGRAPHY)))
    return [value for value in _numbers(text, min_digits=2) if value not in found]


def verify_claims(claims, evidence):
    """Check the judge's claim/quote pairs in code instead of trusting its evidence score.

    A claim counts as verified when its quote occurs in the evidence and contains every number
    in the claim. This confirms quotations; it does not prove that a quotation entails its claim.
    """
    if not isinstance(claims, list):
        return {"claims_checked": 0, "claims_verified": 0, "evidence_verified": None, "unverified_claims": []}
    unverified = []
    for item in claims:
        claim, quote = (item.get("claim"), item.get("quote")) if isinstance(item, dict) else (None, None)
        if not (isinstance(claim, str) and isinstance(quote, str) and quote_is_present(quote, evidence)
                and set(_numbers(claim)) <= set(_numbers(quote))):
            unverified.append(item)
    verified = len(claims) - len(unverified)
    return {"claims_checked": len(claims), "claims_verified": verified,
            "evidence_verified": verified / len(claims) if claims else None,
            "unverified_claims": unverified}


def evidence_flags(row, threshold=0.6):
    """Reasons to read a report against its evidence yourself. No flag is not proof of support."""
    flags = []
    score, verified = row.get("accuracy_score"), row.get("evidence_verified")
    if score is not None and score < threshold:
        flags.append("low judge evidence score")
    if score is not None and score >= 0.8 and (verified is None or verified < threshold):
        flags.append("judge evidence score not backed by verified quotes")
    numbers = row.get("unsupported_numbers") or []
    if numbers:
        flags.append(f"{len(numbers)} numbers missing from the evidence: "
                     + ", ".join(numbers[:10]) + (", ..." if len(numbers) > 10 else ""))
    return flags


def check_evidence(row, claims):
    """Record the code checks of a report's evidence next to its judge scores (after ``store_scores``)."""
    row.update(verify_claims(claims, row["source_context"]))
    row["unsupported_numbers"] = unsupported_numbers(row["report"], row["source_context"])
    row["evidence_flags"] = evidence_flags(row)
    return row


def review_sample(rows, compare=None, size=3):
    """Pick cases worth reading first: failures, the largest gaps between two measurements of
    the same case (``compare`` names two 0–1 score keys), then the lowest scores.

    A few cases are a smoke check; calibration needs independent ratings on a larger set.
    """
    def gap(row):
        values = [row.get(key) for key in compare or ()]
        if len(values) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            return None
        return abs(values[0] - values[1])
    failures = [row for row in rows if row.get("judge_status") != "ok"]
    graded = [row for row in rows if row.get("judge_status") == "ok"]
    largest_gaps = sorted((row for row in graded if gap(row) is not None), key=gap, reverse=True)
    lowest = sorted(graded, key=lambda row: row["aggregate_score"])
    picked = []
    for group in itertools.zip_longest(failures, largest_gaps, lowest):
        for row in group:
            if row is not None and len(picked) < size and all(row is not seen for seen in picked):
                picked.append(row)
    return picked


def select_dataset(data_dir, name):
    """Use synthetic cases only after their explicit review status is recorded."""
    data_dir = Path(data_dir)
    synthetic = data_dir / f"synthetic_{name}_test_cases.json"
    if synthetic.exists():
        cases = json.loads(synthetic.read_text())
        if cases and all(case.get("review_status") == "reviewed" for case in cases):
            return synthetic
        print(f"{synthetic.name} still needs review; using the provided dataset. "
              "After reviewing, set reviewed_indices in its generator and rerun the save cell.")
    return data_dir / f"{name}_test_cases.json"
