"""Workstation survey: is THIS machine up to par with WORKSTATION.md?

Usage:
  python tools/workstation_survey.py            # HAVE / MISSING table + one ledger line
  python tools/workstation_survey.py --no-ledger

Prints one line per requirement from the CHECKS table (a mirror of the
"What a workstation needs" section in WORKSTATION.md - keep the two in
step), then appends a summary line to docs/history/workstation_runs.txt.
Exit 1 when any REQUIRED item is missing so run_all's check group stops.

The WORKSTATION RULE (Mazhron 2026-09-06): a new machine is set up FROM
WORKSTATION.md, and whatever a machine gains (a package, a tool, a path)
is added to that document in the same batch. This script is the probe
that proves the document and the machine agree.

Portable twin: WORKSTATION_METHOD.md (kit) + reference tools copy.
See also: docs/systems/tooling.md "The workstation survey"; WORKFLOWS.md
"Bring a new workstation up to par".
"""
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "history", "workstation_runs.txt")
HOME = os.path.expanduser("~")
APPDATA = os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
PF = os.environ.get("ProgramFiles", r"C:\Program Files")
PF86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")


def ws_name():
    # WS1 = Owner, WS2 = Travis (the two known machines); else the user name.
    user = os.environ.get("USERNAME", "?")
    return {"Owner": "WS1", "Travis": "WS2"}.get(user, user)


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                           shell=isinstance(cmd, str))
        out = (r.stdout + r.stderr).strip().splitlines()
        return out[0] if out else ""
    except Exception:
        return ""


def ver(cmd, pattern=r"(\d+\.\d+(?:\.\d+)?)"):
    line = run(cmd)
    m = re.search(pattern, line)
    return m.group(1) if m else ""


def first_existing(paths):
    for p in paths:
        for hit in glob.glob(p):
            if os.path.exists(hit):
                return hit
    return ""


def steam_libraries():
    libs = [os.path.join(PF86, "Steam")]
    vdf = os.path.join(PF86, "Steam", "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        with open(vdf, encoding="utf-8", errors="replace") as f:
            libs += [p.replace("\\\\", "\\") for p in
                     re.findall(r'"path"\s+"([^"]+)"', f.read())]
    return libs


def pip_has(pkg):
    line = run([sys.executable, "-m", "pip", "show", pkg])
    return line.startswith("Name:")


def godot_exe():
    cands = [os.environ.get("EVERWOOD_GODOT", ""),
             os.path.join(HOME, "Desktop", "GoDot", "Godot_v4.4-stable_win64_console.exe")]
    return first_existing([c for c in cands if c])


def godot_templates():
    d = os.path.join(APPDATA, "Godot", "export_templates", "4.4.stable")
    need = ["windows_release_x86_64.exe", "web_release.zip"]
    return d if all(os.path.exists(os.path.join(d, n)) for n in need) else ""


def vscode_ext(ext_id):
    return first_existing([os.path.join(HOME, ".vscode", "extensions", ext_id + "-*")])


# (label, required, probe -> detail string or "" when missing)
CHECKS = [
    ("Python 3.12+ (tools/, hooks)", True,
     lambda: ver([sys.executable, "--version"]) if sys.version_info >= (3, 12) else ""),
    ("pip: Pillow (slicers, montages, icon)", True,
     lambda: "ok" if pip_has("Pillow") else ""),
    ("pip: numpy (art repair tools)", True,
     lambda: "ok" if pip_has("numpy") else ""),
    ("Node.js (design-web exporters: node --check)", True,
     lambda: ver("node --version")),
    ("Git (+ Git Bash for the hook command form)", True,
     lambda: ver("git --version")),
    ("git user.name / user.email set", True,
     lambda: run("git config --global user.name") or ""),
    ("Godot 4.4 console exe (Desktop/GoDot or EVERWOOD_GODOT)", True, godot_exe),
    ("Godot 4.4 export templates (windows x86_64 + web release)", True, godot_templates),
    ("Builds folder ../Everwood - Builds", True,
     lambda: first_existing([os.path.join(ROOT, "..", "Everwood - Builds")])),
    ("VS Code", True,
     lambda: ver("code --version")),
    ("VS Code ext: anthropic.claude-code", True,
     lambda: vscode_ext("anthropic.claude-code")),
    ("VS Code ext: geequlim.godot-tools", False,
     lambda: vscode_ext("geequlim.godot-tools")),
    (".claude/settings.json (the hooks)", True,
     lambda: first_existing([os.path.join(ROOT, ".claude", "settings.json")])),
    ("Rootstock kit repo clone (../../../rootstock-os)", False,
     lambda: first_existing([os.path.join(ROOT, "..", "..", "..", "rootstock-os", ".git")])),
    ("GIMP 2.10 (palettes, .xcf; per-machine, gitignored)", False,
     lambda: first_existing([os.path.join(PF, "GIMP 2", "bin", "gimp-2.10.exe"),
                             os.path.join(PF, "GIMP 3", "bin", "gimp-3*.exe")])),
    ("Aseprite (Steam; sprite sheets, .aseprite sources)", False,
     lambda: first_existing([os.path.join(l, "steamapps", "common", "Aseprite", "Aseprite.exe")
                             for l in steam_libraries()])),
    ("Blender (pinned: seamless tiles)", False,
     lambda: first_existing([os.path.join(PF, "Blender Foundation", "Blender*")])),
    ("7-Zip (inspecting build zips by hand)", False,
     lambda: first_existing([os.path.join(PF, "7-Zip", "7z.exe")])),
]


def main():
    ws = ws_name()
    missing_req, missing_opt = [], []
    print("WORKSTATION SURVEY - %s (%s)" % (ws, os.environ.get("COMPUTERNAME", "?")))
    for label, required, probe in CHECKS:
        try:
            detail = probe() or ""
        except Exception as e:  # a probe must never kill the survey
            detail = ""
        status = "HAVE   " if detail else ("MISSING" if required else "absent ")
        print("  %s  %-58s %s" % (status, label, detail if detail not in ("ok",) else ""))
        if not detail:
            (missing_req if required else missing_opt).append(label)
    n = len(CHECKS)
    have = n - len(missing_req) - len(missing_opt)
    summary = "%d/%d present | missing required: %s | optional absent: %s" % (
        have, n, ", ".join(missing_req) or "none", ", ".join(missing_opt) or "none")
    print("\n" + summary)
    if "--no-ledger" not in sys.argv:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write("%s | %s | %s\n" % (stamp, ws, summary))
    if missing_req:
        print("\nUP TO PAR: NO - install the missing items per WORKSTATION.md, then re-run.")
        sys.exit(1)
    print("\nUP TO PAR: YES")


if __name__ == "__main__":
    main()
