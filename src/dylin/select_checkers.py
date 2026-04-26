from pathlib import Path
import fire

# Get path to this module's directory for loading analysis configs
here = Path(__file__).parent.resolve()

# Registry of all available issue codes mapped to analysis implementations
# Each issue has a standardized code (e.g., PC-01), a human-readable name, the analysis class path, and historical aliases
issue_codes = {
    # PC = Program Correctness checks
    "PC-01": {
        "name": "InvalidFunctionComparison",
        "analysis": "dylin.analyses.InvalidComparisonAnalysis.InvalidComparisonAnalysis",
        "aliases": ["A-15"],  # Historical code from earlier versions
    },
    # PC-02: Detect risky float comparisons which may have precision issues
    "PC-02": {
        "name": "RiskyFloatComparison",
        "analysis": "dylin.analyses.InvalidComparisonAnalysis.InvalidComparisonAnalysis",
        "aliases": ["A-12"],
    },
    "PC-03": {
        # Detect adding value of unexpected type to mostly homogeneous containers
        "name": "WrongTypeAdded",
        "analysis": "dylin.analyses.WrongTypeAddedAnalysis.WrongTypeAddedAnalysis",
        "aliases": ["A-11"],
    },
    "PC-04": {
        # Detect mutating list length while iterating over it
        "name": "ChangeListWhileIterating",
        "analysis": "dylin.analyses.ChangeListWhileIterating.ChangeListWhileIterating",
        "aliases": ["A-22"],
    },
    "PC-05": {
        # Detect repeated membership checks in large lists (performance smell)
        "name": "ItemInList",
        "analysis": "dylin.analyses.ItemInListAnalysis.ItemInListAnalysis",
        "aliases": [],
    },
    "SL-01": {
        # Detect unnecessary usage of sorted(...) when in-place sort is enough
        "name": "InPlaceSort",
        "analysis": "dylin.analyses.InPlaceSortAnalysis.InPlaceSortAnalysis",
        "aliases": ["A-09"],
    },
    "SL-02": {
        # Detect surprising any/all behavior for edge-case iterables
        "name": "AnyAllMisuse",
        "analysis": "dylin.analyses.BuiltinAllAnalysis.BuiltinAllAnalysis",
        "aliases": ["A-21"],
    },
    "SL-03": {
        # Detect risky or redundant uses of strip/lstrip/rstrip operations
        "name": "StringStrip",
        "analysis": "dylin.analyses.StringStripAnalysis.StringStripAnalysis",
        "aliases": ["A-19", "A-20"],
    },
    "SL-04": {
        # Detect expensive string concatenation patterns in loops/runtime paths
        "name": "StringConcat",
        "analysis": "dylin.analyses.StringConcatAnalysis.StringConcatAnalysis",
        "aliases": ["A-05"],
    },
    "SL-05": {
        # Detect comparisons between incompatible types
        "name": "InvalidTypeComparison",
        "analysis": "dylin.analyses.InvalidComparisonAnalysis.InvalidComparisonAnalysis",
        "aliases": ["A-13"],
    },
    "SL-06": {
        # Detect reliance on potentially nondeterministic ordering semantics
        "name": "NondeterministicOrder",
        "analysis": f"dylin.analyses.ObjectMarkingAnalysis.ObjectMarkingAnalysis;config={here/'markings/configs/forced_order.yml'}",
        "aliases": ["A-18"],
    },
    "SL-7": {
        # Detect random distribution parameters that make positive values impossible
        "name": "RandomParams_NoPositives",
        "analysis": "dylin.analyses.RandomParams_NoPositives.RandomParams_NoPositives",
        "aliases": ["B-12"],
    },
    "SL-8": {
        # Detect invalid kwargs usage for random.randrange APIs
        "name": "RandomRandrange_MustNotUseKwargs",
        "analysis": "dylin.analyses.RandomRandrange_MustNotUseKwargs.RandomRandrange_MustNotUseKwargs",
        "aliases": ["B-13"],
    },
    "SL-9": {
        # Detect thread subclasses that override run in problematic ways
        "name": "Thread_OverrideRun",
        "analysis": "dylin.analyses.Thread_OverrideRun.Thread_OverrideRun",
        "aliases": ["B-20"],
    },
    "CF-01": {
        # Detect operator-overriding behavior that changes comparison semantics
        "name": "WrongOperatorOverriding",
        "analysis": "dylin.analyses.ComparisonBehaviorAnalysis.ComparisonBehaviorAnalysis",
        "aliases": ["A-01", "A-03", "A-04"],
    },
    # "CF-02": {
    #     "name": "MutableDefaultArgs",
    #     "analysis": "dylin.analyses.MutableDefaultArgsAnalysis.MutableDefaultArgsAnalysis",
    #     "aliases": ["A-10"],
    # },
    "ML-01": {
        # Detect train/test preprocessing mismatch in ML pipelines
        "name": "InconsistentPreprocessing",
        "analysis": "dylin.analyses.InconsistentPreprocessing.InconsistentPreprocessing",
        "aliases": ["M-23"],
    },
    "ML-02": {
        # Detect leakage via tainted data flowing into model training/evaluation steps
        "name": "DataLeakage",
        "analysis": f"dylin.analyses.ObjectMarkingAnalysis.ObjectMarkingAnalysis;config={here/'markings/configs/leaked_data.yml'}"
        + f"\ndylin.analyses.ObjectMarkingAnalysis.ObjectMarkingAnalysis;config={here/'markings/configs/leak_preprocessing.yml'}",
        "aliases": ["M-24", "M-25"],
    },
    "ML-03": {
        # Detect NaN/Inf and other non-finite values in model data or tensors
        "name": "NonFiniteValues",
        "analysis": "dylin.analyses.NonFinitesAnalysis.NonFinitesAnalysis"
        + "\ndylin.analyses.TensorflowNonFinitesAnalysis.TensorflowNonFinitesAnalysis",
        "aliases": ["M-26", "M-27", "M-32", "M-33"],
    },
    "ML-04": {
        # Detect exploding gradients during training runtime
        "name": "GradientExplosion",
        "analysis": "dylin.analyses.GradientAnalysis.GradientAnalysis",
        "aliases": ["M-28"],
    },
    "TP-01": {
        # Detect hostname formatting bug where value ends with '/'
        "name": "HostnamesTerminatesWithSlash",
        "analysis": "dylin.analyses.HostnamesTerminatesWithSlash.HostnamesTerminatesWithSlash",
        "aliases": ["B-6"],
    },
    "TP-02": {
        # Detect known NLTK regexp_span_tokenize misuse pattern
        "name": "NLTK_regexp_span_tokenize",
        "analysis": "dylin.analyses.NLTK_regexp_span_tokenize.NLTK_regexp_span_tokenize",
        "aliases": ["B-8"],
    },
    "TP-03": {
        # Detect requests APIs receiving text-mode file handles where binary is required
        "name": "Requests_DataMustOpenInBinary",
        "analysis": "dylin.analyses.Requests_DataMustOpenInBinary.Requests_DataMustOpenInBinary",
        "aliases": ["B-14"],
    },
    "TP-04": {
        # Detect session upload APIs receiving text-mode file handles where binary is required
        "name": "Session_DataMustOpenInBinary",
        "analysis": "dylin.analyses.Session_DataMustOpenInBinary.Session_DataMustOpenInBinary",
        "aliases": ["B-15"],
    },
}


