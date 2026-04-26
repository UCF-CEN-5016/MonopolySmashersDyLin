import argparse
import sys
import tempfile
from pathlib import Path

import docker

from dylin.select_checkers import select_checkers

# Repo root: src/dylin/cli.py -> src/dylin -> src -> repo root
_DYLIN_ROOT = Path(__file__).parent.parent.parent.resolve()


def instrument_and_run_analysis(project_root, analysis_file, output_dir, setup_cmd, run_command):
    """Docker-based DynaPyt instrumentation + run, with DyLin pre-installed in the container."""
    # Initialize Docker client with 240-second timeout for all container operations
    client = docker.from_env(timeout=240)

    # Build a Docker image with DynaPyt (DyLin is installed at runtime from mounted source)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Define Dockerfile with Python 3.13 slim image and required dependencies
        dockerfile_content = """\
FROM python:3.13-slim
RUN apt-get update && apt-get install -y gcc git
RUN pip install --upgrade pip
RUN pip install git+https://github.com/sola-st/DynaPyt.git@main#egg=dynapyt
RUN pip install git+https://github.com/sola-st/DyLin.git@main#egg=dylin
"""
        (temp_dir_path / "Dockerfile").write_text(dockerfile_content)

        print("Building Docker image with DynaPyt installed...")
        try:
            # Build Docker image from the generated Dockerfile and stream build logs
            image, logs = client.images.build(
                path=str(temp_dir_path), tag="dynapyt_runner", rm=True
            )
            # Print each build log line that contains "stream" key for user feedback
            for log in logs:
                if "stream" in log:
                    print(log["stream"], end="")
        except docker.errors.BuildError as e:
            # Handle Docker build errors by printing all available logs and exiting gracefully
            print("Failed to build Docker image:")
            for log in e.build_logs:
                if "stream" in log:
                    print(log["stream"], end="")
            return

    print(f"\nRunning container for project {project_root}...")
    print(f"Analysis file: {analysis_file}")
    print(f"Setup command: {setup_cmd}")
    print(f"Output directory: {output_dir}")
    print(f"Run command: {run_command}")

    # Set the container output directory path (will be mounted from the host)
    tmp_output_dir = "/tmp/dynapyt_output"

    # Rewrite analysis file so output_dir points to the container path instead of host path
    final_analysis_file = analysis_file.parent / "final_analysis.txt"
    content = analysis_file.read_text()
    with open(final_analysis_file, "w") as f:
        for line in content.splitlines():
            # If output_dir not specified in line, append container path; otherwise replace with container path
            if ";output_dir=" not in line:
                f.write(line + f";output_dir={tmp_output_dir}\n")
            else:
                # Split on output_dir= to replace host path with container path
                analysis, _ = line.split(";output_dir=")
                f.write(analysis + f";output_dir={tmp_output_dir}\n")

    # Create entrypoint script for Docker container that orchestrates instrumentation and test execution
    entrypoint_script = f"""\
#!/bin/bash
set -e
# Copy project to container's /tmp to ensure writable filesystem
cp -r /project_root /tmp/project
cd /tmp/project
# Run optional setup command (e.g., install dependencies)
{setup_cmd}
# Add analysis directory to Python path so DyLin can find analysis modules
export PYTHONPATH="/analysis:$PYTHONPATH"
# Instrument Python code using DynaPyt with specified analyses
python -m dynapyt.run_instrumentation --directory . --analysisFile /analysis/final_analysis.txt
# Set session ID for tracking this analysis run
export DYNAPYT_SESSION_ID="1234-abcd"
# Copy analysis file to standard location for post-processing
cp /analysis/final_analysis.txt /tmp/dynapyt_analyses-1234-abcd.txt
# Execute the test command (e.g., pytest) on instrumented code
{run_command}
# Post-process coverage and results
python -m dynapyt.post_run --coverage_dir="" --output_dir={tmp_output_dir}
# Format findings JSON output to human-readable text if it exists
if [ -f "{tmp_output_dir}/output.json" ]; then
    python -m dylin.format_output --findings_path {tmp_output_dir}/output.json > {tmp_output_dir}/output.txt
fi
"""

    try:
        # Start Docker container with mounted volumes for project, analysis configs, and output
        container = client.containers.run(
            "dynapyt_runner",
            command=["/bin/bash", "-c", entrypoint_script],
            # Mount project as read-only so it cannot be accidentally modified
            mounts=[
                docker.types.Mount(
                    target="/project_root", source=str(project_root), type="bind", read_only=True
                ),
                # Mount analysis directory with read-write access for creating output files
                docker.types.Mount(
                    target="/analysis", source=str(analysis_file.parent), type="bind", read_only=False
                ),
                # Mount output directory for capturing analysis findings
                docker.types.Mount(
                    target="/tmp/dynapyt_output", source=str(output_dir), type="bind", read_only=False
                ),
                # Mount DyLin source as read-only for potential dynamic loading
                docker.types.Mount(
                    target="/dylin_src", source=str(_DYLIN_ROOT), type="bind", read_only=True
                ),
            ],
            # Remove container after execution to clean up resources; stream=True allows real-time output
            remove=True,
            stdout=True,
            stderr=True,
            stream=True,
        )
        # Stream container output to console in real-time as it executes
        for line in container:
            print(line.decode("utf-8"), end="")
    except docker.errors.ContainerError as e:
        # Handle container execution errors and display container logs
        print(f"Container error: {e}")
        try:
            print(e.container.logs().decode("utf-8"))
        except docker.errors.NotFound:
            pass


