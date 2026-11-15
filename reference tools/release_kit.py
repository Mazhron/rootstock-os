"""THE KIT RELEASE (the CEO's ruling 2026-11-15: "Source of truth - This
should be rootstock-os"). The kit repo releases itself.

PURPOSE: release the kit from inside its own repo: pull fast-forward only,
  run the publish gates (the format lint, the README version line, the
  README parity lint; the purpose audit's tally is printed, its colours
  never refuse, an audit that fails to run does), write SHA256SUMS from the bytes git will publish, commit and
  push whatever changed, and make the one signed tag for the kit
  version. `--check` runs the gates and stops; `--dry-run` also shows
  what a release would commit and whether the tag would be made.
INTENT: the CEO 2026-11-15: "Rootstock was meant to work independently of
  Everwood." Until v1.62 the kit's files were copies made by a script in
  the origin project, so a release could only start there; asked where
  the source should live, the CEO ruled "Source of truth - This should be
  rootstock-os".

    python "reference tools/release_kit.py" --check      # the gates only
    python "reference tools/release_kit.py" --dry-run    # the gates + what would be committed and tagged
    python "reference tools/release_kit.py" -m "Kit v1.63: what changed"   # gates, checksums, commit, push, signed tag
    python "reference tools/release_kit.py" --selftest   # offline: the checksum writer, the excludes, the signing words

Run it from the kit repo's root. The repo it acts on is the one its own
folder sits in, whatever the current directory: copied into a project's
tools/ it finds no kit around it and stops before any git verb.

THE ORDER, and why:
  1. the pull, fast-forward only: contributions merge on GitHub into
     community/, so the clone is brought level before anything is judged.
     A clone that has diverged is reported in two plain lines and the
     release stops; nothing is discarded.
  2. the gates, all refusals: format_lint.py must PASS (every kit thing
     carries its header, the safety wiring is whole), README.md's "Kit
     version:" line must equal UPGRADES.md's CURRENT KIT VERSION, and
     readme_lint.py must PASS (counts, the box table, the newest graft
     entry's README: line, the claims table). purpose_audit.py prints the
     flag tally; RED and unflagged are reported, never a refusal - the
     flags travel with the kit. An audit that does not run at all (a
     crash, FLAGS.md without its tally markers) IS a refusal: a release
     never goes out with its flags unread.
  3. the staging and SHA256SUMS: everything the working tree shows is
     staged, then one sha256 line per staged file is written from the
     STAGED bytes - what git publishes - never from the working copy. A
     Windows clone checks text files out with CRLF while the repo and
     every download carry LF, and the checksums up to v1.62 were taken
     from the working copy: 15 of their 115 lines never matched a
     downloaded file. Build junk (__pycache__, *.pyc, anywhere) and a
     session's or an editor's own folders (.claude/, .vscode/, .idea/,
     at the repo's top level only) are named in the clone's own
     .git/info/exclude before anything runs, and the gate scripts are
     run without bytecode, so a script run inside the repo can never
     publish its leftovers (one .pyc went out under v1.62 that way).
  4. the commit and the push, under the -m message (default "Kit release
     vX.Y"). A failed staging, commit or push stops the release there.
  5. the tag: one SIGNED tag per kit version (vX.Y), made only on the
     release branch (main) and only when it does not exist yet. A tag is
     never unsigned, moved or deleted by this script; if signing fails the
     push stays and the tag is reported as not made. A tag that exists
     here but not on the remote (its push failed last time) is pushed
     only when it is an annotated tag carrying a signature and names a
     commit in this branch's history; anything else (a tag made by hand)
     is reported and left alone. A tag that exists and names an older
     commit is reported with the count of commits released since, the
     cue to bump the version.

WHAT EACH MODE WRITES: every mode names the junk in .git/info/exclude
(local to the clone, never published), and the gates' purpose audit
refreshes FLAGS.md's tally block when a thing changed. `--check` and
`--dry-run` write nothing else and run no git verb that changes the
index, the history or the remote; they skip the pull, so a diverged
clone shows only in a real run. Nothing is ledgered: the kit repo keeps
no docs/history, and the release commit with its signed tag is the record.

Search keys: kit release, release script, publish the kit, source of
truth, SHA256SUMS, checksum, signed tag, release gates, rootstock-os.
See also: reference tools/format_lint.py, reference tools/readme_lint.py,
reference tools/purpose_audit.py (the gates; each runs in place inside the
kit repo since v1.63); UPGRADES.md (the version this reads; the v1.63
entry); CONTRIBUTING.md "How a release is made"; SECURITY.md (what the
checksums and the signed tag prove).
"""
import argparse
import fnmatch
import hashlib
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
# ----------------------------------------------------------- CONFIG --
RELEASE_BRANCH = "main"         # the only branch a version tag is made on
JUNK = ("__pycache__", "*.pyc")  # build junk: never checksummed, never committed
LOCAL = (".claude", ".vscode", ".idea")   # a session's or an editor's own folders at the repo's top level: never committed
SUMS_NAME = "SHA256SUMS"
SIGN_WORDS = ("gpg", "signing", "failed to sign", "sign ")
# -----------------------------------------------------------------------


