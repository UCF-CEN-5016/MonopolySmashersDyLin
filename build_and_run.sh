NO_BUILD=false
RUN_TEST=true
RUN_STATIC_LINTERS=true
RUN_COVERAGE=true
DYNAMIC_MODE="cov"

while [ "$#" -gt 0 ]; do
	case "$1" in
		--no-build)
			NO_BUILD=true
			;;
		--test)
			RUN_TEST=true
			;;
		--no-test)
			RUN_TEST=false
			;;
		--cov)
			DYNAMIC_MODE="cov"
			;;
		--no_cov|--no-cov)
			DYNAMIC_MODE="no_cov"
			;;
		--static_linters|--static-linters)
			RUN_STATIC_LINTERS=true
			;;
		--no-static_linters|--no-static-linters)
			RUN_STATIC_LINTERS=false
			;;
		--coverage)
			RUN_COVERAGE=true
			;;
		--no-coverage)
			RUN_COVERAGE=false
			;;
		-h|--help)
			echo "Usage: bash build_and_run.sh [--no-build] [--test|--no-test] [--cov|--no_cov] [--static_linters|--no-static-linters] [--coverage|--no-coverage]"
			echo "  --no-build          Skip Docker image build steps and reuse existing images."
			echo "  --test              Run test stage (default)."
			echo "  --no-test           Skip test stage."
			echo "  --cov               Run dynamic analysis with coverage (default)."
			echo "  --no_cov            Run dynamic analysis without coverage."
			echo "  --static_linters    Run static linter comparison stage (default)."
			echo "  --no-static-linters Skip static linter comparison stage."
			echo "  --coverage          Run test coverage stage (default)."
			echo "  --no-coverage       Skip test coverage stage."
			exit 0
			;;
		*)
			echo "Unknown option: $1"
			echo "Usage: bash build_and_run.sh [--no-build] [--test|--no-test] [--cov|--no_cov] [--static_linters|--no-static-linters] [--coverage|--no-coverage]"
			exit 1
			;;
	esac
	shift
done

# -----------------------------
# Stage 1: Set up Python environment and dependencies
# -----------------------------
echo "[1/7] Setting up virtual environment and installing dependencies..."
python -m venv .venv
source .venv/bin/activate

# Install test requirements only when the test stage is enabled.
if [ "$RUN_TEST" = true ]; then
	pip install -r requirements-tests.txt
else
	echo "[1/7] Skipping test dependency install (--no-test enabled)."
fi
# pip install -r requirements.txt

# -----------------------------
# Stage 2: Run test suite
# -----------------------------
if [ "$RUN_TEST" = true ]; then
	echo "[2/7] Running tests..."
	pytest tests
else
	echo "[2/7] Skipping tests (--no-test enabled)."
fi

# -----------------------------
# Stage 3: Build Docker images for analysis workflows
# -----------------------------
if [ "$NO_BUILD" = true ]; then
	echo "[3/7] Skipping Docker image builds (--no-build enabled)."
else
	echo "[3/7] Building Docker images (project, linter, and test coverage)..."
	bash build_projects.sh
	bash build_linters.sh
	bash build_testcovs.sh
fi
# Optional: enable if Kaggle API credentials are configured locally.
# bash build_kaggle.sh # Comment out if you don't have Kaggle API credentials

# -----------------------------
# Stage 4: Run dynamic analysis workflows with coverage enabled (RQ1)
# -----------------------------
DYNAMIC_RAN=false
if [ "$DYNAMIC_MODE" = "no_cov" ]; then
	echo "[4/7] Running dynamic analysis without coverage..."
	bash run_all_no_cov.sh
	DYNAMIC_RAN=true
else
	echo "[4/7] Running dynamic analysis with coverage..."
	bash run_all_with_cov.sh
	DYNAMIC_RAN=true
fi

# -----------------------------
# Stage 5: Summarize dynamic findings 
# -----------------------------
if [ "$DYNAMIC_RAN" = true ]; then
	echo "[5/7] Summarizing dynamic analysis findings..."
	python ./scripts/summarize_findings.py --results ./project_results
else
	echo "[5/7] Skipping summary because dynamic analysis did not run."
fi

# -----------------------------
# Stage 6: Run static linters and compare static vs dynamic findings (RQ3)
# -----------------------------
if [ "$RUN_STATIC_LINTERS" = true ]; then
	echo "[6/7] Running static linters and comparing with dynamic findings..."
	bash run_all_linters.sh
	python scripts/compare_static_dynamic_linters.py --static_dir ./project_lints --dynamic ./project_results/DyLin_findings.txt
else
	echo "[6/7] Skipping static linter comparison (--no-static-linters enabled)."
fi

# -----------------------------
# Stage 7: Collect and report test coverage metrics (RQ4)
# -----------------------------
if [ "$RUN_COVERAGE" = true ]; then
	echo "[7/7] Running test coverage pipeline and generating comparison report..."
	bash run_all_testcov.sh
	python ./scripts/coverage_report.py coverage_comparison --analysis_dir ./project_results --testcov_dir ./project_testcovs
else
	echo "[7/7] Skipping coverage stage (--no-coverage enabled)."
fi

echo "Pipeline complete."

