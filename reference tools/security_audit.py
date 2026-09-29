"""THE PRE-PRODUCTION SECURITY AUDIT, the scripted half (SECURITY_METHOD.md,
the CEO 2026-09-29).

    python tools/security_audit.py --dir <build output>      # class 1: secrets in the client
    python tools/security_audit.py --url https://your.site   # classes 2-4: headers, exposed files, CORS
    python tools/security_audit.py --url ... --record "note" # ... then one ledger line
    python tools/security_audit.py --record "hand-walked: RLS on, routes checked"
    python tools/security_audit.py --selftest

PURPOSE: Run the read-only checks SECURITY_METHOD.md's checklist gives a
  script: grep a production build folder for secret-shaped strings (class
  1), read the site's response headers for HSTS, CSP and a frame rule
  (class 2), request the exposed-file paths and expect 404 or 403 (class
  3), and read the CORS header under a foreign Origin (class 4); print one
  PASS / WARN / FAIL line per check and, with --record, append the counts
  and a note to docs/history/security_audit_runs.txt.
INTENT: the CEO 2026-09-29, on the survey of 100 AI-built apps (37 with a
  secret in the client, 78 missing a header, 12 serving .git or .env): "We
  should create a file for this specifically ... to help keep users safe
  who are making them." The checks a visitor's browser already makes are
  a script; the checks that need judgment (database rules, auth per route,
  dependencies, logs) stay on the checklist for an employee.

READ-ONLY: GET and HEAD requests to the URL you give it, nothing else; it
sends no payload, no login, no probe beyond the fixed path list, and it
is meant for a deployment you own. The --dir scan reads files and prints
the file, line and pattern name, never the matched secret itself.

Search keys: security audit, exposed secret, secret scan, security
headers, CSP, HSTS, exposed .env, .git exposed, CORS wildcard, ledger,
pre-production, public release, security_audit_runs.
See also: SECURITY_METHOD.md (the checklist and the law); WORKFLOWS.md
"Audit the app for exposed secrets before a public release"; tools/
_ledger.py (the dedup append); REPORTING_METHOD.md.
"""
import datetime
import http.server
import os
import re
import socketserver
import sys
import tempfile
import threading
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "history", "security_audit_runs.txt")
HEADER = ("# SECURITY AUDIT HISTORY (append-only; one line per audit, SECURITY_METHOD.md).\n"
          "# date time | ws | target | PASS n | WARN n | FAIL n | note\n")

