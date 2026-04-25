"""
Module for project_names functionality.
"""
from fire import Fire
from pathlib import Path


def project_names():
    """
Project names: implementation of the project_names logic.

Key Variables:
    here: Local state member.
    projects: Local state member.

Loop Behavior:
    Iterates through projects[:35].
"""
    here = Path(__file__).parent
    with open(str(here / "projects.txt")) as f:
        projects = f.read().split("\n")
    for project in projects[:35]:
        print(project.split(" ")[0])


if __name__ == "__main__":
    Fire(project_names)