def run(args, cwd=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")     # a gate script leaves no __pycache__ behind
    return subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True, env=env)


def is_kit(root):
    """True when root is the Rootstock repo itself: the graft log, the front
    door and a README naming the kit. A wrong folder is never committed to."""
    if not (os.path.isfile(os.path.join(root, "UPGRADES.md"))
            and os.path.isfile(os.path.join(root, "0 - READ ME FIRST.md"))):
        return False
    try:
        with open(os.path.join(root, "README.md"), encoding="utf-8") as fh:
            return "rootstock" in fh.read().lower()
    except OSError:
        return False


def is_junk(name):
    return any(fnmatch.fnmatch(name, pat) for pat in JUNK)


def ensure_excludes(repo):
    """Name JUNK and LOCAL in <repo>/.git/info/exclude -> the lines added.
    The clone's own exclude file makes git blind to them; no kit file changes."""
    path = os.path.join(repo, ".git", "info", "exclude")
    try:
        with open(path, encoding="utf-8") as fh:
            have = fh.read()
    except OSError:
        have = ""
    lines = set(have.splitlines())
    want = [p + "/" if "*" not in p else p for p in JUNK] + ["/%s/" % p for p in LOCAL]
    add = [w for w in want if w not in lines]
    if add:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(("" if not have or have.endswith("\n") else "\n") + "\n".join(add) + "\n")
    return add


def staged_rows(repo):
    """[(path, sha256)] of every STAGED file, hashed from the index blob: the
    bytes git publishes, whatever line endings the working copy carries.
    -> None when git cannot list or read the index."""
    ls = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=repo, capture_output=True)
    if ls.returncode:
        return None
    want = []
    for rec in ls.stdout.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        parts = meta.split()
        if len(parts) < 3 or parts[0] == b"160000":      # a submodule link has no blob
            continue
        want.append((path.decode("utf-8"), parts[1]))
    cat = subprocess.run(["git", "cat-file", "--batch"], cwd=repo, capture_output=True,
                         input=b"".join(oid + b"\n" for _, oid in want))
    if cat.returncode:
        return None
    out, pos, rows = cat.stdout, 0, []
    for path, oid in want:
        nl = out.find(b"\n", pos)
        head = out[pos:nl].split()
        if nl < 0 or len(head) != 3 or head[1] != b"blob":
            return None
        size = int(head[2])
        body = out[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
        name = path.rsplit("/", 1)[-1]
        if path == SUMS_NAME or is_junk(name) or any(is_junk(seg) for seg in path.split("/")[:-1]):
            continue
        rows.append((path, hashlib.sha256(body).hexdigest()))
    return rows


def write_checksums(repo, dry_run=False, staged=False):
    """Write <repo>/SHA256SUMS (sha256sum -c shape) -> file count, or None
    when staged=True and git could not read the index.

    staged=True (a release): one line per staged file, from the index blob.
    staged=False (the selftest, a folder that is no clone): the files on
    disk, minus .git and JUNK. Either way the sums file itself is left out;
    sorted, LF, written only when the content changed. Sets
    write_checksums.changed for the caller."""
    if staged:
        rows = staged_rows(repo)
        if rows is None:
            return None
    else:
        rows = []
        for dirpath, dirnames, filenames in os.walk(repo):
            dirnames[:] = [d for d in dirnames if d != ".git" and not is_junk(d)]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, repo).replace(os.sep, "/")
                if is_junk(fn) or rel == SUMS_NAME:
                    continue
                with open(full, "rb") as fh:
                    rows.append((rel, hashlib.sha256(fh.read()).hexdigest()))
    rows.sort()
    body = "".join("%s  %s\n" % (h, p) for p, h in rows)
    path = os.path.join(repo, SUMS_NAME)
    try:
        with open(path, "rb") as fh:
            old = fh.read()
    except OSError:
        old = None
    write_checksums.changed = old != body.encode("utf-8")
    if write_checksums.changed and not dry_run:
        with open(path, "wb") as fh:
            fh.write(body.encode("utf-8"))
    return len(rows)


