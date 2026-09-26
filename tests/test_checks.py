import unittest

from difflint.checks import (
    CHECKS,
    MAX_LINE_LENGTH,
    check_carriage_return,
    check_conflict_marker,
    check_debug_statement,
    check_line_length,
    check_mixed_indentation,
    check_null_byte,
    check_trailing_whitespace,
    run_checks,
)


class ConflictMarkerTests(unittest.TestCase):
    def test_detects_each_marker(self):
        for marker in ("<<<<<<<", "=======", ">>>>>>>", "|||||||"):
            with self.subTest(marker=marker):
                self.assertIsNotNone(check_conflict_marker(f"{marker} HEAD"))

    def test_marker_is_recognized_after_leading_indent(self):
        self.assertIsNotNone(check_conflict_marker("    <<<<<<< HEAD"))

    def test_clean_line_is_none(self):
        self.assertIsNone(check_conflict_marker("    return req.user.name"))

    def test_equals_signs_inside_a_line_are_not_a_marker(self):
        self.assertIsNone(check_conflict_marker("    if a == b:"))


class NullByteTests(unittest.TestCase):
    def test_detects_null_byte(self):
        self.assertIsNotNone(check_null_byte("garbled\x00text"))

    def test_clean_line_is_none(self):
        self.assertIsNone(check_null_byte("normal text"))


class TrailingWhitespaceTests(unittest.TestCase):
    def test_detects_trailing_spaces(self):
        self.assertIsNotNone(check_trailing_whitespace("return None   "))

    def test_detects_trailing_tab(self):
        self.assertIsNotNone(check_trailing_whitespace("return None\t"))

    def test_clean_line_is_none(self):
        self.assertIsNone(check_trailing_whitespace("return None"))

    def test_blank_line_is_none(self):
        self.assertIsNone(check_trailing_whitespace(""))

    def test_trailing_newline_alone_is_not_flagged(self):
        self.assertIsNone(check_trailing_whitespace("return None\n"))


class CarriageReturnTests(unittest.TestCase):
    def test_detects_crlf(self):
        self.assertIsNotNone(check_carriage_return("return None\r"))

    def test_clean_line_is_none(self):
        self.assertIsNone(check_carriage_return("return None"))


class MixedIndentationTests(unittest.TestCase):
    def test_detects_tab_then_spaces(self):
        self.assertIsNotNone(check_mixed_indentation("\t    padding: 0;"))

    def test_detects_spaces_then_tab(self):
        self.assertIsNotNone(check_mixed_indentation("    \tpadding: 0;"))

    def test_spaces_only_is_none(self):
        self.assertIsNone(check_mixed_indentation("    padding: 0;"))

    def test_tabs_only_is_none(self):
        self.assertIsNone(check_mixed_indentation("\t\tpadding: 0;"))

    def test_no_indentation_is_none(self):
        self.assertIsNone(check_mixed_indentation("padding: 0;"))


class LineLengthTests(unittest.TestCase):
    def test_line_at_limit_is_none(self):
        self.assertIsNone(check_line_length("x" * MAX_LINE_LENGTH))

    def test_line_over_limit_is_flagged(self):
        self.assertIsNotNone(check_line_length("x" * (MAX_LINE_LENGTH + 1)))

    def test_trailing_newline_is_not_counted(self):
        self.assertIsNone(check_line_length("x" * MAX_LINE_LENGTH + "\n"))


class DebugStatementTests(unittest.TestCase):
    def test_detects_each_pattern(self):
        samples = [
            "import pdb; pdb.set_trace()",
            "breakpoint()",
            'console.log("value:", value)',
            "debugger;",
            "binding.pry",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertIsNotNone(check_debug_statement(sample))

    def test_clean_line_is_none(self):
        self.assertIsNone(check_debug_statement("logger.info('starting up')"))

    def test_similar_but_different_call_is_not_flagged(self):
        self.assertIsNone(check_debug_statement("consoleLogger.log('hi')"))


class RunChecksTests(unittest.TestCase):
    def test_clean_line_has_no_findings(self):
        self.assertEqual(run_checks("    return req.user.name"), [])

    def test_findings_are_returned_in_check_order(self):
        line = '<<<<<<< HEAD console.log("x")   '
        findings = run_checks(line)
        rule_ids = [rule_id for rule_id, _ in findings]
        self.assertEqual(
            rule_ids, ["conflict-marker", "trailing-whitespace", "debug-statement"]
        )

    def test_rule_ids_are_unique(self):
        rule_ids = [rule_id for rule_id, _ in CHECKS]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))


if __name__ == "__main__":
    unittest.main()
