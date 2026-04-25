"""
Module for coverage_report functionality.
"""
import json
from pathlib import Path
from typing import Optional

from fire import Fire


def _dylin_coverage_json_for_reports(reports_dir: Path) -> Optional[Path]:
    """
Dylin coverage json for reports: implementation of the _dylin_coverage_json_for_reports logic.

Args:
    reports_dir: Operational parameter.

Key Variables:
    main: Local state member.
    session_dirs: Local state member.

Loop Behavior:
    Iterates through sorted(p for p in reports_dir.glob("dynapyt_coverage-*") if p.is_dir()).
    Iterates through session_dirs.

Returns:
    Standard result object.
"""
    session_dirs = sorted(p for p in reports_dir.glob("dynapyt_coverage/dynapyt_coverage-*") if p.is_dir())
    if not session_dirs:
        for legacy in sorted(p for p in reports_dir.glob("dynapyt_coverage-*") if p.is_dir()):
            main = legacy / "coverage.json"
            if main.is_file():
                return main
        return None
    for session in session_dirs:
        main = session / "coverage.json"
        if main.is_file():
            return main
    return None


def _test_cov_json(test_dir: Path, i: int) -> Optional[Path]:
    """
Test cov json: implementation of the _test_cov_json logic.

Args:
    test_dir: Operational parameter.
    i: Operational parameter.

Key Variables:
    p1: Local state member.
    p2: Local state member.

Returns:
    Standard result object.
"""
    p1 = test_dir / f"testcov_{i}" / "cov.json"
    p2 = test_dir / f"testcov_{i}" / "testcov" / "cov.json"
    if p1.is_file():
        return p1
    if p2.is_file():
        return p2
    return None


def _timing_txt_for_coverage_json(coverage_json: Path) -> Path:
    """
Timing txt for coverage json: implementation of the _timing_txt_for_coverage_json logic.

Args:
    coverage_json: Operational parameter.

Returns:
    Standard result object.
"""
    # .../reports_<i>/dynapyt_coverage/dynapyt_coverage-.../coverage.json -> parents up to reports_<i>
    return coverage_json.parent.parent.parent / "timing.txt"


def _github_project_count() -> int:
    """
Github project count: implementation of the _github_project_count logic.

Key Variables:
    p: Local state member.

Returns:
    Standard result object.
"""
    p = Path(__file__).resolve().parent / "projects.txt"
    if not p.is_file():
        return 37
    with open(p, encoding="utf-8") as f:
        return len([ln for ln in f if ln.strip() and not ln.strip().startswith("#")])

def sanity_check(analysis_coverage, test_coverage):
    """
Sanity check: implementation of the sanity_check logic.

Args:
    analysis_coverage: Operational parameter.
    test_coverage: Operational parameter.

Key Variables:
    X: Local state member.

Loop Behavior:
    Iterates through analysis_coverage.items().
    Iterates through lines.items().
"""
    X = 0 #len("/opt/dylinVenv/lib/python3.10/site-packages/")
    for file, lines in analysis_coverage.items():
        if file[X:-5] not in test_coverage["files"]:
            print(f"File {file} not in test coverage")
            continue
        for line, analyses in lines.items():
            if int(line) not in test_coverage["files"][file[X:-5]]["executed_lines"]:
                print(f"Line {line} not in test coverage for {file}")
                continue
                

