import argparse
import sys
from pathlib import Path
import subprocess
import shutil
from dynapyt.run_instrumentation import instrument_dir
from dynapyt.run_analysis import run_analysis
from dynapyt.post_run import post_run
import os
import signal
import time

# Suppress TensorFlow info/warning messages during execution
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


if __name__ == "__main__":
    # Main script to analyze a git repository using DyLin instrumentation and analysis
    parser = argparse.ArgumentParser(description="Analyze a git repo")
    parser.add_argument("--repo", help="the repo index", type=int)
    parser.add_argument("--config", help="DyLin config file path", type=str)
    parser.add_argument("--cov", help="Whether to collect coverage", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    # Unique session identifier for tracking results and logs
    session_id = "1234-abcd"

    # Load project list from projects.txt file
    here = Path(__file__).parent.resolve()
    with open(here / "projects.txt", "r") as f:
        project_infos = f.read().split("\n")

    # Filter out comment lines (starting with #)
    project_infos = [p for p in project_infos if not p.startswith("#")]

    # Parse repository metadata from projects.txt format
    project_info = project_infos[args.repo - 1].split(" ")
    if "r" in project_info[2]:
        url, commit, flags, requirements, tests = tuple(project_info)
    else:
        url, commit, flags, tests = tuple(project_info)
        requirements = None
    # Extract project name from URL (e.g., https://github.com/user/project.git -> project)
    name = url.split("/")[-1].split(".")[0].replace("-", "_")

    if not url.startswith("http"):
        # If URL is local path, convert to absolute path
        name = str((here / url).resolve())

    # Load analyses to run: either from config file or use default set
    if hasattr(args, "config") and args.config is not None:
        with open(args.config, "r") as f:
            config_content = f.read()
        analyses = config_content.strip().split("\n")
    else:
        # Default analyses list with both base analyses and ML-specific ones
        analyses = [
            f"dylin.analyses.{a}.{a}"
            for a in [
                "ComparisonBehaviorAnalysis",
                "InPlaceSortAnalysis",
                "InvalidComparisonAnalysis",
                "MutableDefaultArgsAnalysis",
                "StringConcatAnalysis",
                "WrongTypeAddedAnalysis",
                "BuiltinAllAnalysis",
                "ChangeListWhileIterating",
                "StringStripAnalysis",
                "NonFinitesAnalysis",
                # Analyses below require tensorflow, pytorch, scikit-learn dependencies
                "GradientAnalysis",
                "TensorflowNonFinitesAnalysis",
                "InconsistentPreprocessing",
            ]
        ] + [
            # Object marking analyses for taint tracking (configured via YAML files)
            f"dylin.analyses.ObjectMarkingAnalysis.ObjectMarkingAnalysis;config={a}"
            for a in [
                "/Work/DyLin/src/dylin/markings/configs/forced_order.yml",
                "/Work/DyLin/src/dylin/markings/configs/leak_preprocessing.yml",
                "/Work/DyLin/src/dylin/markings/configs/leaked_data.yml",
                # "/Work/DyLin/src/dylin/markings/configs/weak_hash.yml",
            ]
        ]

    # Determine test entry point based on test file type
    if tests.endswith(".py"):
        entry = f"{name}/dylin_run_all_tests.py"
    else:
        entry = f"{name}/{tests}/dylin_run_all_tests.py"

    code_args = {'name': name, 'tests': tests}
    # Legacy fallback: in-file pytest runner script content (currently not written to disk)
    run_all_tests = '''
import pytest
pytest.main(['-s', '--timeout=300', '--import-mode=importlib', '{name}/{tests}'])'''.format(
# pytest.main(['-o', 'log_cli=true', '-n', 'auto', '--dist', 'worksteal', '--timeout=300', '--import-mode=importlib', '{name}/{tests}'])'''.format(
        # pytest.main(['--cov={name}', '--import-mode=importlib', '{name}/{tests}'])'''.format(
        **code_args
    )
    # Default command: parallel pytest with work-stealing distribution
    command_to_run = ["pytest", '-n', 'auto', '--dist', 'worksteal', '--import-mode=importlib', f'{name}/{tests}']
    # command_to_run = ["pytest", '-s', '--import-mode=importlib', f'{name}/{tests}']
    # Some projects do not include ML stacks; skip TF/gradient analyses there
    if name in ["rich", "python_future", "requests", "keras"]:
        analyses.remove("dylin.analyses.GradientAnalysis.GradientAnalysis")
        analyses.remove("dylin.analyses.TensorflowNonFinitesAnalysis.TensorflowNonFinitesAnalysis")
    # Keras requires custom home path and selective test invocation
    if name == "keras":
        os.environ["KERAS_HOME"] = "/Work/DyLin/scripts"
        command_to_run = "pytest -n auto --dist worksteal keras --ignore keras/src/applications".split(" ")
    # kafka-python requires extra env vars and a package-installed test path
    if url == "https://github.com/dpkp/kafka-python.git":
        os.environ["CRC32C_SW_MODE"] = "auto"
        os.environ["PROJECT_ROOT"] = f"/opt/dylinVenv/lib/python3.10/site-packages/{name}"
        command_to_run = ['pytest', '-n', 'auto', '--dist', 'worksteal', '/opt/dylinVenv/lib/python3.10/site-packages/test']
    # steam_market has a single test module entrypoint
    if name == "steam_market":
        command_to_run = f"pytest -n auto --dist worksteal {name}/tests.py".split(" ")
    # Pillow tests are run through `python -m pytest` for compatibility
    if name == "Pillow":
        command_to_run = ["python", "-m", "pytest", '-n', 'auto', '--dist', 'worksteal', f'{name}/{tests}']
#         subprocess.run(["ls", "/opt/dylinVenv/lib/python3.10/site-packages/"])
#         run_all_tests = '''
# import pytest

# pytest.main(['-o', 'log_cli=true', '-n', 'auto', '--dist', 'worksteal', '--timeout=300', '--import-mode=importlib', '/Work/kafka_python/test'])'''
#         run_all_tests = '''
# import subprocess
# subprocess.run(["tox", "-c", "./kafka_python/tox.ini"])
#         '''

    #with open(entry, "w") as f:
    #    f.write(run_all_tests)
    #if tests.endswith(".py"):
    #    sys.path.append(str(Path(name).resolve()))
    #else:
    #    sys.path.append(str((Path(name).resolve()) / tests))
    #print("Wrote test runner, starting analysis")
    # Persist analysis specification file consumed by DynaPyt runtime
    with open(f"/tmp/dynapyt_analyses-{session_id}.txt", "w") as f:
        f.write("\n".join([f"{ana};output_dir=/tmp/dynapyt_output-{session_id}" for ana in analyses]))
    # Tie this process to the same DynaPyt session ID for instrumentation + post_run
    os.environ["DYNAPYT_SESSION_ID"] = session_id
    # Hard timeout per run to avoid hanging repositories
    timeout_threshold = 60*60
    timed_out = False
    analysis_time = ""
    if args.cov:
        # Coverage mode: run once and collect coverage artifacts
        os.environ["DYNAPYT_COVERAGE"] = f"/tmp/dynapyt_coverage-{session_id}"
        start = time.time()
        try:
            # subprocess.run(command_to_run)
            # Start process in a new process group so timeout can terminate all children
            proc = subprocess.Popen(command_to_run, start_new_session=True)
            proc.wait(timeout_threshold)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Kill full process group to avoid orphan subprocesses
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        # session_id = run_analysis(entry, analyses, coverage=True, coverage_dir="/Work/reports", output_dir="/Work/reports", script=run_all_tests)
        # Track elapsed wall-clock runtime for this execution
        analysis_time += f" {time.time() - start}"
        # Aggregate findings/coverage artifacts into DynaPyt output files
        post_run(coverage_dir=f"/tmp/dynapyt_coverage-{session_id}", output_dir=f"/tmp/dynapyt_output-{session_id}")
    else:
        # Non-coverage mode: ensure stale coverage env var does not leak across runs
        if "DYNAPYT_COVERAGE" in os.environ:
            del os.environ["DYNAPYT_COVERAGE"]
        # Repeat execution to reduce runtime non-determinism and increase detection chance
        for rep in range(10):
            start = time.time()
            try:
                # subprocess.run(command_to_run)
                # Run each repetition in isolated process group for reliable timeout cleanup
                proc = subprocess.Popen(command_to_run, start_new_session=True)
                proc.wait(timeout_threshold)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            # session_id = run_analysis(entry, analyses, coverage=False, output_dir="/Work/reports", script=run_all_tests)
            # Append elapsed time per repetition to support later benchmarking
            analysis_time += f" {time.time() - start}"
        # Aggregate findings from all repetitions
        post_run(output_dir=f"/tmp/dynapyt_output-{session_id}")
    # print("Finished analysis, copying coverage")
    # shutil.copy("/tmp/dynapyt_coverage/covered.jsonl", "/Work/reports/")
    with open("/Work/reports/timing.txt", "a") as f:
        # Persist timing series and timeout marker for downstream result analysis
        f.write(f"{analysis_time.strip()} {'timed out' if timed_out else ''}\n")
