import logging
import os
from typing import Any, Dict, Optional
import sys
import json
import csv
import uuid
from pathlib import Path
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import Location
import traceback
from filelock import FileLock


class BaseDyLinAnalysis(BaseAnalysis):
    # Base class for all DyLin analyses that hooks into DynaPyt instrumentation
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Generate unique ID for this analysis instance (for file naming to avoid collisions)
        self.unique_id = str(uuid.uuid4())
        # Dictionary to store findings grouped by issue type/name
        self.findings = {}
        # Counter for total findings across all types (includes duplicates)
        self.number_findings = 0
        # Metadata for analysis results (e.g., statistics collected during analysis)
        self.meta = {}
        # Number of stack frames to include in error traces for debugging context
        self.stack_levels = 20
        # Output directory where JSON and CSV results are written
        self.path = Path(self.output_dir)
        if not self.path.exists():
            self.path.mkdir(parents=True)
        logging.basicConfig(stream=sys.stderr)
        self.log = logging.getLogger("TestsuiteWrapper")
        self.log.setLevel(logging.DEBUG)
        # Upper bound on unique findings this analysis type can detect
        self.number_unique_findings_possible = 33
        print(f"$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Loaded analysis {self.analysis_name if hasattr(self, 'analysis_name') else 'no name'} writing to {self.output_dir}")

    def setup(self):
        # Hook for subclasses to perform additional initialization after object construction
        pass

    def add_finding(
        self,
        iid: int,
        filename: str,
        name: Optional[str] = "placeholder name",
        msg: Optional[str] = None,
    ) -> None:
        # Record a finding at the specified IID (instruction ID) with issue code and descriptive message
        print(f"########################### Found something")
        self.number_findings += 1
        # Capture current call stack for debugging (most recent stack_levels frames)
        stacktrace = "".join(traceback.format_stack()[-self.stack_levels :])
        # Convert IID to source code location (file path, line number, column)
        location = self.iid_to_location(filename, iid)
        # Store finding under its issue name code; append to list if name already exists
        if name not in self.findings:
            self.findings[name] = [self._create_error_msg(iid, location, stacktrace, msg)]
        else:
            self.findings[name].append(self._create_error_msg(iid, location, stacktrace, msg))

    def get_result(self) -> Any:
        # Format findings into structure expected by DynaPyt post-processing pipeline
        findings = self._format_issues(self.findings)
        if len(findings) == 0:
            return None
        return {
            self.analysis_name: {
                "nmb_findings": self.number_findings,
                "is_sane": self.is_sane(),
                "meta": self.meta,
                "results": findings,
            }
        }

    def is_sane(self) -> bool:
        # Sanity check: verify total findings count matches the sum of all individual findings
        res = 0
        for name, value in self.findings.items():
            res += len(value)
        return self.number_findings == res

    def add_meta(self, meta: any):
        # Attach metadata statistics to be included in final result (e.g., analysis statistics)
        self.meta = meta

    def _create_error_msg(
        self,
        iid: int,
        location: Location,
        stacktrace: Optional[str] = None,
        msg: Optional[str] = None,
    ) -> Any:
        # Create error message dictionary with all context information needed for reporting
        return {
            "msg": msg,
            "trace": stacktrace,
            "location": location._asdict(),
            "uid": str(location),  # Unique identifier used for finding deduplication
            "iid": iid,
            "test_id": os.environ.get("PYTEST_CURRENT_TEST"),  # Track which test discovered this finding
        }

    def _format_issues(self, findings: Dict) -> Dict:
        # Group findings by IID and count duplicates (same issue found multiple times at same location)
        res = {}
        for name in findings:
            found_iids = {}
            for finding in findings[name]:
                # Use IID as key to deduplicate findings at the same source code location
                if not finding["uid"] in found_iids:
                    found_iids[finding["iid"]] = {"finding": finding, "n": 1}
                else:
                    # Increment count if duplicate found at same IID
                    found_iids[finding["iid"]]["n"] += 1
            res[name] = list(found_iids.values())
        return res

    def get_unique_findings(self):
        # Return findings deduplicated by IID (unique locations in source code)
        return self._format_issues(self.findings)

    def _write_detailed_results(self):
        # Write detailed findings to JSON file with analysis metadata for post-processing
        print(f"$$$$$$$$$$$$$$$$$$$$$ Writing results of {self.analysis_name if hasattr(self, 'analysis_name') else 'noe name'}")
        temp_res = self.get_result()
        if temp_res is not None:
            result = {"meta": self.meta, "results": temp_res}
            # Create unique filename using analysis name and UUID to avoid collisions with parallel analyses
            filename = f"output-{str(self.analysis_name)}-{self.unique_id}-report.json"
            # Ensure filename is unique by regenerating UUID if collision detected
            while (self.path / filename).exists():
                self.unique_id = str(uuid.uuid4())
                filename = f"output-{str(self.analysis_name)}-{self.unique_id}-report.json"
                # print(f"$$$$$$$$$$$$$$$$$$$$ File {filename} exists. Reading ...", file=sys.stderr)
                # with open(self.path / filename, "r") as f:
                #     rep = json.load(f)
                # for k, v in rep.items():
                #     if k == "meta" and "total_comp" in result["meta"] and "total_comp" in v:
                #         result["meta"]["total_comp"] += v["total_comp"]
                #     elif k == "results":
                #         result["results"].extend(v)
            print(f"$$$$$$$$$$$$$$$$$$$$ Writing to file {filename} ...", file=sys.stderr)
            # Write findings as formatted JSON with indentation for readability
            with open(self.path / filename, "w") as report:
                report.write(json.dumps(result, indent=4))

    def _write_overview(self):
        # Update CSV summary of findings (deduplicates by IID to prevent duplicate counts in summary)
        # Use file lock to prevent concurrent access issues from parallel analyses
        results = self.get_unique_findings()
        # Count total unique findings for this analysis (deduplicated by location)
        row_findings = 0
        for f_name in results:
            row_findings += len(results[f_name])
        csv_row = [self.analysis_name, row_findings]
        with FileLock(str(self.path / "findings.csv") + ".lock"):
            csv_rows = []
            # Read existing CSV if it exists to merge results from parallel analyses
            if (self.path / "findings.csv").exists():
                with open(self.path / "findings.csv", "r") as f:
                    reader = csv.reader(f)
                    existed = False
                    for row in reader:
                        # If analysis name already in CSV, update count by addition; else append new row
                        if self.analysis_name == row[0]:
                            csv_row = [self.analysis_name, row_findings + int(row[1])]
                            existed = True
                            csv_rows.append(csv_row)
                        else:
                            csv_rows.append(row)
                    if not existed:
                        csv_rows.append(csv_row)
            else:
                csv_rows = [csv_row]
            # Write updated CSV with all analyses and their finding counts
            with open(self.path / "findings.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerows(csv_rows)

    def end_execution(self) -> None:
        # Called at end of instrumented execution; writes all results to JSON and CSV files
        self._write_detailed_results()
        self._write_overview()