def coverage_report(analysis_coverage: str, test_coverage: str):
    """
Coverage report: implementation of the coverage_report logic.

Args:
    analysis_coverage: Operational parameter.
    test_coverage: Operational parameter.

Key Variables:
    content: Local state member.
    coverage: Local state member.
    covered_by: Local state member.
    fl: Local state member.
    test_coverage: Local state member.
    total_covered_lines: Local state member.

Loop Behavior:
    Iterates through coverage.items().
    Iterates through lines.items().
    Iterates through analyses.items().

Returns:
    Standard result object.
"""
    with open(analysis_coverage) as f:
        coverage = json.load(f)
    with open(test_coverage) as f:
        content = json.load(f)
        test_coverage = content["totals"]["covered_lines"]
    
    # sanity_check(coverage, content)
    
    covered_by = {}
    total_covered_lines = 0
    for file, lines in coverage.items():
        if file.startswith("/opt/dylinVenv/lib/python3.10/site-packages/"):
            fl = file[40:-5]
        elif file.startswith("/Work/"):
            fl = file[6:-5]
        else:
            fl = file[:-5]
        if fl not in content["files"] and file[:-5] not in content["files"]:
            continue
        if fl not in content["files"]:
            fl = file[:-5]
        for line, analyses in lines.items():
            if int(line) not in content["files"][fl]["executed_lines"]:
                continue
            total_covered_lines += 1
            for analysis, count in analyses.items():
                if analysis not in covered_by:
                    covered_by[analysis] = 0
                covered_by[analysis] += 1
    return covered_by, total_covered_lines, test_coverage

def compare_only_one(analysis_dir: str, test_dir: str):
    """
Compare only one: implementation of the compare_only_one logic.

Args:
    analysis_dir: Operational parameter.
    test_dir: Operational parameter.

Key Variables:
    covered_by: Local state member.
    test_cov: Local state member.
    test_coverage: Local state member.
    total_covered_lines: Local state member.

Loop Behavior:
    Iterates through Path(analysis_dir).glob("**/dynapyt_coverage-*/coverage*.json").
"""
    test_cov = Path(test_dir) / "cov.json"
    for ac in Path(analysis_dir).glob("**/dynapyt_coverage-*/coverage*.json"):
        print(f"{ac} {test_cov}")
        covered_by, total_covered_lines, test_coverage = coverage_report(str(ac), str(test_cov))
        with open("coverage_comparison.csv", "a") as f:
                f.write(f"{str(ac)} {total_covered_lines}, {test_coverage}\n")

def coverage_comparison(analysis_dir: str, test_dir: str, max_project: Optional[int] = None):
    """
Coverage comparison: implementation of the coverage_comparison logic.

Args:
    analysis_dir: Operational parameter.
    test_dir: Operational parameter.
    max_project: Operational parameter.

Key Variables:
    analysis_coverage: Local state member.
    analysis_dir: Local state member.
    covered_by: Local state member.
    n: Local state member.
    project_name: Local state member.
    reports_dir: Local state member.
    test_coverage: Local state member.
    test_dir: Local state member.
    timing: Local state member.
    timing_path: Local state member.

Loop Behavior:
    Iterates through range(1, n + 1).
"""
    analysis_dir = Path(analysis_dir).resolve()
    test_dir = Path(test_dir).resolve()
    n = max_project if max_project is not None else _github_project_count()
    for i in range(1, n + 1):
        reports_dir = analysis_dir / f"reports_{i}"
        analysis_coverage = _dylin_coverage_json_for_reports(reports_dir)
        if analysis_coverage is None:
            print(f"No DyLin coverage.json for project index {i} ({reports_dir})")
            continue
        test_coverage = _test_cov_json(test_dir, i)
        if test_coverage is None or not test_coverage.exists():
            print(
                f"Missing test coverage cov.json for project index {i} "
                f"(expected {test_dir}/testcov_{i}/cov.json or .../testcov_{i}/testcov/cov.json)"
            )
            continue
        if not analysis_coverage.exists():
            print(f"Missing DyLin coverage file for project index {i}: {analysis_coverage}")
            continue
        timing_path = _timing_txt_for_coverage_json(analysis_coverage)
        with open(timing_path) as f:
            timing = f.read().strip()
        project_name = timing.split(" ")[0]
        covered_by, total_covered_lines, test_coverage = coverage_report(analysis_coverage, test_coverage)
        with open("coverage_comparison.csv", "a") as f:
            f.write(f"{i}, {total_covered_lines}, {test_coverage}, {project_name}\n")
        # print(f"Project {i}:")
        # print(f"Analysis covered lines: {total_covered_lines}")
        # print(f"Test coverage: {test_coverage}")

if __name__ == '__main__':
    Fire()
                