def select_checkers(include: str = "all", exclude: str = "none", output_dir: str = None) -> str:
    # Normalize None values to sentinel strings used by CLI/API callers
    if include is None:
        include = "none"
    if exclude is None:
        exclude = "none"
    if include.lower() == "all" and exclude.lower() == "none":
        # Fast-path: return all analyses
        res = "\n".join([issue["analysis"] for _, issue in issue_codes.items()])
    elif include.lower() == "all":
        # Include all except explicit exclusions by code or human-readable name
        res = "\n".join(
            [
                issue["analysis"]
                for code, issue in issue_codes.items()
                if (code not in exclude and issue["name"] not in exclude)
            ]
        )
    elif exclude.lower() == "none":
        # Include only explicit selections by code or human-readable name
        res = "\n".join(
            [issue["analysis"] for code, issue in issue_codes.items() if (code in include or issue["name"] in include)]
        )
    else:
        # Apply include and exclude filters together
        res = "\n".join(
            [
                issue["analysis"]
                for code, issue in issue_codes.items()
                if (code in include or issue["name"] in include)
                and (code not in exclude and issue["name"] not in exclude)
            ]
        )
    if output_dir is not None:
        # Attach output directory to each analysis spec for DynaPyt execution
        return "\n".join([f"{ana};output_dir={output_dir}" for ana in res.split("\n")])
    return res


if __name__ == "__main__":
    fire.Fire(select_checkers)
