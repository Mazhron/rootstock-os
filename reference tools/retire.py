"""Retire a file: MOVE it to _retired/ (same relative path), ledgered. Never delete.

THE PRESERVATION LAW (the CEO's ruling 2026-09-10): files, records and
knowledge are never deleted - they move somewhere indexed. This is the
mover for files:
  python tools/retire.py <path> [<path>...] --reason "why"
  -> _retired/<relative path>[.retired]   (the suffix keeps Godot from
     importing .tres/.gd/.tscn/.res/.import/.gdshader; _retired/ also
     carries a .gdignore so the editor skips the whole folder)
  -> docs/history/retired_files.txt gets one line (date | ws | from ->
     to | reason) - THE INDEX of everything retired; read its tail.
A name collision on the shelf gets a numeric suffix; nothing is ever
overwritten. `--list` prints the ledger's data lines. Scripts import
retire() instead of any remove call (apply_upgrade_edits.py does).

PURPOSE: Moves a file to _retired/ (same relative path, Godot import
  extensions suffixed .retired) and appends one line to
  docs/history/retired_files.txt; nothing is ever deleted.
INTENT: THE PRESERVATION LAW, the CEO's ruling 2026-09-10: files, records
  and knowledge are never deleted, they move somewhere indexed; this script
  is the mover for files.

Search keys: retire file, never delete, _retired, preservation law,
retired files ledger, move instead of delete.
See also: tools/hooks/preserve_guard.py (the guard that points here);
tools/cold_shelf.py (wiki sections); tools/delete_grant.py (a real
deletion, twice-approved); docs/history/retired_files.txt.
"""
import argparse
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELF = os.path.join(ROOT, "_retired")
LEDGER = os.path.join(ROOT, "docs", "history", "retired_files.txt")
HEADER = ("# RETIRED FILES (append-only; one line per file moved to _retired/ - THE INDEX of the shelf).\n"
          "# THE PRESERVATION LAW: files move, never die. Read the TAIL.\n"
          "# date time | ws | from -> to | reason\n")
GODOT_EXT = (".tres", ".res", ".gd", ".tscn", ".import", ".gdshader", ".scn")


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


def retire(path, reason, dry_run=False):
    """Move ROOT-relative or absolute `path` onto the shelf; returns the
    destination (ROOT-relative). Raises FileNotFoundError / ValueError."""
    src = path if os.path.isabs(path) else os.path.join(ROOT, path)
    src = os.path.normpath(src)
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    rel = os.path.relpath(src, ROOT)
    if rel.startswith(".."):
        raise ValueError("only files inside the repo retire here: %s" % src)
    dst = os.path.join(SHELF, rel)
    if os.path.isfile(src) and src.lower().endswith(GODOT_EXT):
        dst += ".retired"
    base, n = dst, 1
    while os.path.exists(dst):
        n += 1
        dst = "%s.%d" % (base, n)
    if not dry_run:
        os.makedirs(SHELF, exist_ok=True)
        ignore = os.path.join(SHELF, ".gdignore")
        if not os.path.exists(ignore):
            open(ignore, "w").close()
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        new = not os.path.isfile(LEDGER)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            if new:
                fh.write(HEADER)
            fh.write("%s | %s | %s -> %s | %s\n" % (
                time.strftime("%Y-%m-%d %H:%M"), workstation(),
                rel.replace("\\", "/"), os.path.relpath(dst, ROOT).replace("\\", "/"),
                (reason or "").replace("\n", " ")))
    return os.path.relpath(dst, ROOT).replace("\\", "/")


def main():
    ap = argparse.ArgumentParser(description="Move files to _retired/ (never delete)")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--reason", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        if os.path.isfile(LEDGER):
            for ln in open(LEDGER, encoding="utf-8"):
                if ln.strip() and not ln.startswith("#"):
                    print(ln.rstrip())
        else:
            print("nothing retired yet")
        return 0
    if not a.paths:
        ap.error("give at least one path (or --list)")
    if not a.reason.strip():
        ap.error("--reason is required: the ledger is the index, and an index line needs a why")
    for p in a.paths:
        try:
            dst = retire(p, a.reason, a.dry_run)
        except (FileNotFoundError, ValueError) as exc:
            print("SKIP %s: %s" % (p, exc))
            continue
        print("%s %s -> %s" % ("would retire" if a.dry_run else "RETIRED", p, dst))
    return 0


def _selftest():
    """Exercise the real retire() write path against a temp ROOT/SHELF/LEDGER
    (never the live _retired/ or docs/history/retired_files.txt). The
    tempfile.mkdtemp() directory is left in place afterward - a selftest
    never deletes anything (THE PRESERVATION LAW)."""
    import tempfile
    global ROOT, SHELF, LEDGER
    orig_root, orig_shelf, orig_ledger = ROOT, SHELF, LEDGER
    tmp = tempfile.mkdtemp(prefix="everwood_retire_selftest_")
    fails = 0
    try:
        ROOT = tmp
        SHELF = os.path.join(tmp, "_retired")
        LEDGER = os.path.join(tmp, "retired_files.txt")

        src1 = os.path.join(ROOT, "scratch_one.txt")
        with open(src1, "wb") as fh:
            fh.write(b"selftest payload one")
        before = open(src1, "rb").read()
        dst1 = retire("scratch_one.txt", "selftest reason one")

        ok = os.path.isfile(LEDGER) and open(LEDGER, encoding="utf-8").read().startswith(HEADER)
        print(("PASS  " if ok else "FAIL  ") + "ledger created with its header when absent")
        fails += not ok

        ok = open(os.path.join(tmp, dst1), "rb").read() == before
        print(("PASS  " if ok else "FAIL  ") + "moved file's bytes are identical after the move")
        fails += not ok

        src2 = os.path.join(ROOT, "scratch_two.txt")
        with open(src2, "wb") as fh:
            fh.write(b"selftest payload two")
        dst2 = retire("scratch_two.txt", "selftest reason two")
        text = open(LEDGER, encoding="utf-8").read()
        header_lines = sum(1 for ln in text.splitlines() if ln.startswith("#"))
        ok = header_lines == 3
        print(("PASS  " if ok else "FAIL  ") + "second write appends without repeating the header")
        fails += not ok

        data_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        ok = len(data_lines) == 2 and all(len(ln.split(" | ")) == 4 for ln in data_lines)
        print(("PASS  " if ok else "FAIL  ") + "line format matches the header's 4 columns")
        fails += not ok

        ok = ("scratch_one.txt" in data_lines[0] and dst1 in data_lines[0])
        print(("PASS  " if ok else "FAIL  ") + "ledger line names both the from and to paths")
        fails += not ok

        # a pre-existing header-only ledger must not get a second header
        LEDGER = os.path.join(tmp, "preexisting_ledger.txt")
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write(HEADER)
        src3 = os.path.join(ROOT, "scratch_three.txt")
        with open(src3, "wb") as fh:
            fh.write(b"selftest payload three")
        retire("scratch_three.txt", "selftest reason three")
        text3 = open(LEDGER, encoding="utf-8").read()
        ok = sum(1 for ln in text3.splitlines() if ln.startswith("#")) == 3
        print(("PASS  " if ok else "FAIL  ") + "pre-existing header-only ledger takes its first real append cleanly")
        fails += not ok
    finally:
        ROOT, SHELF, LEDGER = orig_root, orig_shelf, orig_ledger

    print("retire selftest: %d failed (scratch dir left at %s, never cleaned up - THE PRESERVATION LAW)"
          % (fails, tmp))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    sys.exit(main())