# class 1: the secret shapes. (name, regex). The match itself is never printed.
SECRET_PATTERNS = [
    ("stripe secret key", re.compile(r"\bsk_(live|test)_[0-9A-Za-z]{8,}")),
    ("openai style secret key", re.compile(r"\bsk-[0-9A-Za-z_-]{16,}")),
    ("aws access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("supabase service_role key", re.compile(r"service_role")),
    ("github token", re.compile(r"\b(ghp_|github_pat_)[0-9A-Za-z_]{16,}")),
    ("google api key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("slack token", re.compile(r"\bxox[bp]-[0-9A-Za-z-]{10,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password or secret assignment", re.compile(r"(?i)\b(password|secret|api_key|apikey)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("bundled private env name", re.compile(r"\b(VITE_|NEXT_PUBLIC_|REACT_APP_|EXPO_PUBLIC_|NUXT_PUBLIC_|GATSBY_)[A-Z0-9_]*(SECRET|PRIVATE|SERVICE_ROLE|PASSWORD)[A-Z0-9_]*")),
]
SCAN_EXT = {".js", ".mjs", ".cjs", ".html", ".htm", ".map", ".json", ".css", ".txt", ".env", ".yml", ".yaml", ".toml"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}

# class 2: the headers. (header, required, meaning)
HEADERS = [
    ("strict-transport-security", True, "HSTS: HTTPS forced after the first visit"),
    ("content-security-policy", True, "CSP: which scripts, frames and connections may load"),
    ("x-frame-options", True, "a frame rule (or CSP frame-ancestors): no invisible framing"),
    ("x-content-type-options", False, "nosniff"),
    ("referrer-policy", False, "what the URL leaks to the next site"),
    ("permissions-policy", False, "camera, microphone, geolocation off unless used"),
]

# class 3: the paths that must not be served.
EXPOSED_PATHS = [
    "/.git/HEAD", "/.git/config", "/.env", "/.env.local", "/.env.production", "/.env.bak",
    "/.env.example", "/config.json", "/config.yml", "/backup.zip", "/db.sqlite", "/.DS_Store",
    "/server.log", "/phpinfo.php", "/wp-config.php.bak", "/.htpasswd", "/docker-compose.yml",
    "/package.json",
]
UA = "security_audit.py (read-only pre-production audit of the owner's own deployment)"


def workstation():
    home = os.path.expanduser("~").lower()
    return "WS2" if "travis" in home else ("WS1" if "owner" in home else "WS?")


class Report:
    def __init__(self, out=None):
        self.lines = []
        self.counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        self.out = out if out is not None else sys.stdout

    def add(self, verdict, text):
        self.counts[verdict] += 1
        line = "%-4s  %s" % (verdict, text)
        self.lines.append(line)
        print(line, file=self.out)

    def summary(self):
        return "PASS %d | WARN %d | FAIL %d" % (self.counts["PASS"], self.counts["WARN"], self.counts["FAIL"])


# ------------------------------------------------------------ class 1 --
def scan_dir(path, rep):
    """Every scannable file under `path`: one FAIL per (file, pattern) hit,
    naming the line and the pattern, never the match. A clean tree is one PASS."""
    hits = 0
    files = 0
    for dp, dns, fns in os.walk(path):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in SCAN_EXT and not fn.startswith(".env"):
                continue
            fp = os.path.join(dp, fn)
            files += 1
            try:
                with open(fp, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            seen = set()
            for name, rx in SECRET_PATTERNS:
                m = rx.search(text)
                if not m or name in seen:
                    continue
                seen.add(name)
                hits += 1
                line_no = text.count("\n", 0, m.start()) + 1
                rel = os.path.relpath(fp, path)
                rep.add("FAIL", "class 1 secret shape '%s' in %s line %d (rotate it first, then move the call server-side)"
                        % (name, rel, line_no))
    if hits == 0:
        rep.add("PASS", "class 1: %d file(s) scanned under %s, no secret shapes" % (files, path))
    return hits


# ------------------------------------------------------------ http --
def fetch(url, method="GET", headers=None, timeout=10):
    """(status, headers dict lowercased) or (None, {}) on a connection error."""
    req = urllib.request.Request(url, method=method, headers=dict({"User-Agent": UA}, **(headers or {})))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}
    except (urllib.error.URLError, OSError, ValueError):
        return None, {}


def check_headers(url, rep):
    status, h = fetch(url)
    if status is None:
        rep.add("FAIL", "class 2: %s did not answer" % url)
        return
    for name, required, meaning in HEADERS:
        present = name in h
        if name == "x-frame-options" and not present:
            present = "frame-ancestors" in h.get("content-security-policy", "")
        if present:
            rep.add("PASS", "class 2 header %s present (%s)" % (name, meaning))
        else:
            rep.add("FAIL" if required else "WARN", "class 2 header %s missing (%s)" % (name, meaning))


def check_exposed(base, rep):
    base = base.rstrip("/")
    for p in EXPOSED_PATHS:
        status, _ = fetch(base + p)
        if status is None:
            rep.add("WARN", "class 3 %s: no answer" % p)
        elif status in (404, 403, 410):
            rep.add("PASS", "class 3 %s -> %d" % (p, status))
        elif status == 200:
            sev = "FAIL"
            note = " (the whole repo, history included, is downloadable)" if p.startswith("/.git") else ""
            rep.add(sev, "class 3 %s -> 200, served to every visitor%s" % (p, note))
        else:
            rep.add("WARN", "class 3 %s -> %d (expected 404)" % (p, status))


def check_cors(url, rep):
    status, h = fetch(url, headers={"Origin": "https://evil.example"})
    if status is None:
        rep.add("WARN", "class 4: %s did not answer the Origin probe" % url)
        return
    acao = h.get("access-control-allow-origin")
    creds = h.get("access-control-allow-credentials", "").lower() == "true"
    if acao is None:
        rep.add("PASS", "class 4: no Access-Control-Allow-Origin header (no cross-site reads)")
    elif acao.strip() == "*" and creds:
        rep.add("FAIL", "class 4: wildcard origin WITH credentials (any site can call this as the logged-in visitor)")
    elif acao.strip() == "*":
        rep.add("WARN", "class 4: wildcard Access-Control-Allow-Origin (a flag, not a finding; fine for a public read-only API)")
    elif "evil.example" in acao:
        rep.add("FAIL", "class 4: the foreign Origin was reflected back unchecked")
    else:
        rep.add("PASS", "class 4: Access-Control-Allow-Origin names %s" % acao)


def audit_url(url, rep):
    check_headers(url, rep)
    check_exposed(url, rep)
    check_cors(url, rep)


# ------------------------------------------------------------ ledger --
def record(target, rep, note):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _ledger
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    if not os.path.isfile(LEDGER):
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write(HEADER)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "%s | %s | %s | PASS %d | WARN %d | FAIL %d | %s" % (
        stamp, workstation(), target, rep.counts["PASS"], rep.counts["WARN"], rep.counts["FAIL"],
        note.strip().replace("\n", " ") or "-")
    added = _ledger.append_unless_identical(LEDGER, line, payload_from_col=2)
    print(("recorded: " if added else "unchanged, not re-recorded: ") + line)
    return added


# ------------------------------------------------------------ selftest --
class _Bad(http.server.SimpleHTTPRequestHandler):
    """Serves its folder as is: no headers, .env and .git reachable, CORS wildcard with credentials."""
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, *a):
        pass


class _Good(http.server.BaseHTTPRequestHandler):
    """Root answers with the headers; every other path is 404; no CORS header."""
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Strict-Transport-Security", "max-age=63072000")
            self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=()")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    do_HEAD = do_GET

    def log_message(self, *a):
        pass


def _serve(handler, directory=None):
    if directory:
        class H(handler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=directory, **k)
        handler = H
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def _selftest():
    import io
    fails = 0

    def ok(label, cond):
        nonlocal fails
        fails += 0 if cond else 1
        print(("PASS  " if cond else "FAIL  ") + label)

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "node_modules", "x"))
        with open(os.path.join(td, "node_modules", "x", "a.js"), "w") as fh:
            fh.write("var k = 'sk_live_ABCDEFGHIJKLMNOP';\n")
        with open(os.path.join(td, "bundle.js"), "w") as fh:
            fh.write("var a = 1;\nvar key = 'sk_live_ABCDEFGHIJKLMNOP';\nvar r = 'service_role';\n")
        with open(os.path.join(td, "clean.js"), "w") as fh:
            fh.write("export const anon = 'pk_live_publishable_is_fine';\nconst url = 'https://x.supabase.co';\n")
        with open(os.path.join(td, ".env"), "w") as fh:
            fh.write("VITE_SUPABASE_SERVICE_ROLE_KEY=abc\n")
        rep = Report(out=io.StringIO())
        hits = scan_dir(td, rep)
        ok("class 1 finds the stripe key and service_role in the bundle", hits >= 2 and rep.counts["FAIL"] >= 2)
        ok("class 1 flags a private env name behind a public prefix", any("bundled private env name" in l for l in rep.lines))
        ok("class 1 names file, line and pattern, never the secret", all("ABCDEFGHIJKLMNOP" not in l for l in rep.lines)
           and any("bundle.js line 2" in l for l in rep.lines))
        ok("class 1 skips node_modules", not any("node_modules" in l for l in rep.lines))
        rep2 = Report(out=io.StringIO())
        with tempfile.TemporaryDirectory() as clean:
            with open(os.path.join(clean, "app.js"), "w") as fh:
                fh.write("console.log('hello');\n")
            ok("class 1 clean tree is one PASS", scan_dir(clean, rep2) == 0 and rep2.counts["PASS"] == 1)

        # the bad server: the temp dir served raw, with .env and .git/HEAD inside
        os.makedirs(os.path.join(td, ".git"))
        with open(os.path.join(td, ".git", "HEAD"), "w") as fh:
            fh.write("ref: refs/heads/main\n")
        with open(os.path.join(td, "index.html"), "w") as fh:
            fh.write("<html></html>")
        srv, base = _serve(_Bad, td)
        try:
            bad = Report(out=io.StringIO())
            audit_url(base + "/", bad)
        finally:
            srv.shutdown()
            srv.server_close()
        ok("class 2 missing HSTS, CSP and frame rule are three FAILs",
           sum(1 for l in bad.lines if l.startswith("FAIL") and "class 2" in l) == 3)
        ok("class 3 /.git/HEAD served is a FAIL naming the repo", any("/.git/HEAD -> 200" in l and "history" in l for l in bad.lines))
        ok("class 3 /.env served is a FAIL", any("/.env -> 200" in l for l in bad.lines))
        ok("class 3 an absent path is a PASS", any("/backup.zip -> 404" in l and l.startswith("PASS") for l in bad.lines))
        ok("class 4 wildcard with credentials is a FAIL", any("wildcard origin WITH credentials" in l for l in bad.lines))

    srv, base = _serve(_Good)
    try:
        good = Report(out=io.StringIO())
        audit_url(base + "/", good)
    finally:
        srv.shutdown()
        srv.server_close()
    ok("class 2 a CSP frame-ancestors counts as the frame rule", any("x-frame-options present" in l for l in good.lines))
    ok("class 2-4 the good server has zero FAILs", good.counts["FAIL"] == 0)
    ok("class 3 every path 404 on the good server", sum(1 for l in good.lines if "class 3" in l and l.startswith("PASS")) == len(EXPOSED_PATHS))
    ok("class 4 no CORS header is a PASS", any("no Access-Control-Allow-Origin" in l for l in good.lines))
    ok("an unreachable url is a FAIL, not a crash", Report(out=io.StringIO()) is not None and
       (lambda r: (check_headers("http://127.0.0.1:9/", r), r.counts["FAIL"] == 1)[1])(Report(out=io.StringIO())))
    ok("summary line carries the three counts", good.summary().startswith("PASS ") and "| FAIL 0" in good.summary())
    print("security_audit selftest: %d failed" % fails)
    return 1 if fails else 0


# ------------------------------------------------------------ main --
def main(argv):
    if "--selftest" in argv:
        return _selftest()
    rep = Report()
    target = []
    if "--dir" in argv:
        d = argv[argv.index("--dir") + 1]
        if not os.path.isdir(d):
            sys.exit("--dir needs a folder (the production build output)")
        scan_dir(d, rep)
        target.append("dir " + os.path.basename(os.path.abspath(d)))
    if "--url" in argv:
        u = argv[argv.index("--url") + 1]
        if not u.startswith("http"):
            sys.exit("--url needs a full URL, https://...")
        print("read-only audit of %s (your own deployment; SECURITY_METHOD.md rule 6)" % u)
        audit_url(u, rep)
        target.append(u)
    if target:
        print("SECURITY AUDIT: " + rep.summary())
    if "--record" in argv:
        i = argv.index("--record")
        note = argv[i + 1] if i + 1 < len(argv) else ""
        if not note:
            sys.exit("--record needs a note in quotes (the hand-walked verdict for classes 5-8, keys rotated)")
        record(", ".join(target) or "hand-walked only", rep, note)
    if not target and "--record" not in argv:
        print(__doc__.split("\n\n")[1])
        return 2
    return 1 if rep.counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