write_checksums.changed = False


def is_signing_failure(stderr):
    """True when a git tag stderr text says signing is what failed."""
    low = (stderr or "").lower()
    return any(w in low for w in SIGN_WORDS)


def versions(root):
    """-> (UPGRADES.md's current kit version, README.md's version line), each 'X.Y' or None."""
    def find(name, pat):
        try:
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                m = re.search(pat, fh.read())
        except OSError:
            return None
        return m.group(1) if m else None
    return (find("UPGRADES.md", r"CURRENT KIT VERSION:\s*\**v(\d+\.\d+)"),
            find("README.md", r"Kit version:\s*\**v(\d+\.\d+)"))


def gates(root):
    """Run the publish gates -> (refusal text or None, kit version)."""
    fmt = run([sys.executable, os.path.join(HERE, "format_lint.py"), "--quiet"], root)
    print(fmt.stdout.strip())
    if fmt.returncode:
        return ("refused: the format lint failed (above) - `python \"reference tools/format_lint.py\"` "
                "names the files; rewrite each header after a read-only audit, then release"), None
    pa = run([sys.executable, os.path.join(HERE, "purpose_audit.py")], root)
    tally = [ln for ln in pa.stdout.splitlines() if ln.startswith("PURPOSE AUDIT")]
    for ln in tally:
        print(ln)
    if pa.returncode or not tally:      # the colours never refuse; an audit that did not run does
        err = (pa.stderr or pa.stdout or "").strip().splitlines()
        return ("refused: the purpose audit did not run (%s) - `python \"reference tools/purpose_audit.py\"` "
                "shows why; a release never goes out with its flags unread" % (err[-1] if err else "no output")), None
    kit_ver, readme_ver = versions(root)
    if not kit_ver:
        return "refused: UPGRADES.md carries no CURRENT KIT VERSION line", None
    if readme_ver != kit_ver:
        return ("refused: README.md says kit version %s but UPGRADES.md is v%s - bring the README level "
                "(pillars, skills, hooks, the box table, its 'Kit version:' line) before releasing"
                % ("v" + readme_ver if readme_ver else "nothing", kit_ver)), kit_ver
    lint = run([sys.executable, os.path.join(HERE, "readme_lint.py")], root)
    print(lint.stdout.strip())
    if lint.returncode:
        return ("refused: the README parity lint failed (above) - fix the README or the kit so they "
                "agree, then release"), kit_ver
    return None, kit_ver


def remote_of(repo):
    """The remote the current branch pushes to (origin when none is set)."""
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    return run(["git", "config", "branch.%s.remote" % branch], repo).stdout.strip() or "origin"


