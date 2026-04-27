# -----------------------------
# Stage 1: Set up Python environment and dependencies
# -----------------------------
echo "[1/7] Setting up virtual environment and installing dependencies..."
python -m venv .venv
source .venv/bin/activate

# Install test and runtime requirements used by the pipeline.
pip install -r requirements-tests.txt
# pip install -r requirements.txt

# -----------------------------
# Stage 2: Run test suite
# -----------------------------
echo "[2/7] Running tests..."
pytest tests

# -----------------------------
# Stage 3: Build Docker images for analysis workflows
# -----------------------------
echo "[3/7] Building Docker images (project, linter, and test coverage)..."
bash build_projects.sh
bash build_linters.sh
bash build_testcovs.sh
# Optional: enable if Kaggle API credentials are configured locally.
# bash build_kaggle.sh # Comment out if you don't have Kaggle API credentials

# -----------------------------
# Stage 4: Run dynamic analysis workflows with coverage enabled (RQ1)
# -----------------------------
echo "[4/7] Running dynamic analysis with coverage..."
# bash run_all_no_cov.sh # Comment out if you don't want to run dynamic linters without coverage
bash run_all_with_cov.sh

# -----------------------------
# Stage 5: Summarize dynamic findings 
# -----------------------------
echo "[5/7] Summarizing dynamic analysis findings..."
python ./scripts/summarize_findings.py --results ./project_results

# -----------------------------
# Stage 6: Run static linters and compare static vs dynamic findings (RQ3)
# -----------------------------
echo "[6/7] Running static linters and comparing with dynamic findings..."
bash run_all_linters.sh
python scripts/compare_static_dynamic_linters.py --static_dir ./project_lints --dynamic ./project_results/DyLin_findings.txt

# -----------------------------
# Stage 7: Collect and report test coverage metrics (RQ4)
# -----------------------------
echo "[7/7] Running test coverage pipeline and generating comparison report..."
bash run_all_testcov.sh
python ./scripts/coverage_report.py coverage_comparison --analysis_dir ./project_results --testcov_dir ./project_testcovs

echo "Pipeline complete."

