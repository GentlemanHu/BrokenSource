import sys
from pathlib import Path

import mkdocs_gen_files

UNWANTED = (
    "Resources",
    "Community",
    "__",
)

# List of all modules to generate docs for on the path "$name/{reference,resources,*}/*"
# Note: The order is important, Broken must be first to not be included on itself
PROJECTS = (
    Path("Broken"),
    Path("Projects/ShaderFlow/ShaderFlow"),
    Path("Projects/DepthFlow/DepthFlow"),
    Path("Projects/Pianola/Pianola"),
    Path("Projects/SpectroNote/SpectroNote"),
)

# Make each project's root findable
sys.path += map(str, PROJECTS)

for ROOT in PROJECTS:
    PROJECT_NAME = ROOT.name

    for python in reversed(list(ROOT.rglob("*.py"))):

        # Skip unwanted files
        if any(ban in str(python) for ban in UNWANTED):
            continue

        # Get the module import statement and url path
        module   = python.relative_to(ROOT).with_suffix("")
        markdown = Path(ROOT.name, "reference", module).with_suffix(".md")
        url_path = str(markdown).lower()

        # Write the virtual markdown file with documentation
        with mkdocs_gen_files.open(url_path, "w") as file:
            file.write('\n'.join((
                f"# {module.name}",
                "",
                "!!! warning",
                "    **Better Docstrings** and **Formatting** are being worked on for the Code References",
                "",
                f"::: {'.'.join(module.parts)}",
            )))

    # This project's directory under the monorepo Website
    # Note: Avoid writing Broken/Website to itself
    BASE = PROJECT_NAME.lower().replace("broken", "")

    # Override the repository
    with mkdocs_gen_files.open(".meta.yaml", "w", encoding="utf-8") as file:
        file.write(f"repo_url: https://github.com/BrokenSource/{PROJECT_NAME}\n")

    # # Virtually copy all of Project's stuff to

    # This project's own paths
    WHAT_WHERE = [
        ((ROOT/"Resources"), "resources"),
        ((ROOT.parent/"Website"), ""),
    ]

    # Only copy project's readme
    if (ROOT.name != "Broken"):
        WHAT_WHERE.append((ROOT.parent/"Readme.md", "readme.md"))

    WANT_SUFFIXES = (".md", ".png", ".jpg", ".svg")

    # Rebase "$what/*" to "$name/$where/*" local documentation
    for (what, where) in WHAT_WHERE:
        paths = (what.rglob("*") if what.is_dir() else [what])

        for real in paths:

            # Skip "bad" files
            if real.is_dir():
                continue
            if real.suffix not in WANT_SUFFIXES:
                continue

            virtual = Path(BASE, where, str(real.relative_to(what)).lower())

            print(f"• Copying ({real}) -> ({virtual})")

            with mkdocs_gen_files.open(virtual, "wb") as file:
                file.write(real.read_bytes())