def unfit_tag(repo, tag):
    """Why a local tag must not be pushed, or None: it has to be an annotated
    tag object, carry a signature block, and name a commit HEAD descends from."""
    if run(["git", "cat-file", "-t", "refs/tags/" + tag], repo).stdout.strip() != "tag":
        return "it is a lightweight tag (no tag object, so no signature)"
    body = run(["git", "cat-file", "tag", "refs/tags/" + tag], repo).stdout
    if "-----BEGIN SSH SIGNATURE-----" not in body and "-----BEGIN PGP SIGNATURE-----" not in body:
        return "it carries no signature"
    if run(["git", "merge-base", "--is-ancestor", tag + "^{commit}", "HEAD"], repo).returncode:
        return "it names a commit that is not in this branch's history"
    return None


def tag_plan(repo, tag):
    """What ensure_tag would do, without doing it -> (word, line).
    word: 'exists' | 'push' (exists here, not on the remote, fit to push) |
    'unfit' (the same, but not a signed annotated tag on this history) | 'branch' | 'make'."""
    if run(["git", "tag", "-l", tag], repo).stdout.strip():
        remote = remote_of(repo)
        lr = run(["git", "ls-remote", "--tags", remote, tag], repo)
        if lr.returncode == 0 and not lr.stdout.strip():
            why = unfit_tag(repo, tag)
            if why:
                return "unfit", ("tag %s exists here but not on %s and is NOT pushed: %s; a kit tag is "
                                 "signed, annotated and on the released history (made by this script, "
                                 "never by hand)" % (tag, remote, why))
            return "push", "tag %s exists here but not on %s: it would be pushed" % (tag, remote)
        behind = run(["git", "rev-list", "--count", "%s..HEAD" % tag], repo).stdout.strip()
        if behind.isdigit() and int(behind):
            return "exists", ("tag %s exists, %s commit(s) behind this release: it is never moved - bump the "
                              "kit version in UPGRADES.md and README.md for the next tag" % (tag, behind))
        return "exists", "tag %s exists" % tag
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
    if branch != RELEASE_BRANCH:
        return "branch", "tag %s NOT made: on branch %s; a version tag is made on %s only" % (tag, branch, RELEASE_BRANCH)
    return "make", "tag %s would be made, signed, and pushed" % tag


def ensure_tag(repo, tag):
    """Make + push the signed tag if missing -> the line to print."""
    word, line = tag_plan(repo, tag)
    remote = remote_of(repo)
    if word == "push":
        p = run(["git", "push", remote, tag], repo)
        if p.returncode:
            return "tag %s exists here, push failed (`git push %s %s` by hand): %s" % (tag, remote, tag, (p.stderr or "").strip())
        return "tag %s was signed earlier and is now pushed" % tag
    if word != "make":
        return line
    t = run(["git", "tag", "-s", tag, "-m", "Rootstock kit %s" % tag], repo)
    if t.returncode:
        err = (t.stderr or "").strip()
        first = err.splitlines()[0] if err else "no message"
        if is_signing_failure(err):
            return ("tag %s NOT made: signing failed (%s); a kit tag is never unsigned "
                    "(set the signing key up first)" % (tag, first))
        return "tag %s NOT made: %s" % (tag, first)
    p = run(["git", "push", remote, tag], repo)
    if p.returncode:
        return ("tag %s signed, push failed (run this again, or `git push %s %s` by hand): %s"
                % (tag, remote, tag, (p.stderr or "").strip()))
    return "tag %s signed + pushed" % tag


