"""
Module for report_lines functionality.
"""
from fire import Fire


def report_lines(file_path):
    """
Report lines: implementation of the report_lines logic.

Args:
    file_path: Operational parameter.

Key Variables:
    lines: Local state member.
    loc: Local state member.
    ready: Local state member.

Loop Behavior:
    Iterates through lines.
"""
    with open(file_path) as f:
        lines = f.read().split("\n")
    ready = False
    for l in lines:
        if l.startswith("Totals grouped by language"):
            ready = True
        if ready and l.startswith("python:"):
            loc = l[7:].split("(")[0].strip()
            print(loc)
        elif ready and len(l.strip()) == 0:
            ready = False


if __name__ == "__main__":
    Fire(report_lines)
