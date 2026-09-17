"""Command line entry point: read a unified diff, print findings."""

import argparse
import sys

from .checks import run_checks
from .parser import parse_added_lines


def lint_text(text):
    """Return a list of (path, lineno, rule_id, message) findings."""
    findings = []
    for added in parse_added_lines(text):
        for rule_id, message in run_checks(added.raw):
            findings.append((added.path, added.lineno, rule_id, message))
    return findings


def format_finding(finding):
    path, lineno, rule_id, message = finding
    return f"{path}:{lineno}: [{rule_id}] {message}"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="difflint",
        description="Lint a unified diff and report findings by line number.",
    )
    parser.add_argument(
        "diff_file",
        nargs="?",
        help="path to a unified diff file; reads stdin if omitted",
    )
    args = parser.parse_args(argv)

    if args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    findings = lint_text(text)
    for finding in findings:
        print(format_finding(finding))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