def selftest():
    import time
    d = tempfile.mkdtemp(prefix="release_kit_selftest_")  # left on disk on purpose
    files = {"a.md": b"alpha\n", os.path.join("sub", "b.txt"): b"beta\n",
             os.path.join("__pycache__", "x.pyc"): b"junk",
             os.path.join(".git", "config"): b"[core]\n"}
    for rel, data in files.items():
        full = os.path.join(d, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(data)
    fails = []
    n = write_checksums(d)
    if n != 2:
        fails.append("count %d != 2" % n)
    sums = os.path.join(d, SUMS_NAME)
    with open(sums, "rb") as fh:
        text = fh.read().decode("utf-8")
    want = "%s  a.md\n%s  sub/b.txt\n" % (hashlib.sha256(b"alpha\n").hexdigest(),
                                         hashlib.sha256(b"beta\n").hexdigest())
    if text != want:
        fails.append("sums content wrong: %r" % text)
    m1 = os.path.getmtime(sums)
    time.sleep(0.05)
    write_checksums(d)
    if write_checksums.changed or os.path.getmtime(sums) != m1:
        fails.append("second run rewrote an unchanged file")
    if not is_signing_failure("error: gpg failed to sign the data"):
        fails.append("signing failure not recognised")
    if is_signing_failure("fatal: tag 'v1' already exists"):
        fails.append("plain error taken for signing failure")
    if ensure_excludes(d) != ["__pycache__/", "*.pyc", "/.claude/", "/.vscode/", "/.idea/"]:
        fails.append("excludes not added on the first run")
    if ensure_excludes(d):
        fails.append("excludes added twice")
    if is_kit(d):
        fails.append("a folder without the graft log taken for the kit")
    for name, body in (("UPGRADES.md", "CURRENT KIT VERSION: **v9.1**\n"), ("0 - READ ME FIRST.md", "door\n"),
                       ("README.md", "# Rootstock\n\nKit version: **v9.0** (old)\n")):
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(body)
    if not is_kit(d):
        fails.append("the kit's three marks not recognised")
    if versions(d) != ("9.1", "9.0"):
        fails.append("versions read wrong: %r" % (versions(d),))
    # the staged checksums: a real repo whose working copy carries CRLF must
    # yield the hash of the LF bytes git stores (the v1.62 mismatch)
    g = tempfile.mkdtemp(prefix="release_kit_selftest_git_")
    try:
        have_git = run(["git", "init", "-q"], g).returncode == 0
    except OSError:
        have_git = False
    if have_git:
        run(["git", "config", "core.autocrlf", "true"], g)
        with open(os.path.join(g, "t.md"), "wb") as fh:
            fh.write(b"one\r\ntwo\r\n")
        os.makedirs(os.path.join(g, "__pycache__"))
        with open(os.path.join(g, "__pycache__", "x.pyc"), "wb") as fh:
            fh.write(b"junk")
        with open(os.path.join(g, "sp ace.txt"), "wb") as fh:
            fh.write(b"s\n")
        run(["git", "add", "-A"], g)
        rows = dict(staged_rows(g) or [])
        if rows.get("t.md") != hashlib.sha256(b"one\ntwo\n").hexdigest():
            fails.append("staged checksum is not the hash of the stored (LF) bytes")
        if rows.get("sp ace.txt") != hashlib.sha256(b"s\n").hexdigest():
            fails.append("a path with a space lost its staged checksum")
        if any("__pycache__" in k for k in rows):
            fails.append("junk was checksummed from the index")
        if write_checksums(g, staged=True) != 2:
            fails.append("staged write did not count two files")
        # a tag made by hand is never fit to push
        run(["git", "-c", "user.name=selftest", "-c", "user.email=selftest@example.invalid",
             "-c", "commit.gpgsign=false", "commit", "-q", "-m", "one"], g)
        run(["git", "tag", "light"], g)
        run(["git", "-c", "user.name=selftest", "-c", "user.email=selftest@example.invalid",
             "-c", "tag.gpgsign=false", "tag", "-a", "plain", "-m", "unsigned"], g)
        if "lightweight" not in (unfit_tag(g, "light") or ""):
            fails.append("a lightweight tag was called fit to push")
        if "no signature" not in (unfit_tag(g, "plain") or ""):
            fails.append("an unsigned annotated tag was called fit to push")
    else:
        print("note: git not available here, the staged-checksum checks were skipped")
    print("selftest in %s" % d)
    print("FAIL: " + "; ".join(fails) if fails else "PASS")
    sys.exit(1 if fails else 0)


def main():
    ap = argparse.ArgumentParser(description="Release the Rootstock kit from inside its own repo")
    ap.add_argument("--check", action="store_true", help="run the gates and stop")
    ap.add_argument("--dry-run", action="store_true", help="the gates, then show what a release would do")
    ap.add_argument("-m", "--message", help="the commit message (default: Kit release vX.Y)")
    ap.add_argument("--selftest", action="store_true", help="offline check of the pieces")
    args = ap.parse_args()
    if args.selftest:
        selftest()

    if not is_kit(ROOT):
        sys.exit("refused: %s is not the Rootstock repo (no UPGRADES.md, front door and README naming "
                 "the kit beside this script's folder) - run it from a clone of rootstock-os, as "
                 "`python \"reference tools/release_kit.py\"`" % ROOT)
    has_git = os.path.isdir(os.path.join(ROOT, ".git"))
    offline = args.check or args.dry_run
    if not has_git and not args.check:
        sys.exit("refused: %s is not a git clone - only --check runs on a downloaded copy" % ROOT)

    if has_git:
        ensure_excludes(ROOT)       # before any script runs here, so its leftovers are never seen by git

    # 1. THE INBOX PULL: level with the remote before anything is judged.
    if not offline:
        pl = run(["git", "pull", "--ff-only", "--quiet"])
        if pl.returncode:
            sys.exit("refused: the clone could not fast-forward from its remote (the repo is fine; "
                     "the branch has no upstream, the network is down, the clone and its remote have "
                     "diverged, or local edits touch a file the remote changed). In %s: `git status`, "
                     "`git log --oneline -3 origin/%s`, then merge by hand and release again.\n%s"
                     % (ROOT, RELEASE_BRANCH, pl.stderr.strip()))

    # 2. THE GATES.
    refusal, kit_ver = gates(ROOT)
    if refusal:
        sys.exit(refusal)
    tag = "v" + kit_ver
    if args.check:
        print("gates passed: kit %s may be released" % tag)
        return

    if args.dry_run:
        st = run(["git", "status", "--porcelain"]).stdout.strip()
        print("DRY RUN - a release would stage and commit (plus SHA256SUMS, rewritten from the staged bytes):\n"
              + (st or "  (no changes)"))
        word, line = tag_plan(ROOT, tag)
        if st and word == "exists" and "behind" not in line:
            line += (" - and this release's commit would leave it 1 commit behind: it is never moved, "
                     "so bump the kit version if these changes are a new version")
        print("DRY RUN - " + line)
        return

    # 3. THE STAGING AND THE CHECKSUMS, after the gates (the audit may refresh
    # FLAGS.md's tally): stage, hash what was staged, stage the sums file.
    a = run(["git", "add", "-A"])
    if a.returncode:
        sys.exit("STAGING FAILED (nothing committed):\n%s" % a.stderr)
    n = write_checksums(ROOT, staged=True)
    if n is None:
        sys.exit("refused: git could not read the staged files, so no checksum could be written "
                 "(nothing committed; `git status` in %s)" % ROOT)
    print("checksums: %d files, from the staged bytes" % n)
    a = run(["git", "add", "--", SUMS_NAME])
    if a.returncode:
        sys.exit("STAGING FAILED (nothing committed):\n%s" % a.stderr)
    st = run(["git", "status", "--porcelain"]).stdout.strip()

    # 4. THE COMMIT AND THE PUSH.
    if not st:
        ahead = run(["git", "rev-list", "--count", "@{u}..HEAD"]).stdout.strip()
        if ahead and ahead != "0":
            p = run(["git", "push"])
            if p.returncode:
                sys.exit("PUSH FAILED:\n%s" % p.stderr)
            print("nothing to commit; %s local commit(s) pushed." % ahead)
        else:
            print("kit repo already released - nothing to commit or push.")
    else:
        c = run(["git", "commit", "-m", args.message or "Kit release %s" % tag])
        if c.returncode:
            sys.exit("COMMIT FAILED:\n%s\n%s" % (c.stdout, c.stderr))
        p = run(["git", "push"])
        if p.returncode:
            sys.exit("PUSH FAILED (the commit is made; push by hand, then run this again for the tag):\n%s" % p.stderr)
        print("kit released + pushed:\n" + st)

    # 5. THE TAG.
    print(ensure_tag(ROOT, tag))


if __name__ == "__main__":
    main()
