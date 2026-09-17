"""Individual checks run against each added line of a diff.

Each check takes the raw text of one added line (newline stripped, but
with a trailing '\\r' left intact so CRLF can still be detected) and
returns either a message string, or None if the line is fine.
"""

import re

_DEBUG_PATTERNS = [
    re.compile(r"\bpdb\.set_trace\(\)"),
    re.compile(r"\bbreakpoint\(\)"),
    re.compile(r"\bconsole\.log\("),
    re.compile(r"\bdebugger\s*;"),
    re.compile(r"\bbinding\.pry\b"),
]

_CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>", "|||||||")

MAX_LINE_LENGTH = 120


def check_conflict_marker(text):
    stripped = text.lstrip()
    for marker in _CONFLICT_MARKERS:
        if stripped.startswith(marker):
            return f"unresolved merge conflict marker ({marker})"
    return None


def check_null_byte(text):
    if "\x00" in text:
        return "line contains a null byte"
    return None


def check_trailing_whitespace(text):
    stripped = text.rstrip("\r\n")
    if stripped and stripped != stripped.rstrip():
        return "trailing whitespace"
    return None


def check_carriage_return(text):
    if text.endswith("\r"):
        return "trailing carriage return (CRLF line ending)"
    return None


def check_mixed_indentation(text):
    indent = text[: len(text) - len(text.lstrip(" \t"))]
    if " " in indent and "\t" in indent:
        return "indentation mixes tabs and spaces"
    return None


def check_line_length(text):
    length = len(text.rstrip("\r\n"))
    if length > MAX_LINE_LENGTH:
        return f"line is {length} characters, over the {MAX_LINE_LENGTH} limit"
    return None


def check_debug_statement(text):
    for pattern in _DEBUG_PATTERNS:
        if pattern.search(text):
            return f"looks like a leftover debug statement ({pattern.pattern})"
    return None


# Order matters only for output stability: cheap, high-signal checks first.
CHECKS = [
    ("conflict-marker", check_conflict_marker),
    ("null-byte", check_null_byte),
    ("trailing-whitespace", check_trailing_whitespace),
    ("crlf-line-ending", check_carriage_return),
    ("mixed-indentation", check_mixed_indentation),
    ("line-too-long", check_line_length),
    ("debug-statement", check_debug_statement),
]


def run_checks(text):
    """Return a list of (rule_id, message) for every check that fires."""
    findings = []
    for rule_id, check in CHECKS:
        message = check(text)
        if message:
            findings.append((rule_id, message))
    return findings
