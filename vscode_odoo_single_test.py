
# !/usr/bin/env python3
"""
Run Odoo tests from the class or method at the current VS Code cursor position.

Examples:

    # Run the method at line 42:
    python vscode_odoo_single_test.py \
        --test-file addons/event_rya/tests/test_example.py \
        --line 42 \
        --test-module event_rya \
        -c rya-odoo-DEV.conf \
        -d ryadev

    # If the cursor is inside a test class but outside a test method,
    # all test methods in that class are executed.
"""

import argparse
import ast
import runpy
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
ODOO_BIN = SCRIPT_DIR / "odoo-bin"
ADDONS_DIR = SCRIPT_DIR / "addons"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Run Odoo tests at the current VS Code cursor position.",
)

parser.add_argument(
    "--test-file",
    required=True,
    help="Path to the Python test file.",
)

parser.add_argument(
    "--line",
    required=True,
    type=int,
    help="Current cursor line number (1-based).",
)

parser.add_argument(
    "--test-module",
    default="event_rya",
    help="Odoo module name used in test tags (default: event_rya).",
)

options, odoo_args = parser.parse_known_args()


# ---------------------------------------------------------------------------
# Validate test file
# ---------------------------------------------------------------------------

test_file = Path(options.test_file).resolve()

if not test_file.is_file():
    sys.exit(f"ERROR: Test file does not exist: {test_file}")

if not test_file.name.startswith("test_") or test_file.suffix != ".py":
    sys.exit(f"ERROR: Not an Odoo test file: {test_file}")

if not ADDONS_DIR.resolve() in test_file.parents:
    sys.exit(
        "ERROR: Test file must be located inside the Odoo addons directory:\n"
        f"       {ADDONS_DIR}",
    )

if options.line < 1:
    sys.exit("ERROR: Line number must be >= 1.")


# ---------------------------------------------------------------------------
# Parse test file
# ---------------------------------------------------------------------------

try:
    source = test_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(test_file))
except (OSError, SyntaxError) as exc:
    sys.exit(f"ERROR: Cannot parse test file: {exc}")


# ---------------------------------------------------------------------------
# Find test classes and methods
# ---------------------------------------------------------------------------

test_classes = []

for node in tree.body:
    if not isinstance(node, ast.ClassDef):
        continue

    methods = []

    for member in node.body:
        if (
            isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and member.name.startswith("test_")
        ):
            methods.append(
                {
                    "name": member.name,
                    "start": member.lineno,
                    "end": member.end_lineno or member.lineno,
                },
            )

    if methods:
        test_classes.append(
            {
                "name": node.name,
                "start": node.lineno,
                "end": node.end_lineno or node.lineno,
                "methods": methods,
            },
        )


# ---------------------------------------------------------------------------
# Find class containing cursor
# ---------------------------------------------------------------------------

cursor_line = options.line

selected_class = next(
    (
        cls
        for cls in test_classes
        if cls["start"] <= cursor_line <= cls["end"]
    ),
    None,
)

if selected_class is None:
    available = "\n".join(
        f"  {cls['name']} (lines {cls['start']}-{cls['end']})"
        for cls in test_classes
    )

    sys.exit(
        f"ERROR: Cursor at line {cursor_line} is not inside a test class.\n\n"
        f"Test classes found:\n{available or '  None'}",
    )


# ---------------------------------------------------------------------------
# Find method containing cursor
# ---------------------------------------------------------------------------

selected_method = next(
    (
        method
        for method in selected_class["methods"]
        if method["start"] <= cursor_line <= method["end"]
    ),
    None,
)


# ---------------------------------------------------------------------------
# Build Odoo test tag
# ---------------------------------------------------------------------------

class_name = selected_class["name"]

if selected_method:
    selected_methods = [selected_method["name"]]

    test_tag = (
        f"/{options.test_module}:"
        f"{class_name}.{selected_method['name']}"
    )

    selection_description = "Single test method"

else:
    selected_methods = [
        method["name"]
        for method in selected_class["methods"]
    ]

    test_tag = f"/{options.test_module}:{class_name}"

    selection_description = "All test methods in class"


# ---------------------------------------------------------------------------
# Determine logger name
# ---------------------------------------------------------------------------

relative_path = test_file.relative_to(SCRIPT_DIR)

logger_name = (
    "odoo."
    + ".".join(relative_path.with_suffix("").parts)
)


# ---------------------------------------------------------------------------
# Print test selection
# ---------------------------------------------------------------------------

print()
print("=" * 78)
print("ODOO SINGLE TEST RUNNER")
print("=" * 78)

print(f"Test file:       {test_file.name}")
print(f"Test class:      {class_name}")
print(f"Cursor line:     {cursor_line}")
print(f"Selection:       {selection_description}")
print(f"Test logger:     {logger_name}")
print(f"Test tag:        {test_tag}")

print()
print(f"Test methods ({len(selected_methods)}):")

for method in selected_methods:
    print(f"  - {method}")

print()
print("=" * 78)
print()


# ---------------------------------------------------------------------------
# Validate Odoo executable
# ---------------------------------------------------------------------------

if not ODOO_BIN.is_file():
    sys.exit(f"ERROR: odoo-bin not found: {ODOO_BIN}")


# ---------------------------------------------------------------------------
# Build Odoo command line
# ---------------------------------------------------------------------------

sys.argv = [
    str(ODOO_BIN),

    # Original Odoo arguments from VS Code launch configuration
    *odoo_args,

    # Run only the selected test class or method
    "--test-tags",
    test_tag,

    # Do not start cron workers
    "--max-cron-threads=0",

    # Global output: warnings and errors only
    "--log-level=warn",

    # Show INFO messages from the selected test file
    f"--log-handler={logger_name}:INFO",

    # Keep the final Odoo test summary visible
    "--log-handler=odoo.tests.result:INFO",
]


# ---------------------------------------------------------------------------
# Run Odoo
# ---------------------------------------------------------------------------

runpy.run_path(
    str(ODOO_BIN),
    run_name="__main__",
)
