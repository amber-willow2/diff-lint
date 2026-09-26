# difflint

A linter for diffs, not for source files. It reads a unified diff (the
kind `git diff` or `diff -u` produces) and reports problems in the
*added* lines, with the file and line number they'll have once the
diff is applied.

The idea is to catch things that a normal source linter won't, because
a source linter only ever sees the final file, not what changed. A
stray merge conflict marker, a debug `console.log` slipped into a
100-line patch, a line that got CRLF endings mixed into an otherwise
LF file — these are easy to miss in a large diff and easy to catch by
scanning just the additions.

## Usage

```
git diff | python -m difflint.cli
```

or against a saved patch file:

```
python -m difflint.cli mychange.diff
```

Given a diff like this:

```
--- a/app.py
+++ b/app.py
@@ -10,6 +10,9 @@ def handle_request(req):
     if not req.user:
         return None
+    console.log("got here")   
+<<<<<<< HEAD
+    return req.user.name
```

difflint reports:

```
app.py:12: [debug-statement] looks like a leftover debug statement (\bconsole\.log\()
app.py:12: [trailing-whitespace] trailing whitespace
app.py:13: [conflict-marker] unresolved merge conflict marker (<<<<<<<)
```

Each finding is one line: `path:line: [rule-id] message`. Exit status
is 1 if anything was found, 0 if the diff is clean, so it can be used
as a pre-commit or CI check.

## Checks

- `conflict-marker` — unresolved `<<<<<<<` / `=======` / `>>>>>>>` markers
- `null-byte` — a null byte on an added line, usually a sign of a binary
  file diffed as text
- `trailing-whitespace` — spaces or tabs at the end of a line
- `crlf-line-ending` — a line ending in `\r`
- `mixed-indentation` — leading whitespace that mixes tabs and spaces
- `line-too-long` — added line over 120 characters
- `debug-statement` — leftover `console.log`, `pdb.set_trace()`,
  `breakpoint()`, `debugger;`, or `binding.pry`

Only added lines are checked. Context lines and removed lines are
skipped, since the point is to review what's being introduced, not
the whole file.

## Limitations

difflint parses unified diff hunks directly; it doesn't shell out to
`git` or `diff`. It expects standard `--- a/...` / `+++ b/...` /
`@@ ... @@` headers, which is what `git diff`, `git show`, and
`diff -u` all produce. Diffs without those headers (context diffs,
raw `diff` without `-u`) aren't supported.

## Installing

No dependencies beyond the standard library. From the repository root:

```
pip install -e .
```

which gives you a `difflint` command, or just run the module in place
with `python -m difflint.cli`.

## Testing

```
python -m unittest discover
```

Tests live under `tests/`, including a couple of sample diffs under
`tests/fixtures/` used to check the parser and checks together end to
end.
