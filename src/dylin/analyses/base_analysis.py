"""
Module for base_analysis functionality.
"""
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
    """
Basedylinanalysis: logical component class.
"""
    def __init__(self, **kwargs) -> None:
        """
Init: implementation of the __init__ logic.

Key Variables:
    findings: Local state member.
    log: Local state member.
    meta: Local state member.
    number_findings: Local state member.
    number_unique_findings_possible: Local state member.
    path: Local state member.
    stack_levels: Local state member.
    unique_id: Local state member.

Returns:
    Standard result object.
"""
        super().__init__(**kwargs)
        self.unique_id = str(uuid.uuid4())
        self.findings = {}
        self.number_findings = 0
        self.meta = {}
        self.stack_levels = 20
        self.path = Path(self.output_dir)
        if not self.path.exists():
            self.path.mkdir(parents=True)
        logging.basicConfig(stream=sys.stderr)
        self.log = logging.getLogger("TestsuiteWrapper")
        self.log.setLevel(logging.DEBUG)
        self.number_unique_findings_possible = 33
        print(f"$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Loaded analysis {self.analysis_name if hasattr(self, 'analysis_name') else 'no name'} writing to {self.output_dir}")

    def setup(self):
        """
Setup: implementation of the setup logic.
"""
        # Hook for subclasses
        pass

    def add_finding(
        self,
        iid: int,
        filename: str,
        name: Optional[str] = "placeholder name",
        msg: Optional[str] = None,
    ) -> None:
        """
Add finding: implementation of the add_finding logic.

Args:
    iid: Instruction identifier.
    filename: Source file name.
    name: Entity name.
    msg: Informational message.

Key Variables:
    location: Local state member.
    number_findings: Local state member.
    stacktrace: Local state member.

Returns:
    Standard result object.
"""
        print(f"########################### Found something")
        self.number_findings += 1
        stacktrace = "".join(traceback.format_stack()[-self.stack_levels :])
        location = self.iid_to_location(filename, iid)
        if name not in self.findings:
            self.findings[name] = [self._create_error_msg(iid, location, stacktrace, msg)]
        else:
            self.findings[name].append(self._create_error_msg(iid, location, stacktrace, msg))

    def get_result(self) -> Any:
        """
Get result: implementation of the get_result logic.

Key Variables:
    findings: Local state member.

Returns:
    Standard result object.
"""
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

    """
    sanity check to make sure all findings are added properly
    """

    def is_sane(self) -> bool:
        """
Is sane: implementation of the is_sane logic.

Key Variables:
    res: Local state member.

Loop Behavior:
    Iterates through self.findings.items().

Returns:
    Standard result object.
"""
        res = 0
        for name, value in self.findings.items():
            res += len(value)
        return self.number_findings == res

    def add_meta(self, meta: any):
        """
Add meta: implementation of the add_meta logic.

Args:
    meta: Operational parameter.

Key Variables:
    meta: Local state member.
"""
        self.meta = meta

    def _create_error_msg(
        self,
        iid: int,
        location: Location,
        stacktrace: Optional[str] = None,
        msg: Optional[str] = None,
    ) -> Any:
        """
Create error msg: implementation of the _create_error_msg logic.

Args:
    iid: Instruction identifier.
    location: Source code location.
    stacktrace: Operational parameter.
    msg: Informational message.

Returns:
    Standard result object.
"""
        return {
            "msg": msg,
            "trace": stacktrace,
            "location": location._asdict(),
            "uid": str(location),
            "iid": iid,
            "test_id": os.environ.get("PYTEST_CURRENT_TEST"),
        }

    def _format_issues(self, findings: Dict) -> Dict:
        """
Format issues: implementation of the _format_issues logic.

Args:
    findings: Operational parameter.

Key Variables:
    found_iids: Local state member.
    res: Local state member.

Loop Behavior:
    Iterates through findings.
    Iterates through findings[name].

Returns:
    Standard result object.
"""
        res = {}
        for name in findings:
            found_iids = {}
            for finding in findings[name]:
                if not finding["uid"] in found_iids:
                    found_iids[finding["iid"]] = {"finding": finding, "n": 1}
                else:
                    found_iids[finding["iid"]]["n"] += 1
            res[name] = list(found_iids.values())
        return res

    def get_unique_findings(self):
        """
Get unique findings: implementation of the get_unique_findings logic.

Returns:
    Standard result object.
"""
        return self._format_issues(self.findings)

    def _write_detailed_results(self):
        """
Write detailed results: implementation of the _write_detailed_results logic.

Key Variables:
    filename: Local state member.
    result: Local state member.
    temp_res: Local state member.
    unique_id: Local state member.

Loop Behavior:
    Loops while (self.path / filename).exists().
"""
        print(f"$$$$$$$$$$$$$$$$$$$$$ Writing results of {self.analysis_name if hasattr(self, 'analysis_name') else 'noe name'}")
        temp_res = self.get_result()
        if temp_res is not None:
            result = {"meta": self.meta, "results": temp_res}
            filename = f"output-{str(self.analysis_name)}-{self.unique_id}-report.json"
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
            with open(self.path / filename, "w") as report:
                report.write(json.dumps(result, indent=4))

    def _write_overview(self):
        """
Write overview: implementation of the _write_overview logic.

Key Variables:
    csv_row: Local state member.
    csv_rows: Local state member.
    existed: Local state member.
    reader: Local state member.
    results: Local state member.
    row_findings: Local state member.
    writer: Local state member.

Loop Behavior:
    Iterates through results.
    Iterates through reader.
"""
        # prevent reporting findings multiple times to the same iid
        results = self.get_unique_findings()
        row_findings = 0
        for f_name in results:
            row_findings += len(results[f_name])
        csv_row = [self.analysis_name, row_findings]
        with FileLock(str(self.path / "findings.csv") + ".lock"):
            csv_rows = []
            if (self.path / "findings.csv").exists():
                with open(self.path / "findings.csv", "r") as f:
                    reader = csv.reader(f)
                    existed = False
                    for row in reader:
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
            with open(self.path / "findings.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerows(csv_rows)

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Returns:
    Standard result object.
"""
        self._write_detailed_results()
        self._write_overview()
