import unittest
from pathlib import Path

from difflint.checks import MAX_LINE_LENGTH
from difflint.parser import AddedLine, _clean_path, parse_added_lines

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name):
    return (FIXTURES / name).read_text()


class ParseAddedLinesTests(unittest.TestCase):
    def test_basic_fixture(self):
        added = list(parse_added_lines(read_fixture("basic.diff")))
        by_key = {(a.path, a.lineno): a.raw for a in added}
        self.assertEqual(len(by_key), 10)

        long_comment = by_key.pop(("style.css", 4))
        self.assertEqual(
            by_key,
            {
                ("app.py", 12): '    console.log("got here")',
                ("app.py", 13): "<<<<<<< HEAD",
                ("app.py", 15): "=======",
                ("app.py", 16): "    return None",
                ("app.py", 17): ">>>>>>> feature",
                ("style.css", 1): ".header {",
                ("style.css", 2): "    color: red;",
                ("style.css", 3): "\t    padding: 0;",
                ("style.css", 5): "}",
            },
        )
        # Its exact wording doesn't matter, only that the "+" marker got
        # stripped and it's long enough to trip the line-length check.
        self.assertTrue(long_comment.startswith("    /* "))
        self.assertTrue(long_comment.endswith(" */"))
        self.assertGreater(len(long_comment), MAX_LINE_LENGTH)

    def test_clean_fixture(self):
        added = list(parse_added_lines(read_fixture("clean.diff")))
        self.assertEqual(
            added,
            [AddedLine("util.py", 2, '    """Return the sum of a and b."""')],
        )

    def test_removed_lines_do_not_advance_new_lineno(self):
        text = (
            "--- a/f.py\n"
            "+++ b/f.py\n"
            "@@ -1,3 +1,2 @@\n"
            " kept\n"
            "-removed\n"
            "+added\n"
        )
        added = list(parse_added_lines(text))
        self.assertEqual(added, [AddedLine("f.py", 2, "added")])

    def test_multiple_hunks_reset_from_their_own_header(self):
        text = (
            "--- a/f.py\n"
            "+++ b/f.py\n"
            "@@ -1,1 +1,2 @@\n"
            " kept\n"
            "+first\n"
            "@@ -50,1 +51,2 @@\n"
            " kept\n"
            "+second\n"
        )
        added = list(parse_added_lines(text))
        self.assertEqual(
            added,
            [AddedLine("f.py", 2, "first"), AddedLine("f.py", 52, "second")],
        )

    def test_lines_before_first_hunk_are_ignored(self):
        text = (
            "diff --git a/f.py b/f.py\n"
            "new file mode 100644\n"
            "index 0000000..1111111\n"
            "--- /dev/null\n"
            "+++ b/f.py\n"
            "@@ -0,0 +1,1 @@\n"
            "+hello\n"
        )
        added = list(parse_added_lines(text))
        self.assertEqual(added, [AddedLine("f.py", 1, "hello")])

    def test_multiple_files_in_one_diff(self):
        text = (
            "--- a/one.py\n"
            "+++ b/one.py\n"
            "@@ -1,1 +1,2 @@\n"
            " kept\n"
            "+from one\n"
            "--- a/two.py\n"
            "+++ b/two.py\n"
            "@@ -1,1 +1,2 @@\n"
            " kept\n"
            "+from two\n"
        )
        added = list(parse_added_lines(text))
        self.assertEqual(
            added,
            [AddedLine("one.py", 2, "from one"), AddedLine("two.py", 2, "from two")],
        )


class CleanPathTests(unittest.TestCase):
    def test_strips_b_prefix(self):
        self.assertEqual(_clean_path("b/src/app.py"), "src/app.py")

    def test_strips_a_prefix(self):
        self.assertEqual(_clean_path("a/src/app.py"), "src/app.py")

    def test_dev_null_is_kept_as_is(self):
        self.assertEqual(_clean_path("/dev/null"), "/dev/null")

    def test_trailing_timestamp_is_dropped(self):
        self.assertEqual(
            _clean_path("b/src/app.py\t2024-01-01 00:00:00.000000000 +0000"),
            "src/app.py",
        )

    def test_path_without_prefix_is_unchanged(self):
        self.assertEqual(_clean_path("weirdpath.py"), "weirdpath.py")


if __name__ == "__main__":
    unittest.main()
