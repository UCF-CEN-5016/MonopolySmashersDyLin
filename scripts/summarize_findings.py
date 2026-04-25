"""
Module for summarize_findings functionality.
"""
import json
from fire import Fire
from pathlib import Path


def _timing_txt_for_findings(findings_csv: Path) -> Path:
    """
Timing txt for findings: implementation of the _timing_txt_for_findings logic.

Args:
    findings_csv: Operational parameter.

Key Variables:
    candidate: Local state member.

Loop Behavior:
    Iterates through (findings_csv.parent.parent, findings_csv.parent.parent.parent).

Returns:
    Standard result object.
"""
    for anc in (findings_csv.parent.parent, findings_csv.parent.parent.parent):
        candidate = anc / "timing.txt"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"No timing.txt found above {findings_csv} (tried {findings_csv.parent.parent / 'timing.txt'} "
        f"and {findings_csv.parent.parent.parent / 'timing.txt'})"
    )


def _repo_relative_path(file_path: str) -> str:
    """
Repo relative path: implementation of the _repo_relative_path logic.

Args:
    file_path: Operational parameter.

Key Variables:
    s: Local state member.

Returns:
    Standard result object.
"""
    s = file_path
    if s.startswith("/Work/"):
        s = s[len("/Work/") :]
    if s.endswith(".orig"):
        s = s[: -len(".orig")]
    return s


def _load_output_sessions(output_json: Path) -> list:
    """
Load output sessions: implementation of the _load_output_sessions logic.

Args:
    output_json: Operational parameter.

Key Variables:
    data: Local state member.

Returns:
    Standard result object.
"""
    if not output_json.is_file():
        return []
    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _append_findings_for_analysis(findings: list, analysis_name: str, sessions: list) -> None:
    """
Append findings for analysis: implementation of the _append_findings_for_analysis logic.

Args:
    findings: Operational parameter.
    analysis_name: Operational parameter.
    sessions: Operational parameter.

Key Variables:
    block: Local state member.
    fnd: Local state member.
    loc: Local state member.
    rel: Local state member.
    results: Local state member.

Loop Behavior:
    Iterates through sessions.
    Iterates through (block.get("results") or {}).items().
    Iterates through ress.

Returns:
    Standard result object.
"""
    for session in sessions:
        results = session.get("results") or {}
        block = results.get(analysis_name)
        if not block or not isinstance(block, dict):
            continue
        if block.get("nmb_findings", 0) <= 0:
            continue
        for code, ress in (block.get("results") or {}).items():
            for r in ress:
                fnd = r["finding"]
                loc = fnd["location"]
                rel = _repo_relative_path(loc["file"])
                findings.append(
                    f"{rel}:{loc['start_line']}:{loc['start_column']}: {code} {fnd['msg']}"
                )


def summarize_findings(results: str):
    """
Summarize findings: implementation of the summarize_findings logic.

Args:
    results: Operational parameter.

Key Variables:
    _: Local state member.
    analysis_name: Local state member.
    findings: Local state member.
    line: Local state member.
    lines: Local state member.
    parts: Local state member.
    results: Local state member.
    sessions: Local state member.

Loop Behavior:
    Iterates through results.glob("**/findings.csv").
    Iterates through lines.
"""
    results = Path(results)
    findings = []
    for findings_csv in results.glob("**/findings.csv"):
        _ = _timing_txt_for_findings(findings_csv)  # validate reports_<i>/ layout (timing next to dynapyt_output/)
        sessions = _load_output_sessions(findings_csv.parent / "output.json")
        with open(findings_csv, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.endswith(",0"):
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            analysis_name = parts[0].strip()
            if not analysis_name:
                continue
            _append_findings_for_analysis(findings, analysis_name, sessions)
    with open(results / "DyLin_findings.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(findings))


if __name__ == "__main__":
    Fire(summarize_findings)