def main():
    # Set up command-line argument parser for DyLin CLI
    parser = argparse.ArgumentParser(description="DyLin: Dynamic Linter for Python")
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to the root directory of the project to analyze.",
    )
    parser.add_argument(
        "--include",
        default="all",
        help='Comma-separated list of checkers to include (default: "all").',
    )
    parser.add_argument(
        "--exclude",
        default="none",
        help='Comma-separated list of checkers to exclude (default: "none").',
    )
    parser.add_argument(
        "--analysis",
        default=None,
        help="Path to an analysis file. If provided, overrides --include/--exclude.",
    )
    parser.add_argument(
        "--setup",
        required=False,
        default="",
        help="Setup script/command to run inside the container before instrumentation.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to save the raw output from DyLin/DynaPyt.",
    )
    parser.add_argument(
        "run_command",
        nargs=argparse.REMAINDER,
        help="Command to run after instrumentation (e.g. `pytest tests` or `python main.py`).",
    )

    args = parser.parse_args()

    # Resolve and validate project root path exists and is a directory
    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(
            f"Error: Project root '{project_root}' does not exist or is not a directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse and validate run_command from remaining arguments, removing leading "--" separator if present
    run_cmd_list = args.run_command
    if run_cmd_list and run_cmd_list[0] == "--":
        run_cmd_list = run_cmd_list[1:]
    if not run_cmd_list:
        print("Error: No run command provided.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    run_command = " ".join(run_cmd_list)

    # Build the analyses/checkers list to run: either from explicit file or from include/exclude filters
    if args.analysis is not None:
        # Use explicit analysis file if provided
        analysis_file = Path(args.analysis).resolve()
    else:
        # Generate analysis list based on include/exclude parameters
        checkers_str = select_checkers(include=args.include, exclude=args.exclude)
        if not checkers_str.strip():
            print(
                "Error: No checkers selected with the given --include/--exclude parameters.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Write generated analysis list to temporary file for passing to Docker
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="dylin_analysis_", delete=False
        )
        tmp.write(checkers_str)
        tmp.close()
        analysis_file = Path(tmp.name)

    # Execute instrumentation and analysis in Docker container
    instrument_and_run_analysis(
        project_root=project_root,
        analysis_file=analysis_file,
        output_dir=output_dir,
        setup_cmd=args.setup,
        run_command=run_command,
    )


if __name__ == "__main__":
    main()
