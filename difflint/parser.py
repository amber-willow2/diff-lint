"""Parse unified diffs into per-line records with new-file line numbers.

A unified diff hunk header (`@@ -a,b +c,d @@`) tells us where the added
side of the hunk starts in the new file. From there every context line
and added line advances the counter by one; removed lines don't, since
they never existed in the new file.
"""

import re
from dataclasses import dataclass

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class AddedLine:
    path: str
    lineno: int
    raw: str


def parse_added_lines(text):
    """Yield an AddedLine for every '+' line in the diff, in order."""
    path = None
    new_lineno = None
    for raw_line in text.splitlines(keepends=True):
        line = raw_line[:-1] if raw_line.endswith("\n") else raw_line

        if line.startswith("+++ "):
            path = _clean_path(line[4:])
            new_lineno = None
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("@@"):
            match = HUNK_RE.match(line)
            new_lineno = int(match.group(1)) if match else None
            continue

        # Lines outside any hunk (diff --git, index, mode changes, etc.)
        # carry no line number and are not part of the added content.
        if path is None or new_lineno is None:
            continue

        if line.startswith("+"):
            yield AddedLine(path=path, lineno=new_lineno, raw=line[1:])
            new_lineno += 1
        elif line.startswith("-"):
            continue
        else:
            new_lineno += 1


def _clean_path(field):
    # A "+++" line can carry a trailing tab and timestamp; drop that part.
    path = field.split("\t", 1)[0].strip()
    if path == "/dev/null":
        return path
    for prefix in ("b/", "a/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path
