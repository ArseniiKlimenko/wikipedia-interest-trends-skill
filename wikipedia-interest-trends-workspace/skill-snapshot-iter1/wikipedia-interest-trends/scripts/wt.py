#!/usr/bin/env python3
"""Launcher for the wikitrends CLI (standard library only, Python >= 3.9).

On first use it creates an isolated virtual environment with the pinned
dependencies from ../requirements.txt, then runs `python -m wikitrends` inside it.
Later calls reuse the environment, so every command is just:

    python3 scripts/wt.py <command> [options]

Environment variables:
  WIKITRENDS_HOME     where the venv and the data cache live (default ~/.cache/wikitrends)
  WIKITRENDS_CONTACT  email or URL sent in the User-Agent, as Wikimedia asks
  WIKITRENDS_NO_VENV  set to 1 to run with the current interpreter (deps preinstalled)
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = SKILL_DIR / "requirements.txt"


def _writable_home() -> Path:
    candidates = [
        os.environ.get("WIKITRENDS_HOME"),
        os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "wikitrends"),
        str(SKILL_DIR / ".wikitrends"),
        os.path.join(tempfile.gettempdir(), "wikitrends"),
    ]
    for cand in candidates:
        if not cand:
            continue
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".write-test")
            with open(probe, "w") as fh:
                fh.write("ok")
            os.remove(probe)
            return Path(cand)
        except OSError:
            continue
    sys.exit("wt: no writable directory for the environment and cache; set WIKITRENDS_HOME")


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _run(cmd):
    result = subprocess.run([str(c) for c in cmd], stdout=sys.stderr, stderr=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError("command failed: " + " ".join(str(c) for c in cmd))


def _ensure_env(home: Path) -> Path:
    tag = "py%d%d-%s" % (sys.version_info[0], sys.version_info[1],
                         hashlib.sha1(REQUIREMENTS.read_bytes()).hexdigest()[:10])
    venv = home / ("venv-" + tag)
    ready = venv / ".ready"
    if ready.exists():
        return _venv_python(venv)

    lock = home / ("venv-" + tag + ".lock")
    deadline = time.time() + 900
    while True:  # cross-process lock so parallel first runs do not collide
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 900:
                    os.rmdir(lock)
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                sys.exit("wt: timed out waiting for another process to finish installing dependencies")
            time.sleep(1)
    try:
        if not ready.exists():
            print("wt: first run - installing pinned dependencies into %s (about 1 minute)..." % venv,
                  file=sys.stderr)
            shutil.rmtree(venv, ignore_errors=True)
            uv = shutil.which("uv")
            try:
                if uv:
                    _run([uv, "venv", "-q", "--python", sys.executable, venv])
                    _run([uv, "pip", "install", "-q", "--python", _venv_python(venv), "-r", REQUIREMENTS])
                else:
                    _run([sys.executable, "-m", "venv", venv])
                    _run([_venv_python(venv), "-m", "pip", "install", "-q",
                          "--disable-pip-version-check", "-r", REQUIREMENTS])
            except RuntimeError as exc:
                shutil.rmtree(venv, ignore_errors=True)
                sys.exit("wt: could not install dependencies (%s). Check network access to PyPI, "
                         "or install requirements.txt yourself and set WIKITRENDS_NO_VENV=1." % exc)
            ready.touch()
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass
    return _venv_python(venv)


def main() -> None:
    if sys.version_info < (3, 9):
        sys.exit("wt: Python 3.9 or newer is required")
    home = _writable_home()
    env = dict(os.environ)
    env["WIKITRENDS_HOME"] = str(home)
    env["PYTHONPATH"] = str(SKILL_DIR / "scripts") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env.setdefault("MPLCONFIGDIR", str(home / "matplotlib"))
    env.setdefault("PYTHONIOENCODING", "utf-8")
    python = Path(sys.executable) if env.get("WIKITRENDS_NO_VENV") == "1" else _ensure_env(home)
    result = subprocess.run([str(python), "-m", "wikitrends"] + sys.argv[1:], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
