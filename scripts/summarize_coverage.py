"""
Module for summarize_coverage functionality.
"""
import json
from pathlib import Path
from fire import Fire

def summarize_coverage(root_dir: str):
    """
Summarize coverage: implementation of the summarize_coverage logic.

Args:
    root_dir: Operational parameter.

Key Variables:
    checkers: Local state member.
    coverage_comparisons: Local state member.
    data: Local state member.
    here: Local state member.
    project: Local state member.
    projects: Local state member.
    result: Local state member.
    root_dir: Local state member.

Loop Behavior:
    Iterates through coverage_comparisons.
"""
    checkers = ["InconsistentPreprocessing", "InPlaceSortAnalysis", "MutableDefaultArgsAnalysis", "WrongTypeAddedAnalysis", "GradientAnalysis", "BuiltinAllAnalysis", "StringStripAnalysis", "NonFinitesAnalysis", "TensorflowNonFinitesAnalysis", "ObjectMarkingAnalysis", "StringConcatAnalysis", "InvalidComparisonAnalysis", "ComparisonBehaviorAnalysis", "ChangeListWhileIterating"]
    here = Path(__file__).resolve().parent
    with open(here / "projects.txt") as f:
        projects = [p for p in f.read().split("\n") if not p.startswith("#")]
    root_dir = Path(root_dir).resolve()
    coverage_comparisons = list(root_dir.rglob("cov_comp_*.json"))
    if not coverage_comparisons:
        print("No coverage comparisons found")
        return
    result = "Project, " + ", ".join(checkers) + ", Analysis Coverage, Test Coverage\n"
    for comparison in coverage_comparisons:
        project = projects[int(comparison.stem.split("_")[-1])-1].split(".git")[0].split("/")[-1]
        with comparison.open() as f:
            data = json.load(f)
            result += project + ", " + ", ".join([str(data[0].get(ch, 0)) for ch in checkers]) + ", " + str(data[1]) + ", " + str(data[2]) + "\n"
    print(result)

if __name__ == "__main__":
    Fire(summarize_coverage)