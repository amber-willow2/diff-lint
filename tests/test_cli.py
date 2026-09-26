import contextlib
import io
import unittest
from pathlib import Path

from difflint.cli import format_finding, lint_text, main
from difflint.checks import MAX_LINE_LENGTH
from difflint.parser import parse_added_lines

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name):
    return (FIXTURES / name).read_text()


class LintTextTests(unittest.TestCase):
    def test_basic_fixture_findings(self):
        text = read_fixture("basic.diff")
        findings = lint_text(text)

        long_comment_length = next(
            len(added.raw)
            for added in parse_added_lines(text)
            if (added.path, added.lineno) == ("style.css", 4)
        )
        self.assertGreater(long_comment_length, MAX_LINE_LENGTH)

        self.assertEqual(
            findings,
            [
                (
                    "app.py",
                    12,
                    "debug-statement",
                    r'looks like a leftover debug statement (\bconsole\.log\()',
                ),
                (
                    "app.py",
                    13,
                    "conflict-marker",
                    "unresolved merge conflict marker (<<<<<<<)",
                ),
                (
                    "app.py",
                    15,
                    "conflict-marker",
                    "unresolved merge conflict marker (=======)",
                ),
                (
                    "app.py",
                    17,
                    "conflict-marker",
                    "unresolved merge conflict marker (>>>>>>>)",
                ),
                (
                    "style.css",
                    3,
                    "mixed-indentation",
                    "indentation mixes tabs and spaces",
                ),
                (
                    "style.css",
                    4,
                    "line-too-long",
                    f"line is {long_comment_length} characters, "
                    f"over the {MAX_LINE_LENGTH} limit",
                ),
            ],
        )

    def test_clean_fixture_has_no_findings(self):
        self.assertEqual(lint_text(read_fixture("clean.diff")), [])

    def test_crlf_line_ending(self):
        text = "--- a/f.txt\n+++ b/f.txt\n@@ -1,1 +1,1 @@\n+line one\r\n"
        findings = lint_text(text)
        self.assertEqual(
            findings,
            [("f.txt", 1, "crlf-line-ending", "trailing carriage return (CRLF line ending)")],
        )

    def test_null_byte(self):
        text = "--- a/f.bin\n+++ b/f.bin\n@@ -1,1 +1,1 @@\n+garbled\x00text\n"
        findings = lint_text(text)
        self.assertEqual(findings, [("f.bin", 1, "null-byte", "line contains a null byte")])


class FormatFindingTests(unittest.TestCase):
    def test_format(self):
        finding = ("app.py", 12, "debug-statement", "looks like a leftover debug statement")
        self.assertEqual(
            format_finding(finding),
            "app.py:12: [debug-statement] looks like a leftover debug statement",
        )


class MainTests(unittest.TestCase):
    def test_dirty_diff_file_exits_nonzero_and_prints_findings(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([str(FIXTURES / "basic.diff")])
        self.assertEqual(code, 1)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 6)
        self.assertTrue(lines[0].startswith("app.py:12: [debug-statement]"))

    def test_clean_diff_file_exits_zero_and_prints_nothing(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([str(FIXTURES / "clean.diff")])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")

    def test_reads_from_stdin_when_no_file_given(self):
        stdin = io.StringIO(read_fixture("clean.diff"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stdin(stdin):
            code = main([])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
