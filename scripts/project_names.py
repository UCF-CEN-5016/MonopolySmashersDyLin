from fire import Fire
from pathlib import Path


def project_names():
    # Extract and print project names from projects.txt file (first column of each line)
    # Useful for scripting/automation that needs just project names
    here = Path(__file__).parent
    with open(str(here / "projects.txt")) as f:
        projects = f.read().split("\n")
    # Print names from first 35 projects (hardcoded limit)
    for project in projects[:35]:
        # projects.txt format: URL NAME HASH FLAGS TESTS
        # Extract URL (first column), then get project name from it
        print(project.split(" ")[0])


if __name__ == "__main__":
    # Use Fire library to create CLI from project_names() function
    Fire(project_names)
